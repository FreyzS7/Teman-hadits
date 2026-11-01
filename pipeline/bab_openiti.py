#!/usr/bin/env python3
"""Judul kitab & bab berbahasa Arab dari teks OpenITI, dipetakan ke riwayat kita MENURUT ISI.

Masukan : sources/openiti-*/... (lihat sources.json), build/teman-hadits.sqlite
Keluaran: build/bab.sqlite
  riwayat_bab(riwayat_id, kitab_ar, bab_ar, skor, cara, no_openiti)
  kitab_nama(kitab_id, bab_no, nama_ar, setuju, total)   -- nama Arab untuk "kitab" (section) fawazahmed0
  info(kitab_id, kunci, nilai)

Cara:
  1. Urai berkas OpenITI: setiap baris "### " diklasifikasi menjadi kitab / bab / penanda hadits / halaman.
     Teks di antara penanda menjadi "blok", membawa judul kitab & bab terakhir.
  2. Setiap riwayat kita dicocokkan ke blok yang paling memuat teksnya (2-gram berbobot IDF, seperti
     takhrij). Cocok bila >= 70% bobot 2-gram riwayat ada di blok. Nomor penomoran tidak dipakai untuk
     mencocokkan, hanya untuk MENGUJI hasilnya.
  3. Riwayat yang tidak cocok mendapat judul dari tetangganya hanya bila riwayat sebelum & sesudahnya
     berada di bab yang sama (cara = "urutan").
  4. Nama Arab tiap "kitab" fawazahmed0 = judul kitab OpenITI yang paling banyak dimiliki riwayat di dalamnya.

Uji (dilaporkan, juga di test_bab.py):
  - urutan: blok yang cocok untuk riwayat berurutan harus naik;
  - nomor: bila blok OpenITI bernomor, nomornya sama dengan nomor standar riwayat;
  - kesepakatan kitab: berapa % riwayat dalam satu kitab fawazahmed0 sepakat pada satu judul kitab OpenITI.

Jalankan:  python3 pipeline/bab_openiti.py
"""
import collections
import json
import math
import os
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, SRC, norm_ar
from hadeethenc import grams

OUT = os.path.join(BUILD, "bab.sqlite")
BERKAS = {
    "bukhari": "openiti-0275AH/0256Bukhari.Sahih.Shamela0001681-ara1",
    "muslim": "openiti-0275AH/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown",
    "abudawud": "openiti-0275AH/0275AbuDawudSijistani.Sunan.Shamela0001726-ara1",
    "ibnumajah": "openiti-0275AH/0273IbnMaja.Sunan.Shamela0001198-ara1",
    "tirmidzi": "openiti-0300AH/0279Tirmidhi.Sunan.Shamela0007895-ara2",
    "nasai": "openiti-0325AH/0303Nasai.SunanSughra.Shamela0000829-ara1",
    "malik": "openiti-0200AH/0179MalikIbnAnas.Muwatta.Shamela0001699-ara1.completed",
}
AMBANG = 0.7
_GLOSARIUM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "glosarium_kitab.json"), encoding="utf8"))
_GLOS = {norm_ar(k): v for k, v in _GLOSARIUM["nama"].items()}


def nama_indonesia(kitab_ar):
    """'كتاب البيوع' -> 'Kitab Jual Beli'; 'أبواب الطهارة عن رسول الله…' -> 'Bab-bab Thaharah (Bersuci)'.
    None bila tidak ada di glosarium (glosarium disusun Teman Hadits, belum ditinjau)."""
    if not kitab_ar:
        return None
    n = norm_ar(kitab_ar)
    awal = "Kitab " if n.startswith("كتاب") else "Bab-bab " if n.startswith("ابواب") else ""
    inti = re.sub(r"^(كتاب|ابواب)\s+", "", n)
    inti = re.sub(r"\s*عن رسول الله.*$", "", inti).strip()
    v = _GLOS.get(inti)
    return (awal + v) if v else None
_ANGKA_TIMUR = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NOMOR_SAJA = re.compile(r"^\s*\(?\s*([0-9٠-٩]+)\s*\)?\s*[-–]?\s*$")
_AWALAN_NOMOR = re.compile(r"^\s*(?:\(?\s*[0-9٠-٩]+\s*\)?\s*[-–]?\s*)+")
_SAMPAH = re.compile(r"ms\d+|PageV\d+P\d+|\[ص:\s*\d+\]")


def bersihkan_judul(t):
    t = _SAMPAH.sub(" ", t)
    t = re.sub(r"[\"“”]+", "", t)
    return re.sub(r"\s+", " ", t).strip(" :.-–،")


# Judul tingkat kitab. "أبواب" hanya tingkat kitab di Jami' at-Tirmidzi; di Abu Dawud ia sub-bagian
# di dalam kitab (mis. "أبواب قيام الليل" di dalam كتاب الصلاة), jadi tidak boleh menimpa nama kitab.
AWALAN_KITAB = {"tirmidzi": ("كتاب", "ابواب")}


def urai(path, kid=None):
    """Kembalikan daftar blok: {kitab, bab, no, teks}."""
    awalan = AWALAN_KITAB.get(kid, ("كتاب",))
    blok, kitab, bab, no, teks = [], None, None, None, []

    def tutup():
        if teks:
            blok.append({"kitab": kitab, "bab": bab, "no": no, "teks": " ".join(teks)})

    for baris in open(path, encoding="utf8"):
        baris = baris.rstrip("\n")
        if baris.startswith("#META#") or baris.startswith("######"):
            continue
        if baris.startswith("### "):
            m = re.match(r"^### (\|+|\$)\s*(.*)$", baris)
            if not m:
                continue
            isi = m.group(2)
            if re.search(r"\[ص\s*:", isi) and len(norm_ar(re.sub(r"\[ص\s*:[^\]]*\]", " ", _SAMPAH.sub(" ", isi)))) < 5:
                continue                                  # penanda halaman cetak: bukan batas hadits/bab
            polos = norm_ar(_AWALAN_NOMOR.sub("", isi))
            mn = _NOMOR_SAJA.match(isi)
            if mn:                                         # "### | 12 - " = awal hadits bernomor
                tutup()
                teks, no = [], int(mn.group(1).translate(_ANGKA_TIMUR))
                continue
            if polos.startswith(awalan) or polos == "بد الوحي" or polos.startswith("مقدمه الامام"):   # hamzah sudah dibuang norm_ar
                tutup()
                teks, no = [], None
                kitab, bab = bersihkan_judul(_AWALAN_NOMOR.sub("", isi)), None
                continue
            if m.group(1) == "$" and len(polos.split()) > 12:   # Muslim: "### $ وحدثنا ..." = awal hadits
                tutup()
                teks, no = [isi], None
                continue
            if len(polos.split()) <= 60 and polos:         # judul bab (dengan/tanpa kata "باب")
                tutup()
                teks, no = [], None
                bab = bersihkan_judul(_AWALAN_NOMOR.sub("", isi))
                continue
            teks.append(isi)
        elif baris.startswith("# ") or baris.startswith("~~"):
            teks.append(baris.lstrip("#~ "))
    tutup()
    return blok


def petakan(kid, blok, riwayat):
    """riwayat: list (id, arab, no_standar, bab_no) urut. Kembalikan dict id -> (i_blok, skor)."""
    gb = [grams(norm_ar(_SAMPAH.sub(" ", b["teks"]))) for b in blok]
    gr = {rid: grams(norm_ar(ar)) for rid, ar, _, _ in riwayat}
    df = collections.Counter()
    for g in gr.values():
        df.update(g)
    N = max(1, len(gr))
    post = collections.defaultdict(list)
    for i, g in enumerate(gb):
        for x in g:
            if df.get(x, 0) <= 40:
                post[x].append(i)
    kandidat = {}
    for rid, _, _, _ in riwayat:
        g = gr[rid]
        if len(g) < 4:
            continue
        bobot = {x: math.log(N / (1 + df[x])) + 0.1 for x in g}
        total = sum(bobot.values())
        cand = collections.Counter()
        for x in sorted(g, key=lambda x: df[x])[:20]:
            for i in post.get(x, ()):
                cand[i] += 1
        skor = [(sum(bobot[x] for x in g & gb[i]) / total, i) for i, _ in cand.most_common(30)]
        skor = [(s, i) for s, i in skor if s >= AMBANG]
        if skor:
            top = max(s for s, _ in skor)
            # semua blok yang hampir sama baiknya: teks yang diulang penyusun (umum di al-Bukhari)
            kandidat[rid] = [(i, s) for s, i in skor if s >= top - 0.03]
    # Pilih kandidat yang paling dekat dengan posisi tetangga yang tidak ambigu (urutan kitab).
    urut = [rid for rid, *_ in riwayat if rid in kandidat]
    pasti = [(k, kandidat[rid][0][0]) for k, rid in enumerate(urut) if len(kandidat[rid]) == 1]
    import bisect
    kunci = [k for k, _ in pasti]
    hasil = {}
    for k, rid in enumerate(urut):
        c = kandidat[rid]
        if len(c) == 1:
            hasil[rid] = (c[0][0], round(c[0][1], 3))
            continue
        j = bisect.bisect_left(kunci, k)
        tetangga = [pasti[x][1] for x in range(max(0, j - 3), min(len(pasti), j + 3))]
        harapan = sorted(tetangga)[len(tetangga) // 2] if tetangga else c[0][0]
        i, s = min(c, key=lambda x: (abs(x[0] - harapan), -x[1]))
        hasil[rid] = (i, round(s, 3))
    return hasil


def main():
    t0 = time.time()
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE riwayat_bab (riwayat_id TEXT PRIMARY KEY, kitab_ar TEXT, bab_ar TEXT, skor REAL, cara TEXT, no_openiti INT, kitab_nama_id TEXT);
    CREATE TABLE kitab_nama (kitab_id TEXT, bab_no INT, nama_ar TEXT, setuju INT, total INT, nama_id TEXT, PRIMARY KEY (kitab_id, bab_no));
    CREATE TABLE info (kitab_id TEXT, kunci TEXT, nilai TEXT);
    """)
    for kid, rel in BERKAS.items():
        blok = urai(os.path.join(SRC, rel), kid)
        riwayat = src.execute(
            "SELECT id, arab, no_standar, bab_no FROM riwayat WHERE kitab_id=? AND tingkat IN ('A','B') "
            "ORDER BY CAST(no_standar AS REAL)", (kid,)).fetchall()
        peta = petakan(kid, blok, riwayat)
        # isi celah dari tetangga bila keduanya di bab yang sama
        urut = [rid for rid, *_ in riwayat]
        cara = {rid: "teks" for rid in peta}
        akhir = dict(peta)
        for k, rid in enumerate(urut):
            if rid in akhir:
                continue
            a = next((akhir[urut[j]] for j in range(k - 1, -1, -1) if urut[j] in akhir), None)
            b = next((akhir[urut[j]] for j in range(k + 1, len(urut)) if urut[j] in akhir), None)
            if a and b and blok[a[0]]["bab"] == blok[b[0]]["bab"] and blok[a[0]]["kitab"] == blok[b[0]]["kitab"]:
                akhir[rid], cara[rid] = (a[0], 0.0), "urutan"
        for rid, (i, s) in akhir.items():
            b = blok[i]
            db.execute("INSERT INTO riwayat_bab VALUES (?,?,?,?,?,?,?)",
                       (rid, b["kitab"], b["bab"], s, cara[rid], b["no"], nama_indonesia(b["kitab"])))

        # uji: urutan & nomor
        idx = [peta[rid][0] for rid in urut if rid in peta]
        naik = sum(1 for x, y in zip(idx, idx[1:]) if y >= x)
        nomor_dicek = nomor_sama = 0
        no_std = {rid: nos for rid, _, nos, _ in riwayat}
        for rid, (i, _) in peta.items():
            if blok[i]["no"] is not None and no_std[rid] and re.fullmatch(r"\d+", str(no_std[rid])):
                nomor_dicek += 1
                nomor_sama += blok[i]["no"] == int(no_std[rid])
        # nama Arab per "kitab" fawazahmed0 (bab_no di data kita) = judul kitab OpenITI terbanyak
        per_bagian = collections.defaultdict(collections.Counter)
        for rid, _, _, bno in riwayat:
            if rid in akhir and blok[akhir[rid][0]]["kitab"]:
                per_bagian[bno][blok[akhir[rid][0]]["kitab"]] += 1
        setuju = total = 0
        for bno, c in per_bagian.items():
            nama, n = c.most_common(1)[0]
            jml = sum(c.values())
            setuju += n
            total += jml
            # Nama hanya bila mayoritas jelas (>= 60%). Bagian "0" Muslim di fawazahmed0 misalnya adalah
            # tampungan riwayat tanpa nomor kitab yang tersebar di seluruh kitab — tidak punya satu nama.
            jelas = n / jml >= 0.6
            db.execute("INSERT INTO kitab_nama VALUES (?,?,?,?,?,?)",
                       (kid, bno, nama if jelas else None, n, jml, nama_indonesia(nama) if jelas else None))
        info = {"blok": len(blok), "riwayat": len(riwayat), "cocok_teks": len(peta),
                "dari_urutan": sum(1 for c in cara.values() if c == "urutan"),
                "urutan_naik": f"{naik}/{max(1, len(idx) - 1)}", "nomor_sama": f"{nomor_sama}/{nomor_dicek}",
                "kesepakatan_kitab": f"{setuju}/{total}"}
        db.executemany("INSERT INTO info VALUES (?,?,?)", [(kid, k, str(v)) for k, v in info.items()])
        db.commit()
        print(f"{kid:10s} blok {len(blok):5d} | cocok {len(peta):5d}/{len(riwayat)} (+{info['dari_urutan']} urutan) | "
              f"urutan naik {info['urutan_naik']} | nomor sama {info['nomor_sama']} | kitab sepakat {info['kesepakatan_kitab']} "
              f"({time.time() - t0:.0f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
