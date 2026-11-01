#!/usr/bin/env python3
"""Uji impor HadeethEnc (jalankan setelah `python3 -I pipeline/hadeethenc.py bangun`).

    python3 -m unittest pipeline/test_hadeethenc.py -v
"""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, norm_ar

he = sqlite3.connect(os.path.join(BUILD, "hadeethenc.sqlite"))
kita = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


class HadeethEnc(unittest.TestCase):
    def test_tema_lengkap(self):
        # API HadeethEnc (bahasa Indonesia) memuat 447 kategori saat diambil 2026-11-01.
        self.assertGreater(he.execute("SELECT count(*) FROM tema").fetchone()[0], 400)
        self.assertGreater(he.execute("SELECT count(*) FROM he_hadits").fetchone()[0], 2000)

    def test_hadits_niat_terpetakan_ke_bukhari_1_dan_muslim_1907(self):
        niat = [hid for hid, ar in he.execute("SELECT id, teks_ar FROM he_hadits")
                if "انما الاعمال بالني" in norm_ar(ar)]
        self.assertTrue(niat)
        pasangan = {rid for hid in niat for (rid,) in
                    he.execute("SELECT riwayat_id FROM he_riwayat WHERE he_id=?", (hid,))}
        # Versi Arba'in an-Nawawi (lafaz Bukhari no. 1) harus terpetakan ke bukhari:1.
        self.assertIn("bukhari:1", pasangan)
        # Dan minimal satu versi harus terpetakan ke Muslim no. 1907 (penomoran Fu'ad 'Abdul Baqi).
        no_muslim = [kita.execute("SELECT no_arab FROM riwayat WHERE id=?", (r,)).fetchone()[0]
                     for r in pasangan if r.startswith("muslim:")]
        self.assertTrue(any(str(n).startswith("1907") for n in no_muslim), no_muslim)


if __name__ == "__main__":
    unittest.main(verbosity=2)
