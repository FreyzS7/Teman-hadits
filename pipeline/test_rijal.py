#!/usr/bin/env python3
"""Uji emas kitab rijal (rijal.py) dan identifikasi perawi di sanad (perawi.py).

Nilai emas diambil dari teks Taqrib/Tahdzib al-Kamal sendiri dan dari rantai yang identitas perawinya masyhur
(dijelaskan para pensyarah, mis. Fath al-Bari untuk Bukhari no. 1). Jalankan:
    python3 -m unittest pipeline/test_rijal.py -v
"""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD
from nama import urai
from rijal import penilaian_ibnu_hajar, tahun_wafat
from sanad import rantai_arab

r = sqlite3.connect(os.path.join(BUILD, "rijal.sqlite"))
p = sqlite3.connect(os.path.join(BUILD, "perawi.sqlite"))
tq = lambda no: dict(zip(("no", "tabaqah", "wafat", "ragu", "rumuz", "tingkat"),
                         r.execute("SELECT no, tabaqah, wafat, wafat_ragu, rumuz, tingkat FROM taqrib WHERE no=?", (no,)).fetchone()))
rantai = lambda rid: [(t, l) for t, l in p.execute("SELECT taqrib, label FROM sebutan WHERE riwayat_id=? ORDER BY pos", (rid,))]


class Taqrib(unittest.TestCase):
    def test_kaidah_abad_wafat(self):
        # "مات سنة إحدى وعشرين" + tabaqah 9 -> 221 (muqaddimah: tabaqah 9-12 sesudah 200)
        self.assertEqual((tq(132)["tabaqah"], tq(132)["wafat"]), (9, 221))          # Adam bin Abi Iyas
        self.assertEqual((tq(2451)["tabaqah"], tq(2451)["wafat"]), (8, 198))        # Sufyan bin 'Uyainah ("مات في رجب سنة ...")
        self.assertEqual((tq(8633)["tabaqah"], tq(8633)["wafat"]), (1, 57))         # 'A'isyah (bagian perempuan "$$")

    def test_puluhan_berlaku_untuk_semua_pendapat(self):
        # Abu Hurairah: "مات سنة سبع وقيل ثمان وقيل تسع وخمسين" -> 57, ada pendapat lain
        self.assertEqual((tq(8426)["wafat"], tq(8426)["ragu"]), (57, 1))
        self.assertEqual((tq(565)["wafat"], tq(565)["ragu"]), (92, 1))              # Anas: "اثنتين وقيل ثلاث وتسعين"

    def test_angka_tidak_pasti(self):
        self.assertEqual(tahun_wafat("مات سنه نيف واربعين", 3)[0], None)

    def test_tingkatan_ibnu_hajar(self):
        self.assertEqual(tq(2451)["tingkat"], 2)    # ثقة حافظ فقيه إمام حجة
        self.assertEqual(tq(6296)["tingkat"], 2)    # az-Zuhri: متفق على جلالته وإتقانه
        self.assertEqual(tq(878)["tingkat"], 8)     # Jabir al-Ju'fi: ضعيف رافضي
        self.assertEqual(tq(565)["tingkat"], 1)     # Anas: خادم رسول الله
        self.assertEqual(penilaian_ibnu_hajar("فلان بن فلان صدوق يهم من السابعة")[1], 5)
        self.assertEqual(penilaian_ibnu_hajar("فلانة مقبولة من الثالثة")[1], 6)
        # diverifikasi dengan scan cetak hlm. 480: Muhammad bin Sa'id al-Mashlub "كذبوه" (dulu tanpa penilaian)
        self.assertEqual(tq(5907)["tingkat"], 12)
        # tuduhan dusta yang hanya KUTIPAN sesudah penilaian Ibnu Hajar sendiri tidak menaikkan tingkat
        self.assertEqual(penilaian_ibnu_hajar("فلان متروك كذبه أبو داود من السابعة")[1], 10)


class TahdzibKamal(unittest.TestCase):
    def test_kode_tergabung_dan_mukadimah_muslim(self):
        # al-Humaidi: "خ مق د ت س فق" (kode "مق" = muqaddimah Shahih Muslim)
        rz = r.execute("SELECT rumuz FROM tk WHERE kepala LIKE 'عبد الله بن الزبير بن عيسى%'").fetchone()[0].split()
        self.assertEqual(rz, ["خ", "مق", "د", "ت", "س", "فق"])

    def test_daftar_guru_dengan_kode(self):
        tk = r.execute("SELECT id FROM tk WHERE kepala LIKE 'يحيى بن سعيد بن قيس بن عمرو%'").fetchone()[0]
        guru = dict(r.execute("SELECT nama, kode FROM tk_relasi WHERE tk_id=? AND arah='guru'", (tk,)).fetchall())
        self.assertEqual(guru.get("محمد بن إبراهيم بن الحارث التيمي"), "ع")


class Nama(unittest.TestCase):
    def test_bentuk_nama(self):
        self.assertEqual(urai("الحميدي عبد الله بن الزبير").rantai, ["عبد الله", "زبير"])
        self.assertEqual(urai("ابن أبي ذئب").leluhur, ["ابو ذيب"])
        n = urai("أبو بكر بن أبي شيبة")
        self.assertEqual((n.kunyah, n.leluhur), (["ابو بكر"], ["ابو شيبه"]))
        self.assertEqual(urai("عبيد الله بن عمر").rantai, ["عبيد الله", "عمر"])
        self.assertEqual(urai("كُرَيْبًا").rantai, ["كريب"])                       # tanwin manshub
        self.assertEqual(urai("نافع مولى ابن عمر").maula, ["عمر"])
        self.assertIn("ام_المومنين", urai("عائشة أم المؤمنين").atribut)
        self.assertTrue(urai("أبيه").kosong())                                      # rujukan relatif

    def test_huruf_jar_bukan_nama(self):
        segs = rantai_arab("حَدَّثَنَا عَمْرُو بْنُ عَلِيٍّ، حَدَّثَنَا يَحْيَى")
        self.assertEqual(segs[0]["nama_ar"], "عَمْرُو بْنُ عَلِيٍّ")             # "علي" nama, bukan "على"


class Identifikasi(unittest.TestCase):
    def test_bukhari_1(self):
        # al-Humaidi, Sufyan bin 'Uyainah, Yahya bin Sa'id al-Anshari, Muhammad bin Ibrahim at-Taimi, 'Alqamah, 'Umar
        self.assertEqual(rantai("bukhari:1"), [(3320, "pasti"), (2451, "pasti"), (7559, "pasti"), (5691, "pasti"),
                                               (4685, "pasti"), (4888, "pasti")])

    def test_ayah_dan_ummul_mukminin(self):
        # Hisyam bin 'Urwah "عن أبيه" = 'Urwah; 'A'isyah Ummul Mukminin (bukan 'A'isyah bint Thalhah)
        self.assertEqual(rantai("bukhari:2"), [(3721, "pasti"), (6425, "pasti"), (7302, "pasti"), (4561, "pasti"), (8633, "pasti")])

    def test_nasab_ke_kakek(self):
        # "يحيى بن بكير" = Yahya bin 'Abdillah bin Bukair (Taqrib: "وقد ينسب إلى جده"); "ابن شهاب" = az-Zuhri
        self.assertEqual(rantai("bukhari:3")[:4], [(7580, "pasti"), (5684, "pasti"), (4665, "pasti"), (6296, "pasti")])

    def test_tidak_menebak_relatif_yang_tak_tertambat(self):
        n = p.execute("SELECT count(*) FROM sebutan WHERE label='pasti' AND tk_id IS NULL").fetchone()[0]
        self.assertEqual(n, 0)

    def test_cakupan_minimal(self):
        info = dict(p.execute("SELECT kunci, nilai FROM info").fetchall())
        self.assertGreater(int(info["pasti"]), 90000)
        self.assertGreater(int(info["perawi_teridentifikasi"]), 4000)


if __name__ == "__main__":
    unittest.main()
