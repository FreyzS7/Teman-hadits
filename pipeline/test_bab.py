#!/usr/bin/env python3
"""Uji judul kitab & bab dari OpenITI (build/bab.sqlite dari pipeline/bab_openiti.py).

Nomor hadits TIDAK dipakai untuk mencocokkan (hanya isi teks), sehingga kesamaan nomor dengan edisi
cetak adalah uji independen.  Jalankan:  python3 -m unittest pipeline/test_bab.py -v
"""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, norm_ar

b = sqlite3.connect(os.path.join(BUILD, "bab.sqlite"))
q = lambda s, *a: b.execute(s, a).fetchall()
judul = lambda rid: q("SELECT kitab_ar, bab_ar FROM riwayat_bab WHERE riwayat_id=?", rid)[0]
info = lambda kid, k: q("SELECT nilai FROM info WHERE kitab_id=? AND kunci=?", kid, k)[0][0]
rasio = lambda s: int(s.split("/")[0]) / max(1, int(s.split("/")[1]))


class JudulDikenal(unittest.TestCase):
    def test_bukhari_1_permulaan_wahyu(self):
        self.assertEqual(norm_ar(judul("bukhari:1")[0]), "بد الوحي")

    def test_bukhari_2009_kitab_tarawih(self):
        k, bb = judul("bukhari:2009")
        self.assertEqual(norm_ar(k), "كتاب صلاه التراويح")
        self.assertEqual(norm_ar(bb), "باب فضل من قام رمضان")

    def test_hadits_berulang_tidak_tertukar_kitab(self):
        # Bukhari 4531 (Tafsir al-Baqarah) teksnya sama dengan 5344 (Kitab ath-Thalaq): harus tetap di Tafsir.
        self.assertIn("تفسير", norm_ar(judul("bukhari:4531")[0]))
        self.assertIn("الطلاق", norm_ar(judul("bukhari:5344")[0]))

    def test_muslim_1907_kitab_imarah(self):
        self.assertEqual(norm_ar(judul("muslim:4927")[0]), "كتاب الاماره")


class ValidasiIndependen(unittest.TestCase):
    def test_nomor_sama_dengan_edisi_cetak(self):
        # Edisi OpenITI: Bukhari Dar Thauq an-Najah; Abu Dawud Muhyiddin; Ibnu Majah & Muslim Fu'ad 'Abdul Baqi; Nasa'i Abu Ghuddah.
        for kid, minimal in (("bukhari", 0.95), ("abudawud", 0.99), ("ibnumajah", 0.99), ("tirmidzi", 0.99), ("nasai", 0.99)):
            self.assertGreaterEqual(rasio(info(kid, "nomor_sama")), minimal, kid)

    def test_urutan_naik(self):
        for kid in ("bukhari", "muslim", "abudawud", "ibnumajah", "tirmidzi", "nasai", "malik"):
            self.assertGreaterEqual(rasio(info(kid, "urutan_naik")), 0.99, kid)

    def test_cakupan(self):
        for kid in ("bukhari", "muslim", "abudawud", "ibnumajah", "nasai", "malik"):
            self.assertGreaterEqual(rasio(info(kid, "cocok_teks") + "/" + info(kid, "riwayat")), 0.97, kid)


class NamaKitab(unittest.TestCase):
    def test_bagian_tampungan_tidak_diberi_nama_paksa(self):
        # Bagian "0" Bukhari & Muslim di fawazahmed0 berisi riwayat tanpa nomor kitab dari seluruh kitab.
        for kid in ("bukhari", "muslim"):
            self.assertIsNone(q("SELECT nama_ar FROM kitab_nama WHERE kitab_id=? AND bab_no=0", kid)[0][0])

    def test_setiap_nama_arab_punya_nama_indonesia(self):
        self.assertEqual(q("SELECT count(*) FROM kitab_nama WHERE nama_ar IS NOT NULL AND nama_id IS NULL")[0][0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
