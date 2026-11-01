// Perawi: biodata ringkas dari Taqrib at-Tahdzib (Ibnu Hajar) dan identifikasi di sanad (pipeline/perawi.py).
// Hanya identifikasi berlabel 'pasti' yang ada di database: kedua sisi tertambat oleh hubungan guru-murid yang
// dicatat Tahdzib al-Kamal untuk kitab itu.

// 12 tingkatan muqaddimah Taqrib. Padanan Indonesia hanya alat bantu baca; frasa Arab Ibnu Hajar selalu ditampilkan.
export const TINGKAT = {
  1: ["sahabat Nabi ﷺ", "terima"], 2: ["sangat terpercaya", "terima"], 3: ["terpercaya (tsiqah)", "terima"],
  4: ["jujur (shaduq)", "terima"], 5: ["jujur, ada kelemahan", "lemah"], 6: ["maqbul (diterima bila ada penguat)", "lemah"],
  7: ["mastur (keadaannya tidak diketahui)", "lemah"], 8: ["lemah (dha'if)", "lemah"], 9: ["majhul (tidak dikenal)", "lemah"],
  10: ["matruk (ditinggalkan)", "palsu"], 11: ["tertuduh berdusta", "palsu"], 12: ["pendusta / pemalsu", "palsu"],
};

// 12 tabaqah, menurut muqaddimah Taqrib
export const TABAQAH = {
  1: "sahabat", 2: "tabi'in senior (mis. Ibnul Musayyib)", 3: "tabi'in pertengahan (mis. al-Hasan, Ibnu Sirin)",
  4: "tabi'in yang banyak meriwayatkan dari tabi'in senior (mis. az-Zuhri, Qatadah)",
  5: "tabi'in junior, melihat satu-dua sahabat (mis. al-A'masy)", 6: "sezaman dengan tabaqah 5, tidak bertemu sahabat (mis. Ibnu Juraij)",
  7: "atba' tabi'in senior (mis. Malik, ats-Tsauri)", 8: "atba' tabi'in pertengahan (mis. Ibnu 'Uyainah)",
  9: "atba' tabi'in junior (mis. Yazid bin Harun, asy-Syafi'i)", 10: "guru senior para penyusun kitab (mis. Ahmad bin Hanbal)",
  11: "guru pertengahan para penyusun kitab (mis. adz-Dzuhli, al-Bukhari)", 12: "guru junior para penyusun kitab (mis. at-Tirmidzi)",
};

export const RUMUZ = {
  "ع": "keenam kitab", "4": "empat kitab Sunan", "خ": "Shahih al-Bukhari", "خت": "al-Bukhari (mu'allaq)", "بخ": "al-Adab al-Mufrad",
  "عخ": "Khalq Af'al al-'Ibad", "ر": "Juz' al-Qira'ah", "ي": "Raf' al-Yadain", "م": "Shahih Muslim", "مق": "muqaddimah Shahih Muslim",
  "د": "Sunan Abi Dawud", "مد": "al-Marasil (Abu Dawud)", "صد": "Fadha'il al-Anshar", "خد": "an-Nasikh (Abu Dawud)",
  "قد": "al-Qadar (Abu Dawud)", "ف": "at-Tafarrud", "ل": "al-Masa'il", "كد": "Musnad Malik (Abu Dawud)", "ت": "Jami' at-Tirmidzi",
  "تم": "asy-Syama'il", "س": "Sunan an-Nasa'i", "عس": "Musnad 'Ali (an-Nasa'i)", "كن": "Musnad Malik (an-Nasa'i)",
  "سي": "'Amal al-Yaum wa al-Lailah", "ص": "Khasha'ish 'Ali", "ق": "Sunan Ibni Majah", "فق": "at-Tafsir (Ibnu Majah)",
  "تمييز": "disebut hanya untuk membedakan",
};

/** Perawi teridentifikasi per posisi segmen sanad riwayat n: Map(pos -> perawi). */
export async function perawiSanad(db, n) {
  const rows = (await db.prepare(`SELECT sp.pos, p.id, p.taqrib, p.nama, p.penilaian, p.tingkat, p.tabaqah, p.wafat, p.wafat_ragu
    FROM sanad_perawi sp JOIN perawi p ON p.id = sp.perawi_id WHERE sp.n = ?1`).bind(n).all()).results;
  return new Map(rows.map((r) => [r.pos, r]));
}

export async function dataPerawi(db, id) {
  const p = await db.prepare("SELECT * FROM perawi WHERE id = ?1").bind(id).first();
  if (!p) return null;
  const relasi = async (geser) => (await db.prepare(`SELECT q.id, q.nama, q.tingkat, count(*) AS n FROM sanad_perawi a
    JOIN sanad_perawi b ON b.n = a.n AND b.pos = a.pos + ?2 JOIN perawi q ON q.id = b.perawi_id
    WHERE a.perawi_id = ?1 GROUP BY q.id ORDER BY n DESC LIMIT 24`).bind(id, geser).all()).results;
  const [guru, murid, riwayat] = await Promise.all([
    relasi(1), relasi(-1),
    db.prepare(`SELECT r.kitab_id, r.slug, r.no_tampil, k.nama AS kitab_nama FROM sanad_perawi sp JOIN riwayat r ON r.n = sp.n
      JOIN kitab k ON k.id = r.kitab_id WHERE sp.perawi_id = ?1 ORDER BY k.urut, r.urut LIMIT 80`).bind(id).all(),
  ]);
  return { ...p, guru, murid, riwayat: riwayat.results };
}

export async function daftarPerawi(db) {
  return (await db.prepare("SELECT id, nama, tingkat, tabaqah, wafat, n_riwayat FROM perawi ORDER BY n_riwayat DESC LIMIT 300").all()).results;
}
