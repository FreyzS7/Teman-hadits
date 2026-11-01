# Riyadhus Shalihin

Kode: `pipeline/riyadh.py`. Tes: `pipeline/test_riyadh.py`. Hasil: `build/riyadh.sqlite`, lalu diekspor ke situs sebagai kitab `riyadh`.

## Masalah pada data sumber

Berkas `riyadhus-shalihin.sql` (dari repo irsyadulibad/hadits-database) menyimpan **satu baris per bab** (372 baris). Setiap baris berisi teks Arab bab itu dan terjemah Indonesianya dalam HTML. Ada beberapa masalah:

1. **Penomoran terjemah berbeda dari teks Arab.** Terjemah memakai penomoran edisinya sendiri, dengan selisih 0–4 yang berubah-ubah sepanjang kitab. Contohnya, teks Arab 727 (Umar bin Abi Salamah, "سمّ الله") adalah terjemah no. 725, sedangkan terjemah no. 727 adalah hadits Jabir. Memasangkan menurut nomor akan menempelkan terjemah ke hadits yang salah.
2. **Nomor ayat Al-Qur'an** di pengantar bab ("117. Sesungguhnya Allah…") terbaca seperti nomor hadits.
3. Sebagian hadits dipisah dengan tag `<br>`, bukan baris baru. Akibatnya hadits no. 1 menempel ke ayat pengantar bab.
4. Ada **catatan kaki edisi cetak** di bawah garis `__________`, berupa syarah Ibnu 'Utsaimin dan takhrij muhaqqiq ("(2) أخرجه: البخاري 2/ 99 (1281)"). Itu bukan teks an-Nawawi.
5. Ada daftar bernomor di dalam catatan ("1 - لباس الزينة") dan judul kitab yang ditulis tanpa kurung ("19 - كتاب الاستغفار").

## Cara pengolahan

- **Pemecahan Arab:** HTML dibersihkan dulu. Judul kitab dan bab dikenali, dan daftar bernomor yang melanggar urutan dikembalikan ke catatan. Hasilnya **1.896 hadits, nomor 1–1896 tanpa celah**.
- **Teks hadits vs catatan:** semua yang di atas garis catatan kaki adalah teks Riyadhus Shalihin. Itu mencakup riwayat tambahan "وفي رواية…" dan penjelasan kata "قوله…" dari an-Nawawi. Yang di bawah garis disimpan sebagai *catatan kaki edisi*.
- **Pemasangan terjemah menurut isi:** dipakai penjajaran urutan (Needleman–Wunsch berpita) atas seluruh kitab dengan tiga petunjuk:
  - kerangka konsonan kata-kata khas **nama sahabat** ("عايشه" ~ "Aisyah"; "وعنه" = sahabat hadits sebelumnya);
  - **atribusi an-Nawawi** ("متفق عليه" ~ "(Muttafaq 'alaih)");
  - **rasio panjang** teks.

  Terjemah hanya dipasang bila nama sahabat cocok **dan** atribusi tidak bertentangan.
- **Sumber (takhrij):** matan «…» dicocokkan ke riwayat di kitab-kitab kita dengan 2-gram berbobot IDF. Urutan sumber: kitab yang disebut an-Nawawi lebih dulu, lalu sahabat yang sama, baru skor kemiripan.

## Hasil dan pemeriksaan

Angka terbaru ada di `docs/01-audit-data.md`. Pada build 1 Nov 2026:

| Ukuran | Hasil |
|---|---|
| Hadits | 1.896 (1–1896, tanpa celah) |
| Terjemah terpasang "pasti" | 1.726 (91%) |
| Terhubung ke sumber di kitab kita | 1.645 (87%) |
| Sumber teratas = kitab yang disebut an-Nawawi **dan** sahabat yang sama | 1.512 |
| **Uji silang atribusi an-Nawawi** (an-Nawawi menyebut kitab X ⇒ kita menemukannya di X) | 1.613/1.642 = **98,2%** |
| **Validasi independen pasangan terjemah**: terjemah Riyadh lebih mirip dengan terjemah Lidwa dari riwayat sumbernya daripada pasangan yang digeser satu hadits | 1.395/1.429 = **97,6%** |

Pemeriksaan manual 8 sampel acak pasangan "pasti": semuanya benar. Pasangan dengan skor validasi terendah juga diperiksa manual dan ternyata benar. Skornya rendah karena sumber teratasnya diriwayatkan sahabat lain dengan matan yang sama, dan hal itu sekarang ditangani oleh urutan sumber.

## Yang belum

- **Izin terjemah:** terjemah Indonesia Riyadhus Shalihin ini **bukan** dari Lidwa Pusaka, dan penerjemahnya belum dipastikan. Sebelum situs online, pastikan izinnya. Bila belum ada, set `TERJEMAH_RIYADH = "sembunyi"` di `site/wrangler.toml`. Teks Arab, atribusi, dan tautan ke riwayat sumber (yang terjemah Lidwa-nya berizin) tetap tampil.
- **Ejaan nama:** contohnya terjemah no. 725 menulis "'Amr bin Abu Salamah", padahal teks Arabnya عمر (Umar). Kesalahan seperti ini perlu peninjau manusia.
- Berkas versi Arab tahqiq al-Fahl (850 potongan halaman, dengan takhrij muhaqqiq) belum dipakai. Berkas itu bisa menjadi sumber penilaian derajat per hadits Riyadh.
