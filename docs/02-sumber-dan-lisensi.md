# Sumber Data dan Lisensi

## Sumber yang sudah dipakai

### 1. Lidwa Pusaka via carihadis.com, dari repo irsyadulibad/hadits-database

- **Isi:** teks Arab + terjemah Indonesia untuk 12 berkas: 9 imam, Musnad asy-Syafi'i, dan 2 berkas Riyadhus Shalihin.
- **Commit terkunci:** `db43bdaa70ee528a0e663c089d3dab5bb4d855f0`.
- **Lisensi repo:** MIT, © 2020 Ahmad Irsyadul Ibad.
- **Catatan penting:** README repo menyebut sumbernya carihadis.com. Gaya terjemahannya, yaitu nama perawi dalam `[kurung siku]` dan penomoran (Bukhari 7.008, Muslim 5.362, Darimi 3.367), identik dengan *Ensiklopedi Hadits Kitab 9 Imam* terbitan Lidwa Pusaka. Lisensi MIT hanya berlaku untuk karya si pengunggah (kompilasi SQL). Lisensi itu **tidak bisa** memberi izin atas terjemahan yang hak ciptanya milik pihak lain.
- **Tindakan yang disarankan sebelum situs dibuka untuk umum:**
  1. Cantumkan atribusi "Terjemah: Lidwa Pusaka" di setiap halaman. Ini sudah ada di prototipe.
  2. Kirim email permohonan izin ke Lidwa Pusaka untuk pemakaian non-komersial. Lampirkan penjelasan bahwa situs ini gratis, tanpa iklan, dan selalu mengatribusi.
  3. Bila izin tidak diberikan, rencana cadangannya: teks Arab dan penilaian tetap tampil (sumbernya domain publik), dan terjemahan diganti dengan sumber berlisensi terbuka (lihat bagian kandidat).

### 2. fawazahmed0/hadith-api

- **Isi:** teks Arab 7 kitab dengan penomoran standar, nama kitab/bab, dan **penilaian derajat per hadits atas nama ulama**.
- **Commit terkunci:** `df57907be35291c91ad6a6691180e22ca9920784`.
- **Lisensi:** Unlicense (domain publik).
- **Catatan:** repo tidak mendokumentasikan sumber hulunya secara lengkap. Karena itu ia diperlakukan sebagai *sumber digital kedua* untuk pembanding, bukan sumber primer. Terjemah Indonesianya juga berasal dari Lidwa, sehingga **tidak** dipakai sebagai verifikasi terjemahan.

## Kandidat sumber berikutnya

Prioritas ditentukan oleh nilai tambahnya bagi kebenaran data.

| Sumber | Untuk apa | Status akses dari lingkungan build |
|---|---|---|
| Dorar.net, *al-Mausu'ah al-Haditsiyyah* | Takhrij + hukum hadits per ulama, termasuk hadits palsu populer | **Diblokir** oleh kebijakan jaringan sesi ini |
| HadeethEnc.com (Ensiklopedia Hadits Terjemah) | Terjemah Indonesia yang sudah ditinjau, derajat, penjelasan, tema | **Diblokir** |
| sunnah.com API | Pembanding nomor dan teks (perlu API key) | **Diblokir** |
| OpenITI (GitHub) | Teks Arab dengan identitas edisi cetak, untuk Darimi, Musnad Ahmad, Syafi'i, Riyadhus Shalihin, dan kitab rijal | Bisa diakses |
| Kitab rijal: *Taqrib at-Tahdzib*, *Tahdzib al-Kamal*, *al-Kasyif* | Biodata dan penilaian perawi untuk rantai sanad | Lewat OpenITI / Syamilah |
| Scan kitab cetak (archive.org) | Verifikasi sampel (lihat protokol) | **Diblokir**; bisa diunduh manual oleh pemilik proyek |

Host yang diblokir bisa dibuka oleh pemilik proyek di pengaturan *Network access* environment Claude Code, dengan menambah host di *Allowed domains*. Panduannya ada di <https://code.claude.com/docs/en/cloud-environments#network-access>. Host yang perlu ditambah: `dorar.net`, `hadeethenc.com`, `archive.org`, `cdn.jsdelivr.net`.
