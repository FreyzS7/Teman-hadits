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
