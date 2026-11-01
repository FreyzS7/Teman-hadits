# Model Data

## Satuan dasar: riwayat, bukan "hadits"

Satu hadits (satu isi/matan) biasanya diriwayatkan lewat banyak jalur, di banyak kitab, dengan nomor berbeda. Karena itu satuan terkecil di database adalah **riwayat**: satu teks, di satu kitab, dengan satu nomor. Riwayat-riwayat yang semakna dikumpulkan menjadi satu "keluarga" (takhrij) lewat kemiripan matan Arab.

## Tabel

| Tabel | Isi | Catatan |
|---|---|---|
| `kitab` | id, nama, nama Arab, penyusun, tahun wafat, jumlah baris per sumber | |
| `riwayat` | id (`bukhari:1`, `darimi:L12`), nomor standar, nomor Arab (mis. Fu'ad 'Abdul Baqi untuk Muslim), nomor Lidwa, bab, teks Arab, teks Arab sumber kedua, terjemah, rantai perawi, skor kecocokan, **tingkat**, alasan | `L` di id = penomoran Lidwa, dipakai bila belum ada penomoran standar |
| `penilaian` | riwayat, **nama penilai**, hukum asli (apa adanya), kategori kasar, sumber | Kategori (shahih/hasan/lemah/palsu/lainnya) hanya untuk filter. Yang tampil selalu hukum asli |
| `cari` (FTS5) | teks Arab polos, teks Arab tanpa awalan (و، ال، ب، …), terjemah polos, nama perawi | Hanya berisi riwayat tingkat A/B |

## Tingkat data

| Tingkat | Syarat | Tampil? |
|---|---|---|
| **A** | Teks Arab sumber standar cocok dengan teks Arab Lidwa (Jaccard 3-kata ≥ 0,85, atau ≥ 90% tercakup dalam baris Lidwa gabungan), posisinya konsisten dengan urutan kitab, dan terjemah diambil dari baris Lidwa yang sama | Ya |
| **B** | Hanya ada di satu sumber digital, atau pasangan terjemahnya belum pasti | Ya, dengan label |
| **K** | Teks Arab kosong/terlalu pendek, atau berkas tersimpan per bab/halaman | Tidak |

Tingkat menilai **data digital**, bukan derajat hadits. Hadits dha'if bisa bertingkat A (datanya rapi), dan hadits shahih bisa bertingkat B (datanya baru dari satu sumber).

## Penomoran

- Alamat utama memakai **nomor standar** dari fawazahmed0, karena nomor inilah yang dikutip dalam buku dan ceramah (mis. Bukhari no. 1–7563 penomoran Fath al-Bari).
- **Muslim** ditampilkan dengan penomoran Fu'ad 'Abdul Baqi (`1907a`, `1907b`, …), karena itu yang lazim dikutip.
- **Nomor Lidwa** selalu ditampilkan sebagai pembanding, karena banyak pengguna Indonesia mengenalnya dari aplikasi Lidwa/carihadis.

## Rantai sanad (tahap 1)

`rantai_json` berisi nama perawi yang diekstrak otomatis dari `[kurung siku]` di terjemah Lidwa, berurutan dari guru penyusun sampai sahabat. Di halaman hadits, rantai juga dibaca dari teks Arab: setiap lafaz periwayatan (حدثنا، أخبرني، سمعت، عن) memisahkan dua perawi. Tahap berikutnya adalah menautkan tiap nama ke data rijal (Taqrib at-Tahdzib) agar biodata dan penilaian perawi bisa ditampilkan. Bagian itu sengaja dikosongkan sampai datanya terverifikasi.
