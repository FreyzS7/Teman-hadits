#!/usr/bin/env python3
"""Takhrij otomatis: untuk setiap riwayat, cari riwayat lain yang MATAN-nya sama.

Hasil: build/takhrij.sqlite, tabel mirip(a, b, skor, bersama).

Cara kerja:
  1. Pisahkan matan dari sanad secara heuristik:
     - teks setelah tanda kutip pertama (" atau «), atau
     - teks setelah "صلى الله عليه وسلم" pertama (hadits marfu').
     Riwayat yang matannya tidak bisa dipisahkan TIDAK dihitung (lebih baik kosong daripada keliru,
     karena kemiripan sanad bisa menipu: banyak hadits berbeda memakai sanad yang sama).
  2. Ubah matan menjadi pasangan dua kata (2-gram) setelah normalisasi + pemotongan awalan.
  3. Skor a->b = bagian 2-gram matan a yang muncul di teks lengkap b.
     2-gram yang sangat umum (salawat, "رسول الله", "حدثنا") diabaikan supaya tidak menciptakan kemiripan palsu.
     Simpan bila skor >= AMBANG dan jumlah 2-gram bersama >= MIN_BERSAMA.
  4. Tingkat: "sama" (skor >= 0.7 dan >= 8 dua-kata bersama) atau "mirip" (selebihnya, perlu diperiksa pembaca).

Jalankan:  python3 pipeline/takhrij.py
"""
import array
import collections
import os
import re
import sqlite3
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, norm_ar, stem_ar

OUT = os.path.join(BUILD, "takhrij.sqlite")
AMBANG = 0.4            # batas bawah tingkat "mirip"
AMBANG_SAMA = 0.7       # tingkat "sama": skor >= 0.7 dan >= 8 dua-kata bersama
MIN_BERSAMA = 6
BATAS_UMUM = 1500       # 2-gram yang muncul di > 1500 riwayat (mis. "صلي الله", "رسول الله") diabaikan
MIN_KATA_MATAN = 6
MAKS_PER_RIWAYAT = 60
_SAW = re.compile(r"صلي الله عليه وسلم")


def pisah_matan(arab):
    """Kembalikan teks matan (sudah dinormalisasi) atau None bila tidak bisa dipisahkan."""
    for tanda in ('"', "«", "“"):
        if tanda in arab:
            m = norm_ar(arab.split(tanda, 1)[1])
            if len(m.split()) >= MIN_KATA_MATAN:
                return m
    n = norm_ar(arab)
    hit = _SAW.search(n)
    if hit:
        m = n[hit.end():].strip()
        m = re.sub(r"^(قال|يقول|فقال|انه قال)\s+", "", m)
        if len(m.split()) >= MIN_KATA_MATAN:
            return m
    return None


def dua_gram(teks):
    w = [stem_ar(x) for x in teks.split()]
    return {zlib.crc32((w[i] + " " + w[i + 1]).encode()) for i in range(len(w) - 1)}


def main():
    t0 = time.time()
    src = sqlite3.connect(DB_PATH)
    rows = src.execute("SELECT id, arab FROM riwayat WHERE tingkat IN ('A','B')").fetchall()
    ids, matan, teks = [], [], []
    tanpa_matan = 0
    for rid, ar in rows:
        m = pisah_matan(ar)
        ids.append(rid)
        teks.append(array.array("I", sorted(dua_gram(norm_ar(ar)))))
        if m is None:
            tanpa_matan += 1
            matan.append(None)
        else:
            matan.append(dua_gram(m))
    print(f"{len(ids)} riwayat, {tanpa_matan} tanpa matan terpisah ({time.time() - t0:.0f}s)", file=sys.stderr)

    # indeks terbalik atas 2-gram TEKS LENGKAP (kandidat b), dipakai dengan 2-gram MATAN a
    df = collections.Counter()
    post = collections.defaultdict(list)
    for i, t in enumerate(teks):
        for h in t:
            df[h] += 1
            post[h].append(i)

    if os.path.exists(OUT):
        os.remove(OUT)
    out = sqlite3.connect(OUT)
    out.execute("CREATE TABLE mirip (a TEXT, b TEXT, skor REAL, bersama INT, tingkat TEXT)")
    umum = {h for h, n in df.items() if n > BATAS_UMUM}
    print(f"{len(umum)} dua-kata umum diabaikan", file=sys.stderr)
    out.execute("CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT)")
    n_edge = 0
    punya = 0
    for i, m in enumerate(matan):
        if not m:
            continue
        m = m - umum
        if len(m) < MIN_BERSAMA:
            continue
        rare = sorted((h for h in m if df[h] <= 200), key=lambda h: df[h])[:16]
        cand = collections.Counter()
        for h in rare:
            for j in post[h]:
                if j != i:
                    cand[j] += 1
        hasil = []
        for j, _ in cand.most_common(400):
            tj = teks[j]
            bersama = sum(1 for h in m if _ada(tj, h))
            skor = bersama / len(m)
            if skor >= AMBANG and bersama >= MIN_BERSAMA:
                tk = "sama" if (skor >= AMBANG_SAMA and bersama >= 8) else "mirip"
                hasil.append((ids[i], ids[j], round(skor, 3), bersama, tk))
        hasil.sort(key=lambda x: -x[2])
        hasil = hasil[:MAKS_PER_RIWAYAT]
        if hasil:
            punya += 1
            out.executemany("INSERT INTO mirip VALUES (?,?,?,?,?)", hasil)
            n_edge += len(hasil)
        if i % 10000 == 0:
            print(f"  {i} … {n_edge} pasangan ({time.time() - t0:.0f}s)", file=sys.stderr)
    out.execute("CREATE INDEX ix_mirip_a ON mirip(a)")
    for k, v in {"ambang": AMBANG, "ambang_sama": AMBANG_SAMA, "batas_umum": BATAS_UMUM, "min_bersama": MIN_BERSAMA, "riwayat": len(ids), "tanpa_matan": tanpa_matan,
                 "punya_pasangan": punya, "pasangan": n_edge}.items():
        out.execute("INSERT INTO info VALUES (?,?)", (k, str(v)))
    out.commit()
    print(f"selesai: {punya} riwayat punya pasangan, {n_edge} pasangan ({time.time() - t0:.0f}s)", file=sys.stderr)


def _ada(arr, h):
    # pencarian biner pada array terurut
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < h:
            lo = mid + 1
        else:
            hi = mid
    return lo < len(arr) and arr[lo] == h


if __name__ == "__main__":
    main()
