# Persiapan Online (Cloudflare)

Isi dokumen ini:
- hasil pengukuran situs terhadap batas paket gratis Cloudflare;
- perbaikan yang dibuat karena pengukuran itu;
- langkah menerbitkan situs dari akun pemilik proyek;
- daftar yang harus beres sebelum situs diumumkan.

Langkah yang memerlukan akun Cloudflare (login, membuat database, membayar, domain) harus dijalankan pemilik proyek. Semua yang bisa disiapkan dan diuji tanpa akun sudah disiapkan dan diuji.

## Batas paket Cloudflare yang relevan

Angka di bawah ini diambil dari dokumentasi resmi lewat hasil pencarian (batas 500 MB per database paket gratis dicek ulang November 2026). Halaman developers.cloudflare.com sendiri tidak bisa dibuka dari lingkungan build. **Periksa lagi halaman resminya sebelum memilih paket**: [harga D1](https://developers.cloudflare.com/d1/platform/pricing/), [batas Workers](https://developers.cloudflare.com/workers/platform/limits/), [harga Workers](https://developers.cloudflare.com/workers/platform/pricing/).

| | Workers Free | Workers Paid (US$5/bulan) |
|---|---|---|
| Permintaan | 100.000/hari | 10 juta/bulan termasuk |
| CPU per permintaan | 10 ms (waktu menunggu D1 **tidak** dihitung) | sampai 5 menit |
| D1 baris dibaca | 5 juta/hari | 25 miliar/bulan termasuk |
| D1 baris ditulis | **100.000/hari** | 50 juta/bulan termasuk |
| D1 penyimpanan | 5 GB total per akun; **500 MB per database** | 10 GB per database |

Bila batas harian D1 paket gratis habis, D1 **berhenti melayani semua kueri** sampai 00:00 UTC.

## Hasil pengukuran

Diukur di database lokal yang sama persis dengan yang akan diunggah.

| Hal | Hasil | Alat |
|---|---|---|
| Ukuran database | 275 MB (dulu 285 MB) | `npm run estimasi` |
| Ukuran Worker | 127 KiB (38 KiB gzip) | `wrangler deploy --dry-run` |
| **Baris ditulis untuk impor penuh** | **±564 ribu** (dulu ±1,72 juta; baris tabel + entri indeks) | `npm run estimasi` |
| CPU Worker per halaman | 0,3–2 ms (daftar perawi ±3 ms). Pencarian & cek: **p90 paling tinggi ±4,4 ms** (dulu ±10 ms; lihat di bawah) | `npm run ukur:cpu` + profil |
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

**CPU.** Pengukuran A/B (versi sebelum dan sesudah peringanan, data sama) memberi angka yang sama, jadi peringanan database tidak mengubah CPU. Angka lama di bagian ini (pencarian p90 ±17 ms) ternyata kebanyakan galat alat ukur: `process.cpuUsage` ikut menghitung thread GC/JIT di latar belakang. Alat ukur sekarang memakai jam dinding thread utama dikurangi waktu di SQLite, dan hasil kueri diurai ulang dari JSON seperti di produksi (lihat komentar di `site/scripts/ukur-cpu.mjs`).

### Optimasi CPU pencarian & cek (November 2026)

Dengan alat ukur yang benar, yang paling berat adalah **cek teks**: cek teks Indonesia p90 ±10,3 ms (melewati batas 10 ms paket gratis), cek teks Arab ±8,8 ms. Profil menunjukkan waktunya habis untuk menormalkan teks setiap kandidat (120 terjemah, 80 teks Arab) dengan 4–5 regex berantai, lalu memecahnya menjadi kata.

| Perubahan | Akibat |
|---|---|
| `normAr` ditulis sebagai satu putaran per huruf (dulu 5 regex berantai); NFC hanya dijalankan bila ada hamzah/madd penggabung | ±3,5x lebih cepat |
| Cek Indonesia: pencocokan awalan kata langsung di teks (`awalanId`), tanpa membuat string per kata | 120 kandidat: ±4,7 → ±1,3 ms |
| Cek Arab: jumlah 2-gram yang sama dihitung tanpa membangun himpunan 2-gram kandidat | — |
| Katalog: 10 kata pertama diambil tanpa memecah seluruh entri | — |
| Pencarian: bitmap tingkat dibaca langsung dari string biner; pencocokan judul tema tidak lagi membuat string baru di setiap perbandingan; format angka memakai satu `Intl.NumberFormat` | pencarian kalimat panjang p90 6,1 → 4,2 ms |

Hasil (p90, ms): cek Indonesia **10,3 → 4,4**; cek Arab **8,8 → 4,2**; pencarian kalimat panjang **6,1 → 4,2**; «niat» 6,4 → 3,5. Halaman lain tetap 0,3–3 ms.

Isinya tidak berubah. Cara memastikannya:
- **903 halaman** dibandingkan byte demi byte antara versi lama dan baru. Isinya: 634 cek teks (potongan acak terjemah & teks Arab, dengan dan tanpa klaim "HR.", semua ucapan populer dan variannya, judul entri katalog), 132 pencarian, 99 halaman hadits di 11 kitab, 20 halaman ucapan populer, 11 halaman perawi, serta beranda, tema, metode, dan kitab. Semuanya sama persis.
- 1.400 hasil `cek()` (JSON lengkap, termasuk skor) juga sama.
- Uji `test/cepat.test.js` membandingkan versi cepat dengan definisi regex aslinya: semua teks uji ditambah 100.000 string Arab acak dan 50.000 kalimat Indonesia acak. Saat pengembangan, `normAr` juga diuji pada **109.380 teks Arab** di database (riwayat, katalog, bab, perawi, HadeethEnc): semuanya sama.

Catatan: angka ini dari Node di mesin pengembangan, bukan dari Cloudflare. Sesudah terbit, tetap pantau "CPU time" di dasbor Workers. Galat 1102 berarti batas CPU terlewati.

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
- **CPU:** semua halaman yang diukur di bawah 5 ms (p90), jadi ada jarak lebih dari 2x dari batas 10 ms (lihat di atas).
- **Permintaan:** 100.000 per hari, termasuk yang dilayani dari cache.

## Rekomendasi jalur terbit

1. **Impor awal memakai Workers Paid selama 1 bulan** (US$5, ±Rp 85 ribu). Impor penuh menulis ±564 ribu baris. Di paket gratis itu butuh ±6 hari, dan setiap kali batas harian habis, situs ikut mati sampai 00:00 UTC.
2. Sesudah impor dan pengecekan, **kembali ke paket gratis.** Ukuran 275 MB masih di bawah batas 500 MB per database paket gratis.
3. **Pembaruan data besar berikutnya** (impor ulang penuh) juga sebaiknya dilakukan dalam bulan berbayar. Pembaruan kecil bisa langsung dilakukan di paket gratis.

Sisa tulisan terbesar: tabel `riwayat` sendiri beserta 3 indeksnya (±310 ribu), tabel bayangan pencarian teks (±97 ribu), dan `kata_df` (±47 ribu). Semuanya dipakai langsung oleh halaman, jadi tidak dipangkas.

## Langkah menerbitkan (dari komputer pemilik proyek)

Prasyarat: Node.js ≥ 20, Python 3 (hanya pustaka bawaan, tanpa `pip install`), repo ini, dan data sudah dibangun (`bash pipeline/run_all.sh`, dijalankan dari folder utama repo). Skripnya memakai bash: di Windows, jalankan lewat WSL atau Git Bash. `run_all.sh` mencari sendiri Python yang jalan (`python3`, `python`, atau peluncur Windows `py`) dan memaksa mode UTF-8 (`-X utf8`) supaya teks Arab tidak gagal ditulis di Windows.

Membangun data dari nol mengunduh ±300 MB sumber, termasuk unduhan HadeethEnc yang sengaja dibatasi (≤ 3 permintaan/detik), lalu menjalankan seluruh pipeline dan ujinya. Hasilnya `build/d1/` (9 berkas SQL, ±290 MB). Waktu totalnya belum diukur ulang; siapkan beberapa jam dan koneksi yang stabil.

**Jalur lain: terbit dari sesi Claude Code di cloud.** Bila tidak ingin membangun data di komputer sendiri:
1. Buat API token Cloudflare dengan izin *Workers Scripts: Edit* dan *D1: Edit* (Cloudflare → My Profile → API Tokens), lalu catat *Account ID* Anda.
2. Simpan keduanya sebagai rahasia lingkungan, bukan di chat: `CLOUDFLARE_API_TOKEN` dan `CLOUDFLARE_ACCOUNT_ID`.
3. Izinkan domain `api.cloudflare.com` di pengaturan *Network access* lingkungan.
4. Mulai sesi baru. Sesi itu membangun data, membuat database, mengimpor, menerbitkan, dan menjalankan uji. Pembayaran Workers Paid dan domain tetap Anda lakukan sendiri di dashboard.

Token itu bisa mengubah Worker dan database di akun Anda. Cabut token itu di dashboard setelah situs terbit.

1. Buat akun Cloudflare (gratis) di <https://dash.cloudflare.com/sign-up>.
2. Masuk ke folder situs dan pasang wrangler (sekali saja):
   ```bash
   cd site
   ```
   ```bash
   npm install
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
| 1 | Lisensi **OpenITI** (judul bab, edisi tahqiq, katalog palsu, Taqrib, Tahdzib al-Kamal) | **CC BY-NC-SA 4.0** (Zenodo 2025.1.9, dicek 2 Nov 2026) | Atribusi & lisensi sudah dicantumkan. Situs harus tetap **nonkomersial** (tanpa iklan/berbayar) selama memuat teks OpenITI |
| 2 | Terjemah **Riyadhus Shalihin** | Penerjemah belum dipastikan | Produksi sudah diatur `TERJEMAH_RIYADH="sembunyi"`. Ubah ke `"tampil"` hanya bila izinnya ada |
| 3 | **HadeethEnc** | Boleh diterbitkan ulang tanpa diubah, dengan atribusi | Minta nomor versi data lewat email ke pengelola, lalu isi di halaman tema |
| 4 | Izin **Lidwa Pusaka** | Sudah didapat | Simpan bukti tertulisnya di arsip pribadi (bukan di repo) |
| 5 | Data **Ifta' Sunnah** | Hanya untuk uji, tidak diterbitkan | Tidak perlu tindakan |
| 6 | **Glosarium** nama kitab & **daftar ucapan populer** | Ditandai "belum ditinjau" di situs | Sebaiknya ditinjau orang yang paham hadits sebelum diumumkan luas |
| 7 | **Domain** | Belum | Untuk `.my.id`, registrar PANDI biasanya meminta identitas WNI. Alternatif: `.com` atau `.id` |
| 8 | **Privasi** | Sudah dijelaskan di halaman Metode (#privasi) | Tidak ada cookie, iklan, atau analitik pihak ketiga. Teks Cek Hadits dan kata pencarian ada di alamat halaman dan bisa tersimpan di cache Cloudflare ±1 jam; pengguna diminta tidak menempel data pribadi |

## Anggaran tahun pertama (batas Rp 500.000)

| Pos | Perkiraan |
|---|---|
| Cloudflare Workers Paid, 1 bulan untuk impor awal | ±Rp 85.000 |
| Cloudflare paket gratis, bulan-bulan berikutnya | Rp 0 |
| Domain `.my.id` / `.com` | ±Rp 20.000 / ±Rp 200.000 per tahun |
| **Total** | **±Rp 105.000 – 285.000** |
