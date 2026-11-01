// Cek teks yang beredar: apakah teks ini ada di kitab-kitab kita, dan apakah klaim "HR. …" di belakangnya benar.
// Prinsip: kata kunci khas harus ADA. Bila satu saja tidak muncul di terjemahan mana pun, jawabannya
// "tidak ditemukan" dan kata itu disebutkan. Tidak ada tebakan.
import { akarAr, adaArab, normAr, normId, stemAr, stemId } from "./teks.js";
import { NAMA_KITAB } from "./cari.js";

const STOP = new Set(("yang dan itu ini dengan akan ia dia ke di dari pada untuk apa sesuai seseorang sesungguhnya kepada kami " +
  "telah adalah bahwa atau juga tidak orang dalam saya beliau bersabda berkata hr bukhari muslim sampai shallallahu alaihi " +
  "wasallam rasulullah nabi saw radhiyallahu anhu anha ra allah swt").split(" "));
const AMBANG_ID = 0.75;
const AMBANG_AR = 0.5;

export function bacaKlaim(teks) {
  const polos = normId(teks);
  const kitab = new Set();
  if (/\bmuttafaq(?:un)? ?(?:alaih|alaihi)\b/.test(polos)) { kitab.add("bukhari"); kitab.add("muslim"); }
  const m = polos.match(/\b(?:hr|h r|diriwayatkan oleh|riwayat)\b(.*)$/);
  if (m) for (const [re, id] of NAMA_KITAB) if (re.test(m[1])) kitab.add(id);
  return [...kitab];
}

const tanpaKlaim = (t) => t.replace(/\((?:[^()]*\b(?:HR|H\.R|riwayat|muttafaq)[^()]*)\)/gi, " ").replace(/\b(?:HR|H\.R)\.?\s.*$/i, " ");

function duaGram(teksNorm) {
  const w = teksNorm.split(" ").filter(Boolean).map(stemAr);
  const s = new Set();
  for (let i = 0; i < w.length - 1; i++) s.add(w[i] + " " + w[i + 1]);
  return s;
}

export async function cek(db, teks) {
  const masukan = String(teks ?? "").slice(0, 2000);
  const klaim = bacaKlaim(masukan);
  const isi = tanpaKlaim(masukan);
  const total = (await db.prepare("SELECT nilai FROM info WHERE kunci = 'terbit'").first())?.nilai;
  const hasil = { teks: masukan, klaim, total: Number(total), mode: adaArab(isi) ? "arab" : "indonesia" };

  let terbaik = null, skorTerbaik = 0;
  if (hasil.mode === "indonesia") {
    const Q = [...new Set(normId(isi).split(" ").filter((w) => w.length >= 3 && !STOP.has(w)).map(stemId))];
    if (!Q.length) return { ...hasil, status: "kosong" };
    const df = new Map((await db.prepare("SELECT kata, n FROM kata_df WHERE kata IN (SELECT value FROM json_each(?1))").bind(JSON.stringify(Q)).all()).results.map((x) => [x.kata, x.n]));
    hasil.langkah = Q.map((w) => ({ kata: w, muncul: df.get(w) || 0 }));
    hasil.absen = Q.filter((w) => !df.get(w));
    if (hasil.absen.length) return { ...hasil, status: "tidak-ditemukan" };
    const N = hasil.total || 60000;
    const idf = new Map(Q.map((w) => [w, Math.log(N / (1 + df.get(w)))]));
    const tot = [...idf.values()].reduce((a, b) => a + b, 0);
    const match = "terjemah_polos:(" + Q.map((w) => (w.length >= 4 ? `"${w}"*` : `"${w}"`)).join(" OR ") + ")";
    const cand = (await db.prepare("SELECT r.n, r.terjemah FROM riwayat r WHERE r.n IN (SELECT rowid FROM cari WHERE cari MATCH ?1 ORDER BY rank LIMIT 120)").bind(match).all()).results;
    for (const c of cand) {
      const kata = new Set(normId(c.terjemah).split(" ").map(stemId));
      const s = Q.reduce((a, w) => a + ([...kata].some((k) => k === w || k.startsWith(w)) ? idf.get(w) : 0), 0) / tot;
      if (s > skorTerbaik) { skorTerbaik = s; terbaik = c.n; }
    }
    hasil.skor = Math.round(skorTerbaik * 100) / 100;
    if (skorTerbaik < AMBANG_ID) return { ...hasil, status: "tidak-ditemukan", alasan: "kata-katanya ada, tetapi tidak muncul bersama dalam satu riwayat" };
  } else {
    const norm = normAr(isi);
    const G = duaGram(norm);
    if (G.size < 3) return { ...hasil, status: "kosong" };
    const kata = [...new Set(akarAr(norm).split(" "))].filter((w) => w.length >= 3).sort((a, b) => b.length - a.length).slice(0, 14);
    const match = "arab_akar:(" + kata.map((w) => `"${w}"`).join(" OR ") + ")";
    const cand = (await db.prepare("SELECT r.n, r.arab FROM riwayat r WHERE r.n IN (SELECT rowid FROM cari WHERE cari MATCH ?1 ORDER BY rank LIMIT 80)").bind(match).all()).results;
    for (const c of cand) {
      const D = duaGram(normAr(c.arab));
      let sama = 0;
      for (const g of G) if (D.has(g)) sama++;
      const s = sama / G.size;
      if (s > skorTerbaik) { skorTerbaik = s; terbaik = c.n; }
    }
    hasil.skor = Math.round(skorTerbaik * 100) / 100;
    hasil.langkah = kata.map((w) => ({ kata: w, muncul: null }));
    if (skorTerbaik < AMBANG_AR) return { ...hasil, status: "tidak-ditemukan", alasan: "tidak ada teks Arab yang cukup mirip" };
  }

  // perluas ke keluarga riwayat (takhrij) dari hasil terbaik
  const kel = (await db.prepare(
    `SELECT r.n, r.kitab_id, r.slug, r.no_tampil, r.tingkat, k.nama AS kitab_nama, k.urut AS ku, r.urut,
            CASE WHEN r.n = ?1 THEN 'terbaik' ELSE m.tingkat END AS hubungan
     FROM riwayat r JOIN kitab k ON k.id = r.kitab_id LEFT JOIN mirip m ON m.a = ?1 AND m.b = r.n
     WHERE r.n = ?1 OR r.n IN (SELECT b FROM mirip WHERE a = ?1)
     ORDER BY k.urut, r.urut`).bind(terbaik).all()).results;
  const pen = (await db.prepare("SELECT n, penilai, hukum, kategori FROM penilaian WHERE n IN (SELECT value FROM json_each(?1)) ORDER BY penilai").bind(JSON.stringify(kel.map((x) => x.n))).all()).results;
  const byN = new Map(kel.map((x) => [x.n, { ...x, penilaian: [] }]));
  for (const p of pen) byN.get(p.n)?.penilaian.push(p);
  const keluarga = [...byN.values()];
  const adaDi = new Set(keluarga.map((x) => x.kitab_id));
  return {
    ...hasil, status: "ditemukan", terbaik, keluarga,
    klaimHasil: klaim.map((k) => ({ kitab: k, ada: adaDi.has(k), nomor: keluarga.filter((x) => x.kitab_id === k).map((x) => x.no_tampil) })),
  };
}
