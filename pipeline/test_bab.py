#!/usr/bin/env python3
"""Uji judul kitab & bab dari OpenITI (build/bab.sqlite dari pipeline/bab_openiti.py).

Pencocokan memakai isi teks. Nomor hadits hanya dipakai untuk MEMILIH di antara blok yang isinya sudah lolos
ambang (teks yang diulang penyusun di beberapa bab; 14 riwayat), jadi kesamaan nomor dengan edisi cetak tetap
hampir sepenuhnya uji independen.  Jalankan:  python3 -m unittest pipeline/test_bab.py -v
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

    def test_fihris_dibaca_utuh(self):
        # seluruh fihris rinci 9 juz dibaca langsung (docs/13): 26 bab tanpa judul lagi yang terlewat teks digital
        for no in (149, 218, 506, 882, 946, 1153, 1293, 1386, 1420, 2327, 2336, 2337, 2348, 2439, 3019, 3181, 3183,
                   3403, 3405, 5154, 5196, 5284, 5441, 5714, 6320, 6967, 7099, 7107, 7120, 7121, 7222, 7223):
            self.assertEqual(judul(f"bukhari:{no}")[1], "باب", no)
        for no in (148, 150, 1152, 1154, 1419, 1421, 2326, 2328, 3180, 3184, 3402, 3406, 7098, 7108, 7119, 7122, 7221):
            self.assertNotEqual(judul(f"bukhari:{no}")[1], "باب", no)
        self.assertEqual(judul("bukhari:1419")[1], "باب فضل صدقة الشحيح الصحيح")
        self.assertEqual(judul("bukhari:7108")[1], "باب إذا أنزل الله بقوم عذابا")


class Penguraian(unittest.TestCase):
    def test_hadits_bernomor_ganda(self):
        # teks gabungan 3164-3165 / 299-301 ada di setiap nomor; OpenITI memecahnya per nomor -> dicocokkan lewat nomor
        bab_3163 = judul("bukhari:3163")[1]
        for no in (3164, 3165):
            self.assertEqual(judul(f"bukhari:{no}")[1], bab_3163)
        for no in (299, 300, 301):
            self.assertEqual(judul(f"bukhari:{no}")[1], "باب مباشرة الحائض")
        cara = dict(q("SELECT riwayat_id, cara FROM riwayat_bab WHERE riwayat_id IN ('bukhari:3164','bukhari:300')"))
        self.assertEqual(set(cara.values()), {"nomor"})

    def test_sanad_bukan_judul_bab(self):
        # Muslim "### $ حدثنا ..." pendek, Tirmidzi "(م ٢) - حدثنا ...": awal/lanjutan hadits, bukan judul bab
        n = q("SELECT count(*) FROM riwayat_bab WHERE bab_ar LIKE 'حدثن%' OR bab_ar LIKE 'وحدثن%' "
              "OR bab_ar LIKE 'أخبرن%' OR bab_ar LIKE '(م%'")[0][0]
        self.assertEqual(n, 0)
        self.assertTrue(judul("muslim:106")[1].startswith("باب بيان الإيمان الذي يدخل به الجنة"))
        self.assertEqual(judul("ibnumajah:2016")[1], "باب")          # "باب حدثنا سويد بن سعيد" = bab tanpa judul

    def test_judul_bab_tirmidzi(self):
        # potongan baris karena penanda catatan kaki "(١)" tidak lagi menjadi judul bab
        lain = [x for (x,) in q("SELECT DISTINCT bab_ar FROM riwayat_bab WHERE riwayat_id LIKE 'tirmidzi:%'")
                if x and not norm_ar(x).startswith(("باب", "ما جاء"))]
        self.assertEqual(lain, [])
        self.assertEqual(judul("tirmidzi:13")[1], "باب ما جاء في الرخصة في ذلك")
        self.assertGreater(int(info("tirmidzi", "cocok_teks")), 3850)

    def test_judul_tambahan_muslim_bertanda_bintang(self):
        # "### || * باب ..." tidak ada di cetakan Fu'ad 'Abd al-Baqi: fihris Kitab al-Haid bab 6 = hadits 305-309,
        # halaman isi hlm. 249 tanpa judul sebelum no. 308 dan 309 (scan archive.org alfirdwsiy2018_gmail_2778)
        self.assertEqual(q("SELECT count(*) FROM riwayat_bab WHERE bab_ar LIKE '*%'")[0][0], 0)
        for rid in ("muslim:707", "muslim:708"):                    # Fu'ad no. 308, 309
            self.assertTrue(judul(rid)[1].startswith("باب جواز نوم الجنب"), rid)
        self.assertEqual(judul("muslim:709")[1], "باب وجوب الغسل على المرأة بخروج المني منها")

    def test_judul_muslim_sesuai_cetakan(self):
        # teks digital memakai judul lain untuk 5 bab ini; halaman isi cetakan Fu'ad 'Abd al-Baqi dilihat langsung
        self.assertEqual(judul("muslim:5494")[1], "باب استحباب لبس النعال وما في معناها")
        self.assertTrue(judul("muslim:5498")[1].startswith("باب استحباب لبس النعل في اليمنى أولا"))
        self.assertTrue(judul("muslim:5538")[1].startswith("باب تحريم تصوير صورة الحيوان"))
        self.assertEqual(judul("muslim:3590")[1], "باب في المصة والمصتان")
        self.assertEqual(judul("muslim:4772")[1], "باب الإمام جنة يقاتل به من ورائه ويتقى به")
        self.assertEqual(judul("muslim:5546")[1], "باب كراهة الكلب والجرس في السفر")      # bab 27 tidak ikut berubah
        # fihris menyingkat "غرز الخشب في الجدار", halaman isi = teks digital: tidak dikoreksi
        cara = q("SELECT cara FROM riwayat_bab WHERE bab_ar = 'باب غرز الخشب في جدار الجار'")
        self.assertTrue(cara and all(c != "koreksi-cetak" for (c,) in cara))

    def test_judul_bab_baris_biasa_ibnu_majah(self):
        # 121 judul bab Ibnu Majah ditulis "# باب ..." (bukan "### | باب"); fihris cetakan al-Halabi memuatnya
        self.assertEqual(judul("ibnumajah:639")[1], "باب النهي عن إتيان الحائض")
        self.assertEqual(judul("ibnumajah:638")[1], "باب ما للرجل من امرأته إذا كانت حائضا")
        self.assertEqual(judul("ibnumajah:690")[1], "باب وقت صلاة العشاء")              # "# باب / # وقت / # صلاة / # العشاء"
        self.assertEqual(judul("ibnumajah:1404")[1],
                         "باب ما جاء في فضل الصلاة في المسجد الحرام ومسجد النبي صلى الله عليه وسلم")
        n = q("SELECT count(DISTINCT kitab_ar || bab_ar) FROM riwayat_bab WHERE riwayat_id LIKE 'ibnumajah:%'")[0][0]
        self.assertGreater(n, 1450)                                          # dulu 1.415 judul berbeda

    def test_judul_bab_nasai_utuh(self):
        # judul terpecah ke beberapa baris di teks digital; fihris cetakan Abu Ghuddah (jilid 9) memuatnya utuh
        self.assertEqual(judul("nasai:158")[1], "باب الوضوء من الغائط والبول")
        self.assertTrue(judul("nasai:1011")[1].endswith("[الإسراء: 110]"))
        self.assertEqual(judul("nasai:543")[1], "أول وقت الصبح")                  # judul tanpa "###" di antara dua hadits
        self.assertEqual(judul("nasai:1066")[1], "ما يقول في قيامه ذلك")
        n = q("SELECT count(*) FROM riwayat_bab WHERE bab_ar GLOB '*0' OR bab_ar LIKE '%</%'")[0][0]
        self.assertEqual(n, 0)

    def test_judul_abu_dawud_sesuai_fihris(self):
        self.assertEqual(judul("abudawud:867")[1], "باب تفريع أبواب الركوع والسجود ووضع اليدين على الركبتين")
        self.assertEqual(judul("abudawud:3253")[1], "باب كراهية الحلف بالأمانة")
        self.assertEqual(judul("abudawud:3416")[1], "باب في كسب المعلم")
        self.assertEqual(q("SELECT count(*) FROM riwayat_bab WHERE bab_ar LIKE '%حكم الألباني%'")[0][0], 0)


class TirmidziCetak(unittest.TestCase):
    """Fihris & halaman isi cetakan Basyar 'Awwad (Dar al-Gharb 1996), lihat docs/13-verifikasi-cetak.md."""

    def test_teks_berulang_di_tempat_bernomor_sama(self):
        # Teks yang diulang penyusun di bab lain: dulu terpasang ke tempat yang salah (kitab & bab salah tampil)
        for rid, kitab, bab in (("tirmidzi:2700", "الاستيذان", "اهل الذمه"), ("tirmidzi:3227", "تفسير", "سوره يس"),
                                ("tirmidzi:3875", "المناقب", "خديجه"), ("tirmidzi:624", "الزكاه", "زكاه البقر"),
                                ("bukhari:2776", "الوصايا", "نفقه القيم للوقف"), ("ibnumajah:3441", "الطب", "يشتهي"),
                                ("ibnumajah:3584", "اللباس", "العمامه السودا"), ("nasai:290", "الطهاره", "المحرمه اذا حاضت"),
                                ("nasai:1588", "العيدين", "ذبح الامام")):
            k, bb = judul(rid)
            self.assertIn(kitab, norm_ar(k), rid)
            self.assertIn(bab, norm_ar(bb), rid)

    def test_kitab_nadzar_dan_sumpah(self):
        # «# بسم الله الرحمن الرحيم أبواب النذور والأيمان» = baris biasa di teks digital; fihris jilid 3 hlm. 630
        for no in (1524, 1536, 1547):
            self.assertTrue(judul(f"tirmidzi:{no}")[0].startswith("أبواب النذور والأيمان"), no)
        self.assertEqual(judul("tirmidzi:1493")[0], "أبواب الأضاحي")
        self.assertEqual(judul("tirmidzi:488")[0], "أبواب الجمعة")                 # teks digital: «أبواب ٣٠ الجمعة»

    def test_judul_bersih_dan_utuh(self):
        self.assertEqual(q("SELECT count(*) FROM riwayat_bab WHERE bab_ar LIKE '%@QUR@%' OR bab_ar LIKE '% ب بسم%'")[0][0], 0)
        self.assertEqual(judul("tirmidzi:244")[1], "باب ما جاء في ترك الجهر ببسم الله الرحمن الرحيم")
        self.assertEqual(judul("tirmidzi:3232")[1], "باب ومن سورة {ص}")
        # judul yang berlanjut ke baris berikutnya (cetakan: satu blok judul)
        self.assertTrue(judul("tirmidzi:2608")[1].endswith("أمرت بقتالهم حتى يقولوا: لا إله إلا الله ويقيموا الصلاة"))
        self.assertTrue(judul("tirmidzi:2876")[1].endswith("سورة البقرة وآية الكرسي"))
        self.assertTrue(judul("tirmidzi:1655")[1].endswith("وعون الله إياهم"))
        self.assertIn("أبو تراب، وأبو الحسن", judul("tirmidzi:3712")[1])
        self.assertTrue(judul("tirmidzi:3757")[1].endswith("واسمه سعيد بن زيد بن عمرو بن نفيل رضي الله عنه"))
        self.assertNotIn("@MATN@", " ".join(r[0] for r in q("SELECT bab_ar FROM riwayat_bab WHERE riwayat_id LIKE 'tirmidzi:%'")))

    def test_koreksi_dari_halaman_isi(self):
        self.assertEqual(judul("tirmidzi:1311")[1], "باب ما جاء في السلف في الطعام والتمر")
        self.assertEqual(judul("tirmidzi:2374")[1], "باب ما جاء في أخذ المال")
        self.assertEqual({judul(f"tirmidzi:{n}")[1] for n in range(3276, 3285)}, {"باب ومن سورة النجم"})
        self.assertEqual(judul("tirmidzi:3363")[1], "باب ومن سورة تبت")
        # fihris berbeda, tetapi halaman isi = teks digital: TIDAK dikoreksi
        self.assertEqual(judul("tirmidzi:3343")[1], "باب ومن سورة والشمس وضحاها")
        self.assertEqual(judul("tirmidzi:1536")[1], "باب ما جاء فيمن يحلف بالشيء ولا يستطيع")
        self.assertEqual(judul("tirmidzi:1212")[1], "باب ما جاء في التبكير بالتجارة")

    def test_bab_tambahan_ahmad_syakir_diberi_catatan(self):
        for rid in ("tirmidzi:611", "tirmidzi:612"):
            cara, catatan = q("SELECT cara, catatan FROM riwayat_bab WHERE riwayat_id=?", rid)[0]
            self.assertEqual(cara, "catatan-cetak")
            self.assertIn("Ahmad Syakir", catatan)
        self.assertEqual(q("SELECT catatan FROM riwayat_bab WHERE riwayat_id='tirmidzi:613'")[0][0], None)


class MalikCetak(unittest.TestCase):
    """Fihris & halaman isi al-Muwaththa' cetakan Fu'ad 'Abd al-Baqi (Dar Ihya' at-Turath 1406 H)."""

    def test_judul_sesuai_halaman_isi(self):
        self.assertEqual({judul(f"malik:{n}")[1] for n in range(193, 197)}, {"باب ما جاء في التأمين خلف الإمام"})
        # fihris berbeda, halaman isi = teks digital: tidak dikoreksi
        self.assertEqual(judul("malik:102")[1], "باب واجب الغسل إذا التقى الختانان")


class DarimiSyafiiCetak(unittest.TestCase):
    """ad-Darimi (Asad, Dar al-Mughni) dan asy-Syafi'i (al-Fahl, Ghiras): fihris + halaman isi cetakan."""

    def judul_edisi(self, kid, no):
        return q("SELECT bab_ar FROM riwayat_bab WHERE riwayat_id LIKE ? AND no_openiti=?", kid + ":%", no)[0][0]

    def test_judul_darimi_di_baris_berikutnya(self):
        # «### | باب» lalu «# النهي عن استقبال القبلة لغائط أو بول</span>» (halaman isi hlm. 526: judul bab ke-6)
        self.assertEqual(self.judul_edisi("darimi", 691), "باب النهي عن استقبال القبلة لغائط أو بول")
        self.assertEqual(self.judul_edisi("darimi", 159), "باب الفتيا وما فيه من الشدة")
        # bab tanpa judul sungguhan tetap «باب»: fihris memberi deskripsi dalam kurung, halaman isi hanya «باب»
        self.assertEqual(self.judul_edisi("darimi", 176), "باب")

    def test_koreksi_darimi_nomor_edisi(self):
        self.assertEqual(self.judul_edisi("darimi", 2435), "باب الجهاد في سبيل الله أفضل العمل")
        # fihris «نبيذ الخمر», halaman isi = teks digital «نبيذ الجر»: tidak dikoreksi
        self.assertEqual(self.judul_edisi("darimi", 2155), "باب النهي عن نبيذ الجر، وما ينبذ فيه")

    def test_syafii_judul_dan_nomor_satu_baris(self):
        # «### $ 1277 - باب ما كان من الطلاق والرجعة»: hadits 1277 kini bernomor edisi
        self.assertEqual(self.judul_edisi("syafii", 1277), "باب ما كان من الطلاق والرجعة")

    def test_koreksi_syafii_nomor_edisi(self):
        # halaman isi jilid 2 hlm. 33: «باب: ترك الجمعة /٦٢و/ للعذر» (penanda manuskrip, bukan huruf و)
        self.assertEqual(self.judul_edisi("syafii", 458), "باب: ترك الجمعة للعذر")
        # jilid 3 hlm. 233–234: «في الضبع» (1508–1509) lalu «في الضب» (1510 dst.)
        self.assertEqual(self.judul_edisi("syafii", 1508), "باب: في الضبع")
        self.assertEqual(self.judul_edisi("syafii", 1509), "باب: في الضبع")
        self.assertEqual(self.judul_edisi("syafii", 1510), "باب: في الضب")
        # «عنها» sudah benar di teks digital (halaman isi & fihris sama)
        self.assertEqual(self.judul_edisi("syafii", 1103), "باب زواج النبي صلى الله عليه وسلم عائشة رضي الله عنها")


class AhmadNomorEdisi(unittest.TestCase):
    """Musnad Ahmad (ar-Risalah): nomor edisi bertanda «•», «*», «°», salah ketik, dan nomor yang tak tertulis.
    Semua contoh di bawah dilihat di halaman cetak (docs/13)."""

    @classmethod
    def setUpClass(cls):
        import bab_openiti as B
        from common import SRC
        cls.blok = B.urai(os.path.join(SRC, B.BERKAS["ahmad"]), "ahmad")
        cls.no = {}
        for x in cls.blok:
            if x["no"] is not None:
                cls.no.setdefault(x["no"], x)

    def awal(self, n):
        return norm_ar(self.no[n]["teks"])[:60]

    def test_nomor_naik_dan_lengkap(self):
        nos = [x["no"] for x in self.blok if x["no"] is not None]
        self.assertTrue(all(a <= b for a, b in zip(nos, nos[1:])))
        self.assertGreaterEqual(len(set(nos)), 27630)

    def test_hadits_bertanda_terpisah(self):
        # jilid 2 hlm. 446: «• ١٣٣١ - حدثنا عبد الله، حدثني أبو معمر»; jilid 9 hlm. 93: «○ ٥٠٦٩ - قال: وجدت في كتاب أبي»
        self.assertIn("ابو معمر", self.awal(1331))
        self.assertIn("عكرمه بن خالد", norm_ar(self.no[5069]["teks"])[:120])
        self.assertIn("ابو داود المباركي", self.awal(1170))

    def test_salah_ketik_dipulihkan(self):
        # «1431» dua kali (jilid 3 hlm. 44), «13349» (jilid 21 hlm. 178), «16663» dua kali (jilid 27 hlm. 222),
        # «22293» (jilid 37 hlm. 454)
        self.assertIn("ابو عامر", self.awal(1431))
        self.assertIn("ابراهيم بن خالد", self.awal(1432))
        self.assertIn("سهيل اخو حزم", self.awal(13549))
        self.assertIn("القواريري", self.awal(16662))
        self.assertIn("محمد بن ابي بكر", self.awal(16663))
        self.assertIn("يعمر بن بشر", self.awal(22793))

    def test_nomor_tak_tertulis(self):
        # 5632 tak bernomor di teks digital («# حدثنا يحيى بن آدم…»): dipotong dari blok 5631
        self.assertIn("المعرس", norm_ar(self.no[5632]["teks"]))
        self.assertNotIn("المعرس", norm_ar(self.no[5631]["teks"]))

    def test_yang_ragu_dikosongkan(self):
        # «22669» dua kali (yang kedua mestinya 22670: beda dua digit) dan 9125+9126 tergabung: tanpa nomor
        for n in (9126, 22669, 22670):
            self.assertNotIn(n, self.no)
        self.assertTrue(self.no[9125].get("celah"))                  # memuat dua hadits -> diputuskan di main()
        self.assertEqual(q("SELECT count(*) FROM riwayat_bab WHERE riwayat_id LIKE 'ahmad:%' AND no_openiti=9125")[0][0], 0)

    def test_riwayat_lidwa_bernomor_benar(self):
        # dulu: 4041, 5054, 5054, 2331 (tergabung ke blok sebelumnya)
        for rid, n in (("ahmad:L3837", 4042), ("ahmad:L4815", 5059), ("ahmad:L4825", 5069), ("ahmad:L2216", 2332)):
            self.assertEqual(q("SELECT no_openiti FROM riwayat_bab WHERE riwayat_id=?", rid)[0][0], n, rid)


class DarimiSyafiiNomorEdisi(unittest.TestCase):
    """Pembersihan nomor yang sama dengan Musnad Ahmad (nomor_naik)."""
    no = staticmethod(lambda rid: q("SELECT no_openiti FROM riwayat_bab WHERE riwayat_id=?", rid)[0][0])

    def test_darimi_nomor_ms(self):
        # «### | 177 ms052 -»: dulu tak terbaca, riwayatnya tampil sebagai 176
        self.assertEqual(self.no("darimi:L173"), 177)
        self.assertEqual(self.no("darimi:L404"), 416)

    def test_darimi_kembar_dikosongkan(self):
        for rid in ("darimi:L1151", "darimi:L1152", "darimi:L2293", "darimi:L2294"):
            self.assertIsNone(self.no(rid), rid)

    def test_syafii_salah_ketik(self):
        # «392» di antara 691 & 693, «1720» di antara 1701 & 1703, «1393» dua kali
        self.assertEqual(self.no("syafii:L450"), 692)
        self.assertEqual(self.no("syafii:L1669"), 1702)
        self.assertEqual(self.no("syafii:L662"), 1392)

    def test_syafii_dua_hadits_satu_blok(self):
        # «### | 78 -» memuat dua hadits; yang kedua dipotong = 79 (al-Fahl jilid 1 hlm. 188: «٧٩ - … بن رقيش»)
        self.assertEqual(self.no("syafii:L1093"), 79)


class DuaHaditsEdisi(unittest.TestCase):
    """Riwayat Lidwa yang memuat dua hadits edisi berurutan diberi rentang nomor (bab_openiti.dua_blok)."""
    r = staticmethod(lambda rid: q("SELECT no_openiti, no_akhir, tahqiq FROM riwayat_bab WHERE riwayat_id=?", rid)[0])

    def test_rentang(self):
        # L46 = hadits 47 (Ibnu Mahdi) + 48 (Muhammad bin Ja'far … «إلا أنه قال»); L257 = 266 + zawa'id 267 («فذكر نحو»)
        self.assertEqual(self.r("ahmad:L46")[:2], (47, 48))
        self.assertEqual(self.r("ahmad:L257")[:2], (266, 267))

    def test_tanpa_penilaian_muhaqqiq(self):
        # dua hadits bisa berbeda penilaiannya: penilaian satu blok tidak dipasang
        self.assertIsNone(self.r("ahmad:L46")[2])
