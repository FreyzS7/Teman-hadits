#!/usr/bin/env python3
"""Uji emas (golden test): fakta yang dapat dicek siapa pun di kitab cetak.

Tes ini sengaja tidak bergantung pada pendapat pembuat situs. Setiap kasus menyebut
rujukan cetak yang bisa dibuka untuk memastikan tes itu sendiri benar.

Jalankan setelah build:  python3 -m unittest pipeline/test_golden.py -v
"""
import json
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB_PATH, akar_ar, norm_ar

db = sqlite3.connect(DB_PATH)


def q(sql, *a):
    return db.execute(sql, a).fetchall()


def cari_frasa(frasa, kitab=None):
    """Cari frasa Arab (setelah normalisasi + pemotongan awalan) di riwayat yang terbit."""
    f = akar_ar(norm_ar(frasa))
    rows = q("SELECT riwayat_id FROM cari WHERE cari MATCH ?", f'arab_akar:"{f}"')
    ids = [r[0] for r in rows]
    return [i for i in ids if kitab is None or i.startswith(kitab + ":")]


class AdaDiKitab(unittest.TestCase):
    """Hadits yang pasti ada di posisi tertentu."""

    def test_bukhari_1_hadits_niat(self):
        # Shahih al-Bukhari no. 1 (penomoran Fath al-Bari / Fu'ad 'Abdul Baqi): Kitab Bad' al-Wahyi.
        r = q("SELECT arab, tingkat, no_lidwa FROM riwayat WHERE id='bukhari:1'")[0]
        self.assertIn("انما الاعمال بالنيات", norm_ar(r[0]))
        self.assertEqual(r[1], "A")
        self.assertEqual(r[2], 1)

    def test_bukhari_1_sanad_lengkap(self):
        # Sanad Bukhari no. 1: al-Humaidi > Sufyan > Yahya bin Sa'id > Muhammad bin Ibrahim at-Taimi
        # > 'Alqamah bin Waqqash > 'Umar bin al-Khaththab.
        rantai = json.loads(q("SELECT rantai_json FROM riwayat WHERE id='bukhari:1'")[0][0])
        teks = " | ".join(rantai)
        for nama in ["Humaidi", "Sufyan", "Yahya bin Sa'id", "Muhammad bin Ibrahim", "Alqamah", "Umar bin Al Khaththab"]:
            self.assertIn(nama, teks)

    def test_muslim_1907_hadits_niat(self):
        # Shahih Muslim no. 1907 (penomoran Fu'ad 'Abdul Baqi), Kitab al-Imarah.
        rows = [r for r in q("SELECT no_arab, arab FROM riwayat WHERE kitab_id='muslim'")
                if "انما الاعمال بالنيه" in norm_ar(r[1])]
        self.assertTrue(rows)
        self.assertTrue(all(str(r[0]).startswith("1907") for r in rows))

    def test_bukhari_2236_haram_jual_babi(self):
        # Bukhari no. 2236 (Kitab al-Buyu'): "إن الله ورسوله حرم بيع الخمر والميتة والخنزير والأصنام".
        self.assertIn("bukhari:2236", cari_frasa("حرم بيع الخمر والميتة والخنزير"))


class Takhrij(unittest.TestCase):
    def test_tujuh_tempat_hadits_niat_di_bukhari(self):
        # Al-Bukhari meriwayatkan hadits niat di 7 tempat: no. 1, 54, 2529, 3898, 5070, 6689, 6953
        # (lihat Fath al-Bari, syarah hadits no. 1). Pencocokan matan harus menemukan ketujuhnya.
        from common import stem_ar

        def grams(t):
            w = [stem_ar(x) for x in norm_ar(t).split()]
            return {" ".join(w[i:i + 2]) for i in range(len(w) - 1)}

        arab = q("SELECT arab FROM riwayat WHERE id='bukhari:1'")[0][0]
        G = grams(arab.split('"', 1)[1])
        ketemu = {rid for rid, ar in q("SELECT id, arab FROM riwayat WHERE kitab_id='bukhari' AND tingkat IN ('A','B')")
                  if len(G & grams(ar)) / len(G) >= 0.4}
        self.assertEqual(ketemu, {f"bukhari:{n}" for n in (1, 54, 2529, 3898, 5070, 6689, 6953)})


class TakhrijTersimpan(unittest.TestCase):
    """Tabel mirip di build/takhrij.sqlite (pipeline/takhrij.py) harus memuat keluarga hadits niat."""

    def test_keluarga_hadits_niat(self):
        t = sqlite3.connect(os.path.join(os.path.dirname(DB_PATH), "takhrij.sqlite"))
        b = {r[0] for r in t.execute("SELECT b FROM mirip WHERE a='bukhari:1'")}
        for n in (54, 2529, 3898, 5070, 6689, 6953):
            self.assertIn(f"bukhari:{n}", b)
        for rid in ("muslim:4927", "abudawud:2201", "tirmidzi:1647", "nasai:75", "ibnumajah:4227"):
            self.assertIn(rid, b)
        # tidak boleh ada pasangan dengan hadits lain dari Bukhari selain 7 tempat itu
        self.assertEqual({x for x in b if x.startswith("bukhari:")},
                         {f"bukhari:{n}" for n in (54, 2529, 3898, 5070, 6689, 6953)})


class TidakAdaDiKitab(unittest.TestCase):
    """Situs wajib jujur: yang tidak ada harus dilaporkan tidak ada."""

    def test_niat_tidak_ada_di_muwaththa_yahya(self):
        # Hadits "innamal a'malu bin niyyat" TIDAK terdapat dalam al-Muwaththa' riwayat Yahya al-Laitsi
        # (ia ada di riwayat Muhammad bin al-Hasan asy-Syaibani). Kesalahan atribusi yang sering terjadi.
        self.assertEqual(cari_frasa("انما الاعمال بالنيات", "malik"), [])

    def test_hadits_palsu_populer_tidak_ada(self):
        # "Tuntutlah ilmu walau ke negeri Cina": tidak ada di kitab-kitab ini
        # (Ibnul Jauzi memasukkannya ke al-Maudhu'at; al-Albani menilainya batil).
        self.assertEqual(cari_frasa("اطلبوا العلم ولو بالصين"), [])
        # "Cinta tanah air sebagian dari iman": tidak ada asalnya dalam kitab hadits.
        self.assertEqual(cari_frasa("حب الوطن من الايمان"), [])


class PencarianTanpaAI(unittest.TestCase):
    def test_tarawih_lewat_qiyam_ramadhan(self):
        # Kata "tarawih" tidak ada di teks Arab hadits; kamus konsep harus menemukannya lewat قيام رمضان.
        # Bukhari 2009 (Kitab Shalat at-Tarawih) dan Muslim 759 = riwayat "man qama Ramadhan".
        from cari import cari
        out = cari("tolong carikan hadits tentang sholat tarawih", batas=500, db=db)
        ids = {h["id"] for h in out["hasil"]}
        self.assertIn("bukhari:2009", ids)
        self.assertTrue(any(h["kitab"] == "muslim" and str(h["no_arab"]).startswith("759") for h in out["hasil"]))
        self.assertGreaterEqual(out["total"], 40)
        self.assertEqual([k["id"] for k in out["rencana"]["konsep"]], ["tarawih"])

    def test_babi_menemukan_bukhari_2236(self):
        from cari import cari
        ids = {h["id"] for h in cari("apakah makan babi itu hukumnya haram?", batas=500, db=db)["hasil"]}
        self.assertIn("bukhari:2236", ids)


class Integritas(unittest.TestCase):
    def test_jumlah_baris_sesuai_readme_sumber(self):
        # Angka dari README repo sumber (pernyataan pihak ketiga, bukan hitungan kita).
        harapan = {"bukhari": 7008, "muslim": 5362, "abudawud": 4590, "ibnumajah": 4332, "nasai": 5662,
                   "tirmidzi": 3891, "malik": 1594, "ahmad": 26363, "darimi": 3367, "syafii": 1800}
        for k, n in harapan.items():
            self.assertEqual(q("SELECT jumlah_lidwa FROM kitab WHERE id=?", k)[0][0], n, k)

    def test_tidak_ada_riwayat_terbit_tanpa_teks_arab(self):
        self.assertEqual(q("SELECT count(*) FROM riwayat WHERE tingkat IN ('A','B') AND length(trim(arab))<10")[0][0], 0)

    def test_tingkat_A_selalu_punya_terjemah(self):
        self.assertEqual(q("SELECT count(*) FROM riwayat WHERE tingkat='A' AND (terjemah IS NULL OR terjemah='')")[0][0], 0)

    def test_penilaian_selalu_bernama(self):
        self.assertEqual(q("SELECT count(*) FROM penilaian WHERE trim(penilai)='' OR trim(hukum)=''")[0][0], 0)

    def test_bukhari_muslim_tanpa_penilaian_per_hadits(self):
        # Sumber kita tidak memuat penilaian per hadits untuk Bukhari/Muslim; situs tidak boleh mengarangnya.
        self.assertEqual(q("SELECT count(*) FROM penilaian WHERE riwayat_id LIKE 'bukhari:%' "
                           "OR riwayat_id LIKE 'muslim:%'")[0][0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
