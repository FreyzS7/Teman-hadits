#!/usr/bin/env python3
"""Bangun build/teman-hadits.sqlite dari sumber yang sudah diunduh.

Langkah:
  1. Muat semua baris Lidwa/carihadis (Arab + terjemah Indonesia, penomoran Lidwa).
  2. Muat edisi Arab fawazahmed0 (penomoran standar) + penilaian derajat per ulama.
  3. Cocokkan teks Arab kedua sumber (crosswalk) -> nomor Lidwa <-> nomor standar.
  4. Tentukan status tiap riwayat: tingkat A (2 sumber cocok), B (1 sumber), atau karantina.
  5. Buat indeks pencarian FTS5.

Jalankan:  python3 pipeline/build_db.py
"""
import collections
import json
import os
import sqlite3
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BUILD, DB_PATH, KITAB, SRC, akar_ar, norm_ar, norm_id, rantai_dari_terjemah,
                    read_mysql_dump)

SCHEMA = """
CREATE TABLE kitab (
  id TEXT PRIMARY KEY, nama TEXT, nama_arab TEXT, penyusun TEXT, wafat_h INT,
  sistem_nomor TEXT, jumlah_lidwa INT, jumlah_standar INT
);
CREATE TABLE riwayat (
  id TEXT PRIMARY KEY,           -- contoh: bukhari:1 (nomor standar) / darimi:L12 (nomor Lidwa)
  kitab_id TEXT NOT NULL,
  no_standar TEXT,               -- penomoran fawazahmed0 (= penomoran umum sunnah.com / Fath al-Bari utk Bukhari)
  no_arab TEXT,                  -- 'arabicnumber' fawazahmed0 (mis. penomoran Fu'ad 'Abdul Baqi utk Muslim)
  no_lidwa INT,                  -- penomoran Ensiklopedi Hadits 9 Imam (Lidwa) / carihadis
  bab_no INT, bab_nama TEXT,
  arab TEXT,                     -- teks utama berharakat
  arab_lidwa TEXT,               -- teks Arab dari sumber kedua (untuk pembanding)
  terjemah TEXT,                 -- terjemah Indonesia (Lidwa), dipasangkan dgn arab_lidwa pada baris yg sama
  rantai_json TEXT,              -- nama perawi diekstrak dari [kurung] terjemahan (otomatis, belum diverifikasi)
  kecocokan REAL,                -- skor kemiripan teks Arab 2 sumber (0..1), NULL bila hanya 1 sumber
  tingkat TEXT NOT NULL,         -- 'A' 2 sumber cocok | 'B' 1 sumber | 'K' karantina
  alasan TEXT                    -- alasan karantina / catatan
);
CREATE TABLE penilaian (
  riwayat_id TEXT NOT NULL, penilai TEXT NOT NULL, hukum TEXT NOT NULL, kategori TEXT NOT NULL,
  sumber TEXT NOT NULL
);
CREATE TABLE karantina_berkas (berkas TEXT, baris INT, alasan TEXT);
CREATE INDEX ix_riwayat_kitab ON riwayat(kitab_id);
CREATE INDEX ix_penilaian ON penilaian(riwayat_id);
CREATE VIRTUAL TABLE cari USING fts5(
  riwayat_id UNINDEXED, arab_polos, arab_akar, terjemah_polos, perawi,
  tokenize = 'unicode61 remove_diacritics 2'
);
"""

# Penyeragaman label derajat dari berbagai penilai -> kategori kasar untuk filter.
# Label asli SELALU disimpan & ditampilkan; kategori hanya untuk penyaringan.
def kategori_derajat(g):
    s = g.lower().replace("'", "").replace("’", "")
    if "maudu" in s or "mawdu" in s or "fabricat" in s or "batil" in s:
        return "palsu"
    if "munkar" in s or "shadh" in s or "syadz" in s:
        return "lemah"
    if "daif" in s or "da if" in s or "dhaif" in s or "weak" in s:
        return "lemah"
    if "hasan" in s:
        return "hasan" if "sahih" not in s else "shahih-hasan"
    if "sahih" in s or "saheeh" in s or "sound" in s:
        return "shahih"
    return "lainnya"


def shingles(words, n=3):
    return {zlib.crc32(" ".join(words[i:i + n]).encode()) for i in range(max(1, len(words) - n + 1))}


def crosswalk(L, F):
    """Untuk tiap riwayat standar F[j], cari baris Lidwa L[i] terbaik.

    Kembalikan dict j -> (i, jaccard, containment) dengan containment = bagian teks F yang
    juga ada di L. jaccard tinggi = 1:1; containment tinggi + jaccard rendah = baris Lidwa
    menggabungkan beberapa nomor standar (umum di Shahih Muslim).
    """
    df = collections.Counter()
    post = collections.defaultdict(list)
    for i, l in enumerate(L):
        for h in l["sh"]:
            df[h] += 1
            post[h].append(i)
    out = {}
    for j, f in enumerate(F):
        if not f["sh"]:
            continue
        rare = sorted((h for h in f["sh"] if h in df), key=lambda h: df[h])[:12]
        cand = collections.Counter()
        for h in rare:
            if df[h] <= 60:
                for i in post[h]:
                    cand[i] += 1
        scored = []
        for i, _ in cand.most_common(40):
            a, b = L[i]["sh"], f["sh"]
            inter = len(a & b)
            jac, cont = inter / len(a | b), inter / len(b)
            scored.append(((jac >= 0.85, cont >= 0.9, round(jac, 2)), i, jac, cont))
        if scored:
            top = max(s[0] for s in scored)
            # Simpan semua kandidat yang sama baiknya: teks yang diulang dalam kitab (umum di
            # al-Bukhari) cocok sempurna dengan beberapa baris; pilih berdasarkan urutan di bawah.
            out[j] = [s[1:] for s in scored if s[0] == top]

    # Jangkar urutan: kedua sumber menyusun hadits dengan urutan yang kurang lebih sama.
    # Pilih kandidat terdekat dengan posisi yang diharapkan dari tetangga yang tidak ambigu.
    unik = {j: c[0][0] for j, c in out.items() if len(c) == 1}
    keys = sorted(unik)
    import bisect

    def jangkar(j):
        k = bisect.bisect_left(keys, j)
        near = [unik[keys[x]] for x in range(max(0, k - 8), min(len(keys), k + 8)) if keys[x] != j]
        return sorted(near)[len(near) // 2] if near else None

    hasil = {}
    for j, cands in out.items():
        a = jangkar(j)
        i, jac, cont = min(cands, key=lambda c: abs(c[0] - a) if a is not None else 0)
        urutan_ok = a is None or abs(i - a) <= 40
        hasil[j] = (i, jac, cont, urutan_ok)
    return hasil


def fmt_no(n):
    if n is None:
        return None
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return str(n)


def main():
    t0 = time.time()
    os.makedirs(BUILD, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    info = json.load(open(os.path.join(SRC, "fawazahmed0", "info.json"), encoding="utf8"))
    laporan = {}

    for kid, nama, nama_ar, penyusun, wafat, berkas, fawaz in KITAB:
        lidwa = []
        for rid, _k, arab, terj in read_mysql_dump(os.path.join(SRC, "lidwa-carihadis", berkas)):
            n = norm_ar(arab)
            lidwa.append({"id": rid, "arab": arab.strip(), "terj": terj.strip(), "norm": n,
                          "sh": shingles(n.split()) if len(n) > 10 else set()})
        rep = {"lidwa": len(lidwa)}

        if fawaz is None:
            # Hanya satu sumber digital: tingkat B, nomor Lidwa.
            seen = {}
            for l in lidwa:
                alasan, tingkat = None, "B"
                if len(l["norm"]) < 15:
                    tingkat, alasan = "K", "teks Arab kosong/terlalu pendek"
                elif not l["terj"]:
                    tingkat, alasan = "K", "terjemahan kosong"
                elif l["norm"] in seen:
                    alasan = f"teks identik dengan no. Lidwa {seen[l['norm']]} (pengulangan dalam kitab atau duplikat data)"
                seen.setdefault(l["norm"], l["id"])
                db.execute("INSERT INTO riwayat(id,kitab_id,no_lidwa,arab,terjemah,rantai_json,tingkat,alasan)"
                           " VALUES(?,?,?,?,?,?,?,?)",
                           (f"{kid}:L{l['id']}", kid, l["id"], l["arab"], l["terj"],
                            json.dumps(rantai_dari_terjemah(l["terj"]), ensure_ascii=False), tingkat, alasan))
            rep["tingkat"] = dict(collections.Counter(r[0] for r in db.execute(
                "SELECT tingkat FROM riwayat WHERE kitab_id=?", (kid,))))
            db.execute("INSERT INTO kitab VALUES(?,?,?,?,?,?,?,?)",
                       (kid, nama, nama_ar, penyusun, wafat, "Lidwa", len(lidwa), None))
            laporan[kid] = rep
            continue

        ed = json.load(open(os.path.join(SRC, "fawazahmed0", f"ara-{fawaz}.json"), encoding="utf8"))
        sections = ed["metadata"].get("sections", {})
        grades = {fmt_no(h["hadithnumber"]): h.get("grades", []) for h in info[fawaz]["hadiths"]}
        F = []
        for h in ed["hadiths"]:
            n = norm_ar(h["text"])
            F.append({"no": fmt_no(h["hadithnumber"]), "arno": fmt_no(h.get("arabicnumber")),
                      "bab": h.get("reference", {}).get("book"), "arab": h["text"].strip(), "norm": n,
                      "sh": shingles(n.split()) if len(n) > 10 else set()})
        rep["standar"] = len(F)

        cw = crosswalk(lidwa, F)
        hist = collections.Counter()
        dipakai = collections.Counter()  # berapa nomor standar memakai baris Lidwa yg sama
        cocok = {}
        for j, (i, jac, cont, urutan_ok) in cw.items():
            if not urutan_ok:
                hist["tidak cocok (posisi menyimpang dari urutan kitab)"] += 1
                continue
            if jac >= 0.85:
                cocok[j] = (i, jac, cont, "1:1")
            elif cont >= 0.9:
                cocok[j] = (i, jac, cont, "gabungan")
            else:
                hist["tidak cocok (<0.85 & <0.9)"] += 1
                continue
            hist[cocok[j][3]] += 1
            dipakai[i] += 1
        rep["pasangan"] = dict(hist)
        rep["lidwa_tak_terpasang"] = len(lidwa) - len(dipakai)

        seen = {}
        for j, f in enumerate(F):
            m = cocok.get(j)
            l = lidwa[m[0]] if m else None
            skor = round(max(m[1], m[2]) if m[3] == "gabungan" else m[1], 3) if m else None
            alasan, tingkat = None, "B"
            if len(f["norm"]) < 15:
                tingkat, alasan = "K", "teks Arab kosong/terlalu pendek di sumber standar"
            elif l is None:
                alasan = "pasangan di sumber Lidwa tidak ditemukan; terjemahan belum tersedia"
            else:
                tingkat = "A"
                if m[3] == "gabungan":
                    alasan = (f"teks ini tercakup utuh di Lidwa no. {l['id']} yang menggabungkan "
                              f"{dipakai[m[0]]} nomor standar; terjemahan mencakup seluruh gabungan"
                              if dipakai[m[0]] > 1 else
                              f"teks ini tercakup utuh di Lidwa no. {l['id']}, yang teksnya lebih panjang; "
                              f"terjemahan mengikuti teks Lidwa")
            if tingkat != "K" and f["norm"] in seen:
                alasan = ((alasan + "; ") if alasan else "") + f"teks identik dengan no. {seen[f['norm']]} (pengulangan dalam kitab)"
            seen.setdefault(f["norm"], f["no"])
            terj = l["terj"] if (l and tingkat == "A") else None
            db.execute(
                "INSERT INTO riwayat(id,kitab_id,no_standar,no_arab,no_lidwa,bab_no,bab_nama,arab,arab_lidwa,terjemah,"
                "rantai_json,kecocokan,tingkat,alasan) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"{kid}:{f['no']}", kid, f["no"], f["arno"], l["id"] if l else None, f["bab"],
                 sections.get(str(f["bab"])), f["arab"], l["arab"] if l else None, terj,
                 json.dumps(rantai_dari_terjemah(terj), ensure_ascii=False) if terj else None,
                 skor, tingkat, alasan))
            for g in grades.get(f["no"], []):
                db.execute("INSERT INTO penilaian VALUES(?,?,?,?,?)",
                           (f"{kid}:{f['no']}", g["name"], g["grade"], kategori_derajat(g["grade"]), "fawazahmed0"))
        rep["tingkat"] = dict(collections.Counter(r[0] for r in db.execute(
            "SELECT tingkat FROM riwayat WHERE kitab_id=?", (kid,))))
        db.execute("INSERT INTO kitab VALUES(?,?,?,?,?,?,?,?)",
                   (kid, nama, nama_ar, penyusun, wafat, "standar (fawazahmed0) + Lidwa", len(lidwa), len(F)))
        laporan[kid] = rep
        print(kid, rep, f"{time.time() - t0:.0f}s", file=sys.stderr)

    # Indeks pencarian: hanya riwayat yang terbit (A/B).
    for rid, arab, terj, rantai in db.execute(
            "SELECT id, arab, terjemah, rantai_json FROM riwayat WHERE tingkat IN ('A','B')").fetchall():
        names = " ".join(json.loads(rantai)) if rantai else ""
        na = norm_ar(arab)
        db.execute("INSERT INTO cari VALUES(?,?,?,?,?)", (rid, na, akar_ar(na), norm_id(terj), norm_id(names)))
    db.commit()
    json.dump(laporan, open(os.path.join(BUILD, "laporan-build.json"), "w"), indent=1, ensure_ascii=False)
    print(f"selesai {time.time() - t0:.0f}s -> {DB_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
