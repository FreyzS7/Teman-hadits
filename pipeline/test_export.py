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


class RapikanTerjemah(unittest.TestCase):
    """pipeline/rapikan_terjemah.py: contoh nyata dari pemindaian terjemah Lidwa."""

    def setUp(self):
        from rapikan_terjemah import rapikan, terpotong
        self.r = lambda t, rid=None: rapikan(t, rid)[0]
        self.rapikan, self.terpotong = rapikan, terpotong

    def test_kata_tugas_ganda(self):
        self.assertEqual(self.r("yaitu dari meminum dari dari al hantam"), "yaitu dari meminum dari al hantam")   # bukhari:87
        self.assertEqual(self.r("berkata, telah telah menceritakan kepada kami"), "berkata, telah menceritakan kepada kami")
        self.assertEqual(self.r("dari [Abu Abu Hurairah] Rasulullah"), "dari [Abu Hurairah] Rasulullah")          # muslim:7278
        self.assertEqual(self.r("kepada kami kami [Baqiyah]"), "kepada kami [Baqiyah]")

    def test_pengulangan_yang_mungkin_sengaja_dibiarkan(self):
        for t in ("Nama Allah Allah yang paling agung", "Aku tidak tidak peduli", "Labbaika labbaika",
                  "ummatku ummatku", "[Harun Al Al'war]"):
            self.assertEqual(self.r(t), t)

    def test_kata_ulang_diberi_tanda_hubung(self):
        self.assertEqual(self.r("orang orang dan laki laki, tiba tiba"), "orang-orang dan laki-laki, tiba-tiba")
        self.assertEqual(self.r("Hamba Hamba Allah"), "Hamba-hamba Allah")
        self.assertEqual(self.r("khawatir jangAn jangan hal itu"), "khawatir jangan-jangan hal itu")      # ahmad:L15433

    def test_entitas_spasi_dan_nomor_catatan(self):
        self.assertEqual(self.r("bertaubat darinya.&quot;"), 'bertaubat darinya."')                          # tirmidzi:1973
        self.assertEqual(self.r("Ibnu Abu Aufa . Abu Isa berkata"), "Ibnu Abu Aufa. Abu Isa berkata")          # tirmidzi:507
        self.assertEqual(self.r("bahwa Rasulullah  pernah bersabda"), "bahwa Rasulullah pernah bersabda")
        self.assertEqual(self.r("hingga pipinya kelihatan. 185"), "hingga pipinya kelihatan.")                # syafii:L179
        self.assertEqual(self.r('oleh kalian."731'), 'oleh kalian."')
        self.assertEqual(self.r("sebanyak 100"), "sebanyak 100")                                             # angka isi tetap

    def test_kurung_rusak_diperbaiki_manual(self):
        t = "disampaikan oleh [Aun bin Abdullah [kepadaku, aku kagum dengan hadis tersebut"
        self.assertEqual(self.r(t, "darimi:L509"), "disampaikan oleh [Aun bin Abdullah] kepadaku, aku kagum dengan hadis tersebut")
        self.assertIn("aku kagum", tanpa_kurung(self.r(t, "darimi:L509")))   # matan tidak lagi terbuang dari pencarian
        self.assertEqual(self.r(t), t.replace("  ", " "))                  # perbaikan manual hanya untuk riwayatnya

    def test_penanda_belum_selesai(self):
        t, tl = self.rapikan("belum sampai pada bagian dasarnya #BELUM SELESAI#")                           # ahmad:L16917
        self.assertEqual((t, tl), ("belum sampai pada bagian dasarnya (…)", True))
        self.assertFalse(self.rapikan("terjemah biasa.")[1])

    def test_terpotong(self):
        arab = "ا" * 400
        self.assertTrue(self.terpotong("x" * 200, arab))                     # tanpa tanda akhir, 0,5 x Arab
        self.assertFalse(self.terpotong("x" * 200 + ".", arab))
        self.assertTrue(self.terpotong("x" * 300 + ",", arab))              # berakhir koma, lebih pendek dari Arab
        self.assertFalse(self.terpotong("x" * 500 + ",", arab))
        self.assertFalse(self.terpotong("x" * 100, "ا" * 200))              # Arab pendek: tidak dinilai
