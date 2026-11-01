#!/usr/bin/env python3
"""Uji katalog hadits populer & palsu (build/katalog.sqlite dari pipeline/katalog_palsu.py).

Tiga lapis:
  1. kata kunci penilaian: kasus yang dulu salah ("ومعناه صحيح" terbaca shahih, "حديث حسن العهد" terbaca hasan, dst.)
  2. struktur & jumlah entri per kitab
  3. emas: ucapan populer -> entri kitab (dan TIDAK ke entri yang hanya menyebutnya) -> riwayat (kontrol shahih)

Jalankan:  python3 -m unittest pipeline/test_katalog.py -v
"""
import json
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD
from katalog_palsu import judul_entri, kata_kunci

db = sqlite3.connect(os.path.join(BUILD, "katalog.sqlite"))
q = lambda s, *a: db.execute(s, a).fetchall()
padanan = lambda teks: [x[1] for x in kata_kunci(teks)]
tautan = lambda pid: {r[0] for r in q("SELECT katalog_id FROM populer_katalog WHERE populer_id=?", pid)}
sebut = lambda pid: {r[0] for r in q("SELECT katalog_id FROM populer_sebut WHERE populer_id=?", pid)}
riwayat = lambda pid: {r[0] for r in q("SELECT riwayat_id FROM populer_riwayat WHERE populer_id=?", pid)}
kunci_entri = lambda eid: [x[1] for x in json.loads(q("SELECT kata_kunci FROM katalog WHERE id=?", eid)[0][0])]


class KataKunci(unittest.TestCase):
    def test_makna_benar_bukan_shahih(self):
        # al-Maqashid no. 386: "لم أقف عليه، ومعناه صحيح" = tidak ditemukan; MAKNANYA benar. Bukan penilaian shahih.
        g = padanan("حديث: حب الوطن من الإيمان، لم أقف عليه، ومعناه صحيح")
        self.assertIn("maknanya benar (bukan penilaian sanad)", g)
        self.assertIn("“tidak saya temukan”", g)
        self.assertNotIn("shahih", g)

    def test_matan_bukan_penilaian(self):
        self.assertEqual(padanan("ألا ترى إلى حديث حسن العهد من الإيمان"), [])     # "husnul 'ahdi" = isi hadits
        self.assertEqual(padanan("من كذب علي متعمدا فليتبوأ مقعده من النار"), [])
        self.assertEqual(padanan("هو خلق حسن"), [])
        self.assertEqual(padanan("إن مما أدرك الناس من كلام النبوة الأولى"), [])

    def test_judul_kitab_bukan_penilaian(self):
        self.assertEqual(padanan("رواه في صحيح مسلم"), [])
        self.assertEqual(padanan("وأخرجه في صحيح ابن حبان"), [])

    def test_negasi(self):
        self.assertNotIn("shahih", padanan("ليس في فضل الأضحية حديث صحيح"))

    def test_bantahan_pendapat_bukan_dusta(self):
        self.assertNotIn("dusta", padanan("وكذب من قال إنه اسم امرأة"))

    def test_penilaian_dikenali(self):
        self.assertEqual(padanan("هذا حديث موضوع"), ["maudhu' (palsu)"])
        self.assertEqual(padanan("إسناده صحيح"), ["shahih"])
        self.assertEqual(padanan("قال الترمذي حديث حسن صحيح"), ["hasan", "shahih"])
        self.assertEqual(padanan("رواه الطبراني بسند حسن"), ["hasan"])
        self.assertEqual(padanan("قال ابن حبان إنه باطل لا أصل له"), ["batil", "tidak ada asalnya"])

    def test_tingkatan_tidak_ganda(self):
        self.assertEqual(padanan("وهو ضعيف جدا"), ["sangat lemah"])
        self.assertEqual(padanan("قال البخاري منكر الحديث"), ["munkar al-hadits (kritik terhadap perawi)"])

    def test_kelas_warna(self):
        kelas = {x[1]: x[3] for x in kata_kunci("موضوع، وقال آخر لم أقف عليه، ومعناه صحيح، وإسناده حسن")}
        self.assertEqual(kelas, {"maudhu' (palsu)": "palsu", "“tidak saya temukan”": "lemah",
                                 "maknanya benar (bukan penilaian sanad)": "lain", "hasan": "terima"})


class JudulEntri(unittest.TestCase):
    def test_pola_tiap_kitab(self):
        self.assertEqual(judul_entri("(اطلبوا العلم ولو بالصين) رواه البيهقي"), "اطلبوا العلم ولو بالصين")   # Kasyf
        self.assertEqual(judul_entri("حديث: اطلبوا العلم ولو بالصين، فإن"), "اطلبوا العلم ولو بالصين")    # Maqashid
        self.assertEqual(judul_entri("حديث العلماء ورثة الأنبياء // قال"), "العلماء ورثة الأنبياء")         # al-Asrar


class Struktur(unittest.TestCase):
    def test_jumlah_entri(self):
        n = dict(q("SELECT kitab_id, count(*) FROM katalog GROUP BY 1"))
        # al-Maqashid 1356 nomor, Kasyf 3281 nomor (sebagian kosong/gabungan), al-Asrar ±1000 nomor (sebagian tidak
        # berjudul di teks digital), al-Maudhu'at per bab
        self.assertGreaterEqual(n["maqashid"], 1350)
        self.assertGreaterEqual(n["kasyf"], 3200)
        self.assertGreaterEqual(n["asrar"], 700)
        self.assertGreaterEqual(n["maudhuat"], 700)

    def test_id_unik_dan_teks_terisi(self):
        self.assertEqual(q("SELECT count(*) - count(DISTINCT id) FROM katalog")[0][0], 0)
        self.assertEqual(q("SELECT count(*) FROM katalog WHERE trim(teks_ar) = '' OR trim(judul_ar) = ''")[0][0], 0)

    def test_format_kata_kunci(self):
        for (kk,) in q("SELECT kata_kunci FROM katalog"):
            for x in json.loads(kk):
                self.assertEqual(len(x), 4)
                self.assertIn(x[3], ("palsu", "lemah", "lain", "terima"))

    def test_daftar_populer_belum_ditinjau_tercatat(self):
        self.assertEqual(dict(q("SELECT kunci, nilai FROM info"))["ditinjau"], "False")


class Emas(unittest.TestCase):
    def test_negeri_cina(self):
        self.assertEqual(tautan("ilmu-negeri-cina"), {"maqashid:125", "kasyf:397", "maudhuat:71"})
        self.assertEqual(q("SELECT judul_ar FROM katalog WHERE id='maqashid:125'")[0][0], "اطلبوا العلم ولو بالصين")
        self.assertTrue({"batil", "tidak ada asalnya"} <= set(kunci_entri("maqashid:125")))
        self.assertIn("tidak sahih", kunci_entri("maudhuat:71"))      # Ibnul Jauzi: "هذا حديث لا يصح عن رسول الله"
        self.assertEqual(riwayat("ilmu-negeri-cina"), set())

    def test_cinta_tanah_air_tanpa_shahih_palsu(self):
        self.assertEqual(tautan("cinta-tanah-air"), {"maqashid:386", "kasyf:1102", "asrar:164"})
        for eid in tautan("cinta-tanah-air"):
            self.assertNotIn("shahih", kunci_entri(eid), eid)
            self.assertNotIn("hasan", kunci_entri(eid), eid)
        self.assertIn("maudhu' (palsu)", kunci_entri("kasyf:1102"))   # ash-Shaghani: موضوع

    def test_hanya_disebut_tidak_ditautkan(self):
        # "نوم الصائم عبادة" hanya disebut di pembahasan al-Asrar no. 567 yang berjudul "نوم العالم عبادة";
        # "لا أصل له" di sana tentang ucapan lain, jadi bukan tautan judul, melainkan "disebut".
        self.assertEqual(tautan("tidur-puasa-ibadah"), set())
        self.assertEqual(sebut("tidur-puasa-ibadah"), {"asrar:567"})
        self.assertNotIn("asrar:479", tautan("ulama-pewaris-nabi"))
        self.assertIn("asrar:479", sebut("ulama-pewaris-nabi"))

    def test_kontrol_ada_di_kitab_hadits(self):
        self.assertTrue({"tirmidzi:2682", "abudawud:3641"} <= riwayat("ulama-pewaris-nabi"))
        self.assertIn("tirmidzi:1956", riwayat("senyum-sedekah"))
        self.assertIn("muslim:534", riwayat("bersuci-separuh-iman"))
        self.assertIn("tirmidzi:1924", riwayat("sayangi-yang-di-bumi"))

    def test_tidak_ada_tautan_ganda(self):
        self.assertEqual(q("SELECT count(*) FROM (SELECT populer_id, katalog_id FROM populer_katalog GROUP BY 1, 2 HAVING count(*) > 1)")[0][0], 0)
        self.assertEqual(q("SELECT count(*) FROM populer_sebut s JOIN populer_katalog k USING (populer_id, katalog_id)")[0][0], 0)


if __name__ == "__main__":
    unittest.main()
