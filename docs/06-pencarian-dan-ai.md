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

Contoh kedua adalah batas aturan: kata kuncinya cocok, tetapi maknanya tidak. Ada dua jalan memperbaikinya, dan keduanya masuk rencana:

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
