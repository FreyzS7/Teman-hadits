#!/usr/bin/env python3
"""Verifikasi sampel acak terhadap KITAB CETAK: teks OCR dari scan cetakan di archive.org (digitalisasi yang terpisah
dari teks OpenITI yang kita pakai). Yang diperiksa adalah isi yang TAMPIL di situs.

  - Taqrib at-Tahdzib (cetakan 'Awwamah, Dar ar-Rasyid; sama dengan edisi sumber kita): frasa penilaian, tabaqah,
    tahun wafat (kata bilangan), dan ada-tidaknya entri itu di cetakan.
  - al-Maqashid al-Hasanah (cetakan tahqiq al-Khusyt; sama dengan sumber) dan Kasyf al-Khafa' (cetakan al-Qudsi
    1351 H; sama dengan sumber): judul entri dan kata kunci penilaian yang ditampilkan situs.

Cara: entri dicari di teks OCR dengan pemungutan suara pasangan-kata (toleran salah OCR), lalu setiap butir dicek di
jendela itu dengan toleransi satu huruf. OCR bahasa Arab tidak sempurna, jadi "tidak terbaca" BUKAN berarti salah;
yang dihitung sebagai beda hanya bila jendela ditemukan dengan yakin tetapi isinya berlainan.
Nomor entri tidak diperiksa di sini: OCR mengacaukan angka Arab-Hindi di kolom nomor. Pemeriksaan visual halaman
(scan) menunggu akses ke server unduhan archive.org (lihat docs/13-verifikasi-cetak.md).

Jalankan:  python3 -I pipeline/verifikasi_cetak.py   -> build/verifikasi_cetak.json
"""
import collections
import hashlib
import html
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, norm_ar

DIR = os.path.join(BUILD, "cetak")
CETAK = {   # buku: (identifier archive.org, berkas OCR, keterangan cetakan)
    "taqrib": ("alfirdwsiy2018_gmail_1957", "1957 - تقريب التهذيب - عوامة  كتاب اقرا  اونلاين   _djvu.txt",
               "Taqrib at-Tahdzib, tahqiq Muhammad 'Awwamah, Dar ar-Rasyid"),
    "maqashid": ("20260220_20260220_0309", "المقاصد الحسنة في بيان كثير من الأحاديث المشتهرة على الألسنة - ت الخشت_djvu.txt",
                 "al-Maqashid al-Hasanah, tahqiq Muhammad 'Utsman al-Khusyt"),
    "kasyf": ("AAlexandrina-141236", "141236_كشف_الخفاء_ومزيل_الالباس_عما_اشتهر_من_الاحاديث_عل_الناس_djvu.txt",
              "Kasyf al-Khafa', Maktabah al-Qudsi, Kairo 1351-1352 H (scan Bibliotheca Alexandrina)"),
}
BENIH = 20261101


def ocr(buku):
    """Teks OCR cetakan (diunduh sekali lewat halaman /stream/ archive.org)."""
    os.makedirs(DIR, exist_ok=True)
    p = os.path.join(DIR, buku + ".txt")
    if not os.path.exists(p):
        ident, berkas, _ = CETAK[buku]
        url = f"https://archive.org/stream/{ident}/{urllib.parse.quote(berkas)}"
        t = subprocess.run(["curl", "-sfL", url], capture_output=True, check=True).stdout.decode("utf8", "replace")
        m = re.search(r"<pre[^>]*>(.*?)</pre>", t, re.S)
        open(p, "w", encoding="utf8").write(html.unescape(m.group(1)) if m else "")
    return open(p, encoding="utf8").read()


def kata(t):
    return [w for w in norm_ar(t).split() if len(w) > 1]


def mirip(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) < 4 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    p, q = (a, b) if len(a) < len(b) else (b, a)
    return any(q[:i] + q[i + 1:] == p for i in range(len(q)))


class Cetak:
    def __init__(self, buku):
        self.w = kata(ocr(buku))
        self.idx = collections.defaultdict(list)
        for i in range(len(self.w) - 1):
            self.idx[self.w[i] + " " + self.w[i + 1]].append(i)

    def cari(self, teks, n=24):
        """Posisi awal jendela terbaik + skor (bagian pasangan-kata teks yang ada di jendela)."""
        k = kata(teks)[:n]
        g = [(j, k[j] + " " + k[j + 1]) for j in range(len(k) - 1)]
        suara = collections.Counter()
        for j, x in g:
            pos = self.idx.get(x, [])
            if len(pos) > 300:          # pasangan terlalu umum ("بن عبد"): tidak membedakan
                continue
            for p in pos:
                suara[(p - j) // 6] += 1
        if not suara:
            return None, 0.0
        ember = max(suara, key=suara.get)
        awal = max(0, ember * 6 - 6)
        jendela = self.w[awal:awal + len(k) + 40]
        gj = {jendela[i] + " " + jendela[i + 1] for i in range(len(jendela) - 1)}
        return awal, sum(1 for _, x in g if x in gj) / max(1, len(g))

    def ada(self, awal, frasa, lebar=90):
        """Bagian kata frasa yang ada di jendela (toleran 1 huruf)."""
        jendela = self.w[awal:awal + lebar]
        k = kata(frasa)
        return sum(1 for x in k if any(mirip(x, y) for y in jendela)) / max(1, len(k))


def nilai_ambang(c, contoh):
    """Skor 'nol': teks yang diacak urutan katanya; ambang = di atas 99% skor nol."""
    rnd = random.Random(1)
    nol = []
    for t in contoh:
        k = kata(t)[:24]
        rnd.shuffle(k)
        nol.append(c.cari(" ".join(k))[1])
    nol.sort()
    return max(0.3, nol[int(len(nol) * 0.99) - 1] + 0.05) if nol else 0.3


def main():
    rnd = random.Random(BENIH)
    hasil = {"benih": BENIH, "cetakan": {b: {"archive_org": CETAK[b][0], "keterangan": CETAK[b][2]} for b in CETAK}, "butir": []}
    pr = sqlite3.connect(os.path.join(BUILD, "perawi.sqlite"))
    # --- Taqrib: 80 perawi yang tampil di situs --------------------------------------------------------------
    c = Cetak("taqrib")
    hasil["cetakan"]["taqrib"]["sha256_ocr"] = hashlib.sha256(open(os.path.join(DIR, "taqrib.txt"), "rb").read()).hexdigest()
    rows = pr.execute("SELECT id, taqrib, teks_taqrib, penilaian, tabaqah, wafat, rumuz FROM perawi WHERE taqrib IS NOT NULL ORDER BY taqrib").fetchall()
    sampel = rnd.sample(rows, 80)
    ambang = nilai_ambang(c, [r[2] for r in sampel])
    r_ = sqlite3.connect(os.path.join(BUILD, "rijal.sqlite"))
    for pid, no, teks, penilaian, tabaqah, wafat, rumuz in sampel:
        awal, skor = c.cari(teks)
        b = {"buku": "taqrib", "id": pid, "no": no, "skor": round(skor, 2), "ditemukan": skor >= ambang, "cek": {}}
        if b["ditemukan"]:
            if penilaian:
                b["cek"]["penilaian"] = round(c.ada(awal, penilaian.replace("…", "")), 2)
            m = re.search(r"من (?:\S+ )?(?:الطبقه )?(الحاديه عشره|الثانيه عشره|\S+)", norm_ar(teks)[norm_ar(teks).find(" من "):]) if tabaqah else None
            if tabaqah and m:
                b["cek"]["tabaqah"] = round(c.ada(awal, m.group(1)), 2)
            wt = r_.execute("SELECT wafat_teks FROM taqrib WHERE no=?", (no,)).fetchone()[0]
            if wafat and wt:
                b["cek"]["wafat"] = round(c.ada(awal, " ".join(wt.split()[2:]) if wt.split()[1:2] == ["سنه"] else wt), 2)
        hasil["butir"].append(b)
    hasil["ambang"] = {"taqrib": round(ambang, 2)}
    # --- katalog: 40 entri al-Maqashid, 40 entri Kasyf -----------------------------------------------------------
    kt = sqlite3.connect(os.path.join(BUILD, "katalog.sqlite"))
    for buku in ("maqashid", "kasyf"):
        c = Cetak(buku)
        hasil["cetakan"][buku]["sha256_ocr"] = hashlib.sha256(open(os.path.join(DIR, buku + ".txt"), "rb").read()).hexdigest()
        rows = kt.execute("SELECT id, no, judul_ar, teks_ar, kata_kunci FROM katalog WHERE kitab_id=? AND length(teks_ar) > 80", (buku,)).fetchall()
        sampel = rnd.sample(rows, 40)
        ambang = nilai_ambang(c, [r[3] for r in sampel])
        hasil["ambang"][buku] = round(ambang, 2)
        for eid, no, judul, teks, kk in sampel:
            awal, skor = c.cari(teks)
            b = {"buku": buku, "id": eid, "no": no, "skor": round(skor, 2), "ditemukan": skor >= ambang, "cek": {}}
            if b["ditemukan"]:
                b["cek"]["judul"] = round(c.ada(awal, judul[:120]), 2)
                for k, g, ctx, kelas in json.loads(kk):
                    b["cek"][f"kunci:{g}"] = round(c.ada(max(0, awal - 10), k, lebar=len(kata(teks)) + 60), 2)
            hasil["butir"].append(b)
    # --- ringkasan ------------------------------------------------------------------------------------------
    ring = {}
    for buku in CETAK:
        bs = [b for b in hasil["butir"] if b["buku"] == buku]
        cek = collections.defaultdict(list)
        for b in bs:
            for k, v in b["cek"].items():
                cek[k.split(":")[0]].append(v)
        ring[buku] = {"sampel": len(bs), "ditemukan": sum(b["ditemukan"] for b in bs),
                      **{k: {"dicek": len(v), "cocok_penuh": sum(1 for x in v if x >= 0.99), "cocok_>=0.8": sum(1 for x in v if x >= 0.8)}
                         for k, v in cek.items()}}
    hasil["ringkasan"] = ring
    json.dump(hasil, open(os.path.join(BUILD, "verifikasi_cetak.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(ring, ensure_ascii=False, indent=1))
    print("ambang:", hasil["ambang"])


if __name__ == "__main__":
    main()
