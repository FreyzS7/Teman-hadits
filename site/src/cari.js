// Pencarian lapis 1 (tanpa AI). Port dari pipeline/cari.py; rencana() harus memberi hasil yang sama
// (diuji oleh test/paritas.test.js). Semua hasil berasal dari database dan membawa alasan kemunculannya.
import KAMUS from "../../pipeline/kamus_konsep.json" with { type: "json" };
import { akarAr, normAr, normId } from "./teks.js";

/** Kolom riwayat.nilai_json -> [{penilai, hukum, kategori}] (urut penilai; lihat pipeline/export_d1.py). */
export const nilai = (j) => (j ? JSON.parse(j) : []).map(([penilai, hukum, kategori]) => ({ penilai, hukum, kategori }));

const PENGISI = new Set(KAMUS.pengisi);
const MAKSUD = new Set(KAMUS.kata_maksud);
const VARIAN = new Map();
for (const grup of KAMUS.varian) for (const v of grup) VARIAN.set(v, grup);
const PERTANYAAN_HUKUM = /\b(hukum|hukumnya|halal|haram|boleh|bolehkah|wajib|sunnah|makruh|mubah|membolehkan|melarang|mengharamkan|menghalalkan)\b/;
const KATA_KLAIM = /\b(membolehkan|boleh|halal|menghalalkan|mengharamkan|melarang|wajib)\b/;

// nama kitab yang dikenali untuk rujukan langsung ("muslim 1907", "HR. Tirmidzi no 1647")
export const NAMA_KITAB = [
  [/\briyadh(?:us)? ?(?:sh|s)(?:a|o)lihin\b/, "riyadh"],
  [/\b(?:al ?)?bukhari\b/, "bukhari"], [/\bmuslim\b/, "muslim"], [/\babu ?da(?:w|u)u?d\b/, "abudawud"],
  [/\b(?:at ?)?tirmi(?:dz|dh|z)i\b/, "tirmidzi"], [/\b(?:an ?)?nasa ?i\b/, "nasai"], [/\bibnu? ?majah\b/, "ibnumajah"],
  [/\b(?:imam )?malik\b|\bmuwatha?\b/, "malik"], [/\bahmad\b/, "ahmad"], [/\b(?:ad ?)?darimi\b/, "darimi"],
  [/\b(?:asy ?)?syafi ?i\b/, "syafii"],
];

export function rencana(kueri) {
  const polos = normId(kueri);
  const kata = polos.split(" ").filter(Boolean);
  const dirapikan = kata.map((w) => (VARIAN.get(w) || [w])[0]);
  const konsep = [], sisa = [], dibuang = [], maksud = [];
  for (const w of dirapikan) {
    const k = KAMUS.konsep.find((c) => c.pemicu.includes(w));
    if (k && !konsep.includes(k)) konsep.push(k);
    else if (k) continue;
    else if (PENGISI.has(w) || w.length < 3) dibuang.push(w);
    else if (MAKSUD.has(w)) maksud.push(w);
    else sisa.push(w);
  }
  let rujukan = null;
  for (const [re, id] of NAMA_KITAB) {
    const m = polos.match(new RegExp(re.source + String.raw`\s*(?:no(?:mor)?\s*)?(\d+[a-z]?)\b`));
    if (m) { rujukan = { kitab: id, no: m[1] }; break; }
  }
  return {
    kueri, ejaan: kata.map((a, i) => (a !== dirapikan[i] ? `${a}→${dirapikan[i]}` : null)).filter(Boolean),
    dibuang, konsep, kata: sisa, maksud, rujukan,
    pertanyaanHukum: PERTANYAAN_HUKUM.test(polos),
    klaim: (polos.match(new RegExp(KATA_KLAIM.source, "g")) || []),
  };
}

const varianDari = (w) => VARIAN.get(w) || [w];
const fraseId = (v) => (v.length >= 4 ? `"${v}"*` : `"${v}"`);
const grupFts = (w) => "(" + varianDari(w).map((v) => `terjemah_polos:${fraseId(v)}`).join(" OR ") + ")";
const jsonIds = (xs) => JSON.stringify([...xs]);

/** n -> {kitab_id, tingkat, urut, ku} dari dua baris info (2 baris dibaca, berapa pun jumlah hasilnya). */
async function petaN(db) {
  const info = Object.fromEntries((await db.prepare("SELECT kunci, nilai FROM info WHERE kunci IN ('peta_n', 'bitmap_tingkat_b')").all()).results.map((x) => [x.kunci, x.nilai]));
  const rentang = JSON.parse(info.peta_n || "[]");
  const bit = Uint8Array.from(atob(info.bitmap_tingkat_b || ""), (c) => c.charCodeAt(0));
  return (n) => {
    let lo = 0, hi = rentang.length - 1;
    while (lo <= hi) {
      const m = (lo + hi) >> 1, [kid, a, b] = rentang[m];
      if (n < a) hi = m - 1; else if (n > b) lo = m + 1;
      else return { n, kitab_id: kid, tingkat: (bit[n >> 3] >> (n & 7)) & 1 ? "B" : "A", urut: n, ku: m };
    }
    return null;
  };
}

/**
 * @param {D1Database} db
 * @returns {Promise<{rencana, total, hasil, perKitab, halaman, perHalaman}>}
 */
export async function cari(db, kueri, { halaman = 1, perHalaman = 20, kitab = null, tingkat = null } = {}) {
  const r = rencana(kueri);
  const skor = new Map(), alasan = new Map();
  const tambah = (n, nilai, sebab) => {
    skor.set(n, (skor.get(n) || 0) + nilai);
    if (!alasan.has(n)) alasan.set(n, []);
    const a = alasan.get(n);
    if (!a.includes(sebab)) a.push(sebab);
  };
  const ftsIds = async (match, limit = 2000) =>
    (await db.prepare(`SELECT rowid AS n FROM cari WHERE cari MATCH ?1 ORDER BY rank LIMIT ${limit}`).bind(match).all()).results.map((x) => x.n);

  for (const k of r.konsep) {
    for (const frasa of k.arab) for (const n of await ftsIds(`arab_akar:"${akarAr(normAr(frasa))}"`)) tambah(n, 3, `teks Arab memuat ${frasa}`);
    for (const [kid, bab] of k.bab) {
      // bab dulu (tabel kecil), lalu riwayat lewat indeks (kitab_id, bab_no): versi JOIN dulu memindai semua riwayat kitab
      // itu (diukur: 22.741 baris D1 untuk satu pencarian "sholat tarawih").
      const rs = await db.prepare("SELECT r.n FROM riwayat r WHERE r.kitab_id = ?1 AND r.bab_no IN (SELECT no FROM bab WHERE kitab_id = ?1 AND (nama = ?2 OR nama_en = ?2 OR nama_ar = ?2))").bind(kid, bab).all();
      for (const x of rs.results) tambah(x.n, 3, `masuk kitab/bab "${bab}"`);
    }
    for (const t of k.terjemah) for (const n of await ftsIds(`terjemah_polos:"${normId(t)}"`)) tambah(n, 2, `terjemah memuat "${t}"`);
  }

  let totalKata = 0;
  if (r.kata.length && !r.konsep.length) {
    let mode = "semua kata";
    let match = r.kata.map(grupFts).join(" AND ");
    totalKata = (await db.prepare("SELECT count(*) AS c FROM cari WHERE cari MATCH ?1").bind(match).first()).c;
    if (!totalKata) {
      mode = "sebagian kata";
      match = r.kata.map(grupFts).join(" OR ");
      totalKata = (await db.prepare("SELECT count(*) AS c FROM cari WHERE cari MATCH ?1").bind(match).first()).c;
    }
    const ids = await ftsIds(match, 400);
    ids.forEach((n, i) => tambah(n, 1 + (ids.length - i) / (10 * ids.length), `terjemah memuat ${mode}: ${r.kata.join(", ")}`));
  }

  // judul kitab/bab (Arab & Indonesia) yang memuat kata kunci: "haid" -> riwayat di "Kitab Haid"
  if (r.kata.length && !r.konsep.length) {
    for (const w of r.kata) {
      const match = "judul:(" + varianDari(w).map(fraseId).join(" OR ") + ")";
      for (const n of await ftsIds(match, 400)) tambah(n, 1, `judul kitab/bab memuat "${w}"`);
    }
  }

  // penguat: kata sisa (bila ada konsep) + kata maksud — tidak diwajibkan, hanya menaikkan peringkat
  const penguat = [...(r.konsep.length ? r.kata : []), ...r.maksud];
  if (penguat.length && skor.size) {
    for (const w of penguat) {
      const match = "terjemah_polos:(" + varianDari(w).map(fraseId).join(" OR ") + ")";
      const rs = await db.prepare("SELECT rowid AS n FROM cari WHERE cari MATCH ?1 AND rowid IN (SELECT value FROM json_each(?2))").bind(match, jsonIds(skor.keys())).all();
      for (const x of rs.results) tambah(x.n, 1, `terjemah memuat "${w}"`);
    }
  }

  // metadata untuk mengurutkan & menyaring. Dulu membaca baris riwayat (dan kitab) SETIAP hasil — ribuan baris D1 per
  // pencarian. n sudah urut menurut (urutan kitab, urutan riwayat) dan tiap kitab menempati rentang n bersambung, jadi
  // kitab & urutan diturunkan dari n; tingkat B dari bitmap (info: peta_n, bitmap_tingkat_b; pipeline/export_d1.py).
  const meta = new Map();
  if (skor.size) {
    const peta = await petaN(db);
    for (const n of skor.keys()) { const m = peta(n); if (m) meta.set(n, m); }
  }
  const urut = [...skor.keys()].filter((n) => meta.has(n)).sort((a, b) => {
    const A = meta.get(a), B = meta.get(b);
    return (Math.round(skor.get(b) * 1000) - Math.round(skor.get(a) * 1000)) || ((A.tingkat !== "A") - (B.tingkat !== "A")) || (A.ku - B.ku) || (A.urut - B.urut);
  });
  const perKitab = {};
  for (const n of urut) perKitab[meta.get(n).kitab_id] = (perKitab[meta.get(n).kitab_id] || 0) + 1;
  const tersaring = urut.filter((n) => (!kitab || meta.get(n).kitab_id === kitab) && (!tingkat || meta.get(n).tingkat === tingkat));
  const halamanIni = tersaring.slice((halaman - 1) * perHalaman, halaman * perHalaman);

  let hasil = [];
  if (halamanIni.length) {
    const rs = await db.prepare("SELECT n, id, kitab_id, slug, no_tampil, no_lidwa, tingkat, arab, terjemah, alasan AS catatan, nilai_json FROM riwayat WHERE n IN (SELECT value FROM json_each(?1))").bind(jsonIds(halamanIni)).all();
    const byN = new Map(rs.results.map(({ nilai_json, ...x }) => [x.n, { ...x, penilaian: nilai(nilai_json) }]));
    hasil = halamanIni.map((n) => ({ ...byN.get(n), skor: skor.get(n), alasan: alasan.get(n) }));
  }
  return { rencana: r, total: Math.max(urut.length, totalKata), tampil: tersaring.length, hasil, perKitab, halaman, perHalaman };
}

/** Kata-kata untuk disorot di cuplikan hasil. */
export function kataSorot(r) {
  const out = [];
  for (const k of r.konsep) out.push(...k.terjemah, ...k.pemicu);
  for (const w of [...r.kata, ...r.maksud]) out.push(...varianDari(w));
  return [...new Set(out)];
}
export const akarSorot = (r) => r.konsep.flatMap((k) => k.arab.flatMap((a) => normAr(a).split(" ")));
