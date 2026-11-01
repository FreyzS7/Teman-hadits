# Teman Hadits

Pustaka hadits berbahasa Indonesia. Pengguna bisa mencari dengan kata kunci atau tema, atau menempel teks hadits yang beredar untuk mengecek apakah teks itu ada, di kitab mana, nomor berapa, bagaimana sanadnya, dan bagaimana para ulama menilainya.

**Prinsip utama: kebenaran yang bisa dibuktikan.**

- Setiap teks punya rantai sumber sampai ke berkas dan commit tertentu.
- Derajat hadits selalu ditampilkan atas nama ulama penilainya. Situs tidak membuat "nilai akhir" sendiri.
- Data yang rusak atau tidak pasti masuk karantina dan tidak ditampilkan.
- Bila sesuatu tidak ditemukan, situs mengatakan tidak ditemukan dan menyebut cakupan pencariannya.
- Tidak ada terjemahan atau penilaian yang dibuat oleh AI.

## Isi repo

| Path | Isi |
|---|---|
| `pipeline/` | Skrip Python (tanpa library tambahan): unduh sumber, bangun database, pencocokan dua sumber, audit, uji emas, pencarian (`cari.py` + `kamus_konsep.json`) |
| `docs/01-audit-data.md` | Laporan audit, dibuat otomatis dari hasil build |
| `docs/02-sumber-dan-lisensi.md` | Sumber data, status lisensi, kandidat sumber berikutnya |
| `docs/03-model-data.md` | Skema database dan alasannya |
| `docs/04-protokol-verifikasi.md` | Cara membuktikan data benar tanpa bergantung pada pembuat situs |
| `docs/05-rencana-dan-hosting.md` | Tahapan kerja, arsitektur, hosting, anggaran |
| `docs/06-pencarian-dan-ai.md` | Pencarian pintar tanpa AI, dan peran AI yang dibatasi |
| `design/` | Prototipe desain (`prototipe.html`), diisi data asli dari database |

## Menjalankan

```bash
python3 pipeline/fetch_sources.py
```

```bash
python3 pipeline/build_db.py
```

```bash
python3 -m unittest pipeline/test_golden.py -v
```

```bash
python3 pipeline/audit.py
```

```bash
python3 design/build_prototype.py
```

Coba pencarian dari terminal:

```bash
python3 pipeline/cari.py "tolong carikan hadits tentang sholat tarawih"
```

Hasil build ada di `build/teman-hadits.sqlite` (±430 MB, tidak di-commit). Langkah fetch, build, dan uji di atas makan waktu sekitar satu menit.

## Status saat ini

- 10 kitab dimuat, 67.512 riwayat terbit (32.578 tingkat A, 34.934 tingkat B), 408 dikarantina. Riyadhus Shalihin dikarantina sampai disegmentasi ulang.
- 21.185 riwayat sudah punya penilaian derajat bernama: al-Albani, Syu'aib al-Arna'uth, Zubair 'Ali Za'i, Ahmad Syakir, Basyar 'Awwad, Abu Ghuddah, Salim al-Hilali, dan lainnya.
- 14 uji emas lulus. Contohnya: hadits niat ditemukan di ketujuh tempatnya dalam Shahih al-Bukhari, dan tidak ada di al-Muwaththa' riwayat Yahya.

Angka terbaru selalu ada di [docs/01-audit-data.md](docs/01-audit-data.md).
