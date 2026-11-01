#!/usr/bin/env python3
"""Uji Riyadhus Shalihin (build/riyadh.sqlite dari pipeline/riyadh.py).

Jalankan:  python3 -m unittest pipeline/test_riyadh.py -v
"""
import os
import re
import sqlite3
import statistics
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, norm_id

ry = sqlite3.connect(os.path.join(BUILD, "riyadh.sqlite"))
q = lambda s, *a: ry.execute(s, a).fetchall()


class Pemecahan(unittest.TestCase):
    def test_1896_hadits_tanpa_celah(self):
        # Riyadhus Shalihin berisi 1896 hadits (penomoran edisi teks Arab sumber ini).
        nos = [r[0] for r in q("SELECT no FROM riyadh ORDER BY urut")]
        self.assertEqual(nos, list(range(1, 1897)))

    def test_catatan_kaki_edisi_dipisah_dari_teks_nawawi(self):
        arab, catatan = q("SELECT arab, catatan_ar FROM riyadh WHERE no=1774")[0]
        self.assertIn("ابن عثيمين", catatan)       # syarah Ibnu 'Utsaimin = catatan kaki edisi, bukan an-Nawawi
        self.assertNotIn("ابن عثيمين", arab)
        self.assertIn("متفق عليه", re.sub(r"[ً-ْ]", "", arab))


class PasanganTerjemah(unittest.TestCase):
    def test_727_tidak_tertukar_dengan_hadits_jabir(self):
        # Kasus awal: nomor terjemah 727 = hadits Jabir, padahal Arab 727 = Umar bin Abi Salamah.
        t727 = q("SELECT terjemah, no_terjemah FROM riyadh WHERE no=727")[0]
        t729 = q("SELECT terjemah FROM riyadh WHERE no=729")[0][0]
        self.assertIn("Abu Salamah", t727[0])
        self.assertEqual(t727[1], 725)
        self.assertTrue(t729.startswith("Dari Jabir"))

    def test_validasi_independen_dengan_terjemah_lidwa(self):
        # Terjemah Riyadh & terjemah Lidwa adalah dua terjemahan berbeda dari hadits yang sama:
        # pasangan yang benar harus lebih mirip daripada pasangan yang digeser satu hadits.
        m = sqlite3.connect(DB_PATH)
        stop = set("yang dan itu ini dengan akan ia dia ke di dari pada untuk apa kepada kami telah adalah bahwa atau "
                   "juga tidak orang dalam saya beliau bersabda berkata rasulullah shallallahu alaihi wasallam saw r "
                   "a radhiallahu anhu anha katanya maka lalu pula".split())
        kata = lambda t: {w for w in norm_id(re.sub(r"\[|\]", "", t or "")).split() if len(w) > 3 and w not in stop}
        rows = q("""SELECT x.terjemah, (SELECT s.riwayat_id FROM riyadh_sumber s WHERE s.urut = x.urut ORDER BY s.peringkat LIMIT 1)
                    FROM riyadh x WHERE x.status_terjemah = 'pasti' ORDER BY x.urut""")
        pasang = []
        for t, rid in rows:
            if rid:
                lt = m.execute("SELECT terjemah FROM riwayat WHERE id=?", (rid,)).fetchone()[0]
                if lt:
                    pasang.append((kata(t), kata(lt)))
        jac = lambda a, b: len(a & b) / max(1, len(a | b))
        lebih = sum(1 for i in range(len(pasang) - 1) if jac(*pasang[i]) > jac(pasang[i][0], pasang[i + 1][1]))
        self.assertGreater(len(pasang), 1300)
        self.assertGreaterEqual(lebih / (len(pasang) - 1), 0.95)


class Sumber(unittest.TestCase):
    def test_hadits_1_bersumber_bukhari_1_dan_muslim_1907(self):
        ids = {r[0] for r in q("SELECT s.riwayat_id FROM riyadh_sumber s JOIN riyadh r ON r.urut = s.urut WHERE r.no = 1")}
        self.assertIn("bukhari:1", ids)
        self.assertIn("muslim:4927", ids)   # Muslim 1907a

    def test_918_sumber_teratas_muslim_dari_sahabat_yang_sama(self):
        # an-Nawawi: رواه مسلم, dari Abu Sa'id. Ibnu Majah dari Abu Hurairah (matan sama) harus di bawahnya.
        top = q("SELECT riwayat_id, kitab_disebut, sahabat_sama FROM riyadh_sumber s JOIN riyadh r ON r.urut = s.urut "
                "WHERE r.no = 918 ORDER BY peringkat LIMIT 1")[0]
        self.assertTrue(top[0].startswith("muslim:"))
        self.assertEqual(top[1:], (1, 1))

    def test_uji_silang_atribusi_nawawi(self):
        info = dict(q("SELECT kunci, nilai FROM info"))
        self.assertGreaterEqual(int(info["uji_silang_cocok"]) / int(info["uji_silang_dicek"]), 0.97)


if __name__ == "__main__":
    unittest.main(verbosity=2)
