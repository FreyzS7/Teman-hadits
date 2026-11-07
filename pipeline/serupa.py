#!/usr/bin/env python3
"""Kelompok riwayat serupa: riwayat yang matan Arabnya hampir sama (atau ditandai 'sama' oleh takhrij).

Dihitung sekali saat ekspor (pipeline/export_d1.py -> kolom riwayat.grup), supaya halaman hasil pencarian bisa
melipat riwayat serupa di beberapa halaman pertama tanpa memproses teks saat pencarian (batas CPU Workers).

Aturan (sama dengan pengelompokan lama di site/src/cari.js):
  - kata matan = kata akar (akar_ar o norm_ar) dari matan, tanpa sanad (sanad.pisah_sanad) dan tanpa komentar
    penyusun sesudah matan (at-Tirmidzi: "قال أبو عيسى ...");
  - dua riwayat serupa bila Jaccard kata matan >= AMBANG (0,8), keduanya minimal 4 kata. (Tautan takhrij 'sama'
    bisa diberikan lewat pasangan_sama, tetapi export_d1 tidak memakainya: digabung berantai, tautan itu menyatukan
    hadits yang berbeda.)
Pasangan dicari secara tepat dengan prefix filtering (tanpa membandingkan semua pasangan): dua himpunan dengan
Jaccard >= t pasti berbagi minimal satu kata di antara (|A| - ceil(t*|A|) + 1) kata terlangka masing-masing.
Kelompok = komponen terhubung; nomor kelompok = n terkecil di komponen itu.
"""
import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import akar_ar, norm_ar  # noqa: E402
from sanad import pisah_sanad  # noqa: E402

AMBANG = 0.8
MIN_KATA = 4
_KOMENTAR = ("قال ابو عيسي", "ابو عيسي")


def kata_matan(arab):
    p = pisah_sanad(arab or "")
    teks = norm_ar(p[1] if p else (arab or ""))
    for k in _KOMENTAR:   # komentar penyusun sesudah matan bukan bagian matan
        i = teks.find(k)
        if i >= 10:
            teks = teks[:i]
            break
    return frozenset(akar_ar(teks).split())


def jaccard(a, b):
    if len(a) < MIN_KATA or len(b) < MIN_KATA:
        return 0.0
    i = len(a & b)
    return i / (len(a) + len(b) - i)


def kelompok(riwayat, pasangan_sama=()):
    """riwayat: iterable (n, arab). pasangan_sama: iterable (n1, n2). Hasil: {n: nomor_kelompok} hanya untuk
    riwayat yang punya pasangan (riwayat tunggal tidak dicantumkan)."""
    kata = {n: kata_matan(a) for n, a in riwayat}
    kata = {n: k for n, k in kata.items() if len(k) >= MIN_KATA}
    df = collections.Counter(w for k in kata.values() for w in k)
    urut = {n: sorted(k, key=lambda w: (df[w], w)) for n, k in kata.items()}
    indeks = collections.defaultdict(list)
    induk = {}

    def akar(x):
        while induk.get(x, x) != x:
            induk[x] = induk.get(induk[x], induk[x])
            x = induk[x]
        return x

    def gabung(a, b):
        ra, rb = akar(a), akar(b)
        if ra != rb:
            induk[max(ra, rb)] = min(ra, rb)
            induk.setdefault(min(ra, rb), min(ra, rb))

    # urut ukuran: pasangan hanya dicek dengan himpunan yang sudah diindeks dan ukurannya sebanding
    for n in sorted(urut, key=lambda x: (len(urut[x]), x)):
        k, s = kata[n], len(urut[n])
        awalan = urut[n][: s - math.ceil(AMBANG * s) + 1]
        dicek = set()
        for w in awalan:
            for m in indeks[w]:
                if m in dicek:
                    continue
                dicek.add(m)
                if len(kata[m]) >= AMBANG * s and jaccard(k, kata[m]) >= AMBANG:
                    gabung(n, m)
        for w in awalan:
            indeks[w].append(n)
    for a, b in pasangan_sama:
        gabung(a, b)
    anggota = collections.defaultdict(list)
    for x in list(induk):
        anggota[akar(x)].append(x)
    return {x: g for g, xs in anggota.items() if len(xs) > 1 for x in xs}


if __name__ == "__main__":
    import sqlite3
    from common import DB_PATH
    db = sqlite3.connect(DB_PATH)
    rows = list(enumerate((a for (a,) in db.execute("SELECT arab FROM riwayat WHERE tingkat IN ('A','B') ORDER BY rowid")), 1))
    g = kelompok(rows)
    ukuran = collections.Counter(collections.Counter(g.values()).values())
    print(f"{len(rows)} riwayat, {len(g)} dalam {len(set(g.values()))} kelompok; ukuran kelompok terbesar:",
          sorted(ukuran.items())[-5:])
