# Katalog Hadits Populer & Palsu

Tujuannya agar orang yang mengecek kalimat seperti *"Tuntutlah ilmu walau sampai ke negeri Cina"* tidak hanya mendapat jawaban "tidak ditemukan di 11 kitab hadits", tetapi juga melihat **apa kata para ulama hadits** tentang kalimat itu, dikutip dari kitab mereka sendiri.

**Prinsip: Teman Hadits tidak membuat vonis.** Yang tampil adalah teks ulama apa adanya, ditambah kata kunci penilaian yang muncul di teks itu (mis. باطل = batil), *selalu* bersama kalimat aslinya.

Skrip: `pipeline/katalog_palsu.py` → `build/katalog.sqlite`. Uji: `pipeline/test_katalog.py` (18 uji) dan 3 uji HTTP di `site/test/http.test.js`.

## Sumber

Empat kitab klasik yang khusus membahas "hadits" yang beredar di masyarakat dan hadits palsu. Teksnya dari OpenITI; commit dan sha256 terkunci di `pipeline/sources.json` dan `sources.lock.json`.

| Kitab | Penulis | Isi | Edisi digital (dari metadata OpenITI) | Entri |
|---|---|---|---|---:|
| *al-Maudhu'at* | Ibnul Jauzi (w. 597 H) | Hadits-hadits yang ia nilai palsu, per bab, lengkap dengan sanad dan alasannya | tahqiq 'Abdurrahman Muhammad 'Utsman, al-Maktabah as-Salafiyyah, Madinah | 707 bab |
| *al-Maqashid al-Hasanah* | as-Sakhawi (w. 902 H) | "Hadits" yang masyhur di lisan orang, dengan takhrij dan penilaiannya | tahqiq Muhammad 'Utsman al-Khusyt, Dar al-Kitab al-'Arabi | 1.358 |
| *al-Asrar al-Marfu'ah* | Mulla 'Ali al-Qari (w. 1014 H) | Hadits-hadits palsu | tahqiq Muhammad ash-Shabbagh, Dar al-Amanah / ar-Risalah | 737 |
| *Kasyf al-Khafa'* | al-'Ajluni (w. 1162 H) | Perluasan *al-Maqashid*; sering mengutip ulama lain | Maktabah al-Qudsi, Kairo | 3.242 |

Nomor entri adalah nomor yang tertulis di teks digital itu (`### | 125 -`), yang mengikuti edisi cetaknya. Nomor ini **belum** dicocokkan dengan scan kitab cetak. Untuk *al-Maudhu'at*, nomor adalah urutan bab di teks digital, bukan nomor cetak.

Entri yang sangat panjang (sebagian bab *al-Maudhu'at*) dipotong pada 12.000 karakter saat diekspor ke situs, dengan tanda "[teks dipotong; lihat kitab aslinya]". Batas ini datang dari ukuran pernyataan D1.

**Sumber yang tidak dipakai:** Dorar.net menolak akses otomatis (403), dan kami tidak menembus proteksinya. *Silsilah al-Ahadits adh-Dha'ifah* (al-Albani) adalah karya modern yang masih dilindungi hak cipta. *Tadzkirah al-Maudhu'at* (al-Fattani) sudah diunduh tetapi belum diurai.

## Kata kunci penilaian

Kata kunci dicari pada teks yang sudah dinormalisasi (harakat, hamzah, ta marbuthah). Kata boleh diawali huruf sambung و/ف ("ومعناه صحيح", "فهو باطل"), tetapi tidak boleh menempel pada huruf lain ("الموضوعات" ≠ "موضوع").

| Kelas (warna) | Kata kunci → padanan |
|---|---|
| **palsu** (merah) | موضوع maudhu' · مكذوب · كذب dusta · باطل batil · لا أصل له / ليس له أصل tidak ada asalnya · ليس بحديث bukan hadits |
| **lemah** (kuning) | لم أقف عليه "tidak saya temukan" · لا أعرفه "tidak saya kenal" · منكر الحديث (kritik perawi) · منكر · ضعيف جدا · ضعيف · لا يصح · لا يثبت / ليس بثابت |
| **lain** (netral) | من كلام … disebut perkataan orang, bukan sabda Nabi · معناه صحيح / صحيح المعنى maknanya benar (*bukan* penilaian sanad) |
| **terima** (hijau) | حسن hasan · صحيح shahih (hanya dalam susunan penilaian, lihat di bawah) |

"لم أقف عليه" dan "لا أعرفه" diterjemahkan apa adanya sebagai orang pertama, karena yang berbicara bisa penulis kitab **atau** ulama yang ia kutip. Contohnya, *Kasyf* no. 1102 mengutip as-Sakhawi.

### Kesalahan yang ditemukan dan diperbaiki

Saat memeriksa hasil untuk *حب الوطن من الإيمان* ("cinta tanah air sebagian dari iman"), versi pertama menampilkan chip **shahih** dan **hasan**. Ini sangat menyesatkan untuk ucapan yang oleh ash-Shaghani dinilai *maudhu'*. Penyebabnya:

| Teks | Dulu | Sekarang | Aturan |
|---|---|---|---|
| لم أقف عليه، **و**معناه صحيح | shahih | "tidak saya temukan", maknanya benar | huruf sambung و dikenali; صحيح setelah معناه bukan penilaian |
| ألا ترى إلى حديث **حسن العهد** من الإيمان | hasan | — | حسن/صحيح yang diikuti kata ber-ال (حسن العهد, صحيح البخاري) adalah bagian matan/judul |
| رواه في **صحيح مسلم** | shahih | — | judul kitab bukan penilaian |
| **ليس** في فضل الأضحية حديث صحيح | shahih | — | ada ليس/لا/لم dalam 5 kata sebelumnya → negasi |
| و**كذب من قال** إنه اسم امرأة | dusta | — | bantahan atas pendapat, bukan vonis hadits |
| إن مما أدرك الناس **من كلام النبوة** الأولى | perkataan orang | — | من كلام النبي/النبوة justru sebaliknya |
| قال البخاري **منكر الحديث** | munkar | munkar al-hadits (kritik perawi) | dibedakan dari "munkar" untuk matan |

"Shahih" dan "hasan" kini hanya dihitung dalam susunan penilaian: didahului حديث / إسناده / سنده / بسند / بإسناد / هو / هذا, atau diikuti صحيح / حسن / غريب / لغيره / الإسناد / على (شرط). Arah kesalahan yang dipilih: lebih baik chip positif **terlewat** (teks lengkap tetap bisa dibaca) daripada chip positif yang salah.

**Pemeriksaan sampel** (dibaca satu per satu, bukan oleh ahli hadits): setelah perbaikan, 30 dari 30 chip shahih/hasan acak adalah susunan penilaian sungguhan. 42 chip negatif acak (maudhu', bukan hadits, dusta, tidak sahih, munkar, perkataan orang, tidak ada asalnya) diperiksa; tiga pola salah yang ditemukan (bantahan pendapat, "كلام النبوة", munkar al-hadits) sudah diperbaiki dan diuji. Sisa keterbatasan yang disengaja: kata seperti shahih/hasan dalam satu entri sering merujuk **riwayat lain** yang dibahas di entri itu. Hal ini dijelaskan di situs, dan kalimat aslinya selalu tampil.

## Ucapan populer berbahasa Indonesia

`pipeline/hadits_populer.json` berisi 20 ucapan yang sering beredar sebagai "hadits", masing-masing dengan varian kalimat dan lafaz Arabnya. Daftar ini **disusun Teman Hadits dan belum ditinjau** (`"ditinjau": false`). Fungsinya hanya menghubungkan kalimat Indonesia ke lafaz Arab; penilaian yang tampil selalu kutipan dari kitab. Empat di antaranya sengaja berupa hadits yang memang ada (kontrol), agar sistem diuji tidak asal menandai "bermasalah".

Tautan dihitung otomatis:

1. **Ke entri katalog (judul):** judul entri ditambah 10 kata pertamanya memuat ≥ 75% 2-gram lafaz, **atau** lafaz ada persis di teks entri dan judulnya memuat ≥ 50% 2-gram. Aturan kedua menangkap judul bab *al-Maudhu'at* yang berupa parafrase (باب طلب العلم ولو بالصين).
2. **"Disebut dalam pembahasan entri lain":** lafaz ada persis di teks entri lain, tetapi bukan judulnya. Tautan ini ditampilkan terpisah **tanpa** kata kunci, karena penilaian entri itu tentang ucapan lain. Contoh: *نوم الصائم عبادة* hanya disebut di *al-Asrar* no. 567 yang berjudul *نوم العالم عبادة*. "لا أصل له" di sana berlaku untuk *نوم العالم*, sedangkan untuk *نوم الصائم* al-Qari menulis "رواه البيهقي بسند ضعيف".
3. **Ke riwayat di 11 kitab hadits kita:** ≥ 80% 2-gram lafaz ada di teks Arab riwayat (tingkat A/B).

Hasil (kata kunci yang tercantum hanya kelas *palsu* dari entri judul; detail lengkap ada di `/populer/<id>`):

| Ucapan | Lafaz | Entri katalog | Kata kunci palsu | Di kitab hadits kita | Disebut di |
|---|---|---|---|---|---|
| Tuntutlah ilmu walau sampai ke negeri Cina | اطلبوا العلم ولو بالصين | Maqashid 125, Kasyf 397, Maudhu'at 71 | batil, tidak ada asalnya | — | Maqashid 660 |
| Cinta tanah air sebagian dari iman | حب الوطن من الإيمان | Maqashid 386, Kasyf 1102, Asrar 164 | maudhu' | — | — |
| Kebersihan sebagian dari iman | النظافة من الإيمان | — | — | — | — |
| Perbedaan pendapat umatku adalah rahmat | اختلاف أمتي رحمة | Maqashid 39, Kasyf 153, Asrar 17 | tidak ada asalnya | — | Maqashid 1325, Kasyf 3125, Asrar 604 |
| Tidurnya orang berpuasa adalah ibadah | نوم الصائم عبادة | — | — | — | Asrar 567 |
| Tuntutlah ilmu dari buaian hingga liang lahat | اطلبوا العلم من المهد إلى اللحد | — | — | — | — |
| Surga di bawah telapak kaki ibu | الجنة تحت أقدام الأمهات | Maqashid 373, Kasyf 1078 | — | — | — |
| Barangsiapa mengenal dirinya … | من عرف نفسه فقد عرف ربه | Maqashid 1149, Kasyf 2532, Asrar 506 | maudhu' | — | — |
| Kembali dari jihad kecil ke jihad besar | رجعنا من الجهاد الأصغر إلى الجهاد الأكبر | Kasyf 1362, Asrar 211 | — | — | — |
| Bekerjalah untuk duniamu seakan hidup selamanya … | اعمل لدنياك كأنك تعيش أبدا | — | — | — | — |
| Berpuasalah, niscaya kalian sehat | صوموا تصحوا | Maqashid 549, 637; Kasyf 1455, 1631 | — | — | — |
| Awal Ramadhan rahmat, pertengahannya ampunan … | أوله رحمة وأوسطه مغفرة وآخره عتق من النار | — | — | — | — |
| Aku kota ilmu dan Ali pintunya | أنا مدينة العلم وعلي بابها | Maqashid 189, Kasyf 618, Asrar 71 | maudhu', dusta, batil, tidak ada asalnya | — | Maudhu'at 153 |
| Sebaik-baik perkara adalah yang pertengahan | خير الأمور أوسطها | Kasyf 1247 | — | — | Kasyf 2209 |
| Berbicaralah sesuai kadar akal mereka | خاطبوا الناس على قدر عقولهم | Maqashid 180, Kasyf 592 | — | — | — |
| Kefakiran hampir menjadi kekufuran | كاد الفقر أن يكون كفرا | Maqashid 789, Kasyf 1919 | — | — | — |
| *Kontrol:* Ulama adalah pewaris para nabi | العلماء ورثة الأنبياء | Maqashid 703, Kasyf 1745, Asrar 299 | — | Tirmidzi 2682, Abu Dawud 3641 | 4 entri |
| *Kontrol:* Senyummu kepada saudaramu sedekah | تبسمك في وجه أخيك لك صدقة | Kasyf 945 | — | Tirmidzi 1956 | — |
| *Kontrol:* Bersuci separuh dari iman | الطهور شطر الإيمان | Kasyf 1669 | — | Muslim 534, Darimi, Ahmad (2) | — |
| *Kontrol:* Sayangilah yang di bumi … | ارحموا من في الأرض يرحمكم من في السماء | Maqashid 88, Kasyf 314 | — | Tirmidzi 1924 | — |

Keempat kontrol tidak mendapat chip *palsu* dan ditemukan di kitab hadits kita dengan lafaz yang sama.

"Kebersihan sebagian dari iman" tidak ditemukan di mana pun dengan lafaz *النظافة من الإيمان*. Kitab-kitab katalog membahas lafaz berbeda, *بني الدين على النظافة* (Maqashid 302, Kasyf 922, Asrar 127). Ini contoh keterbatasan: pencocokan memakai lafaz, bukan makna, jadi lafaz Arab dalam daftar populer perlu ditinjau ahli.

"Tidak ditemukan di 11 kitab hadits kami" **tidak** sama dengan "palsu". Situs mengatakannya secara eksplisit.

## Di situs

- `/populer`: daftar ucapan, status "ada/tidak ada di kitab hadits kami", kitab katalog yang membahasnya, dan ringkasan kata kunci (yang paling tegas dulu).
- `/populer/<id>`: semua entri ulama dengan kata kunci dan kalimatnya, teks lengkap, dan bagian "Disebut dalam pembahasan entri lain".
- `/cek`: teks Indonesia dicocokkan ke daftar populer (≥ 60% kata khas); teks Arab dicocokkan langsung ke judul entri katalog (≥ 75% 2-gram). Hasilnya tampil sebagai kotak "Dibahas ulama" di bawah hasil cek.

## Menambah ucapan populer

1. Tambahkan objek ke `pipeline/hadits_populer.json` (`id`, `teks`, `varian`, `arab`).
2. Jalankan `python3 -I pipeline/katalog_palsu.py`, `python3 -m unittest pipeline/test_katalog.py`, `python3 pipeline/export_d1.py`, lalu `npm run impor` di `site/`.
3. Periksa `/populer/<id>`. Bila tidak ada entri yang tertaut, coba lafaz yang lebih dikenal di kitab-kitab itu (lihat bagian "disebut").

## Yang belum

- Daftar ucapan populer dan lafaz Arabnya perlu ditinjau ahli hadits.
- Lisensi OpenITI: CC BY-NC-SA 4.0 (lihat `docs/02-sumber-dan-lisensi.md`).
- Nomor entri belum dicocokkan dengan scan kitab cetak.
- Kata kunci belum menangkap penilaian berbentuk kata kerja (صححه, حسنه, ضعفه) dan penyebutan *al-Maudhu'at* ("ذكره ابن الجوزي في الموضوعات").
