# Judul Kitab dan Bab

Kode: `pipeline/bab_openiti.py`. Glosarium: `pipeline/glosarium_kitab.json`. Tes: `pipeline/test_bab.py`.

## Masalah

Sumber penomoran kita (fawazahmed0) hanya memuat nama **kitab** dalam bahasa Inggris ("Revelation", "Prayer"). Sumber itu tidak memuat judul **bab** sama sekali. Padahal judul bab sangat penting: judul bab al-Bukhari (*tarajim*) dikenal memuat fiqih beliau.

## Sumber

Teks kitab-kitab hadits di korpus **OpenITI**, yang memuat judul kitab dan bab dari edisi cetaknya (lihat `docs/02-sumber-dan-lisensi.md`). Situs hanya memakai judulnya, bukan teks haditsnya.

## Cara

1. Setiap baris judul di berkas OpenITI diklasifikasi menjadi kitab, bab, penanda nomor hadits, atau penanda halaman cetak. Penanda halaman ("[ص: 30]") bisa muncul di tengah hadits, jadi ia tidak dianggap batas.
2. **Pencocokan menurut isi:** teks Arab setiap riwayat kita dicocokkan ke blok OpenITI yang paling memuatnya (≥ 70% bobot 2-gram). Bila beberapa blok sama cocoknya (al-Bukhari sering mengulang hadits yang persis sama di kitab lain), dipilih blok yang posisinya sesuai dengan urutan riwayat tetangga.
   - **Hadits bernomor ganda** (mis. Bukhari 299–301, 3164–3165): sumber kita memuat teks gabungan di setiap nomornya, sedangkan OpenITI memecahnya per nomor, sehingga skor isi tiap potongan di bawah 70%. Riwayat seperti ini diberi blok OpenITI **bernomor sama**, hanya bila blok bernomor itu tepat satu, letaknya di antara blok tetangga yang sudah cocok, dan ≥ 80% 2-gram blok itu memang ada di teks riwayat. Aturan yang sama juga menolong riwayat lain yang teksnya di sumber kita lebih panjang dari blok OpenITI (mis. Tirmidzi 13, yang memuat komentar at-Tirmidzi). Hasilnya: Bukhari 141, Tirmidzi 31, Abu Dawud 2, Nasa'i 1 riwayat. Halaman hadits menandainya «dicocokkan lewat nomor hadits yang sama».
3. Nama Arab tiap bagian kitab fawazahmed0 diambil dari judul kitab OpenITI yang dimiliki mayoritas riwayat di bagian itu, dengan syarat mayoritasnya ≥ 60%. Bagian "0" Bukhari dan Muslim di fawazahmed0 ternyata tampungan riwayat tanpa nomor kitab dari seluruh kitab, jadi tidak diberi nama paksa.
4. **Nama Indonesia:** hanya untuk nama kitab, dari glosarium 215 istilah yang **disusun Teman Hadits dan belum ditinjau ahli** (`"ditinjau": false`). Judul bab tidak diterjemahkan.

## Validasi

Nomor hadits **tidak dipakai** saat mencocokkan menurut isi (kolom "Nomor sama" hanya menghitung riwayat yang cocok menurut isi; pengecualian hadits bernomor ganda di atas tidak ikut dihitung). Karena itu kesamaan nomor dengan nomor edisi cetak di OpenITI adalah uji independen.

| Kitab | Terpetakan menurut isi | Urutan naik | Nomor sama dengan edisi cetak | Kitab sepakat |
|---|---|---|---|---|
| Bukhari | 7.375/7.580 | 99,8% | 96,4% | 97,3% |
| Muslim | 7.298/7.360 | 99,8% | (OpenITI tanpa nomor) | 98,4% |
| Abu Dawud | 5.264/5.272 | 99,98% | 99,8% | 100% |
| Ibnu Majah | 4.334/4.338 | 99,95% | 99,8% | 99,8% |
| Tirmidzi | 3.872/3.924 | 99,8% | 99,6% | 99,4% |
| Nasa'i | 5.672/5.679 | 99,9% | 99,7% | 99,9% |
| al-Muwaththa' | 1.827/1.829 | 100% | (tanpa nomor) | 100% |

**Baris "###" yang bukan judul bab** (diperbaiki November 2026; sebelumnya 507 riwayat berjudul bab keliru: Tirmidzi 376, Muslim 128, Ibnu Majah 3):

- Muslim: baris sanad pendek («### $ حدثنا قتيبة …», ≤ 12 kata) dulu terbaca sebagai judul bab, sehingga 128 riwayat berjudul «وحدثني محمد بن حاتم…». Kini baris yang diawali حدثنا/أخبرنا/… adalah awal hadits.
- Tirmidzi: penanda riwayat tambahan «(م ٢) - …» dan potongan baris akibat penanda catatan kaki («### || (١) عمرو بن نفيل رضي الله عنه») terbaca sebagai judul bab. Judul bab Tirmidzi selalu diawali «باب»/«ما جاء», selain itu kini menjadi lanjutan teks. Pencocokan Tirmidzi naik dari 3.695 ke 3.872 riwayat.
- Ibnu Majah: «باب حدثنا سويد بن سعيد» (gaya fihris) kini «باب» (bab tanpa judul).
- Ibnu Majah: 121 judul bab ditulis sebagai baris biasa «# باب …» (kadang terpotong ke beberapa baris) dan dulu terlewat, sehingga 346 hadits tampil di bawah bab sebelumnya. Kini dikenali (diverifikasi dengan fihris cetakan al-Halabi, lihat docs/13).
- Muslim: 59 judul bertanda «*» («### || * باب …») adalah tambahan teks digital, tidak ada di cetakan Fu'ad 'Abd al-Baqi (dibuktikan dengan fihris dan halaman isinya, lihat docs/13). Kini diabaikan; haditsnya tetap di bab cetakan.

Selisih nomor Bukhari yang tersisa kebanyakan +1. Penyebabnya, dua nomor di edisi Dar Thauq an-Najah berada dalam satu blok, sehingga bab dan kitabnya tetap benar.

## Musnad Ahmad, Sunan ad-Darimi, Musnad asy-Syafi'i

Ketiga kitab ini di sumber penomoran kita hanya punya **satu** sumber digital (Lidwa), sehingga semula semuanya tingkat B tanpa judul. OpenITI memuat **edisi tahqiq standar** ketiganya:

| Kitab | Edisi OpenITI | Terpetakan | Teks cocok ≥ 90% → **tingkat A** | Urutan naik |
|---|---|---|---|---|
| Musnad Ahmad | ar-Risalah (Syu'aib al-Arna'uth dkk.) | 25.855/26.363 | **23.247** | 99,7% |
| Sunan ad-Darimi | Dar al-Mughni (Husain Salim Asad) | 3.267/3.367 | **2.891** | 99,97% |
| Musnad asy-Syafi'i | Ghiras (Mahir Yasin al-Fahl) | 1.729/1.800 | **1.164** | 68%* |

\* Edisi al-Fahl menyusun ulang Musnad asy-Syafi'i per bab fiqih, jadi urutannya memang berbeda dari versi Lidwa. Untuk Syafi'i hanya kecocokan isi yang dipakai, tanpa pengisian dari tetangga.

Yang didapat:

- **Tingkat A:** teks Arab Lidwa tercakup ≥ 90% di blok edisi tahqiq, dan terjemahnya dari baris Lidwa yang sama.
- **Nomor edisi tahqiq:** nomor inilah yang lazim dikutip di buku. Nomor Lidwa dan nomor edisi bisa jauh berbeda (mis. Darimi Lidwa 2317 = Asad 2468). Situs menampilkan keduanya. Bila pengguna mengetik "darimi 2468", situs **tidak** langsung membuka salah satunya, tetapi menunjukkan bahwa nomor itu ada di dua sistem penomoran.
- **Penilaian Husain Salim Asad** untuk 2.810 riwayat Darimi. Penilaian ini diambil dari blok "[تعليق المحقق]" edisinya, ditampilkan apa adanya dalam bahasa Arab, dan hanya dipasang bila teks riwayat ≥ 90% cocok dengan blok tersebut.
- **Judul:** Darimi dan Syafi'i memakai judul kitab (termasuk *Muqaddimah* Darimi dan gaya "ومن كتاب الزكاة"). Musnad Ahmad memakai judul musnad per sahabat ("مسند عمر بن الخطاب"), dalam bahasa Arab saja.
- Penilaian al-Arna'uth untuk Musnad Ahmad **tidak** tersedia: catatan kakinya tidak ikut terdigitalkan di kedua versi ar-Risalah di OpenITI.

## Yang belum

- Peninjauan glosarium nama kitab Indonesia oleh orang yang paham istilah hadits/fiqih.
- Terjemah judul bab, yang perlu penerjemah ahli.
- Penilaian al-Arna'uth (Ahmad) dan Ahmad Syakir. Perlu sumber yang memuat catatan kaki tahqiqnya.
