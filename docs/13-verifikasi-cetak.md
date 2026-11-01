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

### Fihris dibaca utuh: 26 bab tanpa judul lagi

Sesudah itu **seluruh** fihris rinci 9 juz (77 halaman, leaf 4–80 di scan) dibaca langsung dari gambar, termasuk membaca ulang 14 halaman yang sebelumnya hanya dilihat untuk entri tertentu. Setiap entri «بابٌ: حدثنا X» dicocokkan dengan data: bab bertajuk berikutnya dicari, lalu hadits yang diawali «حدثنا X» di bab sebelumnya. Setiap rentang diperiksa ulang dengan membaca awal hadits-haditsnya (rentang berakhir tepat sebelum bab bertajuk berikutnya).

| Hasil | Jumlah |
|---|---:|
| Entri bab tanpa judul di fihris | 75 |
| — di luar Kitab at-Tafsir, sudah benar di data (sebagian berkat koreksi sebelumnya) | 37 |
| — di luar Kitab at-Tafsir, **terlewat di teks digital → dikoreksi** | **26** |
| — Kitab at-Tafsir, di awal surah: 1 sudah «باب», 11 tampil dengan nama surah | 12 (dibiarkan; lihat di bawah) |

Koreksi baru (nomor hadits): 149; 218; 506; 882; 946; 1153; 1293; 1386; 1420; 2327; 2336–2337; 2348; 2439 (penutup Kitab al-Luqathah); 3019; 3181–3183; 3403–3405; 5154; 5196; 5284; 5441; 5714; 6320; 6967; 7099–7107; 7120–7121; 7222–7223. Setiap entri `koreksi_bab.json` menyebut halaman fihris, leaf scan, dan bab sebelum/sesudahnya.

Di Kitab at-Tafsir, bab tanpa judul di awal surah (mis. «سورة الأنبياء: بابٌ: حدثنا محمد بن بشار») tampil di situs dengan judul **nama surahnya**. Ini tidak salah (hadits itu memang di bagian surah tersebut), jadi tidak diubah.

Total koreksi bertanda bukti untuk Bukhari: **47 rentang** (ditambah 5 untuk Muslim, lihat di bawah). Diuji di `test_bab.py` (`test_fihris_dibaca_utuh`), termasuk hadits tetangga yang harus tetap di babnya.

Pemeriksaan ini juga menemukan dua masalah lain di judul bab, keduanya sudah diperbaiki (rincian di `docs/09-judul-kitab-bab.md`):
- **141 hadits Bukhari bernomor ganda** (mis. 299–301, 3164–3165) sebelumnya tanpa judul bab sama sekali. Kini dicocokkan lewat nomor dengan syarat ketat.
- **507 riwayat Tirmidzi, Muslim, dan Ibnu Majah berjudul bab berupa potongan sanad atau potongan teks** (mis. «وحدثني محمد بن حاتم…», «(م ٢) - حدثنا…», «(غلبت الروم)»). Penyebabnya parser kita. Kini 0, dan riwayat Tirmidzi yang berjudul bab naik dari 3.711 ke 3.919.

### Shahih Muslim: fihris Fu'ad 'Abd al-Baqi

Teks digital Muslim kita (OpenITI/Shamela) berasal dari edisi Dar Ihya' at-Turath, yaitu tahqiq Muhammad Fu'ad 'Abd al-Baqi. Scan cetakan al-Halabi dari tahqiq yang sama ada di archive.org (`alfirdwsiy2018_gmail_2778`), lengkap dengan jilid indeksnya. «فهرس الموضوعات» di jilid itu mencantumkan **setiap bab bernomor beserta rentang nomor hadits (nomor Fu'ad)**. Data kita menyimpan nomor Fu'ad di setiap riwayat (`no_arab`), jadi batas bab bisa dicocokkan langsung.

Cara:
1. OCR bawaan archive.org untuk halaman indeks terlalu rusak, jadi 80 halamannya dibaca ulang dengan Tesseract (bahasa Arab). Judul terbaca cukup baik, angka tidak.
2. Urutan judul fihris (OCR) disejajarkan dengan urutan judul bab teks digital (pemrograman dinamis).
3. Judul yang tidak berpasangan, atau yang kata-katanya tidak ditemukan di teks OCR halamannya, dilihat langsung di gambar (±40 halaman). Bila judul berbeda, halaman isi cetakan juga dilihat.

| Hasil | |
|---|---|
| Entri fihris tanpa pasangan di data (bab hilang di data) | 0 (yang tersisa hanya sampah OCR) |
| **Judul tambahan teks digital bertanda «*»** (bukan bab cetakan) | **59 baris**. Contoh: «* باب من أتى أهله ثم أراد أن يعود» di tengah bab 6 Kitab al-Haid (hadits 305–309); halaman isi hlm. 249 mencetak hadits 308 dan 309 tanpa judul. Kini diabaikan parser |
| Judul berbeda dari cetakan, terbukti di halaman isi | **5 → dikoreksi**: al-Libas bab 18, 19, 26; ar-Radha' bab 5; al-Imarah bab 9 |
| Judul di fihris berbeda, tetapi halaman isi sama dengan data | 1 (al-Musaqah bab 29: fihris menyingkat «غرز الخشب في الجدار»; halaman isi «في جدار الجار») → tidak dikoreksi |

Contoh koreksi: hadits 1841 dulu berjudul «في الإمام إذا أمر بتقوى الله وعدل كان له أجر», sedangkan cetakannya (hlm. 1471) «باب الإمام جنة يقاتل به من ورائه ويتقى به».

Batasan: halaman fihris 2–4 (Muqaddimah dan Kitab al-Iman bab 1–18) tidak ada di scan ini, jadi bagian itu belum dicek. Judul yang OCR-nya cocok ≥ 60% kata dianggap sama; perbedaan kecil di dalamnya (mis. satu kata) mungkin belum tertangkap.

### Sunan Ibnu Majah: fihris Fu'ad 'Abd al-Baqi (cetakan al-Halabi)

Teks digital Ibnu Majah kita adalah cetakan Dar Ihya' al-Kutub al-'Arabiyyah (al-Halabi), tahqiq Fu'ad 'Abd al-Baqi. Scan cetakan yang sama ada di archive.org (`SunanIbnMajaHalabi`). Fihrisnya di akhir jilid 1 (leaf 689–717) dan jilid 2 (leaf 810–845); halaman-halamannya dibaca dengan Tesseract dan disejajarkan seperti untuk Muslim.

- **Temuan utama: 121 bab hilang di data kita.** Di teks digital, 121 judul bab ditulis sebagai baris biasa («# باب النهي عن إتيان الحائض»), bukan baris judul («### | باب …»). Kadang judulnya terpotong ke beberapa baris («# باب / # وقت / # صلاة / # العشاء»). Parser hanya mengenali baris judul, jadi **346 hadits** tampil di bawah judul bab sebelumnya. Contoh: no. 639 dulu berjudul «ما للرجل من امرأته إذا كانت حائضا», padahal babnya «النهي عن إتيان الحائض». No. 690 dulu «وقت صلاة المغرب», padahal «وقت صلاة العشاء». Kini parser membaca baris itu (khusus Ibnu Majah; di kitab lain baris serupa adalah teks biasa).
- Buktinya: sebelum perbaikan, 114 entri fihris tidak berpasangan dengan bab mana pun di data; sesudahnya tinggal 7, dan ketujuhnya sampah OCR.
- Judul: judul yang OCR-nya tidak cocok dilihat langsung di 3 halaman dengan kandidat terbanyak (±25 judul, mis. Kitab ath-Thibb dan awal Kitab at-Tijarat). Semuanya sama dengan data; perbedaannya hanya salah OCR. Judul lain belum dilihat satu per satu.

### Sunan Abu Dawud: fihris cetakan Muhyiddin 'Abd al-Hamid

Scan `04-8461-2` (al-Maktabah al-'Ashriyyah, sama dengan dasar teks digital kita). Fihrisnya ada di akhir setiap jilid (39 halaman), dua kolom, dan berisi nomor halaman, bukan nomor hadits. Setiap halaman dipotong pada garis pemisah kolom lalu di-OCR per kolom.

- **Jumlah bab cocok:** data kita punya 1.873 urutan bab (1.868 diawali «باب»); jumlah yang lazim dikutip untuk Sunan Abu Dawud ±1.871.
- Judul yang kata-katanya tidak ditemukan di OCR fihris tinggal 30, hampir semuanya judul satu kata yang terlewat OCR (mis. «المزارعة», terlihat jelas di gambar).
- **3 judul dikoreksi** (dilihat di gambar fihris): «باب تفريع أبواب الركوع والسجود ووضع اليدين على الركبتين» (dipecah dua di teks digital; hadits 867–868), «باب كراهية الحلف بالأمانة» (teks digital: «في باب …»; 3253), «باب في كسب المعلم» (teks digital tanpa «باب»; 3416–3417).
- Baris «### | [حكم الألباني] :» (catatan penilaian al-Albani, 5 kali) kini diperlakukan sebagai catatan, bukan judul bab.

### Sunan an-Nasa'i: fihris cetakan Abu Ghuddah (jilid 9)

Scan `SunanNissa3AbuGuda` tidak punya OCR, jadi 367 halaman jilid 9 di-OCR sendiri. «فهرس تفصيلي لذكر أسماء الكتب وعناوين الأبواب» ada di leaf 34–103 (dua kolom, ±2.590 entri).

- Sejajar sangat baik: 2.435 pasangan judul cocok.
- **Judul terpotong.** Di teks digital, banyak judul terpecah ke beberapa baris («### || باب» + «### || الوضوء من الغائط» + «# والبول»), sehingga situs dulu hanya menampilkan potongannya. Ada juga 2 judul yang ditulis tanpa baris judul sama sekali («# أول وقت الصبح», «# (25 ما يقول في قيامه ذلك)»). Kini digabung/dibaca (khusus Nasa'i): **94 riwayat** sekarang berjudul lengkap, mis. «باب الوضوء من الغائط والبول», «باب تأويل قول الله عز وجل: {ويسألونك عن المحيض} [البقرة: 222]».
- Entri fihris tanpa pasangan hampir seluruhnya rangkaian «نوع آخر. أخبرنا …» (fihris mendaftar setiap «نوع آخر» terpisah) dan header kolom. Satu-satunya bab yang benar-benar tidak ada di teks digital adalah «باب المسح على الجوربين والنعلين»; haditsnya (no. 125) tidak punya teks Arab di sumber kita, jadi tidak ada yang salah tampil.
- Teks digital mengulang «التيمم في الحضر» untuk hadits 312–313, sedangkan fihris hanya punya satu bab (no. 195). Karena kalimatnya sama, tidak diubah.

### Jami' at-Tirmidzi: fihris dan halaman isi cetakan Basyar 'Awwad Ma'ruf

Teks digital Tirmidzi kita (Shamela 7895) berasal dari tahqiq Basyar 'Awwad Ma'ruf (Dar al-Gharb al-Islami, 1996, 6 jilid). Scan cetakan yang sama ada di archive.org (`gkt6_20251231`, berkas `gkt1`–`gkt6`, diunggah Desember 2025). Fihris babnya ada di akhir setiap jilid (112 halaman, satu kolom: nomor bab, judul, halaman). Fihris menulis «باب» hanya di entri pertama; sesudahnya diganti tanda ulang «.

Cara:
1. Kolom judul dipotong dari setiap halaman fihris lalu di-OCR dengan Tesseract. Judul kitab yang berhuruf besar dibaca dengan OCR tata letak penuh.
2. Urutan judul fihris disejajarkan dengan 2.315 judul bab mentah teks digital (pemrograman dinamis). 2.179 pasangan cocok; sisanya kebanyakan judul pendek («باب منه», «باب») yang rusak di OCR.
3. Judul yang tidak berpasangan atau berbeda kata dicek di gambar fihris. **Bila fihris berbeda dari data, halaman isi cetakan yang menentukan.** Fihris Basyar sering menyingkat (mis. «أبواب الطهارة» untuk «أبواب الطهارة عن رسول الله ﷺ», «مناقب جعفر بن أبي طالب» untuk «… أخي علي»), dan kadang berbeda dari judul di halaman isi.
4. Nomor bab di teks digital (dari cetakan) dicek berurutan per kitab untuk mencari bab yang hilang. Tidak ada yang hilang; selisih nomor yang ada memang begitu di cetakan (mis. Abwab ad-Da'awat).

| Temuan | Tindakan |
|---|---|
| **Judul kitab «أبواب النذور والأيمان» terlewat** (di teks digital ditulis sebagai baris biasa) → 24 hadits (1524–1547) tampil di bawah «أبواب الأضاحي» | Parser diperbaiki (fihris jilid 3, leaf 631) |
| Judul kitab «أبواب ٣٠ الجمعة» | Angka dibuang → «أبواب الجمعة» (fihris jilid 1, leaf 618) |
| Judul yang berlanjut ke baris berikutnya terpotong: «باب ما جاء في قول النبي ﷺ:» (tanpa «أمرت بقتالهم…»), «فضل سورة البقرة» (tanpa «وآية الكرسي»), «وعون الله» (tanpa «إياهم»), «والضرب» (tanpa «والوسم في الوجه») | Parser diperbaiki |
| Baris kedua blok judul di Bab Manaqib («يقال وله كنيتان: أبو تراب، وأبو الحسن», «واسم أبي وقاص: مالك بن وهيب», «واسمه سعيد بن زيد…»), yang di halaman isi dicetak tebal dan rata tengah seperti judulnya | Kini ikut judul (halaman isi jilid 6 hlm. 78, 103, 106) |
| Penanda ayat «@QUR@» di 7 judul; «ب بسم الله» (cetakan: «ببسم الله», jilid 1 hlm. 284) | Dibersihkan |
| **4 judul berbeda dari halaman isi:** «والثمر» → «والتمر» (no. 1311, jilid 2 hlm. 579); «في أخذ المال بحقه» → «في أخذ المال» (2374, jilid 4 hlm. 184); «ومن سورة والنجم» → «ومن سورة النجم» (3276–3284, jilid 5 hlm. 314); «ومن سورة تبت يدا» → «ومن سورة تبت» (3363, jilid 5 hlm. 379) | Dikoreksi (`koreksi_bab.json`) |
| **Bab tambahan edisi Ahmad Syakir:** «باب ما ذكر في مسح النبي ﷺ بعد نزول المائدة» (hadits 611–612). Catatan kaki Basyar (jilid 1 hlm. 600, no. 2): Ahmad Syakir menambahkannya dari naskah as-Sindi, padahal bab ini tidak ada di naskah mana pun. Karena itu Basyar menghapusnya (hadits 610 langsung disusul 613), dan haditsnya sudah ada di no. 94 | Judul tetap, halaman hadits menampilkan **catatan cetakan** (cara baru «catatan-cetak») |
| Fihris berbeda, tetapi halaman isi sama dengan data: «يأخذ المؤذن» (fihris «يؤخذ»), «في القراءة في المغرب», «التبكير بالتجارة», «بعضه بيع نصيب», «يحلف بالشيء» (fihris «بالمشي»), «ستة وأربعين», «دعا»; «والشمس وضحاها», «والتين», «إذا زلزلت الأرض» | Tidak dikoreksi |

**Temuan sampingan: teks yang diulang penyusun.** Penyelarasan memperlihatkan riwayat yang letaknya melompat jauh dari tetangganya, mis. Tirmidzi 2700 (di cetakan: Abwab al-Isti'dzan, bab salam kepada ahludz dzimmah) tampil di Abwab as-Siyar, karena teksnya sama dengan no. 1602. Penyebabnya di pencocokan kita (lihat docs/09). Setelah diperbaiki, 13 riwayat di Bukhari, Ibnu Majah, Tirmidzi, dan Nasa'i kini tampil di kitab dan bab yang benar.

Batasan: judul yang OCR-nya cocok dan kata-katanya ada di halaman fihris dianggap sama. Perbedaan satu huruf (mis. ث/ت) hanya tertangkap bila OCR membaca kata itu berbeda; judul pendek («باب منه») tidak dicek satu per satu.

### al-Muwaththa': fihris dan halaman isi cetakan Fu'ad 'Abd al-Baqi

Teks digital al-Muwaththa' kita berasal dari cetakan Dar Ihya' at-Turath al-'Arabi (tahqiq Muhammad Fu'ad 'Abd al-Baqi). Scan cetakan yang sama (1406 H, dua jilid dalam satu berkas) ada di archive.org (`16241406`). «فهرس الموضوعات حسب ترتيبها في الكتاب» ada di akhir jilid 1 (leaf 458–470) dan jilid 2 (leaf 1072–1091): setiap kitab dan bab bernomor, judul lengkap. Jenis hurufnya lama, jadi OCR-nya lebih lemah daripada cetakan Tirmidzi. Hanya kolom judul yang di-OCR, pada resolusi tinggi.

- 547 pasangan judul cocok langsung. Semua 34 judul data yang tidak berpasangan dicek: semuanya ada di fihris (terlewat OCR, terutama judul kitab berhuruf besar) dan ada di data. Kitab dan bab tidak ada yang hilang.
- Perbedaan kata antara fihris dan data hampir semuanya salah baca OCR. Sembilan calon yang tersisa dilihat di gambar fihris, lalu di halaman isi:
  - **«باب ما جاء بالتأمين خلف الإمام» → «باب ما جاء في التأمين خلف الإمام»** (hadits 193–196; halaman isi jilid 1 hlm. 87). Dikoreksi.
  - Fihris berbeda, tetapi halaman isi sama dengan data, jadi tidak dikoreksi: «من علة» (fihris «عن علة», hlm. 307), «في الإحرام» (fihris «للإحرام», hlm. 324), «من ولدهما», «إذا توفي سيدها» (fihris «توفي عنها»), «باب ما جاء فيما أفسد العبيد» (fihris tanpa «ما جاء»).
  - «باب القضاء فيمن هلك وله دين، وعليه دين له، فيه شاهد واحد»: koma di teks digital salah tempat (cetakan: «وعليه دين، له فيه شاهد واحد»). Bab ini hanya berisi perkataan Malik, tanpa riwayat di data kita, jadi tidak ada yang tampil.

Batasan: karena OCR lebih lemah, perbedaan satu huruf di judul yang OCR-nya rusak bisa terlewat.

### Sunan ad-Darimi: fihris dan halaman isi cetakan Husain Salim Asad

Teks digital ad-Darimi kita berasal dari tahqiq Husain Salim Asad ad-Darani (Dar al-Mughni). Scan cetakan yang sama ada di archive.org (`MusnadDarimiAll`, 4 jilid dalam satu berkas; `SunanDarimiDarani` adalah unggahan lain dari cetakan yang sama). «فهرس الموضوعات» ada di akhir (leaf 2405–2450): satu kolom, dengan titik penuntun ke nomor halaman. Titik penuntun membuat OCR melewatkan banyak baris, jadi titik dan nomor halaman diputihkan dulu per baris sebelum OCR.

- 1.348 pasangan judul cocok. Semua 30 judul data yang tidak berpasangan dilihat di gambar fihris: semuanya ada (terlewat OCR).
- **Dua judul bab hilang di data.** Teks digital menulis «### | باب» lalu judulnya di baris berikut («# النهي عن استقبال القبلة لغائط أو بول</span>», «# الفتيا وما فيه من الشدة</span>»). Polanya sama dengan Bukhari, tetapi dulu hanya ditangani untuk Bukhari. Halaman isi hlm. 526 memang mencetaknya sebagai judul bab («٦ - باب: النهي عن استقبال القبلة لغائط أو بول»). Kini dibaca (19 hadits).
- **Fihris Asad sering berbeda dari halaman isinya.** Fihris menambah atau mengganti kata, dan untuk bab tanpa judul ia memberi deskripsi dalam kurung, mis. «( في الذي يفتي الناس في كل ما يستفتى )», padahal di halaman isi hanya «باب». Dari 15 judul yang dicek di halaman isi, 14 sama dengan data, di antaranya «نبيذ الجر» (fihris «الخمر»), «في قتل العمد» (fihris «الدية في قتل العمد»), «قول علي وعبد الله وزيد في الرد» (fihris «في الجد»), «كم يشمت العاطس» (fihris «كيف»), «جر الولاء» (catatan kaki Asad: «وفي المطبوعات: باب حق جر الولاء»).
- **1 koreksi:** «باب الجهاد في سبيل الله أفضل الأعمال» → «… أفضل العمل» (hadits Asad no. 2435; halaman isi hlm. 1545). Karena riwayat ad-Darimi kita bernomor Lidwa, koreksi untuk kitab ini memakai nomor edisi (`"penomoran": "edisi"` di `koreksi_bab.json`).

Batasan: sekitar 50 perbedaan kata kecil antara fihris dan data lainnya (mis. «يوما»/«يوم», «تزال»/«يزال») tidak dicek satu per satu di halaman isi. Dengan pola di atas (fihris yang berbeda, bukan data), kemungkinan besar data sudah sesuai halaman isi.

### Musnad asy-Syafi'i: daftar isi cetakan al-Fahl (utuh)

Teks digital kita: tartib Sanjar, tahqiq Mahir Yasin al-Fahl (Ghiras, 2004). Scan cetakannya ada di archive.org (`alfirdwsiy2018_gmail_3731_201808`). Daftar isi keempat jilid ada di awal berkas (leaf 4–25). Judulnya berharakat penuh, bergaris bawah, dan bertitik penuntun, sehingga OCR terlalu bising untuk pencocokan otomatis (hanya ±340 dari ±600 judul cocok).

- **Seluruh daftar isi dibaca langsung dari gambar** (leaf 5–25): 32 kitab dan ±565 bab, dibandingkan satu per satu dengan 597 judul data, baik urutan maupun kata-katanya. Fihris kadang menyingkat judul; bila berbeda, halaman isi yang menentukan.
- **2 judul dikoreksi** (dilihat di halaman isi; rentang memakai nomor edisi al-Fahl):
  - «باب: ترك الجمعة للعذر» (hadits 458–459). Teks digital «ترك الجمعة وللعذر»: penanda halaman manuskrip «/٦٢و/» di tengah judul terbaca sebagai huruf «و» (jilid 2 hlm. 33, leaf 403).
  - «باب: في الضبع» (hadits 1508–1509, tentang hyena). Teks digital menulis «باب: في الضب» dua kali berturut-turut; di cetakan, bab ke-2 «في الضبع» dan bab ke-3 «في الضب» mulai hadits 1510 (jilid 3 hlm. 233–234, leaf 906–907).
- Satu kandidat lain («رضي الله عنها» di bab pertama Kitab an-Nikah) ternyata sudah benar di data.
- Temuan parser: «### $ 1277 - باب ما كان من الطلاق والرجعة» (nomor hadits dan judul bab dalam satu baris). Judulnya sudah benar, tetapi hadits 1277 dulu tanpa nomor edisi. Kini diperbaiki.
- Teks digital juga punya «### | كتاب الرجعة.» palsu (ujung kalimat takhrij «أخرجه من كتاب الرجعة.») tepat sebelum judul kitab yang asli. Tidak ada riwayat di bawahnya, jadi tidak ada yang tampil salah.

Batasan: hanya judul yang berbeda dari fihris yang dicek di halaman isi. Judul yang sama di fihris dan data tidak dibuka halaman isinya.

## Batasan dan yang belum

- **Nomor entri belum diverifikasi.** OCR mengacaukan angka Arab-Hindi di kolom nomor.
- **Kasyf al-Khafa'** hanya 11 dari 40 entri yang ditemukan, karena OCR cetakan 1351 H sangat rusak.
- **Teks hadits** (Bukhari, Muslim, dst.) belum dibandingkan dengan cetakan. Scan Bukhari di archive.org tidak punya OCR. Teks hadits saat ini diverifikasi dengan cara lain: dua sumber digital yang sepakat (tingkat A) dan uji silang atribusi.
- **Teks dan nomor hadits Bukhari** belum dicek visual satu per satu. Halamannya harus dicari manual di scan (OCR-nya tidak bisa dipakai untuk mencari), atau dengan scan lain yang OCR-nya lebih baik.
- Muslim: halaman fihris Muqaddimah dan Kitab al-Iman bab 1–18 belum dicek (tidak ada di scan).
- **Fihris Bukhari sudah dibaca utuh**, tetapi hanya untuk bab tanpa judul. Judul bab bertajuk belum dibandingkan satu per satu dengan fihris; baru 14 judul Kitab 62 yang dicek persis.
- **Sudah dicek dengan fihris cetak:** Bukhari, Muslim, Ibnu Majah, Abu Dawud, Nasa'i, Tirmidzi, Malik, ad-Darimi (untuk Abu Dawud, Nasa'i, dan Tirmidzi: struktur dan judul lewat OCR, kandidat dilihat di gambar; Tirmidzi juga di halaman isi). Al-Muwaththa' dan ad-Darimi juga sudah dicek (OCR al-Muwaththa' lebih lemah); asy-Syafi'i (al-Fahl) seluruh daftar isinya. **Belum:** Musnad Ahmad.
