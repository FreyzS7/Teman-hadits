# Identitas & Biodata Perawi

Tujuannya agar setiap nama di rantai sanad bisa dibuka biodatanya: siapa dia, kapan wafat, generasi (tabaqah) ke berapa, dan bagaimana Ibnu Hajar menilainya. Syaratnya, **identitasnya harus pasti**. Nama yang belum pasti tetap tampil apa adanya, tanpa biodata.

Skrip:
- `pipeline/rijal.py` → `build/rijal.sqlite` (mengurai kitab rijal)
- `pipeline/perawi.py` → `build/perawi.sqlite` (identifikasi di sanad)
- `pipeline/uji_perawi_ifta.py` (uji independen)

Uji: `pipeline/test_rijal.py` (13 uji), 3 uji HTTP, dan uji paritas pemisah sanad Python↔JS.

## Sumber (OpenITI, commit terkunci)

| Kitab | Edisi digital | Dipakai untuk |
|---|---|---|
| *Taqrib at-Tahdzib*, Ibnu Hajar (w. 852 H) | tahqiq Muhammad 'Awwamah, Dar ar-Rasyid. Nomor entri = nomor standar yang dikutip peneliti | Ringkasan biodata yang **ditampilkan**: penilaian, tabaqah, tahun wafat, kode kitab |
| *Tahdzib al-Kamal*, al-Mizzi (w. 742 H) | tahqiq Basyar 'Awwad Ma'ruf, ar-Risalah | **Bukti identifikasi**: daftar guru (روى عن) dan murid (روى عنه) tiap perawi enam kitab, dengan kode kitab untuk setiap hubungan |

Hasil penguraian:
- **Taqrib:** 8.824 entri, termasuk bagian perempuan.
  - Tabaqah dikenali: 8.473.
  - Tingkat penilaian dikenali: 8.236.
  - Tahun wafat dikenali: 2.327.
- **Tahdzib al-Kamal:** 8.643 biografi dan 155.709 hubungan guru-murid.

### Kaidah dari muqaddimah Ibnu Hajar yang diterapkan

- **Abad wafat.** "مات سنة إحدى وعشرين" tidak menyebut abad. Ibnu Hajar menetapkan aturannya sendiri: tabaqah 1–2 berarti sebelum 100 H, tabaqah 3–8 sesudah 100 H, tabaqah 9–12 sesudah 200 H. Contoh: Adam bin Abi Iyas (tabaqah 9) wafat 221 H.
- **Puluhan bersama.** Dalam "مات سنة سبع وقيل ثمان وقيل تسع وخمسين", puluhan berlaku untuk semua pendapat. Abu Hurairah wafat 57 H, dan situs menandainya "ada pendapat lain". Situs memakai pendapat **pertama** Ibnu Hajar.
- **12 tingkatan penilaian**, diambil dari muqaddimah. Frasa Arabnya selalu ditampilkan; padanan Indonesia hanya alat bantu baca.
- **Kode kitab.** Ibnu Hajar hanya menulis kode kitab utama bila perawi ada di salah satu dari enam kitab.

## Cara identifikasi (تمييز المهمل)

Nama "سفيان" bisa berarti Sufyan bin 'Uyainah atau Sufyan ats-Tsauri. Ahli hadits membedakannya dari **siapa murid dan gurunya** di rantai itu. `perawi.py` melakukan hal yang sama:

1. **Model nama** (`pipeline/nama.py`). Nama Arab diurai menjadi:
   - ism dan rantai nasab (بن/بنت), dengan leluhur boleh dilompati ("أحمد بن عمرو بن السرح");
   - kunyah ("أبو بكر بن أبي شيبة" = kunyah + nama keluarga);
   - nisbah/laqab (kata ber-ال);
   - rujukan leluhur ("ابن عمر", "ابن شهاب");
   - "مولى X" sebagai pembeda;
   - gelar "أم المؤمنين" sebagai pembeda ('A'isyah Ummul Mukminin bukan 'A'isyah bint Thalhah).
2. **Kandidat.** Entri yang namanya cocok **dan** kode kitabnya memuat kitab hadits ini. Contohnya, perawi di sanad al-Bukhari harus berkode خ atau ع.
3. **Bukti tiap pasangan murid→guru:**
   - **2** bila hubungan itu tercatat di daftar guru/murid *dengan* kode kitab ini;
   - **1** bila tercatat tanpa kode;
   - **0** bila tidak tercatat.

   Ada penalti bila tabaqah guru jauh lebih muda dari muridnya. Penulis kitab ditulis singkat di daftar murid ("البخاري", "مسلم", ...) dan ikut dihitung.
4. **Rujukan relatif.** "عن أبيه" / "حدثني أبي" = ayah perawi sebelumnya, diambil dari nasabnya. Hubungannya tetap harus tercatat di daftar guru. "جده" belum ditangani, karena "عمرو بن شعيب عن أبيه عن جده" memang diperselisihkan.
5. **Keputusan.** Max-marginal sepanjang rantai (Viterbi maju-mundur).
   - **pasti**: satu kandidat unggul ≥ 1 poin bukti atas semua kandidat lain, **dan** kedua sisinya tertambat hubungan bernilai 2. Pada sahabat sebelum Nabi ﷺ, cukup sisi muridnya.
   - **kuat**: unggul, tetapi hanya satu sisi tertambat.
   - **ragu** / tanpa kandidat: tidak diputuskan.
   - Situs hanya menampilkan **pasti**.
6. **Taqrib ↔ Tahdzib al-Kamal** dipetakan menurut urutan abjad kedua kitab. Caranya: jangkar nama+kode, subbarisan naik terpanjang, jangkar kuat tetap dipakai walau urutannya sedikit beda, lalu celah diisi. Hasilnya 7.524 pasangan. Setiap perawi punya **dua varian nama** (TK dan Taqrib), sehingga kesalahan ketik di satu teks tertambal oleh teks lain (lihat di bawah).

## Hasil

Dari 166.341 sebutan nama di sanad enam kitab:

| Label | Jumlah | % |
|---|---:|---:|
| pasti | 96.281 | 57,9% |
| kuat | 39.162 | 23,5% |
| ragu | 18.437 | 11,1% |
| tanpa kandidat | 12.461 | 7,5% |

- 4.315 perawi teridentifikasi; 4.173 di antaranya punya entri Taqrib.
- Bukhari no. 1 teridentifikasi utuh: al-Humaidi, Sufyan bin 'Uyainah, Yahya bin Sa'id al-Anshari, Muhammad bin Ibrahim at-Taimi, 'Alqamah bin Waqqash, 'Umar.

### Uji independen terhadap Ifta' Sunnah

Pembandingnya adalah data **Ifta' Sunnah** (sunna.alifta.gov.sa, Program Raja Abdullah untuk Sunnah Nabawiyah). Di data itu, setiap posisi rantai enam kitab sudah ditetapkan ke satu perawi oleh kurator mereka, lalu ditautkan ke nomor Taqrib oleh proyek `marwangalaly14/Isnad`. Data ini **hanya dipakai untuk mengukur**: tidak dipakai membangun situs dan tidak diterbitkan ulang, karena lisensinya belum jelas. Skrip `uji_perawi_ifta.py` mengunduhnya ke `build/ifta/`.

| | Dibandingkan | Sama | Kesepakatan |
|---|---:|---:|---:|
| **pasti** | 45.772 | 45.704 | **99,85%** |
| kuat | 15.769 | 15.607 | 98,97% |

Cara banding:
- hanya hadits yang teksnya cocok (2-gram ≥ 0,5);
- posisi dipasangkan bila nama di sanad cocok dengan entri Taqrib pilihan Ifta' dan urutannya paling dekat.

Dari pemeriksaan manual atas sampel 68 ketidaksepakatan "pasti":
- **Data pembanding yang keliru.** Contoh: Fadhalah bin 'Ubaid dipetakan ke Taqrib 8342, padahal 5395. "سفيان" sesudah Abu Ahmad az-Zubairi adalah ats-Tsauri.
- **Kasus yang memang diperselisihkan.** Contoh: "عبد الرحمن بن يزيد" dari Abu Usamah. Abu Usamah menyebutnya Ibnu Jabir, tetapi al-Bukhari dan Abu Dawud menjelaskan bahwa ia sebenarnya Ibnu Tamim, dan hasil kita Ibnu Tamim.
- **Kesalahan kita yang tersisa**, mis. "ابن عباس" yang tertukar dengan cucu al-'Abbas.

### Kesalahan yang ditemukan dan diperbaiki selama pengembangan

| Masalah | Akibat | Perbaikan |
|---|---|---|
| "علي" (nama) dianggap "على" (huruf jar) oleh pemisah sanad **situs** | Nama "عمرو بن علي" terpotong; segmen yang diawali "علي بن ..." hilang (2.140 segmen) | Bedakan dari tulisan berharakat: "على" (alif maqshurah) vs "علي". Python & JS, diuji paritas |
| Kepala biografi TK menyebut orang lain ("وأمه ... أخت أم سلمة", "شريك ابن جريج") | 'Abdullah bin Zam'ah dikira "Ummu Salamah" | Nama hanya dari potongan nama, bukan dari keterangan kerabat/guru |
| "ومولاه عبد الله بن عمر" di daftar guru Nafi' | Hubungan Nafi'→Ibnu 'Umar hilang | Kata hubungan (مولاه, خالته, أبيه, ...) dilepas |
| "كُرَيْبًا" (tanwin manshub) | Tidak dikenali sebagai "كريب" | Alif tanwin dibuang |
| Kode tergabung ("دس", "مدت") dan "مق" (muqaddimah Muslim) | Kode al-Humaidi terbaca sebagai nama → ia hilang dari kandidat | Pemecah kode |
| **Teks digital TK**: "عبيد الله بن عتبة بن مسعود **الباهلي**" | Seharusnya "عبيد الله بن عبد الله بن عتبة بن مسعود الهذلي"; Ibnu 'Utbah kalah dari Ibnu Abi Tsaur | Varian nama dari Taqrib menambal |
| "أبو زرعة عن أبي إدريس" (entri tanpa nama di Taqrib) | Abu Idris al-Khaulani dipetakan ke entri itu | Potong di "عن" |
| "يحيى بن بكير" (dinisbahkan ke kakek) | Tidak ada kandidat | Varian tanpa ayah, **hanya** bila Taqrib menulis "ينسب إلى جده" |

## Di situs

- **Rantai sanad di halaman hadits.** Di bawah setiap nama yang pasti tampil:
  - frasa penilaian Ibnu Hajar (Arab) dan padanan tingkatnya;
  - tabaqah dan tahun wafat;
  - tautan "biodata →".
  Nama yang belum pasti tidak diberi biodata.
- **`/perawi/:id`** (`t2451` = Taqrib no. 2451; `k…` bila tidak ada di Taqrib):
  - teks lengkap Taqrib beserta nomornya;
  - penilaian, arti tabaqah, wafat beserta penjelasan kaidah abad;
  - kitab-kitab tempat riwayatnya ada;
  - guru dan murid **di rantai kami**;
  - daftar riwayat.
- **`/perawi`**: 300 perawi dengan riwayat terbanyak. Ada juga `sitemap-perawi.xml`.

## Yang belum

- Kitab di luar enam kitab (Malik, Ahmad, ad-Darimi, asy-Syafi'i, Riyadhus Shalihin) belum diidentifikasi, karena Tahdzib al-Kamal tidak memberi kode hubungan untuk kitab-kitab itu.
- Perawi yang meriwayatkan bersamaan ("حدثنا قتيبة وابن رمح"), jalur tahwil (ح), "جده", dan "رجل/فلان" belum ditangani.
- Label "kuat" (98,97%) belum ditampilkan; bisa ditinjau satu per satu.
- Penilaian ulama lain (jarh wa ta'dil lengkap dari Tahdzib at-Tahdzib) belum dimuat; yang tampil hanya ringkasan Ibnu Hajar.
- Lisensi OpenITI: CC BY-NC-SA 4.0 (lihat `docs/02-sumber-dan-lisensi.md`).
