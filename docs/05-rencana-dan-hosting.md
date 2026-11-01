# Rencana Kerja dan Hosting

## Tahapan

| Fase | Isi | Status |
|---|---|---|
| 0 | Audit data, sumber terkunci, laporan otomatis | **Selesai** |
| 1 | Model data, pencocokan dua sumber, tingkat data, uji emas | **Selesai** (tahap awal) |
| 1b | Desain prototipe dengan data asli | **Selesai**: `design/prototipe.html` |
| 2 | Riyadhus Shalihin disegmentasi per hadits; teks Darimi, Ahmad, dan Syafi'i dicocokkan dengan OpenITI agar naik ke tingkat A; nama bab Arab/Indonesia | **Selesai** (lihat docs/08, docs/09) |
| 3 | Rantai sanad tertaut ke data rijal (Taqrib at-Tahdzib): nama, tahun wafat, penilaian perawi | **Selesai untuk enam kitab** (lihat docs/11): 58% sebutan nama pasti, 4.315 halaman perawi, 99,85% sama dengan Ifta' Sunnah. Malik/Ahmad/Darimi/Syafi'i belum |
| 4 | Katalog hadits palsu populer dengan penilaian ulama bernama | **Selesai, tahap awal** (lihat docs/10): 4 kitab klasik (6.044 entri) dari OpenITI, 20 ucapan populer, `/populer`, terintegrasi di `/cek`. Dorar tetap tidak dipakai (menolak bot). Daftar ucapan belum ditinjau ahli |
| 5 | Situs sungguhan: halaman per riwayat, pencarian, cek teks, SEO | **Berjalan lokal** (`site/`): beranda, cari, cek, halaman riwayat + rantai sanad + takhrij, kitab/bab, tema, metode, sitemap |
| 6 | Verifikasi sampel kitab cetak + peninjau independen, lalu rilis publik | |

## Lokal dulu, Cloudflare kemudian

Seluruh pengembangan berjalan di komputer sendiri. Cloudflare menyediakan alat `wrangler dev` yang menjalankan Worker **dan** database D1 (berkas SQLite lokal) di laptop tanpa akun dan tanpa internet. Kode yang jalan lokal adalah kode yang sama persis yang nanti di-deploy, jadi tidak ada "pindah platform". Saat siap online, cukup `wrangler d1 import` dan `wrangler deploy`.

Kebutuhan di komputer: Node.js ≥ 20 dan Python 3 (untuk pipeline data).

## Arsitektur yang disarankan

- **Situs:** satu Cloudflare Worker yang merender semua halaman di server (tanpa kerangka tambahan seperti Astro), jadi hanya ada satu runtime, satu cara deploy, dan semua halaman tetap berupa HTML utuh untuk SEO.
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
