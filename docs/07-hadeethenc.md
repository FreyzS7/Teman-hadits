# HadeethEnc: Tema, Terjemah, dan Pemetaan ke Riwayat

Sumber: **HadeethEnc.com**, *Ensiklopedia Terjemahan Hadis-hadis Nabi*, API v1 bahasa Indonesia. Diambil 2026-11-01 (UTC).

## Yang diambil

| Isi | Jumlah |
|---|---:|
| Kategori tema (bahasa Indonesia), dengan 7 tema akar | 447 |
| Tema yang langsung dipakai oleh minimal satu hadits | 422 |
| Hadits unik: judul, terjemah Indonesia, teks Arab, atribusi, derajat, penjelasan, faedah | 2.260 |

Hasilnya ada di `build/hadeethenc.sqlite`, dengan tabel `tema`, `he_hadits`, `he_tema`, `he_riwayat`, dan `hadeethenc_meta`. Cache mentahnya ada di `sources/hadeethenc/` (±32 MB, tidak di-commit).

Derajat menurut HadeethEnc sendiri: "Hadis sahih" 1.290, "Sahih" 767, "Hadis hasan" 91, "Hasan" 49, dan sisanya label lain (mis. "Hasan li gairihi"). Derajat ini **penilaian penyusun HadeethEnc** dan harus ditampilkan atas nama mereka.

## Syarat pemakaian dan keputusan tampil

Teks dari modal "Terms and Policies" di hadeethenc.com: terjemahan **boleh diunduh dan diterbitkan ulang** dengan syarat:

1. tidak diubah, ditambah, atau dikurangi;
2. penerbit dan sumber (HadeethEnc.com) disebut dengan jelas;
3. nomor versi disebut saat menerbitkan ulang;
4. informasi versi terjemah tetap disertakan;
5. catatan atas terjemah dilaporkan ke HadeethEnc.com;
6. terjemah diperbarui mengikuti versi terbaru;
7. tidak ditampilkan bersama iklan yang tidak pantas.

**Keputusan:** `boleh_tampil = 1` untuk semua hadits. Situs wajib:

- menampilkan teks persis seperti dari API, tanpa disunting;
- menulis "Sumber: HadeethEnc.com" dan menautkan ke `url` tiap hadits;
- menampilkan info versi.

**Kekurangan yang perlu ditindaklanjuti:** API tidak menyediakan nomor versi terjemah. Untuk sementara, versi dicatat sebagai "API v1, diambil 2026-11-01" (tabel `hadeethenc_meta`). Sebaiknya pemilik proyek mengirim email ke HadeethEnc. Tujuannya dua: menanyakan cara menyebut nomor versi, dan sekaligus memberi tahu bahwa terjemah mereka dipakai (sesuai syarat no. 5). Situs ini tanpa iklan, jadi syarat no. 7 terpenuhi.

Catatan teknis: server HadeethEnc menolak identitas bawaan `urllib` Python. Pengunduh memakai `curl` biasa dengan identitas aslinya; kami tidak menyamar sebagai peramban.

## Pemetaan ke riwayat kita (`he_riwayat`)

**Metode:**

1. Matan HadeethEnc diambil dari `hadeeth_ar`. Bila ada kutipan «…», isinya yang dipakai. Bila tidak, pembuka "عن … رضي الله عنه قال" dibuang.
2. Catatan editor dibuang, yaitu bagian dalam kurung seperti «(ولمسلم: …)» dan sisipan seperti "-أو قال: …-".
3. Matan dinormalisasi dengan `common.norm_ar` dan `stem_ar`, lalu dipecah jadi 2-gram.
4. Kandidat riwayat dicari lewat 2-gram langka.
5. Skor = bagian 2-gram matan HadeethEnc yang ada di teks riwayat, **berbobot IDF**. Frasa umum seperti رسول الله dan صلى الله عليه وسلم hampir tidak berbobot.
6. Pasangan disimpan bila skor ≥ 0,6, maksimal 40 per hadits.

| Ukuran | Hasil |
|---|---|
| Hadits HadeethEnc yang punya ≥ 1 pasangan | **1.998 / 2.260 (88,4%)** |
| Jumlah pasangan | 8.181 |
| Tidak terpetakan | 262. Dari jumlah ini, 45 hanya beratribusi ke kitab di luar koleksi kita (Ibnu Khuzaimah, Baihaqi, Thabrani, dll.) dan 46 matannya terlalu pendek (< 4 dua-gram) |

### Cek manual 10 sampel acak (seed 20261101)

Saya membaca sendiri matan HadeethEnc dan teks riwayat pasangannya, satu per satu.

- **Putaran akhir (bobot IDF): 10/10 benar.** Sampelnya HE 6271→Tirmidzi 807, 10947→Ahmad L21374, 11195→Bukhari 2905, 8915→Bukhari 3468, 4202→Bukhari 35, 10706→Abu Dawud 532, 6040→Bukhari 6616, 10575→Bukhari 4987, 10623→Muslim 3114, 5860→Tirmidzi 2360.
- **Putaran sebelumnya (tanpa bobot IDF): 9/10 benar.** HE 10940 (Ibnu Umar meletakkan tangan sebelum lutut, riwayat Ibnu Khuzaimah) salah terpetakan ke Abu Dawud 1130 (shalat Jumat Ibnu Umar). Keduanya hanya sama-sama memuat frasa umum "كان رسول الله ﷺ يفعل ذلك". Kesalahan inilah alasan bobot IDF ditambahkan. Sekarang HE 10940 tidak terpetakan, dan itu benar karena kitab sumbernya tidak ada di koleksi kita.

### Uji silang atribusi (saksi independen)

Atribusi HadeethEnc ("متفق عليه", "رواه مسلم", "رواه أبو داود والترمذي", …) dibuat penyusun HadeethEnc, bukan oleh kita. Atribusi itu dibandingkan dengan kitab tempat pemetaan kita menemukan pasangannya.

| Ukuran | Hasil |
|---|---|
| Hadits terpetakan yang atribusinya menyebut ≥ 1 kitab di koleksi kita | 1.993 |
| ≥ 1 kitab yang disebut atribusi juga ditemukan pemetaan kita | **1.969 (98,8%)** |
| Semua kitab yang disebut ditemukan | 1.320 (66,2%) |
| Tidak satu pun cocok | 24 |

Kenapa angka "semua kitab" lebih rendah: HadeethEnc mengutip *satu* lafaz, misalnya lafaz Muslim. Riwayat kitab lain yang disebut dalam atribusi sering memakai lafaz berbeda, sehingga skornya di bawah 0,6.

Dari 24 kasus "tidak satu pun", 5 diperiksa manual pada putaran akhir (HE 4244, 8890, 11253, 6982, 2957). **Semuanya isi yang sama**, hanya ditemukan di kitab lain yang juga meriwayatkannya. Contohnya HE 6982 "رواه مسلم في مقدمته": teks Arab muqaddimah Shahih Muslim memang kosong di sumber kita (lihat audit), sehingga yang terpetakan adalah Ibnu Majah 41. Pada putaran tanpa bobot IDF, 6 kasus serupa juga diperiksa dengan hasil yang sama.

### Validasi hadits niat

- **HE 66511** (versi Arba'in an-Nawawi) → **bukhari:1**, Bukhari 54/2529/5070/6689/6953, dan **Muslim 1907a**.
- **HE 4560** ("متفق عليه") → Muslim 1907a dan Bukhari 54/2529/5070/6689/6953, tetapi **tidak** Bukhari 1. Ini benar. HE 4560 menggabungkan lafaz Muslim (بالنية، لامرئ) dengan kalimat "فمن كانت هجرته إلى الله ورسوله…", padahal kalimat itu memang tidak ada di Bukhari no. 1 (riwayat al-Humaidi). Skornya terhadap bukhari:1 hanya 0,55.

## Menjalankan

```bash
python3 -I pipeline/hadeethenc.py unduh --maks-detik 500
```

Perintah unduh boleh diulang sampai muncul "unduhan lengkap". Ia bisa dilanjutkan, sopan (≤ 3 permintaan/detik), dan memakai cache.

```bash
python3 -I pipeline/hadeethenc.py bangun
```

```bash
python3 -m unittest pipeline/test_hadeethenc.py -v
```
