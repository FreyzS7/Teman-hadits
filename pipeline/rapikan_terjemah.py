#!/usr/bin/env python3
"""Perapian teknis terjemah Indonesia (Lidwa) saat ekspor ke D1. Isi terjemah TIDAK diubah maknanya.

Dipakai oleh export_d1.py (bukan build_db.py), supaya perbaikan cukup dengan `npm run terbit` tanpa membangun
ulang database. Semua aturan di bawah lahir dari pemindaian 64.108 terjemah (docs/06, bagian "Kualitas terjemah"):

  1. Entitas HTML yang tertinggal: «&quot;» -> «"» (15 kali).
  2. Kata tugas tertulis dua kali: «dari dari», «telah telah», «kepada kepada», «[Abu Abu Hurairah]» -> satu kata.
     Hanya kata yang pengulangannya PASTI salah ketik (daftar KATA_TUGAS). «Allah Allah» (zikir), «tidak tidak»,
     «labbaika labbaika», «apa apa», «ummatku ummatku» dibiarkan: bisa memang begitu bunyinya.
  3. Kata ulang tanpa tanda hubung: «orang orang», «laki laki», «tiba tiba» -> «orang-orang» ... (daftar KATA_ULANG,
     hanya kata benda/keterangan yang bentuk ulangnya baku). Pencarian tidak berubah: tanda hubung = spasi.
  4. Spasi sebelum tanda baca («Aufa . Abu Isa») dan spasi ganda (sisa ikon ﷺ yang hilang di asy-Syafi'i).
  5. Nomor catatan yang menempel di akhir terjemah sesudah tanda baca («... kelihatan. 185»; 1.599 dari 1.800
     terjemah Musnad asy-Syafi'i).
  6. Penanda «#BELUM SELESAI#» / «#KOSONG#» dari penerjemah -> «(…)», dan terjemah ditandai tidak lengkap.
  7. Kurung siku nama perawi yang rusak (16 riwayat; diperbaiki satu per satu di PERBAIKAN_MANUAL). Kurung yang
     rusak membuat kolom pencarian membuang potongan matan (isi kurung dianggap nama perawi).

Fungsi terpotong() menandai terjemah yang tampak terpotong di sumber (dipakai untuk catatan di halaman hadits).
"""
import html
import re

KATA_TUGAS = (
    "dari yang telah dan kepada dengan di pada bahwa bin untuk tentang dalam karena oleh adalah itu ia aku kami kalian "
    "mereka beliau rasulullah abu hingga akan para atau kecuali jika maka saat antara tersebut seorang setelah kemudian "
    "lalu berkata bersabda menjawab menyebutkan meriwayatkan pernah"
).split()
KATA_ULANG = (
    "orang laki tiba hal benar betul baik anak sampai hampir shaf dosa amal surat masing hadis jangan sahabat hamba "
    "tempat masjid alat saudara kalimat hari rumah tanda budak musuh pagi taman ular nabi harta langit istri isteri "
    "wanita tangan waktu sandal kuda binatang jalan pintu hewan tiang saksi hukum pemimpin teman gambar ayat umat ummat "
    "rasul utusan bejana kanak bangunan tumpukan kira angan sembunyi bulu celah malam sama"
).split()

# kata ulang hanya bila diikuti spasi/tanda baca/akhir, supaya «Al Al'war» dan sejenisnya tidak tersentuh
_SESUDAH = r"(?=[\s,.;:!?)\]\"”’]|$)"
_GANDA = re.compile(r"\b(%s) (\1)\b%s" % ("|".join(KATA_TUGAS), _SESUDAH), re.I)
_ULANG = re.compile(r"\b(%s) (\1)\b%s" % ("|".join(KATA_ULANG), _SESUDAH), re.I)
_ENTITAS = re.compile(r"&(?:quot|amp|lt|gt|apos|nbsp|#\d{1,5});")
_SPASI_TANDA = re.compile(r"(\w) +([,.;:!?])(?=[\s\"'”’)]|$)")
_SPASI_GANDA = re.compile(r"[ \t]{2,}")
_NOMOR_AKHIR = re.compile(r"([.!?\"”’])\s*\d{1,4}\s*$")
_PENANDA = re.compile(r"\s*#(?:BELUM SELESAI|KOSONG)#")

PERBAIKAN_MANUAL = {
    "darimi:L377": [("[Minhal bin Khalifah] [dari [Mathar", "[Minhal bin Khalifah] dari [Mathar")],
    "darimi:L509": [("[Aun bin Abdullah [kepadaku", "[Aun bin Abdullah] kepadaku")],
    "darimi:L610": [("['Atha`, [Thawus]", "['Atha`], [Thawus]")],
    "darimi:L702": [("[Malik bin Isma'il telah", "[Malik bin Isma'il] telah")],
    "darimi:L1466": [("[Umar bin Al Khathab, \"Allah", "[Umar bin Al Khathab], \"Allah")],
    "darimi:L1534": [("[Ibnu Sirin dari", "[Ibnu Sirin] dari")],
    "darimi:L1686": [("[Muhammad bin Rifa'ah dari", "[Muhammad bin Rifa'ah] dari")],
    "darimi:L1922": [("[Malik dari [Nafi'", "[Malik] dari [Nafi'")],
    "darimi:L2059": [("['Ubaidullah dari [Nafi'", "['Ubaidullah] dari [Nafi'")],
    "darimi:L2264": [("dari [Nabi shallallahu 'alaihi wasallam, beliau", "dari Nabi shallallahu 'alaihi wasallam, beliau")],
    "darimi:L2360": [("[Al Hakam dari [Abdurrahman", "[Al Hakam] dari [Abdurrahman")],
    "darimi:L2481": [("dari Al A'raj]", "dari [Al A'raj]")],
    "darimi:L2654": [("mantan budak Al Hasan bin Ali] dari", "mantan budak Al Hasan bin Ali dari")],
    "darimi:L2743": [("[Umair bin [Sa'id]", "[Umair bin Sa'id]")],
    "darimi:L2787": [("[Ali] dan] Zaid]", "[Ali] dan [Zaid]")],
    "syafii:L236": [("'A[akah engkau", "'Apakah engkau")],
}


def _ulang(m):
    a, b = m.group(1), m.group(2)
    if not (a.islower() or a.istitle()):
        a = a.lower()                                # «jangAn jangan»
    return f"{a}-{b.lower() if a[:1].isupper() else b}"


def rapikan(teks, rid=None):
    """Kembalikan (teks_rapi, tidak_lengkap). tidak_lengkap = penerjemah menandai «#BELUM SELESAI#»/«#KOSONG#»."""
    if not teks:
        return teks, False
    for lama, baru in PERBAIKAN_MANUAL.get(rid, ()):
        if lama in teks:
            teks = teks.replace(lama, baru, 1)
    teks = _ENTITAS.sub(lambda m: html.unescape(m.group()), teks)
    tidak_lengkap = bool(_PENANDA.search(teks))
    teks = _PENANDA.sub(" (…)", teks)
    teks = _GANDA.sub(r"\1", teks)
    teks = _GANDA.sub(r"\1", teks)                   # «dari dari dari»
    teks = _ULANG.sub(_ulang, teks)
    teks = _SPASI_TANDA.sub(r"\1\2", teks)
    teks = _SPASI_GANDA.sub(" ", teks)
    teks = _NOMOR_AKHIR.sub(r"\1", teks.strip())
    return teks.strip(), tidak_lengkap


_AKHIR_KALIMAT = re.compile(r"[.!?\"'”’)\]»…]\s*$")


def terpotong(terj, arab):
    """Terjemah tampak terpotong di sumber: tanpa tanda akhir kalimat DAN jauh lebih pendek dari teks Arabnya
    (median panjang terjemah/Arab = 1,29). Dua pola yang dicek manual seluruhnya terpotong (12 riwayat):
      - berakhir koma/titik koma dan lebih pendek dari Arabnya;
      - tanpa tanda akhir, Arab > 300 huruf, dan panjang terjemah < 0,65 x Arab."""
    if not terj or not arab or _AKHIR_KALIMAT.search(terj):
        return False
    r = len(terj) / len(arab)
    if re.search(r"[,;]\s*$", terj):
        return r < 1.0
    return len(arab) > 300 and r < 0.65
