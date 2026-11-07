"""Uji kecil untuk pipeline/export_d1.py (tanpa membangun database)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_d1 import nama_saja, tanpa_kurung  # noqa: E402


class KolomPencarianTerjemah(unittest.TestCase):
    def test_nama_di_kurung_siku_tidak_masuk_terjemah(self):
        t = tanpa_kurung("Telah menceritakan kepada kami [Hisyam] dari [ayahnya] dari ['Aisyah] berkata; ayahku sakit")
        self.assertNotIn("Hisyam", t)
        self.assertNotIn("ayahnya", t)
        self.assertIn("ayahku sakit", t)

    def test_kolom_perawi_hanya_kata_nama(self):
        self.assertEqual(nama_saja("bapaknya, Al Qasim"), "Al Qasim")
        self.assertEqual(nama_saja("Abdullah bin Az Zubair al-A'masy"), "Abdullah bin Az Zubair al-A'masy")
        self.assertEqual(nama_saja("seorang laki-laki"), "")
        self.assertEqual(nama_saja("'Amir bin Sa'd"), "'Amir bin Sa'd")


if __name__ == "__main__":
    unittest.main()


class KelompokSerupa(unittest.TestCase):
    SANAD = "حَدَّثَنَا قُتَيْبَةُ، حَدَّثَنَا اللَّيْثُ، عَنْ نَافِعٍ، عَنِ ابْنِ عُمَرَ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ "

    def r(self, matan):
        return self.SANAD + '"' + matan + '"'

    def test_matan_sama_sekelompok_yang_beda_tidak(self):
        from serupa import kelompok
        g = kelompok([
            (1, self.r("إِذَا دَخَلَ أَحَدُكُمُ الْمَسْجِدَ فَلْيَقُلِ اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ")),
            (2, self.r("لاَ يَشْرَبَنَّ أَحَدٌ مِنْكُمْ قَائِمًا فَمَنْ نَسِيَ فَلْيَسْتَقِئْ")),
            (3, self.r("إِذَا دَخَلَ أَحَدُكُمُ الْمَسْجِدَ فَلْيَقُلِ اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ")),
        ])
        self.assertEqual(g, {1: 1, 3: 1})

    def test_komentar_penyusun_tidak_ikut_matan(self):
        from serupa import kata_matan
        a = kata_matan(self.r("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى") + " قَالَ أَبُو عِيسَى هَذَا حَدِيثٌ حَسَنٌ صَحِيحٌ")
        b = kata_matan(self.r("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى"))
        self.assertEqual(a, b)
