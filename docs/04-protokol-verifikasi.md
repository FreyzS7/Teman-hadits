# Protokol Verifikasi

Tujuannya: siapa pun, selain pembuat situs, harus bisa memeriksa bahwa data di Teman Hadits benar.

## 1. Uji emas otomatis (`pipeline/test_golden.py`), jalan setiap build

Isinya fakta yang bisa dicek di kitab cetak, dengan rujukan di komentar tiap tes:

- Ada di tempat yang benar: Bukhari no. 1 (hadits niat, beserta sanad lengkapnya), Muslim no. 1907, Bukhari no. 2236 (haram jual khamr, bangkai, babi, berhala).
- Takhrij: hadits niat harus ditemukan di **ketujuh** tempatnya dalam Shahih al-Bukhari (1, 54, 2529, 3898, 5070, 6689, 6953). Tidak boleh kurang, tidak boleh lebih.
- Tidak ada: hadits niat tidak ada di al-Muwaththa' riwayat Yahya. "Tuntutlah ilmu walau ke negeri Cina" dan "Cinta tanah air sebagian dari iman" tidak ada di kitab mana pun yang dimuat.
- Integritas: jumlah baris cocok dengan README sumber; tidak ada riwayat terbit tanpa teks Arab; tidak ada penilaian tanpa nama penilai; tidak ada penilaian yang dikarang untuk Bukhari/Muslim.

Rencananya tes ini terus ditambah, termasuk dari laporan kesalahan pengguna. Setiap kesalahan yang ditemukan menjadi tes baru.

## 2. Perbandingan dua sumber (otomatis, setiap build)

Teks Arab Lidwa dibandingkan dengan teks Arab fawazahmed0. Hasilnya, termasuk berapa yang tidak cocok dan berapa yang posisinya menyimpang, dilaporkan di `docs/01-audit-data.md`. Yang tidak cocok tidak naik ke tingkat A.

## 3. Pencocokan sampel dengan kitab cetak (manual, berkala)

1. Ambil sampel acak bertingkat: 50 riwayat per kitab, dipilih dengan seed yang dicatat agar bisa diulang.
2. Untuk tiap riwayat, cocokkan dengan scan edisi cetak (mis. Bukhari terbitan Dar Thauq an-Najah, Muslim tahqiq Fu'ad 'Abdul Baqi, Darimi tahqiq Husain Salim Asad): nomor, teks Arab, dan nama perawi di sanad.
3. Catat hasilnya di `docs/sampel/<tanggal>.csv` dengan kolom: id, halaman cetak, cocok/tidak, catatan.
4. Laporkan tingkat galat per kitab. Bila galat suatu kitab > 2%, kitab itu turun ke tingkat B sampai diperbaiki.

## 4. Peninjau independen

Minta 1–2 orang yang belajar ilmu hadits (mahasiswa/dosen Ilmu Hadits UIN, LIPIA, atau pesantren hadits) memeriksa sampel dari langkah 3 **tanpa** melihat hasil pemeriksaan kita lebih dulu. Selisih antara dua pemeriksa menunjukkan bagian yang perlu ditinjau ulang.

Contoh hal yang hanya bisa dinilai peninjau manusia: Sunan Abu Dawud no. 3489 «مَنْ بَاعَ الْخَمْرَ فَلْيُشَقِّصِ الْخَنَازِيرَ» diterjemahkan Lidwa sebagai "…hendaknya ia *menghalalkan* babi". Terjemahan seperti ini bisa disalahpahami bila dibaca tanpa teks Arabnya. (Keempat penilai di sumber kita menilai hadits ini dha'if.)

## 5. Publik

- Data dan pipeline terbuka di repo ini, jadi orang lain bisa membangun ulang dan membandingkan hasilnya.
- Setiap halaman hadits punya tombol "Laporkan kesalahan". Setiap perbaikan tercatat di riwayat git.
