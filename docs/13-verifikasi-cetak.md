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

Dari 160 entri sampel (122 di antaranya ditemukan di OCR), **tidak ada satu pun perbedaan isi** antara yang tampil di situs dan cetakan. Pemeriksaan visual sesudahnya (di bawah) menemukan dua hal: penilaian «كذبوه» yang tidak terbaca, dan satu bab tanpa judul yang hilang di teks digital Bukhari. Keduanya sudah diperbaiki. Semua ketidakcocokan otomatis berasal dari OCR. Untuk Taqrib, tabaqah cocok penuh di 68 dari 69 entri yang bisa dicek; satu sisanya tidak terbaca.

## Pemeriksaan visual halaman scan

Setelah server unduhan archive.org dibuka, halaman cetak dilihat langsung sebagai gambar. Halaman dipilih lewat penanda halaman OpenITI (`PageV01P094` = hlm. 94). Penanda ini tepat: entri 248 → hlm. 94, persis seperti di scan. Untuk Taqrib, leaf scan = halaman cetak + 6.

### Taqrib at-Tahdzib: 3 halaman, 50 entri, semua isi dibandingkan

| Halaman cetak | Entri | Nomor entri | Penilaian · tabaqah · wafat · kode | Temuan |
|---|---|---:|---|---|
| 94 (dipakai untuk kalibrasi) | 248–265 | 18/18 sama | semua sama | 257 «**كذبوه**» tidak terbaca sebagai penilaian |
| 480 (acak) | 5903–5917 | 15/15 sama | semua sama | 5907 Muhammad bin Sa'id **al-Mashlub**: «**كذبوه** … وضع أربعة آلاف حديث» tidak terbaca sebagai penilaian |
| 570 (berisi 7258, yang tak terbaca OCR) | 7252–7268 | 17/17 sama | semua sama | 7258 terkonfirmasi: «ثقة، من السادسة، مات سنة بضع وأربعين» |

Contoh yang terbaca jelas di cetakan dan sama dengan situs:
- 248 «من الحادية عشرة، مات سنة سبعين» → situs menampilkan wafat **270 H** (kaidah abad Ibnu Hajar).
- 256 «مات سنة أربع — وقيل خمس — وعشرين» → **224 H** (ada pendapat lain).
- 261 «قتل سنة إحدى وثلاثين» → 131 H.
- 7256 «مات سنة سبع ومائتين» → 207 H.

**Perbaikan dari temuan ini:**
- «كذبوه» kini dikenali sebagai penilaian (tingkat 12, pendusta/pemalsu), tetapi **hanya bila menjadi kata pertama Ibnu Hajar**.
- «متروك، كذبه أبو داود» tetap *matruk*, karena tuduhan dusta di situ kutipan dari ulama lain.
- «كذبه الشعبي في رأيه» tidak diberi padanan tingkat.
- Diuji di `test_rijal.py`.

### Shahih al-Bukhari (cetakan Dar Thauq an-Najah)

Scan ini: archive.org `alfirdwsiy2018_gmail_2698_201808`. Teks OCR-nya terlalu rusak untuk menemukan halaman hadits secara otomatis; teks berharakat penuh merusak OCR. Satu halaman yang terbuka ternyata **fihris rinci juz 5** (leaf 43, hlm. 183), dan halaman itu tetap berguna:

- **14 judul bab pertama Kitab 62** («باب فضائل أصحاب النبي ﷺ», «سدوا الأبواب إلا باب أبي بكر», «قصة البيعة والاتفاق على عثمان … وفيه مقتل عمر», dst.) **sama persis** dengan judul bab di situs.
- **Kesalahan ditemukan.** Fihris mencatat **bab tanpa judul** («باب: حدثنا الحميدي ومحمد بن عبد الله») antara bab «لو كنت متخذا خليلا» dan «مناقب عمر». Teks digital OpenITI **melewatkan** baris «باب» itu. Akibatnya, hadits no. 3659–3678 tampil di bawah judul «لو كنت متخذا خليلا», padahal al-Bukhari menaruhnya di bab tersendiri. Sudah dikoreksi lewat `pipeline/koreksi_bab.json`, yang mencantumkan buktinya. Halaman hadits kini menampilkan «باب (bab tanpa judul) · dikoreksi dengan kitab cetak». Diuji di `test_bab.py`.
- **Judul kitab berbeda.** Fihris menulis «كتاب **فضائل** أصحاب النبي ﷺ», teks digital «كتاب أصحاب النبي». Ini belum dikoreksi, karena perlu dilihat di halaman isinya (fihris kadang menyeragamkan judul).

### Fihris Bukhari seluruh juz: mencari bab tanpa judul yang terlewat

Edisi Dar Thauq an-Najah mencatat setiap bab tanpa judul di fihrisnya sebagai «باب: حدثنا <perawi pertama>», tepat sebelum bab bertajuk berikutnya. Fihris (leaf 4–80 di scan) OCR-nya cukup terbaca, sehingga pencocokan bisa otomatis:

1. Temukan pola «باب: حدثنا X» lalu judul bab berikutnya di teks OCR fihris. Hasilnya 33 entri.
2. Di data kita, cari bab bertajuk itu, bergerak maju sesuai urutan kitab.
3. Di bab tepat sebelumnya, cari hadits yang diawali «حدثنا X». Hanya diterima bila hadits seperti itu **tepat satu**.
4. Bila hadits itu belum berada di bab tanpa judul, bab tersebut terlewat di teks digital.

| Hasil | Jumlah |
|---|---:|
Skrip: `pipeline/cek_fihris_bukhari.py` (mengunduh OCR fihris sendiri; hasil di `build/cek_fihris_bukhari.json`).

| Hasil skrip | Jumlah | Tindakan |
|---|---:|---|
| Bab tanpa judul sudah benar di data kita | 3 | — |
| Kandidat terlewat | 6 | **5 dikoreksi** (no. 18; 435–437; 745; 797–799; 899–900). **1 dibuang**: 7122–7131, karena no. 7122 justru hadits pertama «باب ذكر الدجال» |
| Ragu (perawi tidak ditemukan unik di bab sebelumnya) | 6 | tidak dikoreksi, kecuali 3659–3678 yang sudah dikoreksi dari pemeriksaan visual (OCR membaca «عبد الله», teksnya «عبيد الله») |
| Judul bab berikutnya tidak terbaca di OCR | 10 | perlu dilihat manual |

**Dua temuan dilihat langsung di gambar fihris** (hlm. 185, Kitab al-Adzan):
- bab 89 «ما يقول بعد التكبير» → **bab 90 «بابٌ: حدثنا ابن أبي مريم»** → bab 91 «رفع البصر إلى الإمام في الصلاة»;
- bab 125 «فضل اللهم ربنا ولك الحمد» → **bab 126 «بابٌ: حدثنا معاذ بن فضالة»** → bab 127 «الاطمأنينة حين يرفع رأسه من الركوع».

Keenam koreksi beserta buktinya ada di `pipeline/koreksi_bab.json` dan diuji di `test_bab.py`, termasuk bahwa hadits tetangganya tidak ikut berpindah.

### Pemeriksaan manual 16 entri sisa: tiga kesalahan PARSER kita ditemukan

Ke-16 entri dilihat langsung di gambar fihris (12 halaman: hlm. 177, 181, 184, 185, 201, 204, 205, 207, 208, 211, 213, 217). Hal pertama yang terlihat: **fihris bercetak dua kolom, dan OCR kadang menyambung baris lintas kolom.** Contohnya, «حدثنا الحسن بن مدرك» (Kitab al-Haidh) terpasang ke «فضل قل هو الله أحد» (Fadha'il al-Qur'an). Karena itu, setiap entri dipastikan dari gambar, bukan dari OCR.

Selain bab yang hilang di teks digital, pemeriksaan ini menemukan **tiga kesalahan di parser kita sendiri**. Semuanya sudah diperbaiki dan diuji:

| Kesalahan parser | Akibat di situs | Perbaikan |
|---|---|---|
| Teks digital sering menulis bab bertajuk sebagai «### \| باب» kosong, dengan judulnya **di baris berikutnya** | Bab bertajuk tampil sebagai "bab tanpa judul" (mis. «نسبة اليمن إلى إسماعيل», «قول الله تعالى: إنا خلقناكم…»). Blok berlabel «باب» telanjang: **345** | Baris pertama sesudah «باب» yang bukan awal sanad (حدثنا/أخبرنا/…) dibaca sebagai judulnya → tersisa **91** bab tanpa judul sungguhan |
| Catatan editor «[تعليق مصطفى البغا]» dibaca sebagai judul bab | **67** hadits (enam kitab) berjudul bab «[تعليق مصطفى البغا]» | Catatan editor diperlakukan seperti «تعليق المحقق» ad-Darimi (bukan judul) |
| Di Kitab at-Tafsir, judul surah ditulis sebagai baris biasa («# سورة إذا جاء نصر الله») | Hadits pembuka surah tampil di bawah bab **surah sebelumnya** (mis. an-Nashr di bawah «ومن يعمل مثقال ذرة شرا يره» dari az-Zalzalah). **38** hadits | Baris «سورة …» di Kitab at-Tafsir menjadi batas bagian; hadits pembuka surah kini berlabel nama surahnya |

**Koreksi baru berdasarkan gambar fihris (15):**
- 51 (bab tanpa judul «حدثنا إبراهيم بن حمزة»);
- **52 «باب فضل من استبرأ لدينه»**: bab bertajuk yang hilang;
- 333; 334–335 (judul bab 1 Kitab at-Tayammum yang kosong); 348;
- 1885–1886; 1888–1890; 1945; 2624; 2669–2670;
- **3464 «حديث أبرص وأعمى وأقرع في بني إسرائيل»**: tertimpa catatan editor;
- 3466–3488; 3497–3499; 3540; 3639–3648.

**Sudah benar setelah perbaikan parser** (dicek di gambar): 3938–3940, 3954, 3984–3991, 3996–4027, 4075–4076, 4293–4296, 4300–4313, 4421–4423, 4467, 4470, 4708, 4806–4807, 4855, 4967–4968, 4971, 4974.

**Pasangan OCR yang ternyata keliru** (tidak ada bab tanpa judul di tempat itu): sebelum «الصائم إذا أكل أو شرب ناسيا», «ما لقي النبي ﷺ…», «إسلام عمر», «بعث أسامة», dan «فضل قل هو الله أحد».

Total koreksi bertanda bukti di `pipeline/koreksi_bab.json`: **21 rentang**. Diuji di `test_bab.py`, termasuk hadits tetangga yang harus tetap di babnya.

## Batasan dan yang belum

- **Nomor entri belum diverifikasi.** OCR mengacaukan angka Arab-Hindi di kolom nomor.
- **Kasyf al-Khafa'** hanya 11 dari 40 entri yang ditemukan, karena OCR cetakan 1351 H sangat rusak.
- **Teks hadits** (Bukhari, Muslim, dst.) belum dibandingkan dengan cetakan. Scan Bukhari di archive.org tidak punya OCR. Teks hadits saat ini diverifikasi dengan cara lain: dua sumber digital yang sepakat (tingkat A) dan uji silang atribusi.
- **Teks dan nomor hadits Bukhari** belum dicek visual satu per satu. Halamannya harus dicari manual di scan (OCR-nya tidak bisa dipakai untuk mencari), atau dengan scan lain yang OCR-nya lebih baik.
- **Fihris belum dibaca utuh.** Baru 14 dari ±77 halaman fihris Bukhari yang dilihat langsung. Bab tanpa judul di halaman lain yang tidak tertangkap OCR mungkin masih ada.
