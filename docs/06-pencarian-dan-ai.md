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

Putaran kelima (55 kueri fiqih ibadah dan muamalah). Banyak istilah fiqih tidak ada di teks hadits, karena hadits memakai kalimat, bukan nama bab fiqih:

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "shalat tahiyatul masjid" | 13.652 (hanya "shalat" yang cocok) | 19 | فليركع ركعتين قبل أن يجلس |
| "shalat rawatib" | 12.264 (hanya "shalat") | 67 | اثنتي عشرة ركعة |
| "masbuq" | 0 | 25 | وما فاتكم فأتموا |
| "badal haji" | 1.659 (hanya "haji") | 50 | حج عن أبيك, أحج عنه |
| "mudharabah" | 0 | 3 | قراضا (atsar, al-Muwaththa') |
| "ghasab" | 0 | 29 | طوقه من سبع أرضين (غصب sendiri tidak ada di teks) |
| "luqathah" | 3 | 62 | اللقطة, terjemah "barang temuan" |
| "gharar" | 11 | 20 | بيع الغرر |
| "sutrah" | 19 | 25 | إلى سترة, مثل مؤخرة الرحل (bukan سترة sendirian: "Allah menutupi aib") |
| "fidyah" | 30 | 43 | طعام مسكين, يطيقونه (bukan فدية sendirian: tebusan tawanan) |
| "bughat" | 0 | 22 | الفئة الباغية |
| "basmalah" | 34 | 114 | بسم الله الرحمن الرحيم |

Tidak diberi entri: "syirkah" (الشركة bercampur dengan doa "شر الشيطان وشركه") dan "mustahik zakat" (hanya 1 riwayat memuat ayatnya). Kata "sutra" tidak dijadikan pemicu karena berarti kain sutra.

Putaran keenam (50 kueri adab makan-minum, kesehatan, hewan, penampilan). Sebagian besar sudah baik tanpa entri baru (mis. "cicak" → Ibnu Majah 3228, "meniup minuman" → Ibnu Majah 3288, "menguap" → Bukhari 6226). Yang ditambah:

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "habbatussauda" | 2 | 28 | الحبة السوداء, terjemah "jintan hitam" |
| "minum tiga tegukan" | hasil ke-2 tentang khamr | 16, dibuka Bukhari 5631 | يتنفس في الإناء ثلاثا |
| "sutra laki laki" | hasil teratas tidak relevan | Ahmad 18694, Ibnu Majah 3597 | الحرير, على ذكور أمتي |
| "ruqyah"/"jampi" | jatuh ke "sebagian kata" | 151 | بالمعوذات, لا رقية إلا (bukan رقية sendirian: nama Ruqayyah) |

Konsep sutrah tadi tidak memakai pemicu "sutra"; kini "sutra" memicu konsep kain sutra (الحرير). "rukyah" sengaja bukan pemicu ruqyah, karena berarti rukyatul hilal.

Putaran ketujuh (44 kueri nabi, malaikat, jin, surat, dzikir):

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "nabi khidir" | 4 | 38 | صاحب موسى هو الخضر (bukan الخضر sendirian: "hijau") |
| "munkar nakir" | 1 | 1 | Tirmidzi 1071, satu-satunya riwayat di koleksi ini |
| "asmaul husna" | 0 | 17 | تسعة وتسعين اسما |
| "hauqalah" | 0 | 84 | لا حول ولا قوة إلا بالله |
| "istirja" | 16 | 28 | إنا لله وإنا إليه راجعون |
| "surat yasin" | 11 | 25 | يس (derajat tiap riwayat berbeda; lihat penilaiannya) |
| "surat al mulk" | 9 | 15 | تبارك الذي بيده الملك |
| "ayat kursi" | 24 | 24 | آية الكرسي, kini dibuka Bukhari 5010 |

Tidak diberi entri: "kesurupan" (hampir tidak ada di data), "surat al ikhlas" ("ikhlas" juga tema keikhlasan, jadi tidak dijadikan pemicu), dan "malaikat maut" (sudah 16 hasil yang tepat lewat ملك الموت di terjemah).

Putaran kedelapan (50 kueri pergaulan, keluarga, isu modern, harta):

| Kueri | Sebelum | Sesudah | Padanan / catatan |
|---|---:|---:|---|
| "khalwat" | 1 | 15 | لا يخلون رجل بامرأة |
| "safar wanita tanpa mahram" | 6.713 (hanya sebagian kata) | 122, dibuka Tirmidzi 1169 | ذو محرم, لا تسافر المرأة |
| "nikah mut'ah" | 462 | 81 | نكاح المتعة, متعة النساء (bukan المتعة sendirian: haji tamattu') |
| "melamar"/"khitbah" | 91/1 | 162 | خطبة أخيه (bukan خطبة sendirian: sama tulisannya dengan khutbah) |
| "homoseksual" | 2 | 16 | عمل قوم لوط |
| "banci" | 15 | 33 | المخنثين, المترجلات |
| "kb" | 0 | 97 | العزل (catatan: riwayat terdekat; hukum KB modern tanyakan ulama) |
| "gambar makhluk hidup" | 46 | 295, dibuka Bukhari 5950 | المصورون, التصاوير, التماثيل |
| "pengemis" | 6 | 182 | يسأل الناس (bukan المسألة sendirian: "pertanyaan") |
| "dzalim" | 15 | 240 | grup ejaan zhalim/zalim/dzalim |

Tidak diberi entri karena tidak ada lafaz hadits yang khusus dan pemetaannya sudah berupa ijtihad: pacaran, ikhtilat, ta'aruf, nikah siri, aborsi, onani, LGBT (selain liwath), valentine, tahun baru, ulang tahun, foto, televisi, rokok, narkoba, olahraga. "wali" tidak dijadikan pemicu karena juga berarti wali Allah.

Putaran kesembilan (297 judul tema HadeethEnc sebagai kueri). Sebagian besar judul yang lemah adalah nama kategori (mis. "Akidah", "Sirah Nabawiyah", "Fikih Muamalah"); untuk kueri itu situs sudah menampilkan tautan "Tema terkait", jadi tidak dibuat entri. Yang diperbaiki adalah ejaan yang berbeda dari terjemah Lidwa, yaitu grup varian:

- adzan/azan (793/12)
- iqamah/iqamat/iqomah
- iddah/idah
- itikaf/iktikaf
- qishash/qisas/qishas
- zhihar/zihar
- istihadhah/istihadlah/istihadah

Ditambah dua konsep: mengusap khuf (على الخفين, 128) dan ahlul bait (أهل بيتي, 57). Hasilnya:

| Kueri | Sebelum | Sesudah |
|---|---:|---:|
| "azan dan iqamah" | 3 | 570 |
| "zihar" | 0 | 21 |
| "idah" | 5 | 327 |
| "iktikaf" | 8 | 193 |

"ahlul" sengaja bukan pemicu, karena juga dipakai untuk "ahlul kitab".

**Kueri berupa kalimat (putaran kesepuluh):** 20 potongan hadits populer diuji, termasuk 4 yang dikenal lemah/palsu. Pencarian kata kunci kurang tepat untuk kalimat: "senyummu kepada saudaramu adalah sedekah" jatuh ke mode "sebagian kata" (63.721 hasil), dan "tuntutlah ilmu sampai ke negeri cina" dibuka kisah Nabi Musa. Cek Hadits menangani kalimat ini jauh lebih baik, dan daftar Populer mengenali keempat ucapan lemah/palsu.

Bila kueri minimal 4 kata dan menyisakan minimal 3 kata kunci (setelah kata pengisi dan istilah kamus), halaman Cari kini:

- menampilkan kotak berisi tautan ke pembahasan ulama bila kalimatnya mirip ucapan populer;
- menyarankan Cek Hadits ("Cek kalimat ini"), dengan keterangan tambahan bila tidak ada riwayat yang memuat semua katanya.

Ambang kemiripan populer di halaman Cari 0,75, lebih ketat dari Cek Hadits (0,6). Alasannya: "malu sebagian dari iman" (shahih) tidak boleh diarahkan ke entri "kebersihan sebagian dari iman" hanya karena 2 dari 3 kata sama. Kueri pertanyaan biasa ("tolong carikan hadits tentang sholat tarawih") tidak memunculkan kotak, karena hanya tersisa satu istilah kamus.

**Ketepatan Cek Hadits (teks Indonesia):** Cek Hadits mencari riwayat yang memuat semua kata khas dari teks yang ditempel, dengan bobot idf. Dulu kata-kata itu boleh tersebar di mana saja dalam riwayat. Akibatnya "surga di bawah telapak kaki ibu" cocok 100% dengan Abu Dawud 726 (tata cara meletakkan tangan dalam shalat) yang panjang. Perubahannya:

- **Skor dihitung dalam satu jendela** sepanjang 3×(jumlah kata kunci)+6 kata yang paling banyak memuat kata kunci (`liputanJendela()` di `site/src/teks.js`).
- **Pemecah seri:** pertama jarak kata yang lebih rapat (selisih ≤ 2 kata dianggap setara), lalu urutan kitab (Bukhari, Muslim, Sunan, al-Muwaththa', Ahmad, ad-Darimi, asy-Syafi'i). Sebelumnya urutan seri ditentukan kebetulan oleh indeks.

Diuji dengan 22 kalimat:

| Kalimat | Sebelum | Sesudah |
|---|---|---|
| surga di bawah telapak kaki ibu | Abu Dawud 726 (salah) | Nasa'i 3104 ("surga di bawah kakinya") |
| menuntut ilmu wajib bagi setiap muslim | Tirmidzi 619 | Ibnu Majah 224 (hadits itu sendiri) |
| sebaik-baik manusia yang paling bermanfaat bagi manusia | "ditemukan" di Abu Dawud 4089 (soal isbal) | tidak ditemukan (memang tidak ada di kitab-kitab ini) |
| tangan di atas lebih baik dari tangan di bawah | Bukhari 1429 | Bukhari 1472 (hadits Hakim bin Hizam) |
| agama itu nasihat | Muslim 55a | Muslim 55a |

Biaya CPU tetap sekitar 2 ms untuk 120 kandidat.

**Uji lebih luas (`npm run uji:cek`, di folder `site`):** 100 riwayat tingkat A diambil acak dengan biji tetap. Dari kutipan sabda di terjemahnya, dipotong 8–15 kata, lalu potongan itu diperiksa lewat Cek Hadits terhadap D1 lokal.

| | Riwayat asal | Kelompok/keluarga | Riwayat lain | Tidak ditemukan |
|---|---:|---:|---:|---:|
| Sebelum (seluruh teks) | 67 | 9 | 24 | 0 |
| Sesudah (jendela) | 78 | 8 | 14 | 0 |

Dari 14 "riwayat lain", 6 memuat potongan yang sama persis (riwayat saudara, mis. Muslim 2089/2090) dan 2 adalah kisah yang sama dari jalur lain (Bukhari 3686/3699: Uhud bergetar; Ahmad 3426/Bukhari 3150: "Allah merahmati Musa"). Sisanya potongan yang terlalu umum, seperti "seorang laki-laki datang kepada Nabi seraya berkata", atau potongan sanad yang ikut terambil. Secara praktis sekitar 94 dari 100 menemukan hadits yang benar. Butuh Node ≥ 22.5 (`node:sqlite`).

**Teks Arab (`npm run uji:cek -- arab`):** 100 potongan 6–12 kata matan Arab berharakat (tanpa sanad). Hasilnya 75 riwayat asal, 20 kelompok/keluarga, 5 riwayat lain, 0 tidak ditemukan, jadi **95/100**. Kelima sisanya potongan yang memang tidak menunjuk satu hadits: frasa baku ("صلى الله عليه وسلم أما إنك"), potongan sanad ("عن ابن أبي مليكة عن عائشة"), komentar at-Tirmidzi ("وفي الباب عن أبي"), dan "صليت خمسا" yang ada di beberapa hadits sujud sahwi. Pencocokan Arab (2-gram) tidak diubah. Tambahkan `rinci` untuk mencetak setiap kasus.

Belum terpecahkan: "kebersihan sebagian dari iman" tetap ke Ahmad 9498. Terjemah Lidwa untuk Muslim 223 (الطهور شطر الإيمان) memakai kata "bersuci", bukan "kebersihan", jadi Cek Hadits yang mencocokkan kata tidak bisa menemukannya. Kotak populer tetap menampilkan pembahasan ulamanya.

**Awalan kata (7 Nov 2026):** orang mengetik kata dasar ("baca", "puasa", "minum"), terjemah memakai kata berimbuhan ("membaca", "berpuasa", "meminum"). Kini kata 3+ huruf juga dicari dengan awalan me-/di-/ber-/ter-, dengan peluluhan meN- yang lazim (pukul→memukul, tulis→menulis, sapu→menyapu, kirim→mengirim). Bentuk yang tidak ada dalam bahasa Indonesia (mis. "meriba") tidak berbahaya karena tidak pernah muncul di terjemah. "wanita haid baca quran": 8.238 (hanya sebagian kata) → 642, dibuka Ibnu Majah 596. "wudhu" 951 → 2.052 ("berwudhu"), "doa" 877 → 2.325 ("berdoa"). Kode: `bentukKata()` di `site/src/cari.js`.

Bukti hitungan tiap entri ada di kolom `bukti` di `kamus_konsep.json`.

**Urutan hasil (7 Nov 2026)**, di `site/src/cari.js`. Setiap aturan tampil sebagai alasan di hasil:

- **Kata berdekatan (+0,5):** bila semua kata kueri muncul berdekatan (FTS5 `NEAR`, jarak 8 kata). "larangan minum berdiri" kini dibuka oleh Muslim 5274 ("melarang minum sambil berdiri").
- **Kata maksud harus dekat kata inti (+1,5):** "keutamaan", "larangan", "doa", dan sejenisnya hanya menambah skor bila letaknya dekat kata kunci. Sebelumnya "keutamaan sedekah" dibuka oleh Bukhari 3711 ("keutamaan anda wahai Abu Bakr").
- **Prioritas kitab bila relevansinya setara:** Bukhari/Muslim +0,12; Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah, al-Muwaththa' +0,06. Bobot ini lebih kecil dari bonus kedekatan, jadi hanya memecah hasil yang hampir seri. Sebelumnya urutan seperti itu ditentukan oleh selisih bm25 yang sangat kecil, sehingga Musnad Ahmad (riwayatnya paling banyak) memenuhi bagian atas.
- **Akhiran, bukan awalan:** kata 4 huruf atau lebih dicari bersama akhiran Indonesia (-nya, -ku, -mu, -lah, -kah, -pun, -kan, -kannya, -kanlah, -an, -i, -inya, -ilah, dst.). Dulu dicocokkan sebagai awalan, sehingga "riba" ikut mencocokkan "ribath" (47 kali, mis. Muslim 587) dan "jual" mencocokkan "ju'alah". Ejaan Lidwa untuk haid (haidl 330, haidh 164) dimasukkan ke grup varian. Akibatnya jumlah hasil berubah: riba 245→208, jual beli 784→756, haid 1042→1022 (yang hilang nama seperti "Haidah"); sedekah, menikah, dan wudhu tidak berubah.

**Riwayat serupa dilipat (7 Nov 2026):** satu hadits sering diriwayatkan lewat banyak jalur, sehingga halaman hasil bisa berisi belasan kartu dengan matan yang sama. Riwayat serupa kini dilipat di bawah riwayat pertamanya, menurut urutan peringkat, sebagai tautan "Riwayat serupa". Tidak ada yang dihapus.

- **Kelompok dihitung sekali di pipeline** (`pipeline/serupa.py`, dipanggil `export_d1.py`, disimpan di kolom `riwayat.grup`). Kata akar matan Arab diambil tanpa sanad dan tanpa komentar penyusun. Dua riwayat sekelompok bila Jaccard ≥ 0,8 (minimal 4 kata). Pasangan dicari secara tepat dengan *prefix filtering*, sekitar 12 detik untuk 67 ribu riwayat. Hasilnya 22.072 riwayat dalam 7.297 kelompok, kelompok terbesar 33 riwayat (mis. "shalat di masjidku lebih utama dari seribu shalat"). Dari 588 anggota sampel, hanya 2 yang bergeser jauh (Jaccard < 0,5) dari anggota pertamanya.
- **Tautan takhrij "sama" tidak dipakai.** Digabung berantai, tautan itu menyatukan hadits yang berbeda: satu kelompok berisi 473 riwayat, dari doa qunut, asmaul husna, sampai talbiyah.
- **Saat pencarian**, hanya kolom `grup` dari 200 kandidat teratas (10 halaman) yang dibaca. Tidak ada pemrosesan teks, karena versi sebelumnya (menghitung kemiripan saat pencarian, per halaman) makan 2–5 ms CPU untuk 100 kandidat, padahal batas paket gratis 10 ms. Setiap halaman tetap berisi 20 kartu berbeda. Bila kolom `grup` belum ada di database, hasil tampil tanpa dilipat.
- **Contoh halaman pertama:** "niat" melipat 15 jalur, "kuda" 17, "larangan minum berdiri" 13.

Kode: `lipat()` di `site/src/cari.js`.

**Di halaman hadits:** anggota kelompok yang sama ditampilkan di "Diriwayatkan juga oleh" (kotak utuh, keterangan "lafaz matan hampir sama, ≥80% kata Arabnya sama"), dan penilaian ulamanya ikut di "Penilaian ulama atas jalur lain yang matannya sama atau hampir sama". Hasilnya, 4.363 riwayat yang tidak punya data takhrij kini punya daftar riwayat serupa (mis. Bukhari 329 dan 478, hadits yang diulang di bab lain). Kueri memakai indeks `ix_riwayat_grup` (parsial, hanya baris bergrup). Di database tanpa kolom `grup`, halaman tetap tampil seperti dulu. Uji: `site/test/kelompok.test.js`, `pipeline/test_export.py`.

**Nama di sanad tidak lagi ikut dicari sebagai kata biasa (7 Nov 2026):** terjemah Lidwa menulis perawi dalam kurung siku ("dari [Hisyam] dari [ayahnya] dari ['Aisyah]"). Dulu seluruh terjemah diindeks, sehingga "ayah" cocok dengan 6.767 riwayat, kebanyakan karena "dari [ayahnya]" di sanad. Kini:

- kolom `terjemah_polos` di D1 diisi terjemah **tanpa** isi kurung siku;
- kolom `perawi` hanya memuat kata nama (huruf kapital, al-/az-/…, bin/binti). Kata kerabat seperti "bapaknya" (2.664), "ayahnya" (2.662), dan "seorang laki-laki" (234) tidak dimasukkan;
- kata kunci dicari di kedua kolom (`{terjemah_polos perawi}`), jadi kueri nama tetap jalan.

| Kueri | Sebelum | Sesudah |
|---|---:|---:|
| ayah | 6.767 | 3.727 |
| bapak | 7.800 | 4.455 |
| kakek | 1.362 | 672 |
| paman | 1.179 | 875 |
| abu hurairah puasa | 648 | 648 |
| aisyah | 6.844 | 6.844 |

Kode: `tanpa_kurung()` dan `nama_saja()` di `pipeline/export_d1.py` (uji: `pipeline/test_export.py`). Perubahan ini ada di database, jadi butuh ekspor dan impor ulang D1. Pencarian Python (`pipeline/cari.py`) memakai indeks `build/teman-hadits.sqlite` yang lama dan tidak ikut berubah; situs memakai `site/src/cari.js`.

**Halaman "Cara mencari" (`/cara-cari`):** penjelasan untuk pengguna awam tentang hal-hal berikut. Daftar istilahnya dibuat langsung dari `kamus_konsep.json` (`daftarKonsep()` di `site/src/cari.js`), jadi selalu sesuai dengan kamus yang dipakai. Halaman ini ditautkan dari halaman hasil pencarian, halaman Metode, dan kaki halaman.

- cara membaca "Kami membaca"
- istilah awam yang dipetakan ke lafaz hadits, beserta alasan istilah modern tidak dipetakan
- alasan dan urutan hasil, serta riwayat serupa
- tingkat data dibandingkan derajat hadits
- tips bila hadits belum ketemu
- daftar semua istilah yang dikenali

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
