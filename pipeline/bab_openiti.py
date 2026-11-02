#!/usr/bin/env python3
"""Judul kitab & bab berbahasa Arab dari teks OpenITI, dipetakan ke riwayat kita MENURUT ISI.

Masukan : sources/openiti-*/... (lihat sources.json), build/teman-hadits.sqlite
Keluaran: build/bab.sqlite
  riwayat_bab(riwayat_id, kitab_ar, bab_ar, skor, cara, no_openiti)
  kitab_nama(kitab_id, bab_no, nama_ar, setuju, total)   -- nama Arab untuk "kitab" (section) fawazahmed0
  info(kitab_id, kunci, nilai)

Cara:
  1. Urai berkas OpenITI: setiap baris "### " diklasifikasi menjadi kitab / bab / penanda hadits / halaman.
     Teks di antara penanda menjadi "blok", membawa judul kitab & bab terakhir.
  2. Setiap riwayat kita dicocokkan ke blok yang paling memuat teksnya (2-gram berbobot IDF, seperti
     takhrij). Cocok bila >= 70% bobot 2-gram riwayat ada di blok. Nomor penomoran tidak dipakai untuk
     mencocokkan, hanya untuk MENGUJI hasilnya.
  3. Riwayat yang tidak cocok mendapat judul dari tetangganya hanya bila riwayat sebelum & sesudahnya
     berada di bab yang sama (cara = "urutan").
     Hadits bernomor ganda yang teks gabungannya dipecah OpenITI per nomor mendapat blok bernomor sama, dengan
     syarat ketat (lihat isi_dari_nomor; cara = "nomor").
  4. Nama Arab tiap "kitab" fawazahmed0 = judul kitab OpenITI yang paling banyak dimiliki riwayat di dalamnya.

Uji (dilaporkan, juga di test_bab.py):
  - urutan: blok yang cocok untuk riwayat berurutan harus naik;
  - nomor: bila blok OpenITI bernomor, nomornya sama dengan nomor standar riwayat;
  - kesepakatan kitab: berapa % riwayat dalam satu kitab fawazahmed0 sepakat pada satu judul kitab OpenITI.

Jalankan:  python3 pipeline/bab_openiti.py
"""
import collections
import json
import math
import os
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, SRC, norm_ar
from hadeethenc import grams

OUT = os.path.join(BUILD, "bab.sqlite")
BERKAS = {
    "bukhari": "openiti-0275AH/0256Bukhari.Sahih.Shamela0001681-ara1",
    "muslim": "openiti-0275AH/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown",
    "abudawud": "openiti-0275AH/0275AbuDawudSijistani.Sunan.Shamela0001726-ara1",
    "ibnumajah": "openiti-0275AH/0273IbnMaja.Sunan.Shamela0001198-ara1",
    "tirmidzi": "openiti-0300AH/0279Tirmidhi.Sunan.Shamela0007895-ara2",
    "nasai": "openiti-0325AH/0303Nasai.SunanSughra.Shamela0000829-ara1",
    "malik": "openiti-0200AH/0179MalikIbnAnas.Muwatta.Shamela0001699-ara1.completed",
    # Kitab yang di sumber kita hanya punya satu sumber digital (Lidwa): OpenITI = sumber kedua + nomor edisi tahqiq.
    "ahmad": "openiti-0250AH/0241IbnHanbal.Musnad.Shamela0025794-ara1.mARkdown",      # ar-Risalah (al-Arna'uth dkk.)
    "darimi": "openiti-0275AH/0255CabdAllahDarimi.Sunan.Shamela0021795-ara3",        # Dar al-Mughni (Husain Salim Asad)
    "syafii": "openiti-0225AH/0204Shafici.Musnad.Shamela0009615-ara1",              # Ghiras (Mahir Yasin al-Fahl)
}
EDISI = {"ahmad": "ar-Risalah (tahqiq Syu'aib al-Arna'uth dkk.)", "darimi": "Dar al-Mughni (tahqiq Husain Salim Asad)",
         "syafii": "Ghiras (tahqiq Mahir Yasin al-Fahl)"}
LIDWA_SAJA = {"ahmad", "darimi", "syafii"}
# Musnad Ahmad: judul tingkat 1–2 ("مسند الصحابة بعد العشرة") = kelompok besar; tingkat 3+ ("مسند عمر بن الخطاب") = bab.
TINGKAT_KITAB = {"ahmad": 2}
AMBANG = 0.7
# Kitab yang nomor hadits OpenITI-nya = nomor standar riwayat kita (info nomor_sama: Bukhari 96%, Tirmidzi 99,6%,
# Abu Dawud/Ibnu Majah/Nasa'i 99,7-99,8%). Muslim (penomoran lain), Malik (blok tanpa nomor), Ahmad/Darimi/Syafi'i
# (nomor Lidwa) tidak termasuk: kesamaan nomor di sana kebetulan.
NOMOR_SEJAJAR = {"bukhari", "tirmidzi", "abudawud", "ibnumajah", "nasai"}
_GLOSARIUM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "glosarium_kitab.json"), encoding="utf8"))
_GLOS = {norm_ar(k): v for k, v in _GLOSARIUM["nama"].items()}


def nama_indonesia(kitab_ar):
    """'كتاب البيوع' -> 'Kitab Jual Beli'; 'أبواب الطهارة عن رسول الله…' -> 'Bab-bab Thaharah (Bersuci)'.
    None bila tidak ada di glosarium (glosarium disusun Teman Hadits, belum ditinjau)."""
    if not kitab_ar:
        return None
    n = norm_ar(kitab_ar)
    awal = "Kitab " if re.sub(r"^و?من\s+", "", n).startswith("كتاب") else "Bab-bab " if n.startswith("ابواب") else ""
    n = re.sub(r"^و?من\s+", "", n)
    inti = re.sub(r"^(كتاب|ابواب)\s+", "", n)
    inti = re.sub(r"\s*عن رسول الله.*$", "", inti).strip()
    v = _GLOS.get(inti)
    return (awal + v) if v else None
_ANGKA_TIMUR = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NOMOR_SAJA = re.compile(r"^\s*\(?\s*([0-9٠-٩]+)\s*\)?\s*(?:ms\d+\s*)?[-–]?\s*$")   # ad-Darimi: «### | 177 ms052 -»
_AWALAN_NOMOR = re.compile(r"^\s*(?:\(?\s*[0-9٠-٩]+\s*\)?\s*[-–]?\s*)+")
_SAMPAH = re.compile(r"ms\d+|PageV\d+P\d+|\[ص:\s*\d+\]")


def bersihkan_judul(t):
    t = _SAMPAH.sub(" ", t).replace("@QUR@", " ")    # penanda ayat OpenITI ("باب ومن سورة @QUR@ {ص}")
    t = re.sub(r"(?<!\S)ب بسم الله", "ببسم الله", t)  # Tirmidzi: cetakannya «ترك الجهر ببسم الله الرحمن الرحيم»
    t = re.sub(r"\(\s*\d+\s*\)", " ", t)            # penanda catatan kaki "(1)" di judul
    t = re.sub(r"[\"“”]+", "", t)
    t = re.sub(r"</?[a-zA-Z][^>]*>", " ", t)          # sisa markup HTML di teks digital ("</span>")
    t = re.sub(r"\s*«\s*$", "", t)                   # tanda kutip pembuka yang tertinggal di akhir judul
    t = re.sub(r"(?<!\d)0\s*$", "", t)                # Nasa'i: penanda akhir hadits "0" yang ikut ke lanjutan judul
    return re.sub(r"\s+", " ", t).strip(" :.-–،")


def bersihkan_kitab(t):
    """Judul kitab: seperti judul bab, ditambah membuang angka lepas («أبواب ٣٠ الجمعة» di teks digital Tirmidzi;
    fihris cetaknya «أبواب الجمعة»)."""
    return bersihkan_judul(re.sub(r"(?<!\S)[0-9٠-٩]+(?!\S)", " ", t))


# Judul tingkat kitab. "أبواب" hanya tingkat kitab di Jami' at-Tirmidzi; di Abu Dawud ia sub-bagian
# di dalam kitab (mis. "أبواب قيام الليل" di dalam كتاب الصلاة), jadi tidak boleh menimpa nama kitab.
AWALAN_KITAB = {"tirmidzi": ("كتاب", "ابواب")}


_AWAL_SANAD = re.compile(r"^(?:و)?(?:حدثنا|حدثني|اخبرنا|اخبرني|انبانا|سمعت|قال|وقال|ح|عن|حدثنيه|حدثناه|ثنا|نا)\b")
# Baris "###" yang BUKAN judul bab walau pendek (teks sudah dinormalkan norm_ar):
_HEADING_SANAD = re.compile(r"^(?:و)?(?:حدثنا|حدثني|اخبرنا|اخبرني|انبانا|حدثنيه|حدثناه)\b")   # awal sanad
_MUKARRAR = re.compile(r"^\s*\(\s*م\s*[0-9٠-٩]*\s*\)\s*[-–]?\s*")                             # "(م ٢) -" Tirmidzi
_BAB_FIHRIS = re.compile(r"^باب\s+(?:حدثنا|حدثني|اخبرنا|اخبرني)\b")


# Musnad Ahmad (ar-Risalah): «# 12 - …», juga bertanda «# • 423 - …» (zawa'id Abdullah), «# * 14 - …», «# ° 519 - …»,
# «# (•) 4344 - …», «# ° • 1539 - …», «# 9936، 9937 - …» (satu hadits dua nomor), «# 16100/1 - …», «# 544 ms0141 - …»,
# «# • 7110 -[قال …». Dulu hanya bentuk pertama yang dikenali: ±700 hadits bertanda tergabung ke blok hadits
# sebelumnya, sehingga riwayatnya tampil dengan nomor edisi (dan penilaian muhaqqiq) hadits sebelumnya.
# Varian lain: «# 1981 حدثنا» (tanpa «-»), «# • 6885 (1) - …», «# 11073/ أ - …», «# "16152- …», «# (1) 17461 - …»,
# «# 24009 /1 - …». Grup 2 = sub-nomor (/1, /أ): nomor sama berturut-turut hanya sah bila bersub-nomor.
_NO_AHMAD = re.compile(r'^#\s+"?(?:\(\d+\)\s*)?(?:\(?[•*°]\)?\s*)*(\d+)(\s*/\s*\S{1,2}(?=\s|-)|\s*[،,]\s*\d+)?\s*'
                       r'(?:\(\d+\)\s*)?(?:ms\d+\s*)?(?:-\s*|(?=حدثنا|حدثني))(.*)$')
# Tiga hadits mulai di tengah baris: «… قصدا " (1) 21036 - حدثنا …». Hanya dipisah bila nomornya = nomor sebelumnya + 1.
_NO_AHMAD_TENGAH = re.compile(r'(?:^|\s)(?:\(\d+\)\s*)?(\d{2,5})\s*-\s*(?=(?:ms\d+\s*)?(?:حدثنا|حدثني|قال|أخبرنا|$))')


def _satu_digit(a, b):
    """a dan b sama, beda satu digit, atau dua digit bersebelahan tertukar (salah ketik, bukan nomor lain)."""
    a, b = str(a), str(b)
    if len(a) != len(b):
        return False
    beda = [i for i in range(len(a)) if a[i] != b[i]]
    return len(beda) <= 1 or (len(beda) == 2 and beda[1] == beda[0] + 1 and a[beda[0]] == b[beda[1]] and a[beda[1]] == b[beda[0]])


def nomor_naik(blok):
    """Nomor edisi di luar urutan naik terpanjang (salah ketik teks digital, mis. «2300» di tengah 233xx) dikosongkan:
    blok tetap terpisah, tetapi tanpa nomor, daripada menampilkan nomor yang salah. Nomor sama berturut-turut
    («16100/1», «16100/2») tetap sah."""
    import bisect
    pos = [i for i, b in enumerate(blok) if b["no"] is not None]
    ekor, ekor_i, induk = [], [], {}
    for i in pos:
        n = blok[i]["no"]
        k = bisect.bisect_right(ekor, n)
        induk[i] = ekor_i[k - 1] if k else None
        if k == len(ekor):
            ekor.append(n); ekor_i.append(i)
        else:
            ekor[k], ekor_i[k] = n, i
    sah, i = set(), (ekor_i[-1] if ekor_i else None)
    while i is not None:
        sah.add(i); i = induk[i]
    for i in pos:
        if i not in sah:
            blok[i]["no_asli"], blok[i]["no"] = blok[i]["no"], None
    # nomor sama berturut-turut tanpa sub-nomor (mis. «1431» dua kali; yang kedua mestinya 1432): tak bisa dipastikan
    # mana yang salah ketik, jadi semuanya dikosongkan
    pos = [i for i in pos if blok[i]["no"] is not None]
    for a, b in zip(pos, pos[1:]):
        if blok[a]["no"] == blok[b]["no"] and not blok[b].get("sub"):
            blok[a]["ragu"] = blok[b]["ragu"] = True
    for i in pos:
        if blok[i].pop("ragu", False):
            blok[i]["no_asli"], blok[i]["no"] = blok[i]["no"], None
    # Pulihkan salah ketik bila pasti: deretan blok yang nomornya dikosongkan di antara n dan m mengisi PERSIS celah
    # n+1..m-1, dan tiap nomor asli hanya beda satu digit dari nomor sasarannya («13349» di antara 13548 & 13550 ->
    # 13549; «1431» dua kali di antara 1430 & 1433 -> 1431, 1432). Semua kasus dicek di halaman cetak (docs/13).
    pos = [i for i, b in enumerate(blok) if b["no"] is not None or "no_asli" in b]
    k = 0
    while k < len(pos):
        if blok[pos[k]]["no"] is not None:
            k += 1
            continue
        j = k
        while j < len(pos) and blok[pos[j]]["no"] is None:
            j += 1
        if 0 < k and j < len(pos):
            n, m = blok[pos[k - 1]]["no"], blok[pos[j]]["no"]
            run = pos[k:j]
            if m - n - 1 == len(run) and all(_satu_digit(blok[i]["no_asli"], n + 1 + t) for t, i in enumerate(run)):
                for t, i in enumerate(run):
                    blok[i]["no"], blok[i]["akhir"] = n + 1 + t, None
        k = j
    # celah: blok n lalu langsung n+2 (tanpa hadits tak bernomor di antaranya) = blok n memuat hadits n+1 yang tak
    # bernomor di teks digital (mis. 5632: «# حدثنا يحيى بن آدم…»). Tepat satu calon awal hadits -> dipotong di situ;
    # selain itu blok ditandai «celah»: bila lebih dari satu riwayat jatuh ke blok itu, ia memuat dua hadits dan
    # nomornya dikosongkan di main(); bila hanya satu, hadits yang hilang memang tidak ada di teks digital (ad-Darimi
    # 589) dan nomor blok itu sah.
    hasil = []
    for k, b in enumerate(blok):
        hasil.append(b)
        if b["no"] is None:
            continue
        akhir = max(b.get("akhir") or 0, b["no"])
        nxt = next((x for x in blok[k + 1:] if x["no"] is not None or re.search(r"حدثنا|حدثني|أخبرنا", x["teks"])), None)
        if nxt is None or nxt["no"] is None or nxt["no"] <= akhir + 1:
            continue
        if nxt["no"] == akhir + 2 and len(b.get("calon") or []) == 1:
            c = b["calon"][0]
            hasil[-1] = dict(b, teks=b["teks"][:c].strip(), tahqiq=None, akhir=None)
            hasil.append(dict(b, teks=b["teks"][c:].strip(), tahqiq=None, no=akhir + 1, akhir=None, sub=False))
        else:
            b["celah"] = True       # mungkin memuat hadits tak bernomor: diputuskan di main() dari jumlah riwayat
    blok[:] = hasil


def urai(path, kid=None):
    """Kembalikan daftar blok: {kitab, bab, no, teks, tahqiq}."""
    awalan = AWALAN_KITAB.get(kid, ("كتاب",))
    tingkat_kitab = TINGKAT_KITAB.get(kid)
    blok, kitab, bab, no, teks = [], None, None, None, []
    if kid == "darimi":
        kitab = "المقدمة"     # Sunan ad-Darimi dibuka dengan Muqaddimah panjang sebelum كتاب الطهارة (tanpa judul di berkas)
    tahqiq, mode_tahqiq = [], False
    # "### | باب" lalu judulnya di baris "# ..." berikutnya (gaya teks digital Bukhari). Bab tanpa judul sungguhan
    # langsung diikuti sanad ("حدثنا ..."), jadi baris pertama yang BUKAN awal sanad adalah judul bab itu.
    tunggu_judul = False
    # Ibnu Majah: 121 judul bab ditulis sebagai baris biasa "# باب ..." (bukan "### | باب"), kadang terpotong ke
    # beberapa baris ("# باب" / "# وقت" / "# صلاة" / "# العشاء"). judul_terbuka = baris pendek berikutnya ikut judul.
    judul_terbuka = False
    # Tirmidzi: satu judul kitab ditulis sebagai baris biasa, «# بسم الله الرحمن الرحيم أبواب النذور والأيمان» +
    # «# عن رسول الله صلى الله عليه وسلم». Tanpa ini, 24 hadits nadzar & sumpah tampil di bawah «أبواب الأضاحي».
    kitab_terbuka = False
    # Tirmidzi: blok judul bab di cetakan kadang dua baris («باب مناقب علي بن أبي طالب رضي الله عنه» / «يقال وله
    # كنيتان: أبو تراب، وأبو الحسن»), dan teks digital memotong judul di akhir baris («باب ما جاء في قول النبي ﷺ:» /
    # «# أمرت بقتالهم…»). judul_tir = baris pendek sesudah judul bab, sebelum hadits pertama, ikut judul.
    judul_tir, judul_tir_mentah = False, ""
    sub = False                                   # Ahmad: nomor bersub-nomor («16100/1»)
    akhir_no = None                               # Ahmad: «9936، 9937» = satu hadits dua nomor (akhir 9937)
    calon = []                                    # Ahmad: posisi «# حدثنا» sesudah catatan «(1)» = awal hadits tanpa nomor?

    def tutup():
        if teks:
            blok.append({"kitab": kitab, "bab": bab, "no": no, "teks": " ".join(teks), "tahqiq": " ".join(tahqiq) or None,
                         "sub": sub, "akhir": akhir_no, "calon": calon})

    semua = open(path, encoding="utf8").read().split("\n")
    for idx, baris in enumerate(semua):
        if baris.startswith("#META#") or baris.startswith("######"):
            continue
        if baris.startswith("### "):
            m = re.match(r"^### (\|+|\$)\s*(.*)$", baris)
            if not m:
                continue
            isi = m.group(2)
            if re.search(r"\[ص\s*:", isi) and len(norm_ar(re.sub(r"\[ص\s*:[^\]]*\]", " ", _SAMPAH.sub(" ", isi)))) < 5:
                continue                                  # penanda halaman cetak: bukan batas hadits/bab
            # Darimi (Asad): penilaian muhaqqiq; Bukhari dll.: "[تعليق مصطفى البغا]" = komentar editor; Abu Dawud:
            # "[حكم الألباني] :" = catatan penilaian. Semuanya BUKAN judul bab.
            if "تعليق المحقق" in isi or re.search(r"\[\s*(?:تعليق|حكم الألباني)", isi):
                mode_tahqiq = True
                continue
            mode_tahqiq = False
            sambung, judul_terbuka = judul_terbuka, False
            polos = norm_ar(_AWALAN_NOMOR.sub("", isi))
            mnb = re.match(r"^\s*([0-9٠-٩]+)\s*-\s*(باب\b.*)$", isi) if kid == "syafii" else None   # di Muslim: nomor bab
            if mnb:                                        # Syafi'i: "### $ 1277 - باب ما كان من الطلاق والرجعة"
                tunggu_judul = judul_tir = False           # = judul bab baru + awal hadits bernomor dalam satu baris
                tutup()
                bab = bersihkan_judul(mnb.group(2))
                teks, tahqiq, no = [], [], int(mnb.group(1).translate(_ANGKA_TIMUR))
                akhir_no, calon, sub = no, [], False
                continue
            mn = _NOMOR_SAJA.match(isi)
            if mn:                                         # "### | 12 - " = awal hadits bernomor
                tunggu_judul = judul_tir = False
                tutup()
                teks, tahqiq, no = [], [], int(mn.group(1).translate(_ANGKA_TIMUR))
                akhir_no, calon, sub = no, [], False
                continue
            if tingkat_kitab and m.group(1) != "$":       # judul bertingkat (Musnad Ahmad)
                tutup()
                teks, tahqiq, no = [], [], None
                if len(m.group(1)) <= tingkat_kitab:
                    kitab, bab = bersihkan_judul(isi), None
                else:
                    bab = bersihkan_judul(isi)
                continue
            # "ومن كتاب الزكاة" / "من كتاب المناسك" (gaya ad-Darimi) juga judul kitab
            inti_polos = re.sub(r"^و?من\s+", "", polos)
            if inti_polos.startswith(awalan) or polos == "بد الوحي" or polos.startswith("مقدمه الامام"):   # hamzah sudah dibuang norm_ar
                tutup()
                teks, tahqiq, no = [], [], None
                kitab, bab = bersihkan_kitab(_AWALAN_NOMOR.sub("", isi)), None
                continue
            if m.group(1) == "$" and len(polos.split()) > 12:   # Muslim: "### $ وحدثنا ..." = awal hadits
                tutup()
                teks, tahqiq, no = [isi], [], None
                continue
            if kid == "muslim" and isi.lstrip().startswith("*"):
                # "### || * باب ..." (59 baris) = judul tambahan teks digital, TIDAK ada di cetakan Fu'ad 'Abd al-Baqi:
                # fihrisnya (mis. Kitab al-Haid bab 6 = hadits 305-309) dan halaman isinya (hlm. 249) tanpa judul itu.
                continue
            if _MUKARRAR.match(isi):                        # Tirmidzi: "### || (م ١) - وسمعت ..." = lanjutan hadits bernomor
                teks.append(_MUKARRAR.sub("", isi))
                continue
            if _HEADING_SANAD.match(polos):                 # Muslim: "### $ حدثنا قتيبة ..." pendek = awal hadits, BUKAN judul
                tutup()
                teks, tahqiq, no = [isi], [], None
                continue
            if kid == "tirmidzi" and polos and not re.match(r"^(?:باب|ما جاء)\b", polos):
                # Teks digital Tirmidzi memecah baris di penanda catatan kaki "(١)", sehingga potongan judul/teks
                # ("### || (١) عمرو بن نفيل رضي الله عنه", "### || (غلبت الروم)") tampil sebagai baris "###".
                # Judul bab Tirmidzi selalu diawali "باب"/"ما جاء"; selain itu = lanjutan teks (atau lanjutan judul
                # bila tepat sesudah judul bab, sebelum hadits pertama).
                if judul_tir and not teks and "@MATN@" not in isi and not _AWAL_SANAD.match(polos) and len(polos.split()) <= 16:
                    judul_tir_mentah += " " + _AWALAN_NOMOR.sub("", isi)
                    bab = bersihkan_judul(judul_tir_mentah)
                    continue
                teks.append(_AWALAN_NOMOR.sub("", isi))
                continue
            if kid == "nasai" and sambung and bab is not None and polos and len(polos.split()) <= 30:
                # Nasa'i: judul terpecah ke beberapa baris "###" ("### || باب" + "### || الوضوء من الغائط")
                bab = bersihkan_judul(bab + " " + _AWALAN_NOMOR.sub("", isi))
                judul_terbuka = True
                continue
            if len(polos.split()) <= 60 and polos:         # judul bab (dengan/tanpa kata "باب")
                if _BAB_FIHRIS.match(polos):                # Ibnu Majah: "باب حدثنا سويد بن سعيد" = bab tanpa judul (gaya fihris)
                    isi = "باب"
                tutup()
                teks, tahqiq, no = [], [], None
                bab = bersihkan_judul(_AWALAN_NOMOR.sub("", isi))
                # «### | باب» lalu judulnya di baris «# …» berikutnya: Bukhari, dan ad-Darimi («# النهي عن استقبال
                # القبلة لغائط أو بول</span>»; halaman isi cetakan Asad hlm. 526 mencetaknya sebagai judul bab)
                tunggu_judul = kid in ("bukhari", "darimi") and norm_ar(bab) == "باب"
                judul_terbuka = kid == "nasai"
                judul_tir, judul_tir_mentah = kid == "tirmidzi", _AWALAN_NOMOR.sub("", isi)
                continue
            teks.append(isi)
        elif baris.startswith("# ") or baris.startswith("~~"):
            isi = baris.lstrip("#~ ")
            if "PageV" in isi and len(_SAMPAH.sub("", isi).strip()) < 3:
                continue
            if mode_tahqiq:
                tahqiq.append(_SAMPAH.sub(" ", isi).strip())
                continue
            if kid == "nasai":
                kal = norm_ar(_SAMPAH.sub(" ", re.sub(r"</?[a-zA-Z][^>]*>", " ", isi))).strip()
                if judul_terbuka and baris.startswith("# ") and kal and not _AWAL_SANAD.match(kal) and len(kal.split()) <= 14:
                    bab = bersihkan_judul(bab + " " + _SAMPAH.sub(" ", isi))     # "# والبول</span>", "# [البقرة: 222]"
                    continue
                judul_terbuka = False
                if baris.startswith("# ") and kal and not _AWAL_SANAD.match(kal) and len(kal.split()) <= 10:
                    # judul tanpa "###" di antara dua hadits: "# أول وقت الصبح", "# (25 ما يقول في قيامه ذلك)"
                    sblm = next((x for x in reversed(semua[:idx]) if x.strip() and "PageV" not in x[:12]), "")
                    ssdh = next((x for x in semua[idx + 1:] if x.strip() and not re.match(r"^#\s*PageV\d+P\d+\s*$", x)), "")
                    if re.search(r"0\s*$", sblm) and re.match(r"^### \|+ \d+ -", ssdh):
                        tutup()
                        teks, tahqiq, no = [], [], None
                        bab = bersihkan_judul(re.sub(r"^\(\s*\d+\s*|\)\s*$", "", _SAMPAH.sub(" ", isi).strip(' "')))
                        continue
            if kid == "ibnumajah":
                kal = norm_ar(_SAMPAH.sub(" ", isi)).strip()
                if baris.startswith("# ") and re.match(r"^باب(?:\s|:|$)", kal) and len(kal.split()) <= 40:
                    tutup()
                    teks, tahqiq, no = [], [], None
                    bab = bersihkan_judul(_SAMPAH.sub(" ", isi))
                    judul_terbuka = True
                    continue
                if judul_terbuka and kal and not _AWAL_SANAD.match(kal) and len(kal.split()) <= 12:
                    bab = bersihkan_judul(bab + " " + _SAMPAH.sub(" ", isi))
                    continue
                judul_terbuka = False
            if (kid == "bukhari" and baris.startswith("# ") and kitab and "تفسير" in kitab
                    and re.match(r"^سوره\s", norm_ar(_SAMPAH.sub(" ", isi))) and len(norm_ar(isi).split()) <= 14):
                # Kitab at-Tafsir: judul surah ditulis sebagai baris biasa ("# سورة إذا جاء نصر الله") dan bab tanpa
                # judul sesudahnya tidak ada di teks digital. Tanpa ini, hadits surah baru mewarisi bab surah sebelumnya.
                tutup()
                teks, tahqiq, no = [], [], None
                bab = bersihkan_judul(_SAMPAH.sub(" ", isi))
                tunggu_judul = False
                continue
            if tunggu_judul and baris.startswith("# "):
                tunggu_judul = False
                kalimat = norm_ar(_SAMPAH.sub(" ", isi))
                if kalimat and not _AWAL_SANAD.match(kalimat) and len(kalimat.split()) <= 60:
                    bab = bersihkan_judul("باب " + _SAMPAH.sub(" ", isi))
                    continue
            if kid == "tirmidzi" and baris.startswith("# "):
                kal = norm_ar(_SAMPAH.sub(" ", isi)).strip()
                if (judul_tir and not teks and kal and "@MATN@" not in isi and not _AWAL_SANAD.match(kal)
                        and len(kal.split()) <= 16):
                    judul_tir_mentah += " " + _SAMPAH.sub(" ", isi)                 # «# وآية الكرسي», «# إياهم»
                    bab = bersihkan_judul(judul_tir_mentah)
                    continue
                judul_tir = judul_tir and not kal and not re.search(r"[0-9٠-٩]", isi)   # «# ١٧٧٠» = awal hadits
                if re.match(r"^(?:بسم الله الرحمن الرحيم\s+)?ابواب\s", kal) and len(kal.split()) <= 10:
                    tutup()
                    teks, tahqiq, no = [], [], None
                    kitab, bab = bersihkan_kitab(re.sub(r"^\s*بسم الله الرحمن الرحيم\s*", "", _SAMPAH.sub(" ", isi))), None
                    kitab_terbuka = True
                    continue
                if kitab_terbuka and re.match(r"^عن رسول الله", kal) and len(kal.split()) <= 8:
                    kitab = bersihkan_kitab(kitab + " " + _SAMPAH.sub(" ", isi))
                    kitab_terbuka = False
                    continue
                kitab_terbuka = False
            mt = _NO_AHMAD.match(baris) if kid == "ahmad" else None
            if mt:                                         # Musnad Ahmad: "# 12 - حدثنا ..." = awal hadits bernomor
                tutup()
                teks, tahqiq, no, sub = [mt.group(3)], [], int(mt.group(1)), "/" in (mt.group(2) or "")
                ganda = re.search(r"\d+", mt.group(2) or "") if "/" not in (mt.group(2) or "") else None
                akhir_no, calon = (int(ganda.group()) if ganda else no), []
                continue
            if (kid == "ahmad" and no is not None and re.match(r"^# (?:حدثنا|حدثني)", baris)
                    and re.search(r"\(\d+\)\s*$", semua[idx - 1])):
                calon.append(len(" ".join(teks)))
            # ad-Darimi & asy-Syafi'i: «# أخبرنا مالك…» sesudah kalimat yang selesai = awal hadits tanpa nomor? (al-Fahl
            # 79: dua hadits di bawah «### | 78 -»). Hanya dipakai bila celah nomornya pas (nomor_naik).
            if kid == "darimi" and no is not None and not teks and isi.startswith("مكرر"):
                sub, isi = True, isi[len("مكرر"):].strip()     # «### | 402 -» lalu «# مكرر أخبرنا …» = 402 مكرر (sah)
            if (kid in ("darimi", "syafii") and no is not None and teks and re.match(r"^# (?:حدثنا|حدثني|أخبرنا|أخبرني)", baris)
                    and re.search(r'(?:\(\d+\)|[.»"])\s*(?:PageV\d+P\d+\s*)?(?:ms\d+\s*)?$', semua[idx - 1])):
                calon.append(len(" ".join(teks)))
            mt = _NO_AHMAD_TENGAH.search(isi) if kid == "ahmad" and no is not None else None
            if mt and int(mt.group(1)) == no + 1:
                teks.append(isi[:mt.start()])
                tutup()
                teks, tahqiq, no, sub = [isi[mt.end():]], [], int(mt.group(1)), False
                akhir_no, calon, sub = no, [], False
                continue
            teks.append(isi)
    tutup()
    if kid in ("ahmad", "darimi", "syafii"):     # kitab yang menampilkan nomor edisi tahqiq (LIDWA_SAJA)
        nomor_naik(blok)
    return blok


def petakan(kid, blok, riwayat):
    """riwayat: list (id, arab, no_standar, bab_no) urut. Kembalikan dict id -> (i_blok, skor)."""
    gb = [grams(norm_ar(_SAMPAH.sub(" ", b["teks"]))) for b in blok]
    gr = {rid: grams(norm_ar(ar)) for rid, ar, _, _ in riwayat}
    df = collections.Counter()
    for g in gr.values():
        df.update(g)
    N = max(1, len(gr))
    no_std = {rid: int(nos) for rid, _, nos, _ in riwayat if re.fullmatch(r"\d+", str(nos or ""))} if kid in NOMOR_SEJAJAR else {}
    post = collections.defaultdict(list)
    for i, g in enumerate(gb):
        for x in g:
            if df.get(x, 0) <= 40:
                post[x].append(i)
    kandidat = {}
    for rid, _, _, _ in riwayat:
        g = gr[rid]
        if len(g) < 4:
            continue
        bobot = {x: math.log(N / (1 + df[x])) + 0.1 for x in g}
        total = sum(bobot.values())
        cand = collections.Counter()
        for x in sorted(g, key=lambda x: df[x])[:20]:
            for i in post.get(x, ()):
                cand[i] += 1
        skor = [(sum(bobot[x] for x in g & gb[i]) / total, i) for i, _ in cand.most_common(30)]
        skor = [(s, i) for s, i in skor if s >= AMBANG]
        if skor:
            top = max(s for s, _ in skor)
            # Blok bernomor SAMA dengan nomor riwayat yang juga lolos AMBANG didahulukan. Penyusun kadang mengulang
            # teks yang sama di bab lain (mis. at-Tirmidzi 2700 = 1602, 3227 = 2186, 3875 = 2017), dan skor isi bisa
            # sedikit lebih tinggi di tempat lain; nomornya yang memastikan letak yang benar (dicek dengan fihris cetak).
            nos = no_std.get(rid)
            senomor = [(i, s) for s, i in skor if nos is not None and blok[i]["no"] == nos]
            # semua blok yang hampir sama baiknya: teks yang diulang penyusun (umum di al-Bukhari)
            kandidat[rid] = senomor or [(i, s) for s, i in skor if s >= top - 0.03]
    # Pilih kandidat yang paling dekat dengan posisi tetangga yang tidak ambigu (urutan kitab).
    urut = [rid for rid, *_ in riwayat if rid in kandidat]
    pasti = [(k, kandidat[rid][0][0]) for k, rid in enumerate(urut) if len(kandidat[rid]) == 1]
    import bisect
    kunci = [k for k, _ in pasti]
    hasil = {}
    for k, rid in enumerate(urut):
        c = kandidat[rid]
        if len(c) == 1:
            hasil[rid] = (c[0][0], round(c[0][1], 3))
            continue
        j = bisect.bisect_left(kunci, k)
        tetangga = [pasti[x][1] for x in range(max(0, j - 3), min(len(pasti), j + 3))]
        harapan = sorted(tetangga)[len(tetangga) // 2] if tetangga else c[0][0]
        i, s = min(c, key=lambda x: (abs(x[0] - harapan), -x[1]))
        hasil[rid] = (i, round(s, 3))
    return hasil


MIN_ISI_NOMOR = 0.8


def isi_dari_nomor(kid, blok, riwayat, akhir, cara):
    """Hadits bernomor ganda (mis. al-Bukhari 299-301, 3164-3165): sumber kita memuat teks GABUNGAN di setiap
    nomornya, sedangkan OpenITI memecahnya per nomor, sehingga skor isi tiap blok di bawah AMBANG. Riwayat seperti
    ini diberi blok OpenITI bernomor SAMA, hanya bila: tepat satu blok bernomor itu, letaknya di antara blok
    tetangga yang sudah cocok (urutan kitab), dan >= 80% 2-gram blok itu memang ada di teks riwayat (cara "nomor")."""
    if kid == "syafii":       # susunan edisi berbeda dari penomoran kita
        return
    per_no = collections.defaultdict(list)
    for i, b in enumerate(blok):
        if b["no"] is not None:
            per_no[b["no"]].append(i)
    urut = [r[0] for r in riwayat]
    for k, (rid, arab, nos, _) in enumerate(riwayat):
        if rid in akhir or not re.fullmatch(r"\d+", str(nos or "")):
            continue
        a = next((akhir[urut[j]][0] for j in range(k - 1, -1, -1) if urut[j] in akhir), None)
        c = next((akhir[urut[j]][0] for j in range(k + 1, len(urut)) if urut[j] in akhir), None)
        calon = [i for i in per_no.get(int(nos), ()) if a is not None and c is not None and a <= i <= c]
        if len(calon) != 1:
            continue
        gb = grams(norm_ar(_SAMPAH.sub(" ", blok[calon[0]]["teks"])))
        isi = len(gb & grams(norm_ar(arab))) / max(1, len(gb))
        if isi >= MIN_ISI_NOMOR:
            akhir[rid], cara[rid] = (calon[0], round(isi, 3)), "nomor"


MIN_ISI_LETAK = 0.6


def betulkan_letak(kid, blok, riwayat, akhir, cara):
    """Riwayat yang terpasang ke blok JAUH dari tetangganya (urutan kitab terlompat), padahal blok bernomor sama
    dengan nomornya ada tepat di antara tetangga itu. Contoh: at-Tirmidzi 624 («سألت أبا عبيدة هل تذكر من عبد الله
    شيئا؟ قال: لا», bab zakat sapi) terpasang ke blok no. 17 (bab istinja'), karena kalimat yang sama dikutip dalam
    komentar at-Tirmidzi di sana. Dipindah hanya bila: kitab bernomor sejajar, tepat satu blok bernomor itu di antara
    tetangga, dan isi keduanya saling memuat >= 60% (cara "nomor")."""
    if kid not in NOMOR_SEJAJAR:
        return
    per_no = collections.defaultdict(list)
    for i, b in enumerate(blok):
        if b["no"] is not None:
            per_no[b["no"]].append(i)
    urut = [r[0] for r in riwayat]
    for k, (rid, arab, nos, _) in enumerate(riwayat):
        if rid not in akhir or not re.fullmatch(r"\d+", str(nos or "")) or blok[akhir[rid][0]]["no"] == int(nos):
            continue
        a = next((akhir[urut[j]][0] for j in range(k - 1, -1, -1) if urut[j] in akhir), None)
        c = next((akhir[urut[j]][0] for j in range(k + 1, len(urut)) if urut[j] in akhir), None)
        if a is None or c is None or a <= akhir[rid][0] <= c:
            continue
        calon = [i for i in per_no.get(int(nos), ()) if a <= i <= c]
        if len(calon) != 1:
            continue
        gb, gr = grams(norm_ar(_SAMPAH.sub(" ", blok[calon[0]]["teks"]))), grams(norm_ar(arab))
        sama = len(gb & gr)
        if sama / max(1, len(gb)) >= MIN_ISI_LETAK and sama / max(1, len(gr)) >= MIN_ISI_LETAK:
            akhir[rid], cara[rid] = (calon[0], round(sama / max(1, len(gb)), 3)), "nomor"


_KOREKSI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "koreksi_bab.json"), encoding="utf8"))["koreksi"]


def koreksi_cetak(rid, no_edisi=None):
    """Koreksi judul bab yang sudah diverifikasi terhadap kitab cetak (pipeline/koreksi_bab.json). Rentang memakai
    nomor riwayat kita, kecuali entri ber-"penomoran": "edisi" (kitab Lidwa-saja: Ahmad, ad-Darimi, asy-Syafi'i),
    yang memakai nomor edisi tahqiq (= nomor blok OpenITI)."""
    kid, _, no = rid.partition(":")
    for k in _KOREKSI:
        if k["kitab_id"] != kid:
            continue
        n = no_edisi if k.get("penomoran") == "edisi" else (int(no) if no.isdigit() else None)
        if n is not None and k["dari"] <= n <= k["sampai"]:
            return k
    return None


def main():
    t0 = time.time()
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE riwayat_bab (riwayat_id TEXT PRIMARY KEY, kitab_ar TEXT, bab_ar TEXT, skor REAL, cara TEXT, no_openiti INT,
      kitab_nama_id TEXT, tahqiq TEXT, urut_openiti INT, catatan TEXT, cara_cocok TEXT);
    CREATE TABLE kitab_nama (kitab_id TEXT, bab_no INT, nama_ar TEXT, setuju INT, total INT, nama_id TEXT, PRIMARY KEY (kitab_id, bab_no));
    CREATE TABLE info (kitab_id TEXT, kunci TEXT, nilai TEXT);
    """)
    for kid, rel in BERKAS.items():
        blok = urai(os.path.join(SRC, rel), kid)
        riwayat = src.execute(
            "SELECT id, arab, no_standar, bab_no FROM riwayat WHERE kitab_id=? AND tingkat IN ('A','B') "
            "ORDER BY COALESCE(CAST(no_standar AS REAL), no_lidwa)", (kid,)).fetchall()
        peta = petakan(kid, blok, riwayat)
        # isi celah dari tetangga bila keduanya di bab yang sama
        urut = [rid for rid, *_ in riwayat]
        cara = {rid: "teks" for rid in peta}
        akhir = dict(peta)
        for k, rid in enumerate(urut):
            if rid in akhir or kid == "syafii":   # Syafi'i: susunan edisi al-Fahl berbeda dari Lidwa, tetangga tak bermakna
                continue
            a = next((akhir[urut[j]] for j in range(k - 1, -1, -1) if urut[j] in akhir), None)
            b = next((akhir[urut[j]] for j in range(k + 1, len(urut)) if urut[j] in akhir), None)
            if a and b and blok[a[0]]["bab"] == blok[b[0]]["bab"] and blok[a[0]]["kitab"] == blok[b[0]]["kitab"]:
                akhir[rid], cara[rid] = (a[0], 0.0), "urutan"
        isi_dari_nomor(kid, blok, riwayat, akhir, cara)
        betulkan_letak(kid, blok, riwayat, akhir, cara)
        isi_blok = collections.Counter(i for i, _ in akhir.values())
        for rid, (i, s) in akhir.items():
            b = blok[i]
            no_b = None if (b.get("celah") and isi_blok[i] > 1) else b["no"]
            # Penilaian muhaqqiq hanya dipasang bila teks riwayat jelas ada di blok edisi itu (>= 0.9)
            tq = b.get("tahqiq") if (cara[rid] == "teks" and s >= 0.9) else None
            bab_ar, cr, catatan = b["bab"], cara[rid], None
            k = koreksi_cetak(rid, no_b)
            if k:
                # cara "catatan-cetak": judul tetap, tetapi cetakan memberi catatan penting (mis. bab tambahan edisi lain)
                bab_ar, cr, catatan = k["bab_ar"], k.get("cara", "koreksi-cetak"), k.get("catatan_id")
            # cara_cocok = cara pencocokan asli (cara bisa ditimpa koreksi cetak; tingkat A kitab Lidwa-saja butuh "teks")
            db.execute("INSERT INTO riwayat_bab VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (rid, b["kitab"], bab_ar, s, cr, no_b, nama_indonesia(b["kitab"]),
                        tq if no_b is not None or not b.get("celah") else None, i, catatan, cara[rid]))

        # uji: urutan & nomor
        idx = [peta[rid][0] for rid in urut if rid in peta]
        naik = sum(1 for x, y in zip(idx, idx[1:]) if y >= x)
        nomor_dicek = nomor_sama = 0
        no_std = {rid: nos for rid, _, nos, _ in riwayat}
        for rid, (i, _) in peta.items():
            if blok[i]["no"] is not None and no_std[rid] and re.fullmatch(r"\d+", str(no_std[rid])):
                nomor_dicek += 1
                nomor_sama += blok[i]["no"] == int(no_std[rid])
        # nama Arab per "kitab" fawazahmed0 (bab_no di data kita) = judul kitab OpenITI terbanyak
        per_bagian = collections.defaultdict(collections.Counter)
        for rid, _, _, bno in riwayat:
            if rid in akhir and blok[akhir[rid][0]]["kitab"]:
                per_bagian[bno][blok[akhir[rid][0]]["kitab"]] += 1
        setuju = total = 0
        for bno, c in (per_bagian.items() if kid not in LIDWA_SAJA else []):
            nama, n = c.most_common(1)[0]
            jml = sum(c.values())
            setuju += n
            total += jml
            # Nama hanya bila mayoritas jelas (>= 60%). Bagian "0" Muslim di fawazahmed0 misalnya adalah
            # tampungan riwayat tanpa nomor kitab yang tersebar di seluruh kitab — tidak punya satu nama.
            jelas = n / jml >= 0.6
            db.execute("INSERT INTO kitab_nama VALUES (?,?,?,?,?,?)",
                       (kid, bno, nama if jelas else None, n, jml, nama_indonesia(nama) if jelas else None))
        info = {"blok": len(blok), "riwayat": len(riwayat), "cocok_teks": len(peta),
                "dari_urutan": sum(1 for c in cara.values() if c == "urutan"),
                "dari_nomor": sum(1 for c in cara.values() if c == "nomor"),
                "urutan_naik": f"{naik}/{max(1, len(idx) - 1)}", "nomor_sama": f"{nomor_sama}/{nomor_dicek}",
                "cocok_090": sum(1 for _, sk in peta.values() if sk >= 0.9), "edisi": EDISI.get(kid, ""),
                "tahqiq": sum(1 for rid, (i, sk) in akhir.items() if cara[rid] == "teks" and sk >= 0.9 and blok[i].get("tahqiq")),
                "kesepakatan_kitab": f"{setuju}/{total}"}
        db.executemany("INSERT INTO info VALUES (?,?,?)", [(kid, k, str(v)) for k, v in info.items()])
        db.commit()
        print(f"{kid:10s} blok {len(blok):5d} | cocok {len(peta):5d}/{len(riwayat)} (+{info['dari_urutan']} urutan, +{info['dari_nomor']} nomor) | "
              f"urutan naik {info['urutan_naik']} | nomor sama {info['nomor_sama']} | kitab sepakat {info['kesepakatan_kitab']} "
              f"({time.time() - t0:.0f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
