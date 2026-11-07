-- Catatan kueri pencarian yang tidak menemukan hasil (atau hanya cocok sebagian kata), untuk memperbaiki kamus.
-- Hanya teks kueri yang sudah dinormalkan, tanpa alamat IP atau data lain. Tidak dihapus oleh impor ulang data
-- (build/d1/000-skema.sql hanya menghapus tabel data). Batas 2.000 kueri tercatat per hari (catatan_batas), supaya
-- kuota tulis D1 paket gratis (100.000/hari) tidak bisa dihabiskan oleh bot.
CREATE TABLE IF NOT EXISTS kueri_kosong (kueri TEXT PRIMARY KEY, n INT, jenis TEXT, pertama TEXT, terakhir TEXT) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS catatan_batas (hari TEXT PRIMARY KEY, n INT) WITHOUT ROWID;
