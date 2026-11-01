# Audit Data Teman Hadits

_Dibuat otomatis oleh `pipeline/audit.py` pada 2026-11-01. Jangan disunting manual — jalankan ulang pipeline._

## Ringkasan

- Riwayat dimuat: **67,920**
- Tingkat **A** (teks Arab cocok di 2 sumber digital + terjemah terpasang): **32,578**
- Tingkat **B** (baru 1 sumber digital / belum terpasang terjemahnya): **34,934**
- **Karantina** (tidak ditampilkan): **408**
- Riwayat yang punya ≥1 penilaian derajat bernama: **21,185**

## Per kitab

| Kitab | Baris Lidwa | Nomor standar | A | B | Karantina | Ada penilaian | Penilai |
|---|---:|---:|---:|---:|---:|---:|---|
| Shahih al-Bukhari | 7,008 | 7589 | 7,281 | 299 | 9 | 0 | — |
| Shahih Muslim | 5,362 | 7563 | 6,191 | 1,169 | 203 | 0 | — |
| Sunan Abu Dawud | 4,590 | 5274 | 4,893 | 379 | 2 | 5,274 | Al-Albani, Muhammad Muhyi Al-Din Abdul Hamid, Shuaib Al Arnaut, Zubair Ali Zai |
| Jami' at-Tirmidzi | 3,891 | 3998 | 3,304 | 620 | 74 | 3,954 | Ahmad Muhammad Shakir, Al-Albani, Bashar Awad Maarouf, Zubair Ali Zai |
| Sunan an-Nasa'i | 5,662 | 5765 | 5,469 | 210 | 86 | 5,758 | Abu Ghuddah, Al-Albani, Zubair Ali Zai |
| Sunan Ibnu Majah | 4,332 | 4343 | 4,048 | 290 | 5 | 4,341 | Al-Albani, Muhammad Fouad Abd al-Baqi, Shuaib Al Arnaut, Zubair Ali Zai |
| Al-Muwaththa' (riwayat Yahya al-Laitsi) | 1,594 | 1858 | 1,392 | 437 | 29 | 1,858 | Salim al-Hilali |
| Musnad Ahmad | 26,363 | — | 0 | 26,363 | 0 | 0 | — |
| Sunan ad-Darimi | 3,367 | — | 0 | 3,367 | 0 | 0 | — |
| Musnad asy-Syafi'i | 1,800 | — | 0 | 1,800 | 0 | 0 | — |

## Pencocokan dua sumber (crosswalk)

Teks Arab Lidwa/carihadis dicocokkan dengan teks Arab fawazahmed0 memakai irisan 3-kata (Jaccard) setelah harakat dan variasi hamzah diseragamkan. *1:1* = Jaccard ≥ 0,85. *gabungan* = ≥ 90% teks nomor standar tercakup dalam satu baris Lidwa yang lebih panjang (Lidwa sering menggabungkan beberapa jalur sanad Muslim dalam satu nomor). Kandidat yang posisinya menyimpang > 40 baris dari urutan tetangganya ditolak.

| Kitab | 1:1 | gabungan | tidak cocok | posisi menyimpang | baris Lidwa tak terpakai |
|---|---:|---:|---:|---:|---:|
| bukhari | 6,536 | 745 | 222 | 77 | 202 |
| muslim | 3,061 | 3,130 | 1,112 | 53 | 472 |
| abudawud | 3,583 | 1,310 | 366 | 13 | 281 |
| tirmidzi | 2,827 | 477 | 618 | 2 | 693 |
| nasai | 5,147 | 322 | 207 | 3 | 285 |
| ibnumajah | 3,776 | 272 | 289 | 1 | 294 |
| malik | 1,227 | 165 | 273 | 164 | 224 |

## Perbedaan penilaian antar ulama

Satu hadits bisa dinilai berbeda oleh ulama yang berbeda. Situs menampilkan **semua** penilaian berdampingan dan tidak membuat "nilai akhir" sendiri.

- **abudawud**: 908 riwayat dinilai diterima oleh sebagian ulama dan lemah oleh yang lain. Contoh `abudawud:1005`: Al-Albani — *Daif*; Muhammad Muhyi Al-Din Abdul Hamid — *Daif*; Shuaib Al Arnaut — *Hasan Lighairihi*; Zubair Ali Zai — *Hasan*
- **ibnumajah**: 679 riwayat dinilai diterima oleh sebagian ulama dan lemah oleh yang lain. Contoh `ibnumajah:1002`: Al-Albani — *Hasan Sahih*; Muhammad Fouad Abd al-Baqi — *Hasan Sahih*; Shuaib Al Arnaut — *Hasan*; Zubair Ali Zai — *Daif*
- **tirmidzi**: 580 riwayat dinilai diterima oleh sebagian ulama dan lemah oleh yang lain. Contoh `tirmidzi:1016`: Ahmad Muhammad Shakir — *Sahih*; Al-Albani — *Sahih*; Zubair Ali Zai — *Daif*
- **nasai**: 476 riwayat dinilai diterima oleh sebagian ulama dan lemah oleh yang lain. Contoh `nasai:1022`: Abu Ghuddah — *Daif*; Al-Albani — *Daif*; Zubair Ali Zai — *Isnaad Hasan*

## Pencocokan dengan edisi tahqiq (OpenITI)

Lihat `docs/09-judul-kitab-bab.md`. Tingkat di tabel "Per kitab" di atas adalah tingkat **sebelum** pencocokan ini; untuk Ahmad, Darimi, dan Syafi'i, riwayat yang teksnya ≥ 90% cocok dengan edisi tahqiq naik ke tingkat A saat ekspor ke situs.

| Kitab | Edisi | Terpetakan menurut isi | Cocok ≥ 90% | Urutan naik | Nomor sama | Penilaian muhaqqiq |
|---|---|---:|---:|---:|---:|---:|
| bukhari | — | 7375/7580 | 7143 | 7362/7374 | 7057/7318 | 1 |
| muslim | — | 7298/7360 | 7231 | 7286/7297 | 0/7086 | 0 |
| abudawud | — | 5264/5272 | 5169 | 5262/5263 | 5246/5258 | 0 |
| tirmidzi | — | 3872/3924 | 2875 | 3864/3871 | 3812/3827 | 0 |
| nasai | — | 5672/5679 | 5572 | 5664/5671 | 5637/5654 | 0 |
| ibnumajah | — | 4334/4338 | 3970 | 4331/4333 | 4317/4326 | 0 |
| malik | — | 1827/1829 | 1813 | 1826/1826 | — | 0 |
| ahmad | ar-Risalah (tahqiq Syu'aib al-Arna'uth dkk.) | 25855/26363 | 23247 | 25781/25854 | — | 0 |
| darimi | Dar al-Mughni (tahqiq Husain Salim Asad) | 3267/3367 | 2891 | 3265/3266 | — | 2823 |
| syafii | Ghiras (tahqiq Mahir Yasin al-Fahl) | 1729/1800 | 1164 | 1177/1728 | — | 0 |

## Katalog hadits populer & palsu

Lihat `docs/10-katalog-palsu.md`. Teks entri apa adanya dari OpenITI; kata kunci penilaian dikenali otomatis dan selalu ditampilkan bersama kalimat aslinya.

| Kitab | Penulis | Edisi digital | Entri | Entri dengan kata kunci |
|---|---|---|---:|---:|
| al-Maudhu'at | Ibnul Jauzi (w. 597 H) | عبد الرحمن محمد عثمان — محمد عبد المحسن صاحب المكتبة السلفية بالمدينة المنورة | 707 | 606 |
| al-Maqashid al-Hasanah | as-Sakhawi (w. 902 H) | محمد عثمان الخشت — دار الكتاب العربي - بيروت | 1,358 | 502 |
| al-Asrar al-Marfu'ah | Mulla 'Ali al-Qari (w. 1014 H) | محمد الصباغ — دار الأمانة / مؤسسة الرسالة - بيروت | 737 | 440 |
| Kasyf al-Khafa' | al-'Ajluni (w. 1162 H) | مكتبة القدسي، لصاحبها حسام الدين القدسي - القاهرة | 3,242 | 1,201 |

Ucapan populer berbahasa Indonesia: 20 (daftar **belum ditinjau**); tautan ke judul entri: 35; disebut di pembahasan entri lain: 11; ada di kitab hadits kita: 4; tidak ada: 16.

## Identitas perawi di sanad (enam kitab)

Lihat `docs/11-perawi.md`. Hanya label **pasti** yang tampil di situs.

| Label | Sebutan nama | % |
|---|---:|---:|
| pasti | 96,281 | 57.9% |
| kuat | 39,162 | 23.5% |
| ragu | 18,437 | 11.1% |
| tanpa_kandidat | 12,461 | 7.5% |

Perawi teridentifikasi: 4,315 (4,173 tertaut ke Taqrib). Hubungan guru-murid Tahdzib al-Kamal yang terselesaikan: 100,861 dari 155,709.

## Temuan kualitas data

- **Riyadhus Shalihin** dipecah ulang per hadits oleh `pipeline/riyadh.py` (lihat `docs/08-riyadhus-shalihin.md`): 1896 hadits; terjemah terpasang pasti 1726; terhubung ke sumber 1645; uji silang atribusi an-Nawawi 1613/1642. Berkas versi Arab tahqiq al-Fahl (850 potongan halaman) belum dipakai.
- Penomoran Lidwa **berbeda** dari penomoran standar (mis. Bukhari Lidwa 7.008 vs standar 7.563; Muslim 5.362 vs 7.563). Situs memakai nomor standar sebagai alamat utama dan menampilkan nomor Lidwa sebagai pembanding.
- Teks identik di nomor berbeda **tidak** dianggap rusak: al-Bukhari dan penyusun lain memang mengulang hadits yang sama di bab berbeda. Ditandai sebagai "pengulangan".
- Musnad Ahmad, Sunan ad-Darimi, Musnad asy-Syafi'i baru punya **satu** sumber digital (Lidwa) dan belum ada penilaian derajat per hadits → tingkat B, label "belum ada penilaian tercatat".
- Terjemahan Indonesia di **kedua** sumber berasal dari Lidwa Pusaka (gaya `[nama perawi]` identik). Jadi terjemahan baru diverifikasi oleh satu pihak; kecocokan dua sumber hanya menguji teks Arab dan nomor.
- Lima berkas SQL yang diunggah pemilik proyek identik byte-per-byte (sha256) dengan berkas di repo irsyadulibad/hadits-database commit `db43bda`.

## Sumber terkunci

| Berkas | Commit | sha256 (12 awal) | Ukuran |
|---|---|---|---:|
| `fawazahmed0/ara-abudawud.json` | `df57907` | `216139c5f40a` | 7,345,422 |
| `fawazahmed0/ara-bukhari.json` | `df57907` | `e34a3402889c` | 9,770,083 |
| `fawazahmed0/ara-ibnmajah.json` | `df57907` | `b406e6be8158` | 5,583,102 |
| `fawazahmed0/ara-malik.json` | `df57907` | `088b1f354e11` | 2,150,337 |
| `fawazahmed0/ara-muslim.json` | `df57907` | `194073b24090` | 8,685,140 |
| `fawazahmed0/ara-nasai.json` | `df57907` | `c705983c19bb` | 7,152,291 |
| `fawazahmed0/ara-nawawi.json` | `df57907` | `91f559b90422` | 49,340 |
| `fawazahmed0/ara-qudsi.json` | `df57907` | `8645482e46b9` | 55,258 |
| `fawazahmed0/ara-tirmidhi.json` | `df57907` | `408028cd5632` | 7,120,806 |
| `fawazahmed0/info.json` | `df57907` | `cf1ced267ada` | 10,319,127 |
| `lidwa-carihadis/musnad-ahmad.sql` | `db43bda` | `c9f064415a77` | 42,168,744 |
| `lidwa-carihadis/musnad-syafii.sql` | `db43bda` | `fa4d29b31329` | 2,287,894 |
| `lidwa-carihadis/musnad_darimi.sql` | `db43bda` | `d13f9a5d8de6` | 4,481,920 |
| `lidwa-carihadis/muwatho_malik.sql` | `db43bda` | `6aa9337ee7c8` | 2,106,139 |
| `lidwa-carihadis/riyadhus-shalihin-arab.sql` | `db43bda` | `6d6512216f9c` | 2,060,658 |
| `lidwa-carihadis/riyadhus-shalihin.sql` | `db43bda` | `cc729d406147` | 3,989,948 |
| `lidwa-carihadis/shahih-bukhari.sql` | `db43bda` | `4b8385fcffce` | 14,159,692 |
| `lidwa-carihadis/shahih-muslim.sql` | `db43bda` | `3c9976e0438a` | 12,841,949 |
| `lidwa-carihadis/sunan-abu-daud.sql` | `db43bda` | `29cdfbcdcc06` | 8,928,446 |
| `lidwa-carihadis/sunan-ibnu-majah.sql` | `db43bda` | `b017e6cfe6df` | 6,502,240 |
| `lidwa-carihadis/sunan-nasai.sql` | `db43bda` | `27a38643817e` | 9,041,176 |
| `lidwa-carihadis/sunan-tirmidzi.sql` | `db43bda` | `79c5710963a1` | 9,385,426 |
| `openiti-0200AH/0179MalikIbnAnas.Muwatta.Shamela0001699-ara1.completed` | `599f22f` | `1402840d20bf` | 1,397,896 |
| `openiti-0225AH/0204Shafici.Musnad.Shamela0009615-ara1` | `2cfdc8c` | `a6c164b549d5` | 954,567 |
| `openiti-0250AH/0241IbnHanbal.Musnad.Shamela0025794-ara1.mARkdown` | `0cc00c0` | `00ee0f74327d` | 15,695,392 |
| `openiti-0275AH/0255CabdAllahDarimi.Sunan.Shamela0021795-ara3` | `44e1c36` | `d069cc7479ea` | 2,059,441 |
| `openiti-0275AH/0256Bukhari.Sahih.Shamela0001681-ara1` | `44e1c36` | `16f95173b9ea` | 6,039,255 |
| `openiti-0275AH/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown` | `44e1c36` | `8126f063f535` | 4,933,663 |
| `openiti-0275AH/0273IbnMaja.Sunan.Shamela0001198-ara1` | `44e1c36` | `a8ca42780445` | 2,535,073 |
| `openiti-0275AH/0275AbuDawudSijistani.Sunan.Shamela0001726-ara1` | `44e1c36` | `f153a439d58e` | 3,398,133 |
| `openiti-0300AH/0279Tirmidhi.Sunan.Shamela0007895-ara2` | `01a1544` | `8ac7c1a66705` | 3,826,249 |
| `openiti-0325AH/0303Nasai.SunanSughra.Shamela0000829-ara1` | `089e665` | `be25ffbca47a` | 3,460,338 |
| `openiti-0600AH/0597IbnJawzi.Mawducat.Shamela0000882-ara1` | `ea4bdc6` | `be16979ad3b2` | 2,411,907 |
| `openiti-0750AH/0742Mizzi.TahdhibKamal.Shamela0003722-ara1.mARkdown` | `7c9c84d` | `f4f26e71dd9c` | 24,585,892 |
| `openiti-0875AH/0852IbnHajarCasqalani.TaqribTahdhib.JK000121-ara1.completed` | `5835c18` | `178d493bd150` | 1,899,042 |
| `openiti-0925AH/0902Sakhawi.MaqasidHasana.Shamela0023177-ara1` | `4f0f456` | `76df9ad68656` | 1,503,556 |
| `openiti-1025AH/1014MullaCaliQari.AsrarMarfuca.Shamela0006056-ara1` | `f2aa39a` | `4cbef7e2d5dc` | 503,884 |
| `openiti-1175AH/1162IbnMuammadAbuFidaCajluni.KashfKhafa.Shamela0000856-ara1` | `2c367f7` | `641607994c63` | 2,536,775 |
