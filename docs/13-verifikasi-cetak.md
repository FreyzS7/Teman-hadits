# Verifikasi terhadap Kitab Cetak

Tujuannya membuktikan bahwa yang tampil di situs sama dengan isi **kitab cetaknya**, bukan hanya sama dengan satu salinan digital. Pembandingnya adalah **teks OCR dari scan cetakan** di archive.org. Ini digitalisasi yang terpisah sama sekali dari teks OpenITI yang kita pakai (orang lain, mesin lain, dari kertas). Bila keduanya sepakat, kesalahan ketik di salah satu salinan digital akan ketahuan.

Skrip: `pipeline/verifikasi_cetak.py`. Sampel acak memakai benih tetap 20261101, jadi bisa diulang. Hasil per butir ada di `build/verifikasi_cetak.json`.

## Cetakan pembanding

Ketiganya edisi yang sama dengan sumber digital kita.

| Kitab | Cetakan | archive.org | sha256 OCR (12 awal) |
|---|---|---|---|
| *Taqrib at-Tahdzib* | tahqiq Muhammad 'Awwamah, Dar ar-Rasyid | `alfirdwsiy2018_gmail_1957` | `653a4f694287` |
| *al-Maqashid al-Hasanah* | tahqiq Muhammad 'Utsman al-Khusyt | `20260220_20260220_0309` | `d9d6157aa1a6` |
| *Kasyf al-Khafa'* | Maktabah al-Qudsi, Kairo 1351–1352 H (scan Bibliotheca Alexandrina) | `AAlexandrina-141236` | `69393881f5cb` |

## Cara

1. **Sampel acak:**
   - 80 perawi yang tampil di situs (entri Taqrib);
   - 40 entri al-Maqashid;
   - 40 entri Kasyf.
2. **Menemukan entri di teks OCR.** Pasangan kata entri kita "memilih" posisi di OCR, sehingga toleran terhadap salah baca OCR.
   - Ambangnya ditentukan dari "skor nol" (teks yang sama dengan urutan kata diacak): di atas 99% skor nol.
   - Entri yang tidak lolos ambang dihitung **tidak terbaca**, bukan salah.
3. **Mengecek setiap butir di jendela teks itu** (toleransi satu huruf per kata):
   - *Taqrib*: frasa penilaian Ibnu Hajar, tabaqah, dan kata bilangan tahun wafat;
   - *katalog*: judul entri dan kata kunci penilaian yang menjadi chip di situs.
4. **Setiap butir yang tidak cocok penuh dibaca manual**, lalu digolongkan sebagai salah OCR, salah lokasi, atau **beda sungguhan**.

## Hasil

| Kitab | Sampel | Ditemukan di OCR | Butir dicek | Cocok penuh otomatis | Dibaca manual | **Beda sungguhan** |
|---|---:|---:|---|---:|---:|---:|
| Taqrib | 80 | 74 | penilaian 73, tabaqah 69, wafat 31 | 65 · 68 · 23 | 14 entri | **0** |
| al-Maqashid | 40 | 37 | judul 37, kata kunci 15 | 17 · 11 | 11 entri | **0** |
| Kasyf al-Khafa' | 40 | 11 | judul 11, kata kunci 5 | 2 · 2 | 4 entri | **0** |

### Temuan pembacaan manual (contoh)

| Butir | Situs kita | Teks OCR cetakan | Kesimpulan |
|---|---|---|---|
| Taqrib 4484, penilaian | ثقة ثبت سني وربما **دلس** | ثقه ثبت سني وربما **دلر** | salah OCR (س→ر) |
| Taqrib 4021, penilaian | صدوق **ربما** أخطأ | صدوق **رما** اخطا | salah OCR |
| Taqrib 5231, penilaian | **صحابي** جليل عمل على البحرين … | **صحاب** جليل عمل علي البحرين … | salah OCR |
| Taqrib 5497, wafat | مات سنة خمس **وسبعين** | مات سنه خمس **وسبع** | kata terpotong di OCR |
| Taqrib 7258, tabaqah | ثقة **من السادسة** … | ثقه, lalu langsung entri berikutnya | **tidak terbaca**: OCR melompati baris; perlu cek visual |
| al-Maqashid 279, kata kunci | chip *batil*, *tidak ada asalnya* | حديث الباذنجان لما ال له **باطل لا اصل له** | cocok |
| al-Maqashid 181, kata kunci | chip *tidak sahih* | قال النووي **لا صح** | cocok (salah OCR) |
| Kasyf 710, judul | أن عليا رضي الله عنه حمل باب خيبر | ان **عل رض اه** عنه حمل باب **خ…** | cocok (OCR rusak) |

Beberapa butir al-Maqashid berskor rendah karena lokasinya keliru. Penyebabnya, cetakan al-Khusyt memuat catatan kaki daftar rujukan ("كشف الخفا، الدرر، ...") yang mirip pembahasan. Butir-butir itu tidak dihitung beda.

### Kesimpulan

Dari 160 entri sampel (122 di antaranya ditemukan di OCR), **tidak ada satu pun perbedaan isi** antara yang tampil di situs dan cetakan. Semua ketidakcocokan otomatis berasal dari OCR. Untuk Taqrib, tabaqah cocok penuh di 68 dari 69 entri yang bisa dicek; satu sisanya tidak terbaca.

## Batasan dan yang belum

- **Nomor entri belum diverifikasi.** OCR mengacaukan angka Arab-Hindi di kolom nomor.
- **Kasyf al-Khafa'** hanya 11 dari 40 entri yang ditemukan, karena OCR cetakan 1351 H sangat rusak.
- **Teks hadits** (Bukhari, Muslim, dst.) belum dibandingkan dengan cetakan. Scan Bukhari di archive.org tidak punya OCR. Teks hadits saat ini diverifikasi dengan cara lain: dua sumber digital yang sepakat (tingkat A) dan uji silang atribusi.
- **Pemeriksaan visual halaman scan** (melihat gambar halamannya langsung, termasuk nomor entri dan nomor hadits) membutuhkan server unduhan archive.org: `ia800000.us.archive.org` (semua `*.us.archive.org`) dan `*.ca.archive.org`. Server-server ini **diblokir** oleh pengaturan jaringan lingkungan build. Teks OCR di atas diambil lewat halaman `/stream/` di domain utama archive.org. Bila domain itu dibuka (Network access → Allowed domains), langkah berikutnya:
  1. Petakan halaman cetak ↔ halaman scan memakai penanda halaman OpenITI (`PageV01P076` = jilid 1 hlm. 76).
  2. Lihat gambar halaman untuk sampel yang sama: nomor entri, Taqrib 7258, dan 20 hadits Bukhari pada cetakan Dar Thauq an-Najah.
