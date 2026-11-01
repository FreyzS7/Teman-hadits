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
| `docs/07-hadeethenc.md` | Impor tema & hadits HadeethEnc, syarat pemakaian, uji silang atribusi |
| `docs/08-riyadhus-shalihin.md` | Riyadhus Shalihin: pemecahan per hadits, pemasangan terjemah menurut isi, validasi |
| `docs/09-judul-kitab-bab.md` | Judul kitab & bab Arab (OpenITI) dan nama kitab Indonesia (glosarium) |
| `docs/10-katalog-palsu.md` | Katalog hadits populer & palsu: 4 kitab klasik, kata kunci penilaian, ucapan populer |
| `site/` | Situs sungguhan: Cloudflare Worker + database D1, jalan lokal dengan `wrangler dev` |
| `design/` | Prototipe desain (`prototipe.html`), diisi data asli dari database |

## Menjalankan

Butuh Python 3 dan Node.js ≥ 20.

**1. Bangun data** (sekali; ±4 menit, ditambah ±25 menit untuk unduhan pertama HadeethEnc):

```bash
bash pipeline/run_all.sh
```

**2. Jalankan situs di komputer sendiri:**

```bash
cd site
```

```bash
npm install
```

```bash
npm run impor
```

```bash
npm run dev
```

Buka <http://127.0.0.1:8787>. `npm run impor` cukup diulang bila data dibangun ulang.

**3. Uji:**

```bash
npm test
```

Uji emas lewat HTTP (saat `npm run dev` sedang jalan di terminal lain):

```bash
BASE_URL=http://127.0.0.1:8787 npm run test:http
```

Pencarian juga bisa dicoba dari terminal tanpa situs:

```bash
python3 pipeline/cari.py "tolong carikan hadits tentang sholat tarawih"
```

## Status saat ini

- 11 kitab dimuat, 69.408 riwayat terbit, 408 dikarantina. Termasuk Riyadhus Shalihin (1.896 hadits): sumbernya dicocokkan dengan atribusi an-Nawawi (98,2% cocok).
- 21.185 riwayat sudah punya penilaian derajat bernama: al-Albani, Syu'aib al-Arna'uth, Zubair 'Ali Za'i, Ahmad Syakir, Basyar 'Awwad, Abu Ghuddah, Salim al-Hilali, dan lainnya.
- Musnad Ahmad, ad-Darimi, asy-Syafi'i dicocokkan dengan edisi tahqiq (ar-Risalah, Husain Salim Asad, al-Fahl): 27.302 riwayat naik ke tingkat A, nomor edisi tahqiq ditampilkan, 2.810 riwayat Darimi mendapat penilaian Husain Salim Asad.
- Judul kitab & bab Arab dari teks kitabnya (OpenITI) untuk 10 kitab, dipetakan menurut isi; nomor hadits cocok dengan edisi cetak 96–99,8% tanpa dipakai saat mencocokkan. Nama kitab Indonesia dari glosarium yang belum ditinjau ahli.
- Katalog hadits populer & palsu: 6.044 entri dari *al-Maudhu'at* (Ibnul Jauzi), *al-Maqashid al-Hasanah* (as-Sakhawi), *al-Asrar al-Marfu'ah* (Mulla 'Ali al-Qari), dan *Kasyf al-Khafa'* (al-'Ajluni). 20 ucapan populer berbahasa Indonesia (belum ditinjau) ditautkan ke pembahasan ulama dan ke kitab hadits, di `/populer` dan `/cek`. Kata kunci penilaian ditampilkan bersama kalimat aslinya, tanpa vonis dari situs.
- 447 tema berbahasa Indonesia dan 2.260 hadits dari HadeethEnc.com. 1.998 di antaranya terhubung ke riwayat kita; uji silang atribusi: 98,8% cocok dengan atribusi HadeethEnc sendiri.
- Uji: uji emas data (Python, termasuk HadeethEnc dan katalog palsu), 9 uji unit + paritas Python↔JavaScript, 15 uji emas lewat HTTP. Contohnya: hadits niat ditemukan di ketujuh tempatnya dalam Shahih al-Bukhari, dan tidak ada di al-Muwaththa' riwayat Yahya.

Angka terbaru selalu ada di [docs/01-audit-data.md](docs/01-audit-data.md).
