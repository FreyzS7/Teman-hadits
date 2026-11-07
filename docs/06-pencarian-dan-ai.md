# Pencarian Pintar dan Peran AI

## Prinsip

**AI boleh menjadi pustakawan, tidak boleh menjadi sumber.** AI hanya boleh mengubah kalimat pengguna menjadi rencana pencarian. Semua teks hadits, nomor, terjemah, dan penilaian yang tampil harus berasal dari database. AI tidak pernah menulis isi hadits, menerjemahkan, meringkas hukum, atau menilai derajat. Model bahasa bisa "mengarang" hadits yang terdengar meyakinkan, dan itu justru kebalikan dari tujuan situs ini.

## Lapis 1: tanpa AI (selalu aktif, gratis, tanpa batas)

Kode: `pipeline/cari.py`. Kamus: `pipeline/kamus_konsep.json`.

1. **Varian ejaan dicari bersamaan:** shalat/sholat/solat/salat, sedekah/shadaqah/shodaqoh, dst. Terjemahan Lidwa sendiri memakai ejaan campuran (sedekah 821, shadaqah 248, shodaqoh 16).
2. **Kata pengisi dibuang:** tolong, carikan, hadits, tentang, min, dong, …
3. **Kata maksud** (keutamaan, anjuran, larangan, adab, …) tidak diwajibkan ada, hanya menaikkan peringkat.
4. **Kamus konsep:** satu istilah awam dipetakan ke padanan Arabnya dan ke judul kitab/bab, lengkap dengan bukti hitungan.
5. **Alasan selalu ditampilkan:** setiap hasil membawa keterangan kenapa ia muncul ("teks Arab memuat قيام رمضان", "masuk kitab Taraweeh").

Contoh terukur (build 1 Nov 2026):

| Kueri | Pencarian kata biasa | Lapis 1 |
|---|---:|---:|
| "tolong carikan hadits tentang sholat tarawih" | 5 (hanya terjemah yang kebetulan memuat "tarawih") | **47**, termasuk Bukhari 2009 dan Muslim 759; kata "tarawih" (تراويح) tidak ada di teks Arab mana pun, hadits menyebutnya قيام رمضان |
| "min ada hadist tentang keutamaan sedekah ga" | 4 | 1.083 kandidat, tetapi **urutan teratas belum relevan** (mis. kisah warisan Fathimah yang memuat kata "sedekah") |

Contoh kedua adalah batas aturan: kata kuncinya cocok, tetapi maknanya tidak.

**Pembaruan (tema HadeethEnc sudah dimuat):** pencarian kini menampilkan *Tema terkait* di atas hasil. Kata inti (mis. "sedekah", dengan semua varian ejaannya) wajib cocok dengan judul tema, sementara kata maksud ("keutamaan") hanya menambah skor. "keutamaan sedekah" → tema **Sedekah Sunah** (27 hadits kurasi ulama, terhubung ke Bukhari 1442, Muslim 1010, dst.); "keutamaan puasa" → **Keutamaan Puasa**. Ini tanpa AI.

**Pembaruan 7 Nov 2026 (kamus diperluas):** 45 kueri awam diuji; yang hasilnya lemah karena istilah awamnya tidak ada di terjemah diberi entri kamus. Setiap padanan dicek jumlahnya di database dan contoh teks Arabnya dibaca. Padanan yang bermakna ganda tidak dipakai (mis. الغيبة sendirian juga berarti "bepergian lama"; مزامير di hadits Abu Musa berarti suara merdu).

| Kueri | Sebelum | Sesudah | Padanan |
|---|---:|---:|---|
| "birrul walidain" | 0 | 60 | بر الوالدين, عقوق الوالدين |
| "tahajud" | 2 | 95 | تهجد, قيام الليل, ejaan tahajjud |
| "silaturahmi" | 26 | 199 | صلة الرحم, فليصل رحمه, ejaan silaturrahim |
| "isbal" | 22 | 84 | إسبال, جر ثوبه |
| "ziarah kubur" | 26 | 42 | زيارة القبور, زوروا القبور |
| "musik" | 7 | 13 | المعازف, مزمار الشيطان (hanya riwayat; tanpa kesimpulan hukum) |
| "utang" | 57 | 540 | ejaan Lidwa "hutang" |
| "ghibah" | 20 | 24 | ما الغيبة, ejaan gibah |
| "sholawat nabi" | 1 | 105 | من صلى علي صلاة, اللهم صل على محمد (bukan صلى علي, yang juga berarti menshalati jenazah) |
| "takziah" | 2 | 16 | من عزى مصابا, التعزية |
| "tawakal" | 4 | 93 | حق توكله, يتوكلون (bukan توكل sendirian: "Allah menjamin") |
| "menjaga lisan" | 7 | 39 | فليقل خيرا أو ليصمت, ما بين لحييه |
| "istinja" | 10 | 95 | الاستنجاء, ejaan beristinja' |
| "cadar" | 14 | 18 | تنتقب (bukan النقاب sendirian: "jalan masuk Madinah") |
| "hak tetangga" | 22 | 332 | الجار, جاره |
| "jilbab" | 32 | 20 | جلباب; lebih sedikit tetapi semuanya tentang jilbab |
| "khitan" | 35 | 55 | اختتن, خمس من الفطرة الختان (bukan الختان sendirian: hadits mandi junub) |

Putaran kedua menguji 60 kueri lagi. Kueri lain sudah cukup baik tanpa entri baru (mis. zakat fitrah, lailatul qadar, aqiqah, dajjal, siwak).

Putaran ketiga (60 kueri doa, muamalah, fiqih):

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "shalat id" | 12.266 (kata "id" terbuang, jadi hanya "shalat" yang dicari) | 552 | العيدين, يوم العيد, يوم الفطر, يوم الأضحى |
| "doa masuk wc" | hasil teratas tidak relevan | Muslim 831, Bukhari 142 | دخل الخلاء, أتى الخلاء |
| "doa naik kendaraan" | hasil teratas tidak relevan | Muslim 3275, Ahmad | سخر لنا هذا |
| "korupsi" | 4 | 74 | الغلول (istilah hadits terdekat; catatannya tampil di hasil) |
| "monopoli"/"menimbun" | 2/45 | 29 | يحتكر, احتكر |
| "wakaf" | 27 | 14 | حبست أصلها (lebih sedikit, semuanya hadits wakaf 'Umar) |
| "ijma" | 2 | 4 | لن تجتمع, لا يجمع أمتي (riwayatnya memang sedikit) |
| "jimat", "judi", "ihsan", "suap" | 15, 30, 25, 98 | 15, 80, 25, 55 | التمائم; الخمر والميسر, النرد; ما الإحسان; الراشي والمرتشي |

Tidak dipakai karena bermakna ganda: تميمة/"tamimah" (nama perawi Abu Tamimah), الميسر sendirian (كل ميسر = "dimudahkan"), على ضلالة sendirian.

"doa", "berdoa", dan "bacaan" kini menjadi kata maksud: tidak diwajibkan, tetapi menambah +1,5 bila letaknya dekat kata kunci. Banyak hadits doa tidak memuat kata "doa" ("apabila naik kendaraan, beliau mengucapkan ..."). Bila kueri hanya berisi kata maksud ("doa", "keutamaan"), kata itu dicari sebagai kata biasa.

Putaran keempat (50 kueri akhlak, keluarga, akhirat, sirah):

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "telaga kautsar" | 9 | 226 | على الحوض, حوضي, الكوثر (bukan الحوض sendirian: kolam biasa) |
| "isra miraj" | 8 | 63 | أسري بي, عرج بي (bukan terjemah "isra" sendirian: Surat al-Isra') |
| "shirath" | 26 | 51 | على الصراط, جسر جهنم (bukan الصراط sendirian: الصراط المستقيم) |
| "padang mahsyar" | 12 | 55 | يحشر الناس, المحشر |
| "namimah" | 5 | 53 | النميمة, لا يدخل الجنة قتات (bukan قتات sendirian: nama perawi) |
| "tawadhu" | 4 | 27 | تواضع |
| "qanaah" | 1 | 9 | قنعه الله (riwayatnya memang sedikit) |
| "poligami" | 0 | 11 | امرأتان فمال, أمسك أربعا (bukan كانت له امرأتان / أربع نسوة: kisah lain) |
| "khulafaur rasyidin" | 4 | 12 | الخلفاء الراشدين |
| "mizan" | – | – | أثقل في الميزان, تملأ الميزان (bukan الميزان sendirian: timbangan dagang) |

Tidak diberi entri karena tidak ada padanan Arab yang khusus: "mukjizat" (آية terlalu umum), "mertua" (الحمو berarti kerabat suami, bukan mertua), "mendidik anak".

Bukti hitungan tiap entri ada di kolom `bukti` di `kamus_konsep.json`.

**Urutan hasil (7 Nov 2026)**, di `site/src/cari.js`. Setiap aturan tampil sebagai alasan di hasil:

- **Kata berdekatan (+0,5):** bila semua kata kueri muncul berdekatan (FTS5 `NEAR`, jarak 8 kata). "larangan minum berdiri" kini dibuka oleh Muslim 5274 ("melarang minum sambil berdiri").
- **Kata maksud harus dekat kata inti (+1,5):** "keutamaan", "larangan", "doa", dan sejenisnya hanya menambah skor bila letaknya dekat kata kunci. Sebelumnya "keutamaan sedekah" dibuka oleh Bukhari 3711 ("keutamaan anda wahai Abu Bakr").
- **Prioritas kitab bila relevansinya setara:** Bukhari/Muslim +0,12; Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah, al-Muwaththa' +0,06. Bobot ini lebih kecil dari bonus kedekatan, jadi hanya memecah hasil yang hampir seri. Sebelumnya urutan seperti itu ditentukan oleh selisih bm25 yang sangat kecil, sehingga Musnad Ahmad (riwayatnya paling banyak) memenuhi bagian atas.
- **Akhiran, bukan awalan:** kata 4 huruf atau lebih dicari bersama akhiran Indonesia (-nya, -ku, -mu, -lah, -kah, -pun, -kan, -kannya, -kanlah, -an, -i, -inya, -ilah, dst.). Dulu dicocokkan sebagai awalan, sehingga "riba" ikut mencocokkan "ribath" (47 kali, mis. Muslim 587) dan "jual" mencocokkan "ju'alah". Ejaan Lidwa untuk haid (haidl 330, haidh 164) dimasukkan ke grup varian. Akibatnya jumlah hasil berubah: riba 245→208, jual beli 784→756, haid 1042→1022 (yang hilang nama seperti "Haidah"); sedekah, menikah, dan wudhu tidak berubah.

**Riwayat serupa dilipat (7 Nov 2026):** satu hadits sering diriwayatkan lewat banyak jalur, sehingga satu halaman hasil bisa berisi belasan kartu dengan matan yang sama. Kini, dalam satu halaman, riwayat kedua dan seterusnya yang serupa dilipat di bawah riwayat pertama sebagai tautan "Riwayat serupa di halaman ini". Tidak ada yang dihapus. Dua riwayat dianggap serupa bila:

- takhrij menandai keduanya "sama" (`riwayat.jalur_json`), atau
- kata akar matan Arabnya (tanpa sanad dan komentar penyusun) beririsan minimal 80% (Jaccard), dengan matan minimal 4 kata.

Ambang 0,8 dipilih setelah melihat pasangan nyata. Pada 1,00, Muslim 831, Bukhari 6322, dan Tirmidzi 6 sama-sama doa masuk WC. Pada 0,5–0,7, mulai tercampur hadits yang berbeda (mis. Tirmidzi 5 dan 6). Data takhrij tidak cukup sebagai satu-satunya dasar: 27.115 dari 69.408 riwayat tidak punya jalur, termasuk banyak riwayat Ahmad. Contoh: halaman pertama "niat" kini 7 kartu, dengan 10 jalur hadits "innamal a'mal" sebagai tautan. Pengelompokan hanya dalam satu halaman, jadi penomoran halaman tidak berubah. Kode: `kelompokkan()` di `site/src/cari.js`, uji: `site/test/kelompok.test.js`.

Jalan perbaikan yang lain:

- **Kategori HadeethEnc** (tanpa AI): 447 tema berbahasa Indonesia yang disusun dan ditinjau ulama, misalnya "Sedekah Sunah" berisi 27 hadits. Pertanyaan bertema dicocokkan dulu ke kategori ini.
- **Lapis 2** (AI terbatas), di bawah.

## Lapis 2: AI sebagai penerjemah maksud (opsional, dibatasi)

Dipakai hanya bila lapis 1 tidak menemukan konsep atau hasilnya sedikit.

1. Kalimat pengguna dikirim ke model dengan instruksi tunggal: kembalikan **JSON** berisi kata kunci Indonesia, padanan Arab, dan kemungkinan tema (dari daftar kategori yang kita berikan). Tidak ada teks bebas.
2. JSON divalidasi. Kata Arab yang tidak ada di database dibuang. Lalu pencarian lapis 1 dijalankan dengan rencana itu.
3. Rencana ditampilkan ke pengguna ("Kami mencari: صدقة، فضل الصدقة, tema: Sedekah Sunah"), sehingga terbuka dan bisa diperiksa.
4. **Cache per kueri yang dinormalisasi:** pertanyaan yang sama tidak memanggil AI dua kali.
5. **Dari AI ke kamus:** rencana AI yang sering dipakai diusulkan menjadi entri `kamus_konsep.json`, lalu ditinjau manusia. Lama-kelamaan makin sedikit kueri yang butuh AI.

### Batas pemakaian (agar tetap gratis)

- Per pengguna (IP/sidik ringan): misalnya 10 kueri AI per hari. Setelah habis, situs tetap jalan dengan lapis 1.
- Batas global per hari, di bawah kuota gratis penyedia. Bila tercapai, AI dimatikan otomatis sampai besok.
- Hanya kueri lebih dari ~3 kata yang tidak dikenali kamus yang dikirim ke AI.

### Pilihan model gratis

Angka kuota sering berubah, jadi cek halaman resmi saat implementasi.

| Pilihan | Kelebihan | Catatan |
|---|---|---|
| **Cloudflare Workers AI** | Satu atap dengan hosting (Worker + D1); ada kuota gratis harian; bisa diemulasikan lokal | Model open-weight (Llama/Qwen/Gemma); cukup untuk tugas "kalimat → JSON" |
| Google Gemini API (tier gratis) | Kualitas bahasa Indonesia bagus | Data di tier gratis dapat dipakai Google untuk pengembangan produk; jangan kirim data pribadi |
| Groq (tier gratis) | Sangat cepat | Batas per menit ketat |

Saran: **Cloudflare Workers AI**, karena kita memang akan memakai Cloudflare.

## Lapis 3 (nanti): pencarian makna dengan embedding

Setiap riwayat diberi vektor makna (model multibahasa seperti bge-m3, yang paham Indonesia dan Arab). Vektor dihitung **sekali** saat build di komputer lokal, jadi gratis. Saat pencarian, hanya kueri yang perlu diubah menjadi vektor. Lapis ini menangani "keutamaan sedekah" tanpa kamus, tetapi hasilnya tetap riwayat dari database, bukan teks buatan.
