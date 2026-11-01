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

/** Perawi teridentifikasi per posisi segmen sanad: Map(pos -> perawi). perawiJson = riwayat.perawi_json [[pos, id], ...]. */
export async function perawiSanad(db, perawiJson) {
  const pos = JSON.parse(perawiJson || "[]");
  if (!pos.length) return new Map();
  const rows = (await db.prepare(`SELECT id, taqrib, nama, penilaian, tingkat, tabaqah, wafat, wafat_ragu FROM perawi
    WHERE id IN (SELECT value FROM json_each(?1))`).bind(JSON.stringify([...new Set(pos.map(([, id]) => id))])).all()).results;
  const byId = new Map(rows.map((p) => [p.id, p]));
  return new Map(pos.filter(([, id]) => byId.has(id)).map(([p, id]) => [p, { pos: p, ...byId.get(id) }]));
}

export async function dataPerawi(db, id) {
  // Satu baris: guru/murid/riwayat sudah dihitung pipeline (export_d1.py) supaya halaman tidak memindai sanad semua riwayat.
  const p = await db.prepare("SELECT * FROM perawi WHERE id = ?1").bind(id).first();
  if (!p) return null;
  const orang = (j) => JSON.parse(j || "[]").map(([id, nama, tingkat, n]) => ({ id, nama, tingkat, n }));
  return {
    ...p, guru: orang(p.guru_json), murid: orang(p.murid_json),
    riwayat: JSON.parse(p.riwayat_json || "[]").map(([kitab_id, slug, no_tampil]) => ({ kitab_id, slug, no_tampil })),
  };
}

export async function daftarPerawi(db) {
  return (await db.prepare("SELECT id, nama, tingkat, tabaqah, wafat, n_riwayat FROM perawi ORDER BY n_riwayat DESC LIMIT 300").all()).results;
}
