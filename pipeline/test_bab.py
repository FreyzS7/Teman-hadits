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


class KitabLidwaSaja(unittest.TestCase):
    """Ahmad, Darimi, Syafi'i: edisi tahqiq OpenITI sebagai sumber kedua, judul, nomor edisi, penilaian muhaqqiq."""

    def test_penilaian_asad_terpasang_ke_hadits_yang_benar(self):
        # Edisi Asad no. 4: atsar Abu Raja' "كنا في الجاهلية إذا أصبنا حجرا حسنا عبدناه" — dinilai lemah karena 'Abbad bin Manshur.
        no, tq = q("SELECT no_openiti, tahqiq FROM riwayat_bab WHERE riwayat_id='darimi:L4'")[0]
        self.assertEqual(no, 4)
        self.assertIn("عباد بن منصور", tq)

    def test_judul_kitab_gaya_darimi(self):
        # "من كتاب الأضاحي" harus dikenali sebagai judul kitab (bukan tetap di كتاب الصلاة).
        self.assertIn("الأضاحي", judul("darimi:L1895")[0])
        self.assertEqual(norm_ar(judul("darimi:L4")[0]), "المقدمه")

    def test_cakupan_tingkat_a(self):
        for kid, minimal in (("ahmad", 0.85), ("darimi", 0.8), ("syafii", 0.6)):
            self.assertGreaterEqual(int(info(kid, "cocok_090")) / int(info(kid, "riwayat")), minimal, kid)

    def test_urutan_ahmad_darimi(self):
        # Syafi'i dikecualikan: edisi al-Fahl menyusun ulang per bab fiqih.
        for kid in ("ahmad", "darimi"):
            self.assertGreaterEqual(rasio(info(kid, "urutan_naik")), 0.99, kid)


class NamaKitab(unittest.TestCase):
    def test_bagian_tampungan_tidak_diberi_nama_paksa(self):
        # Bagian "0" Bukhari & Muslim di fawazahmed0 berisi riwayat tanpa nomor kitab dari seluruh kitab.
        for kid in ("bukhari", "muslim"):
            self.assertIsNone(q("SELECT nama_ar FROM kitab_nama WHERE kitab_id=? AND bab_no=0", kid)[0][0])

    def test_setiap_nama_arab_punya_nama_indonesia(self):
        self.assertEqual(q("SELECT count(*) FROM kitab_nama WHERE nama_ar IS NOT NULL AND nama_id IS NULL")[0][0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class KoreksiCetak(unittest.TestCase):
    def test_bab_tanpa_judul_bukhari_3659(self):
        # Teks digital melewatkan "باب" tanpa judul; fihris cetak Dar Thauq an-Najah juz 5 menunjukkannya
        self.assertEqual(judul("bukhari:3658")[1].endswith("خليلا»"), True)
        self.assertEqual(judul("bukhari:3659")[1], "باب")
        self.assertEqual(judul("bukhari:3678")[1], "باب")
        self.assertNotEqual(judul("bukhari:3679")[1], "باب")      # bab 6: مناقب عمر

    def test_bab_tanpa_judul_lain_dari_fihris(self):
        # fihris cetak hlm. 185 (dilihat langsung): "باب: حدثنا ابن أبي مريم", "باب: حدثنا معاذ بن فضالة"
        for no in (18, 435, 437, 745, 797, 799, 899, 900):
            self.assertEqual(judul(f"bukhari:{no}")[1], "باب", no)
        for no in (17, 19, 434, 438, 744, 746, 796, 800, 898, 901):
            self.assertNotEqual(judul(f"bukhari:{no}")[1], "باب", no)

    def test_judul_di_baris_berikutnya(self):
        # "### | باب" lalu judul di baris "# ..." berikutnya (fihris hlm. 217): bukan bab tanpa judul
        self.assertTrue(judul("bukhari:3489")[1].startswith("باب قول الله تعالى: {يا أيها الناس إنا خلقناكم"))
        self.assertEqual(judul("bukhari:3507")[1], "باب نسبة اليمن إلى إسماعيل")
        self.assertEqual(judul("bukhari:3508")[1], "باب")          # bab 5 "حدثنا أبو معمر": memang tanpa judul

    def test_catatan_editor_bukan_judul_bab(self):
        n = q("SELECT count(*) FROM riwayat_bab WHERE bab_ar LIKE '%[تعليق%'")[0][0]
        self.assertEqual(n, 0)
        self.assertEqual(judul("bukhari:3464")[1], "باب حديث أبرص وأعمى وأقرع في بني إسرائيل")

    def test_batas_surah_kitab_tafsir(self):
        # hadits pembuka surah tidak lagi mewarisi bab surah sebelumnya (fihris hlm. 205, 207, 208, 211)
        self.assertEqual(judul("bukhari:4967")[1], "سورة إذا جاء نصر الله")
        self.assertEqual(judul("bukhari:4974")[1], "سورة قل هو الله أحد")
        self.assertEqual(judul("bukhari:4708")[1], "سورة بني إسرائيل")
        self.assertEqual(judul("bukhari:4855")[1], "سورة والنجم")

    def test_koreksi_dari_gambar_fihris(self):
        self.assertEqual(judul("bukhari:52")[1], "باب فضل من استبرأ لدينه")
        for no in (51, 333, 348, 1885, 1888, 1945, 2624, 2669, 3466, 3497, 3540, 3639):
            self.assertEqual(judul(f"bukhari:{no}")[1], "باب", no)
        for no in (50, 332, 347, 1884, 1887, 1944, 2623, 2668, 3465, 3496, 3539, 3638):
            self.assertNotEqual(judul(f"bukhari:{no}")[1], "باب", no)
