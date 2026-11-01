# Rencana Kerja dan Hosting

## Tahapan

| Fase | Isi | Status |
|---|---|---|
| 0 | Audit data, sumber terkunci, laporan otomatis | **Selesai** |
| 1 | Model data, pencocokan dua sumber, tingkat data, uji emas | **Selesai** (tahap awal) |
| 1b | Desain prototipe dengan data asli | **Selesai**: `design/prototipe.html` |
| 2 | Riyadhus Shalihin disegmentasi per hadits; teks Darimi, Ahmad, dan Syafi'i dicocokkan dengan OpenITI agar naik ke tingkat A; nama bab Arab/Indonesia | Berikutnya |
| 3 | Rantai sanad tertaut ke data rijal (Taqrib at-Tahdzib): nama, tahun wafat, penilaian perawi | |
| 4 | Katalog hadits palsu populer dengan penilaian ulama bernama (perlu akses Dorar atau sumber setara) | |
| 5 | Situs sungguhan: halaman per riwayat, pencarian, cek teks, SEO | |
| 6 | Verifikasi sampel kitab cetak + peninjau independen, lalu rilis publik | |

## Arsitektur yang disarankan

- **Situs:** Astro. Halaman beranda, metode, dan rak kitab dibuat statis.
- **Halaman hadits dan pencarian:** Cloudflare Worker + **Cloudflare D1** (SQLite di server). Datanya ±67 ribu riwayat, padahal Cloudflare Pages versi gratis membatasi jumlah berkas per situs (sekitar 20 ribu). Karena itu halaman hadits dirender oleh Worker dari D1, dan tetap ramah SEO karena HTML-nya dikirim utuh dari server.
- **Database produksi:** versi ramping dari `build/teman-hadits.sqlite`, tanpa kolom pembanding `arab_lidwa`, kira-kira < 300 MB. Masih di bawah batas ukuran D1 gratis (sekitar 500 MB per database).
- **Pencarian:** FTS5 di D1. Normalisasi Arab dan pemotongan awalan sudah ada di `pipeline/common.py` dan harus dipakai sama persis saat membuat kueri.
- **Cek teks tempel:** dua tahap. Pertama, kata kunci khas harus ada semua (kalau satu saja tidak ada, jawabannya "tidak ditemukan" beserta kata yang absen). Kedua, hasil diperluas ke satu keluarga riwayat lewat kemiripan matan Arab. Logikanya sudah terbukti di `design/build_prototype.py`.

## Hosting dan anggaran (maks. Rp 500.000)

| Pos | Pilihan | Perkiraan biaya |
|---|---|---|
| Hosting situs + Worker + D1 | Cloudflare paket gratis | Rp 0 |
| Domain | `temanhadits.my.id` (murah) atau `.com` / `.id` | Kisaran puluhan ribu (.my.id) sampai ±Rp 200–400 ribu/tahun (.com/.id) |
| Repo + build | GitHub (gratis) | Rp 0 |

**Mengapa bukan Vercel:** paket Hobby (gratis) Vercel hanya untuk penggunaan pribadi non-komersial dan punya batas bandwidth serta jumlah fungsi. Untuk layanan publik yang bisa ramai, Cloudflare lebih longgar, dan bandwidth situs statis tidak dihitung. Batas paket gratis bisa berubah, jadi cek halaman harga resmi saat akan deploy.
