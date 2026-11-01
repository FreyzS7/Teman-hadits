# Judul Kitab dan Bab

Kode: `pipeline/bab_openiti.py`. Glosarium: `pipeline/glosarium_kitab.json`. Tes: `pipeline/test_bab.py`.

## Masalah

Sumber penomoran kita (fawazahmed0) hanya memuat nama **kitab** dalam bahasa Inggris ("Revelation", "Prayer"). Sumber itu tidak memuat judul **bab** sama sekali. Padahal judul bab sangat penting: judul bab al-Bukhari (*tarajim*) dikenal memuat fiqih beliau.

## Sumber

Teks kitab-kitab hadits di korpus **OpenITI**, yang memuat judul kitab dan bab dari edisi cetaknya (lihat `docs/02-sumber-dan-lisensi.md`). Situs hanya memakai judulnya, bukan teks haditsnya.

## Cara

1. Setiap baris judul di berkas OpenITI diklasifikasi menjadi kitab, bab, penanda nomor hadits, atau penanda halaman cetak. Penanda halaman ("[ص: 30]") bisa muncul di tengah hadits, jadi ia tidak dianggap batas.
2. **Pencocokan menurut isi:** teks Arab setiap riwayat kita dicocokkan ke blok OpenITI yang paling memuatnya (≥ 70% bobot 2-gram). Bila beberapa blok sama cocoknya (al-Bukhari sering mengulang hadits yang persis sama di kitab lain), dipilih blok yang posisinya sesuai dengan urutan riwayat tetangga.
3. Nama Arab tiap bagian kitab fawazahmed0 diambil dari judul kitab OpenITI yang dimiliki mayoritas riwayat di bagian itu, dengan syarat mayoritasnya ≥ 60%. Bagian "0" Bukhari dan Muslim di fawazahmed0 ternyata tampungan riwayat tanpa nomor kitab dari seluruh kitab, jadi tidak diberi nama paksa.
4. **Nama Indonesia:** hanya untuk nama kitab, dari glosarium 215 istilah yang **disusun Teman Hadits dan belum ditinjau ahli** (`"ditinjau": false`). Judul bab tidak diterjemahkan.

## Validasi

Nomor hadits **tidak dipakai** saat mencocokkan. Karena itu kesamaan nomor dengan nomor edisi cetak di OpenITI adalah uji independen.

| Kitab | Terpetakan menurut isi | Urutan naik | Nomor sama dengan edisi cetak | Kitab sepakat |
|---|---|---|---|---|
| Bukhari | 7.375/7.580 | 99,8% | 96,4% | 97,3% |
| Muslim | 7.276/7.360 | 99,8% | (OpenITI tanpa nomor) | 98,4% |
| Abu Dawud | 5.264/5.272 | 99,98% | 99,8% | 100% |
| Ibnu Majah | 4.334/4.338 | 99,95% | 99,8% | 99,8% |
| Tirmidzi | 3.695/3.924 | 99,8% | 99,6% | 99,4% |
| Nasa'i | 5.672/5.679 | 99,9% | 99,7% | 99,9% |
| al-Muwaththa' | 1.827/1.829 | 100% | (tanpa nomor) | 100% |

Selisih nomor Bukhari yang tersisa kebanyakan +1. Penyebabnya, dua nomor di edisi Dar Thauq an-Najah berada dalam satu blok, sehingga bab dan kitabnya tetap benar.

## Yang belum

- Peninjauan glosarium nama kitab Indonesia oleh orang yang paham istilah hadits/fiqih.
- Judul bab untuk Musnad Ahmad, Sunan ad-Darimi, dan Musnad asy-Syafi'i. Berkasnya ada di OpenITI, tetapi penomorannya perlu dicocokkan dulu.
- Terjemah judul bab, yang perlu penerjemah ahli.
