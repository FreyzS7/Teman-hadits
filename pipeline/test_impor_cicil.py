"""Uji pipeline/impor_cicil.py dengan cermin kecil buatan: cicilan yang diterapkan ke data lama = data baru."""
import glob
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_d1 import SKEMA  # noqa: E402
from impor_cicil import rencana  # noqa: E402

KOL = {
    "info": ["kunci", "nilai"],
    "riwayat": ["n", "id", "kitab_id", "slug", "urut", "no_tampil", "terjemah", "tingkat"],
    "cari": ["rowid", "arab_polos", "arab_akar", "terjemah_polos", "perawi", "judul"],
    "he_tema": ["he_id", "tema_id"],
    "bab": ["kitab_id", "no", "nama"],
}


def cermin(path, data, skema=SKEMA):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE _skema (sql TEXT)")
    c.execute("INSERT INTO _skema VALUES (?)", (skema,))
    for t, rows in data.items():
        c.execute(f'CREATE TABLE "{t}" ({", ".join(KOL[t])})')
        c.executemany(f'INSERT INTO "{t}" VALUES ({",".join("?" * len(KOL[t]))})', rows)
    c.commit()
    c.close()


def isi(data):
    d = sqlite3.connect(":memory:")
    d.executescript(SKEMA)
    for t, rows in data.items():
        d.executemany(f"INSERT INTO {t} ({','.join(KOL[t])}) VALUES ({','.join('?' * len(KOL[t]))})", rows)
    return d


def rw(n, teks):
    return (n, f"bukhari:{n}", "bukhari", str(n), n, str(n), teks, "A")


LAMA = {
    "info": [("versi", "1"), ("terbit", "100")],
    "riwayat": [rw(n, f"teks lama {n}") for n in range(1, 41)],
    "cari": [(n, "", "", f"teks lama {n} kurma", "", "") for n in range(1, 41)],
    "he_tema": [("h1", "t1"), ("h2", "t2")],
    "bab": [("bukhari", 1, "Wahyu"), ("bukhari", 2, "Iman")],
}
BARU = {
    "info": [("versi", "2"), ("terbit", "100")],
    "riwayat": [rw(n, f"teks baru {n}" if n % 3 == 0 else f"teks lama {n}") for n in range(2, 46)],   # n=1 hilang, 41-45 baru
    "cari": [(n, "", "", (f"teks baru {n} madu" if n % 3 == 0 else f"teks lama {n} kurma"), "", "") for n in range(2, 46)],
    "he_tema": [("h1", "t1"), ("h2", "t9")],
    "bab": [("bukhari", 1, "Permulaan Wahyu"), ("bukhari", 2, "Iman")],
}


class ImporCicil(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lama, self.baru, self.out = (os.path.join(self.tmp, x) for x in ("lama.sqlite", "baru.sqlite", "cicil"))

    def terapkan(self, batas):
        cermin(self.lama, LAMA)
        cermin(self.baru, BARU)
        self.assertEqual(rencana(self.lama, self.baru, self.out, batas), 0)
        d = isi(LAMA)
        berkas = sorted(glob.glob(os.path.join(self.out, "*.sql")))
        for f in berkas:
            d.executescript(open(f, encoding="utf8").read())
        return d, berkas

    def periksa(self, d):
        b = isi(BARU)
        for t in ("info", "riwayat", "he_tema", "bab"):
            self.assertEqual(sorted(d.execute(f"SELECT * FROM {t}")), sorted(b.execute(f"SELECT * FROM {t}")), t)
        for w in ("kurma", "madu", "lama", "baru"):
            q = "SELECT rowid FROM cari WHERE cari MATCH ? ORDER BY rowid"
            self.assertEqual(d.execute(q, (w,)).fetchall(), b.execute(q, (w,)).fetchall(), w)

    def test_hasil_sama_dengan_data_baru(self):
        d, berkas = self.terapkan(70_000)
        self.assertEqual(len(berkas), 1)
        self.periksa(d)

    def test_dibagi_beberapa_hari_tetap_benar(self):
        d, berkas = self.terapkan(300)     # batas kecil: harus terbagi ke beberapa berkas
        self.assertGreater(len(berkas), 1)
        self.periksa(d)

    def test_tanpa_perubahan_tanpa_berkas(self):
        cermin(self.lama, LAMA)
        cermin(self.baru, LAMA)
        self.assertEqual(rencana(self.lama, self.baru, self.out), 0)
        self.assertEqual(glob.glob(os.path.join(self.out, "*.sql")), [])

    def test_skema_berubah_ditolak(self):
        cermin(self.lama, LAMA, skema=SKEMA + "\n-- lama")
        cermin(self.baru, BARU)
        self.assertEqual(rencana(self.lama, self.baru, self.out), 2)


if __name__ == "__main__":
    unittest.main()
