# Persiapan Online (Cloudflare)

Isi dokumen ini:
- hasil pengukuran situs terhadap batas paket gratis Cloudflare;
- perbaikan yang dibuat karena pengukuran itu;
- langkah menerbitkan situs dari akun pemilik proyek;
- daftar yang harus beres sebelum situs diumumkan.

Langkah yang memerlukan akun Cloudflare (login, membuat database, membayar, domain) harus dijalankan pemilik proyek. Semua yang bisa disiapkan dan diuji tanpa akun sudah disiapkan dan diuji.

## Batas paket Cloudflare yang relevan

Angka di bawah ini diambil dari dokumentasi resmi lewat hasil pencarian. Halaman developers.cloudflare.com sendiri tidak bisa dibuka dari lingkungan build. **Periksa lagi halaman resminya sebelum memilih paket**: [harga D1](https://developers.cloudflare.com/d1/platform/pricing/), [batas Workers](https://developers.cloudflare.com/workers/platform/limits/), [harga Workers](https://developers.cloudflare.com/workers/platform/pricing/).

| | Workers Free | Workers Paid (US$5/bulan) |
|---|---|---|
| Permintaan | 100.000/hari | 10 juta/bulan termasuk |
| CPU per permintaan | 10 ms (waktu menunggu D1 **tidak** dihitung) | sampai 5 menit |
| D1 baris dibaca | 5 juta/hari | 25 miliar/bulan termasuk |
| D1 baris ditulis | **100.000/hari** | 50 juta/bulan termasuk |
| D1 penyimpanan | 5 GB total | lebih besar |

Bila batas harian D1 paket gratis habis, D1 **berhenti melayani semua kueri** sampai 00:00 UTC.

## Hasil pengukuran

Diukur di database lokal yang sama persis dengan yang akan diunggah.

| Hal | Hasil | Alat |
|---|---|---|
| Ukuran database | 285 MB | `npm run estimasi` |
| Ukuran Worker | 122 KiB (36 KiB gzip) | `wrangler deploy --dry-run` |
| **Baris ditulis untuk impor penuh** | **±1,72 juta** (baris tabel + entri indeks) | `npm run estimasi` |
| CPU Worker per halaman | 0,2–3 ms. Pencarian kalimat panjang ±1–3 ms kode sendiri; sisanya di D1, yang tidak dihitung | `npm run ukur:cpu` + profil |
| Baris dibaca per halaman hadits | **±250** | header `X-D1-Baris` |
| Baris dibaca per halaman perawi | 1 | header `X-D1-Baris` |
| Baris dibaca per pencarian | 1.500–30.000 (tergantung banyaknya hasil) | header `X-D1-Baris` |

### Masalah besar yang ditemukan pengukuran, dan sudah diperbaiki

| Masalah | Sebelum | Sesudah | Perbaikan |
|---|---:|---:|---|
| Halaman hadits: tabel `mirip` (219.657 baris) tidak berindeks pada kolom `b` | **±450.000 baris dibaca per halaman**, artinya kuota gratis habis setelah ±11 kunjungan sehari | 243 | indeks `ix_mirip_b`, `ix_he_tema_he` |
| Halaman perawi menghitung guru/murid/riwayat setiap kali dibuka | 14.000–28.000 | 1 | dihitung di pipeline, disimpan sebagai JSON di baris perawi |
| Daftar perawi diurutkan tanpa indeks | 8.630 | 300 | indeks `ix_perawi_n` |

### Perlindungan lain yang ditambahkan

- **Cache tepi (Cache API).** Halaman yang sama tidak lagi menyentuh D1.
  - Halaman data disimpan 1 hari; pencarian dan cek disimpan 1 jam.
  - Kunci cache memuat `VERSI_DATA`, yang diisi otomatis setiap kali `npm run deploy`, sehingga data baru langsung memakai cache baru.
  - `?segar` melewati cache (untuk pengecekan).
  - Header `X-Cache: HIT/MISS` menunjukkan apakah halaman diambil dari cache.
- **Header `X-D1-Baris`** di setiap respons (jumlah baris D1 dibaca dan jumlah kueri), untuk memantau beban.
- **Header keamanan:**
  - CSP: hanya skrip dari situs sendiri; font dari Google Fonts; tidak bisa dibingkai situs lain.
  - `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
- **Galat tidak disimpan di cache.** Halaman 404 hanya disimpan 60 detik.

### Perkiraan kapasitas di paket gratis

- **Kunjungan yang tidak dari cache:** 5 juta baris ÷ ±250 = **±20.000 halaman hadits per hari**, atau sekitar 200–3.000 pencarian unik per hari. Halaman dan pencarian yang berulang dilayani dari cache tanpa memakai kuota D1.
- **CPU:** jauh di bawah 10 ms untuk semua halaman.
- **Permintaan:** 100.000 per hari, termasuk yang dilayani dari cache.

## Rekomendasi jalur terbit

1. **Impor awal memakai Workers Paid selama 1 bulan** (US$5, ±Rp 85 ribu). Impor penuh menulis ±1,72 juta baris. Di paket gratis itu butuh ±18 hari, dan setiap kali batas harian habis, situs ikut mati sampai 00:00 UTC.
2. Sesudah impor dan pengecekan, **kembali ke paket gratis.** Ukuran 285 MB masih jauh di bawah 5 GB.
3. **Pembaruan data besar berikutnya** (impor ulang penuh) juga sebaiknya dilakukan dalam bulan berbayar. Pembaruan kecil bisa langsung dilakukan di paket gratis.

Bila ingin menekan impor lebih jauh: tabel `mirip`, `sanad_perawi`, dan `judul` (±920 ribu tulisan) bisa diganti kolom JSON di tabel `riwayat`. Ini memangkas impor menjadi ±0,8 juta tulisan, tetapi tetap lebih dari sehari di paket gratis.

## Langkah menerbitkan (dari komputer pemilik proyek)

Prasyarat: Node.js ≥ 20, Python 3, repo ini, dan data sudah dibangun (`bash pipeline/run_all.sh`).

1. Buat akun Cloudflare (gratis) di <https://dash.cloudflare.com/sign-up>.
2. Masuk ke folder situs:
   ```bash
   cd site
   ```
3. Login wrangler:
   ```bash
   npx wrangler login
   ```
4. Buat database:
   ```bash
   npx wrangler d1 create teman-hadits
   ```
   Salin `database_id` yang dicetak ke `wrangler.toml`, di bagian `[[env.production.d1_databases]]`, menggantikan `GANTI-DENGAN-ID-DARI-wrangler-d1-create`.
5. Di dashboard Cloudflare, buka **Workers & Pages → Plans**, lalu pilih **Workers Paid** (sementara).
6. Impor data ke database online. Skrip meminta konfirmasi `YA`, lalu mengimpor 9 berkas:
   ```bash
   npm run impor:online
   ```
7. Terbitkan. Skrip menjalankan uji dulu, lalu `wrangler deploy --env production` dengan `VERSI_DATA` baru:
   ```bash
   npm run deploy
   ```
8. Uji situs online dengan 18 uji emas yang sama seperti lokal:
   ```bash
   BASE_URL=https://teman-hadits.<subdomain-anda>.workers.dev npm run test:http
   ```
9. Pasang domain:
   - tambahkan domain ke akun Cloudflare;
   - buka komentar baris `routes = [...]` di `[env.production]` dan isi nama domainnya;
   - terbitkan ulang:
   ```bash
   npm run deploy
   ```
10. Kembali ke paket **Free** di dashboard. Pantau **D1 → Metrics** (baris dibaca per hari) selama beberapa hari pertama.

## Daftar wajib sebelum diumumkan

| # | Hal | Status | Yang perlu dilakukan |
|---|---|---|---|
| 1 | Lisensi **OpenITI** (judul bab, edisi tahqiq, katalog palsu, Taqrib, Tahdzib al-Kamal) | **Belum terverifikasi** | Buka rilis Zenodo OpenITI (doi:10.5281/zenodo.3082463) dari jaringan biasa, catat lisensinya, dan cantumkan di halaman Metode. Bila tidak mengizinkan penerbitan ulang teks, sembunyikan kutipan katalog palsu dan teks Taqrib, sisakan rujukan nomornya |
| 2 | Terjemah **Riyadhus Shalihin** | Penerjemah belum dipastikan | Produksi sudah diatur `TERJEMAH_RIYADH="sembunyi"`. Ubah ke `"tampil"` hanya bila izinnya ada |
| 3 | **HadeethEnc** | Boleh diterbitkan ulang tanpa diubah, dengan atribusi | Minta nomor versi data lewat email ke pengelola, lalu isi di halaman tema |
| 4 | Izin **Lidwa Pusaka** | Sudah didapat | Simpan bukti tertulisnya di arsip pribadi (bukan di repo) |
| 5 | Data **Ifta' Sunnah** | Hanya untuk uji, tidak diterbitkan | Tidak perlu tindakan |
| 6 | **Glosarium** nama kitab & **daftar ucapan populer** | Ditandai "belum ditinjau" di situs | Sebaiknya ditinjau orang yang paham hadits sebelum diumumkan luas |
| 7 | **Domain** | Belum | Untuk `.my.id`, registrar PANDI biasanya meminta identitas WNI. Alternatif: `.com` atau `.id` |
| 8 | **Privasi** | Tidak ada analitik pihak ketiga dan tidak ada cookie | Teks yang ditempel di Cek Hadits ada di URL dan bisa tersimpan di cache tepi selama 1 jam. Sebutkan hal ini di halaman Metode, atau ubah Cek Hadits menjadi POST bila perlu |

## Anggaran tahun pertama (batas Rp 500.000)

| Pos | Perkiraan |
|---|---|
| Cloudflare Workers Paid, 1 bulan untuk impor awal | ±Rp 85.000 |
| Cloudflare paket gratis, bulan-bulan berikutnya | Rp 0 |
| Domain `.my.id` / `.com` | ±Rp 20.000 / ±Rp 200.000 per tahun |
| **Total** | **±Rp 105.000 – 285.000** |
