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
| D1 penyimpanan | 5 GB total per akun; **per database seingat kami 500 MB** (belum bisa dipastikan dari sini, cek halaman batas D1) | 10 GB per database |

Bila batas harian D1 paket gratis habis, D1 **berhenti melayani semua kueri** sampai 00:00 UTC.

## Hasil pengukuran

Diukur di database lokal yang sama persis dengan yang akan diunggah.

| Hal | Hasil | Alat |
|---|---|---|
| Ukuran database | 275 MB (dulu 285 MB) | `npm run estimasi` |
| Ukuran Worker | 122 KiB (36 KiB gzip) | `wrangler deploy --dry-run` |
| **Baris ditulis untuk impor penuh** | **±564 ribu** (dulu ±1,72 juta; baris tabel + entri indeks) | `npm run estimasi` |
| CPU Worker per halaman | 0,2–2 ms. Pencarian & cek: median 1–6 ms; **pencarian kalimat panjang p90 ±17 ms** (lihat di bawah) | `npm run ukur:cpu` + profil |
| Baris dibaca per halaman hadits | **30–120** (dulu ±40–250) | header `X-D1-Baris` |
| Baris dibaca per halaman perawi | 1 | header `X-D1-Baris` |
| Baris dibaca per pencarian | ±250–3.000 (dulu 700–29.000) | header `X-D1-Baris` |
| Baris dibaca halaman tema | 4–60 (dulu ±900) | header `X-D1-Baris` |

### Masalah besar yang ditemukan pengukuran, dan sudah diperbaiki

| Masalah | Sebelum | Sesudah | Perbaikan |
|---|---:|---:|---|
| Halaman hadits: tabel `mirip` (219.657 baris) tidak berindeks pada kolom `b` | **±450.000 baris dibaca per halaman**, artinya kuota gratis habis setelah ±11 kunjungan sehari | 243 | indeks `ix_mirip_b`, `ix_he_tema_he` |
| Halaman perawi menghitung guru/murid/riwayat setiap kali dibuka | 14.000–28.000 | 1 | dihitung di pipeline, disimpan sebagai JSON di baris perawi |
| Daftar perawi diurutkan tanpa indeks | 8.630 | 300 | indeks `ix_perawi_n` |

### Peringanan database (November 2026)

Isi semua halaman tidak berubah: 23 halaman (hadits, Riyadh, kitab, bab, pencarian, cek, tema, perawi, API) dibandingkan byte demi byte sebelum dan sesudah, semuanya sama persis.

| Perubahan | Akibat |
|---|---|
| Tabel `penilaian`, `mirip` (takhrij), `sanad_perawi`, `judul` (±430 ribu baris + indeks) diganti kolom JSON di baris `riwayat` (`nilai_json`, `jalur_json`, `perawi_json`) dan tabel judul unik `judul_bab` (16 ribu baris) | Impor: 1,72 juta → ±564 ribu baris ditulis. Halaman hadits membaca ±60% lebih sedikit baris (Bukhari 1: 243 → 95) |
| Indeks nomor edisi hanya untuk riwayat yang punya nomor edisi (indeks parsial); kolom `id` tidak lagi UNIQUE (tidak dipakai untuk mencari) | ±105 ribu tulisan lebih sedikit |
| Pencarian: kitab, urutan, dan tingkat setiap hasil diturunkan dari nomor `n` (urutan `n` = urutan kitab lalu urutan riwayat; tingkat B dari bitmap di `info`), bukan dibaca baris per baris | «shalat malam»: 7.061 → ±2.900 baris |
| Pencarian kata konsep yang menyebut bab (mis. «tarawih»): bab dicari dulu, lalu riwayat lewat indeks (kitab, bab). Versi lama memindai semua riwayat kitab itu | «tolong carikan hadits tentang sholat tarawih»: **28.938 → 445 baris** |
| Daftar tema (447) disimpan sebagai satu baris `info` dengan judul yang sudah dinormalkan | Setiap pencarian −443 baris; halaman tema ±900 → 4–60 |

**CPU.** Pengukuran A/B (versi sebelum dan sesudah peringanan, data sama) memberi angka yang sama: pencarian kalimat panjang median ±6 ms, **p90 ±17 ms**; cek teks Indonesia p90 7–11 ms. Jadi angka "0,2–3 ms" di versi dokumen sebelumnya sudah usang. Profil: ±91% waktu ada di SQLite tiruan (di produksi itu terjadi di D1 dan tidak dihitung), sisanya tersebar di banyak fungsi kecil. Pengukur memakai `process.cpuUsage`, yang ikut menghitung thread GC/JIT, jadi angkanya cenderung lebih tinggi daripada hitungan Cloudflare. Tetapi pencarian kalimat panjang **mungkin sesekali melewati 10 ms di paket gratis** (galat 1102). Pantau "CPU time" di dasbor Workers sesudah terbit. Bila sering terjadi, pilihannya: Workers Paid, atau mengoptimalkan pencarian.

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

- **Kunjungan yang tidak dari cache:** 5 juta baris ÷ ±100 = **±50.000 halaman hadits per hari**, atau sekitar 1.500–20.000 pencarian unik per hari. Halaman dan pencarian yang berulang dilayani dari cache tanpa memakai kuota D1.
- **CPU:** di bawah 10 ms untuk semua halaman, kecuali pencarian kalimat panjang yang p90-nya bisa melewati 10 ms (lihat di atas).
- **Permintaan:** 100.000 per hari, termasuk yang dilayani dari cache.

## Rekomendasi jalur terbit

1. **Impor awal memakai Workers Paid selama 1 bulan** (US$5, ±Rp 85 ribu). Impor penuh menulis ±564 ribu baris. Di paket gratis itu butuh ±6 hari, dan setiap kali batas harian habis, situs ikut mati sampai 00:00 UTC.
2. Sesudah impor dan pengecekan, **kembali ke paket gratis.** Ukuran 275 MB masih di bawah batas per database paket gratis (seingat kami 500 MB; pastikan di halaman batas D1).
3. **Pembaruan data besar berikutnya** (impor ulang penuh) juga sebaiknya dilakukan dalam bulan berbayar. Pembaruan kecil bisa langsung dilakukan di paket gratis.

Sisa tulisan terbesar: tabel `riwayat` sendiri beserta 3 indeksnya (±310 ribu), tabel bayangan pencarian teks (±97 ribu), dan `kata_df` (±47 ribu). Semuanya dipakai langsung oleh halaman, jadi tidak dipangkas.

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
