# Sumber Data dan Lisensi

## Sumber yang sudah dipakai

### 1. Lidwa Pusaka via carihadis.com, dari repo irsyadulibad/hadits-database

- **Isi:** teks Arab + terjemah Indonesia untuk 12 berkas: 9 imam, Musnad asy-Syafi'i, dan 2 berkas Riyadhus Shalihin.
- **Commit terkunci:** `db43bdaa70ee528a0e663c089d3dab5bb4d855f0`.
- **Lisensi repo:** MIT, © 2020 Ahmad Irsyadul Ibad.
- **Catatan penting:** README repo menyebut sumbernya carihadis.com. Gaya terjemahannya, yaitu nama perawi dalam `[kurung siku]` dan penomoran (Bukhari 7.008, Muslim 5.362, Darimi 3.367), identik dengan *Ensiklopedi Hadits Kitab 9 Imam* terbitan Lidwa Pusaka. Lisensi MIT hanya berlaku untuk karya si pengunggah (kompilasi SQL). Lisensi itu **tidak bisa** memberi izin atas terjemahan yang hak ciptanya milik pihak lain.
- **Izin:** pemilik proyek menyatakan sudah **mendapat izin** dari Lidwa Pusaka (dicatat 1 November 2026). Simpan bukti tertulisnya (email/surat) di arsip pribadi, bukan di repo publik, dan cantumkan di halaman Metode: "Terjemah digunakan dengan izin Lidwa Pusaka".
- **Atribusi:** "Terjemah: Lidwa Pusaka" tetap dicantumkan di setiap halaman hadits.
- **Pengecualian, Riyadhus Shalihin:** terjemah Indonesianya di repo yang sama **bukan** dari Ensiklopedi 9 Imam Lidwa, dan penerjemahnya belum dipastikan. Izin Lidwa belum tentu mencakupnya. Lihat `docs/08-riyadhus-shalihin.md` dan pengaturan `TERJEMAH_RIYADH`.

### 2. fawazahmed0/hadith-api

- **Isi:** teks Arab 7 kitab dengan penomoran standar, nama kitab/bab, dan **penilaian derajat per hadits atas nama ulama**.
- **Commit terkunci:** `df57907be35291c91ad6a6691180e22ca9920784`.
- **Lisensi:** Unlicense (domain publik).
- **Catatan:** repo tidak mendokumentasikan sumber hulunya secara lengkap. Karena itu ia diperlakukan sebagai *sumber digital kedua* untuk pembanding, bukan sumber primer. Terjemah Indonesianya juga berasal dari Lidwa, sehingga **tidak** dipakai sebagai verifikasi terjemahan.

### 3. OpenITI (judul kitab & bab, edisi tahqiq, kitab hadits palsu)

- **Isi yang dipakai:** (a) **judul kitab dan bab** (struktur), bukan teks hadits; teks hadits tetap dari sumber 1 dan 2. (b) Untuk Musnad Ahmad, ad-Darimi, dan asy-Syafi'i: teks edisi tahqiq sebagai **pembanding** (menaikkan tingkat A), nomor edisi tahqiq, dan penilaian Husain Salim Asad untuk ad-Darimi. (c) *Taqrib at-Tahdzib* (Ibnu Hajar, tahqiq 'Awwamah) yang entrinya **ditampilkan** di halaman perawi, dan *Tahdzib al-Kamal* (al-Mizzi, tahqiq Basyar 'Awwad) sebagai bukti identifikasi perawi (lihat `docs/11-perawi.md`). (d) Empat kitab tentang hadits populer & palsu (*al-Maudhu'at*, *al-Maqashid al-Hasanah*, *al-Asrar al-Marfu'ah*, *Kasyf al-Khafa'*). Teks pembahasan ulamanya **ditampilkan** per entri dengan atribusi (lihat `docs/10-katalog-palsu.md`).
- **Berkas & edisi** (commit terkunci di `pipeline/sources.json`): Bukhari (Dar Thauq an-Najah, tahqiq Muhammad Zuhair an-Nashir, 1422 H), Muslim (Dar Ihya' at-Turats al-'Arabi), Abu Dawud (tahqiq Muhyiddin 'Abdul Hamid, al-Maktabah al-'Ashriyyah), Ibnu Majah (tahqiq Fu'ad 'Abdul Baqi), Nasa'i (tahqiq Abu Ghuddah), Tirmidzi, al-Muwaththa' (Dar Ihya' at-Turats al-'Arabi), Musnad Ahmad (ar-Risalah, Syu'aib al-Arna'uth dkk.), Sunan ad-Darimi (Dar al-Mughni, Husain Salim Asad), Musnad asy-Syafi'i (Mahir Yasin al-Fahl), dan keempat kitab hadits palsu. Sebelas berkas ini diambil dari tujuh repo OpenITI (0200AH–1175AH).
- **Lisensi:** **CC BY-NC-SA 4.0**. Diperiksa 2 Nov 2026 dari metadata rilis Zenodo terbaru (record 17767721, versi 2025.1.9, 30 Des 2025; konsep DOI 10.5281/zenodo.3082463): `license: cc-by-nc-sa-4.0`. Repo GitHub OpenITI sendiri tidak punya berkas LICENSE.
  - **BY:** atribusi + tautan lisensi + sebutkan perubahan: dicantumkan di Metode → «Sumber dan lisensi», di kaki setiap halaman, di sumber halaman hadits, di Ringkasan Ibnu Hajar (perawi), dan di Pembahasan ulama (katalog).
  - **NC:** situs ini layanan umum tanpa iklan dan tanpa pungutan. Jangan menambah iklan, langganan berbayar, atau penjualan data selama teks OpenITI tampil.
  - **SA:** bagian situs yang memuat teks OpenITI dinyatakan berlisensi CC BY-NC-SA 4.0 di halaman Metode.
  - Catatan: lisensi ini berlaku untuk karya digital OpenITI. Hak atas edisi tahqiq cetak yang menjadi dasar teksnya (mis. ar-Risalah, Dar al-Mughni) adalah soal lain yang tidak diselesaikan oleh lisensi OpenITI; kita menampilkan teks matan klasik, nomor, dan penilaian singkat, bukan catatan kaki tahqiq secara utuh.

## Kandidat sumber berikutnya

Prioritas ditentukan oleh nilai tambahnya bagi kebenaran data.

| Sumber | Untuk apa | Status akses dari lingkungan build |
|---|---|---|
| Dorar.net, *al-Mausu'ah al-Haditsiyyah* | Takhrij + hukum hadits per ulama, termasuk hadits palsu populer | Jaringan sudah dibuka, tetapi **situs Dorar sendiri menolak akses otomatis** (403, proteksi bot). Kami tidak menembusnya. Jalan yang benar: minta akses API resmi ke pengelola Dorar. Sementara itu katalog palsu memakai 4 kitab klasik dari OpenITI (lihat docs/10) |
| HadeethEnc.com (Ensiklopedia Hadits Terjemah) | 447 kategori tema berbahasa Indonesia, terjemah yang sudah ditinjau, derajat, penjelasan, faedah | **Sudah dimuat** (lihat `docs/07-hadeethenc.md`): boleh diterbitkan ulang tanpa diubah, dengan atribusi dan nomor versi |
| sunnah.com API | Pembanding nomor dan teks (perlu API key) | **Diblokir** |
| OpenITI (GitHub) | Teks Arab dengan identitas edisi cetak, untuk Darimi, Musnad Ahmad, Syafi'i, Riyadhus Shalihin, dan kitab rijal | Bisa diakses |
| Kitab rijal: *Taqrib at-Tahdzib*, *Tahdzib al-Kamal* | Biodata dan penilaian perawi untuk rantai sanad | **Sudah dimuat** (docs/11). *al-Kasyif* & *Tahdzib at-Tahdzib* tersedia di OpenITI, belum dipakai |
| Data Ifta' Sunnah (via marwangalaly14/Isnad) | **Hanya uji independen** identifikasi perawi; tidak diterbitkan ulang (lisensi belum jelas) | Rilis GitHub bisa diunduh; Kaggle & sunna.alifta.gov.sa diblokir jaringan |
| Scan kitab cetak (archive.org) | Verifikasi sampel (lihat protokol) | **Bisa diakses** |

Host yang diblokir bisa dibuka oleh pemilik proyek di pengaturan *Network access* environment Claude Code, dengan menambah host di *Allowed domains*. Panduannya ada di <https://code.claude.com/docs/en/cloud-environments#network-access>. Status 1 Nov 2026: `hadeethenc.com` dan `archive.org` sudah terbuka. `dorar.net` terbuka di jaringan tetapi menolak bot.
