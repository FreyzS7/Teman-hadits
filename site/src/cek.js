// Cek teks yang beredar: apakah teks ini ada di kitab-kitab kita, dan apakah klaim "HR. …" di belakangnya benar.
// Prinsip: kata kunci khas harus ADA. Bila satu saja tidak muncul di terjemahan mana pun, jawabannya
// "tidak ditemukan" dan kata itu disebutkan. Tidak ada tebakan.
import { akarAr, adaArab, liputanJendela, normAr, normId, stemAr, stemId } from "./teks.js";
import { NAMA_KITAB, nilai, varianDari } from "./cari.js";

const STOP = new Set(("yang dan itu ini dengan akan ia dia ke di dari pada untuk apa sesuai seseorang sesungguhnya kepada kami " +
  "telah adalah bahwa atau juga tidak orang dalam saya beliau bersabda berkata hr bukhari muslim sampai shallallahu alaihi " +
  "wasallam rasulullah nabi saw radhiyallahu anhu anha ra allah swt").split(" "));
const AMBANG_ID = 0.75;
const URUT_KITAB = ["bukhari", "muslim", "abudawud", "tirmidzi", "nasai", "ibnumajah", "malik", "ahmad", "darimi", "syafii", "riyadh"];
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

/** |G ∩ duaGram(teksNorm)| tanpa membangun himpunan 2-gram teks (kandidat bisa ratusan kata). */
function samaDuaGram(G, teksNorm) {
  const kanan = new Map();
  for (const g of G) {
    const [a, b] = g.split(" ");
    if (!kanan.has(a)) kanan.set(a, new Set());
    kanan.get(a).add(b);
  }
  const sudah = new Set();
  let sebelum = null;
  for (const w of teksNorm.split(" ")) {
    if (!w) continue;
    const k = stemAr(w);
    if (sebelum !== null && kanan.get(sebelum)?.has(k)) sudah.add(sebelum + " " + k);
    sebelum = k;
  }
  return sudah.size;
}

export async function cek(db, teks) {
  const masukan = String(teks ?? "").slice(0, 2000);
  const klaim = bacaKlaim(masukan);
  const isi = tanpaKlaim(masukan);
  const total = (await db.prepare("SELECT nilai FROM info WHERE kunci = 'terbit'").first())?.nilai;
  const hasil = { teks: masukan, klaim, total: Number(total), mode: adaArab(isi) ? "arab" : "indonesia" };

  let terbaik = null, skorTerbaik = 0;
  if (hasil.mode === "indonesia") {
    // Setiap kata kueri = satu grup ejaan dari kamus (sholat/shalat/salat, shodaqoh/sedekah, dzalim/zhalim, ...):
    // teks yang beredar sering memakai ejaan lain dari terjemah Lidwa. Kata dianggap ada bila salah satu ejaannya ada.
    const mentah = [...new Set(normId(isi).split(" ").filter((w) => w.length >= 3 && !STOP.has(w)))];
    const grupKata = new Map(); // kunci grup (ejaan pertama, di-stem) -> ejaan-ejaannya (di-stem)
    for (const w of mentah) {
      const g = [...new Set(varianDari(w).concat(varianDari(stemId(w)).length > 1 ? varianDari(stemId(w)) : []).map(stemId))];
      const v = g.length > 1 ? g : [stemId(w)];
      if (!grupKata.has(v[0])) grupKata.set(v[0], v);
    }
    const kunciDari = new Map([...grupKata].flatMap(([k, vs]) => vs.map((v) => [v, k])));
    const Q = [...kunciDari.keys()];
    if (!Q.length) return { ...hasil, status: "kosong" };
    const dfV = new Map((await db.prepare("SELECT kata, n FROM kata_df WHERE kata IN (SELECT value FROM json_each(?1))").bind(JSON.stringify(Q)).all()).results.map((x) => [x.kata, x.n]));
    const df = new Map([...grupKata].map(([k, vs]) => [k, vs.reduce((a, v) => a + (dfV.get(v) || 0), 0)]));
    hasil.langkah = [...grupKata].map(([k, vs]) => ({ kata: vs.length > 1 ? vs.join("/") : k, muncul: df.get(k) }));
    hasil.absen = [...grupKata.keys()].filter((k) => !df.get(k)).map((k) => (grupKata.get(k).length > 1 ? grupKata.get(k).join("/") : k));
    if (hasil.absen.length) return { ...hasil, status: "tidak-ditemukan" };
    const N = hasil.total || 60000;
    const idf = new Map([...df].map(([k, n]) => [k, Math.log(N / (1 + n))]));
    const tot = [...idf.values()].reduce((a, b) => a + b, 0);
    const match = "terjemah_polos:(" + Q.filter((w) => dfV.get(w)).map((w) => (w.length >= 4 ? `"${w}"*` : `"${w}"`)).join(" OR ") + ")";
    const cand = (await db.prepare("SELECT r.n, r.kitab_id, r.terjemah FROM riwayat r WHERE r.n IN (SELECT rowid FROM cari WHERE cari MATCH ?1 ORDER BY rank LIMIT 120)").bind(match).all()).results;
    // kata kueri harus muncul BERSAMA dalam satu potongan teks (jendela), bukan tersebar di riwayat panjang:
    // "surga di bawah telapak kaki ibu" dulu cocok 100% dengan Abu Dawud 726 (tata cara meletakkan tangan dalam
    // shalat) karena kelima katanya ada di tempat yang berjauhan.
    // Seri (mis. dua riwayat sama-sama memuat "paling baik akhlaknya"): yang katanya lebih rapat, lalu urutan kitab
    // (Bukhari, Muslim, Sunan, al-Muwaththa', Ahmad, ...), bukan urutan kebetulan dari indeks.
    const jendela = 3 * Q.length + 6;
    const urutKitab = (k) => { const i = URUT_KITAB.indexOf(k); return i < 0 ? 99 : i; };
    let rentangTerbaik = Infinity, kitabTerbaik = 99;
    for (const c of cand) {
      const { skor, rentang } = liputanJendela(c.terjemah, Q, idf, jendela, kunciDari);
      const s = skor / tot, uk = urutKitab(c.kitab_id);
      const seri = Math.abs(s - skorTerbaik) <= 1e-9;
      // selisih jarak <= 2 kata (mis. "agama itu adalah nasihat" vs "agama adalah nasihat") dianggap setara
      const rapat = rentang + 2 < rentangTerbaik, setara = Math.abs(rentang - rentangTerbaik) <= 2;
      const lebih = s > skorTerbaik + 1e-9 || (seri && (rapat || (setara && (uk < kitabTerbaik || (uk === kitabTerbaik && c.n < terbaik)))));
      if (s > 0 && lebih) { skorTerbaik = s; terbaik = c.n; rentangTerbaik = rentang; kitabTerbaik = uk; }
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
      const s = samaDuaGram(G, normAr(c.arab)) / G.size;
      if (s > skorTerbaik) { skorTerbaik = s; terbaik = c.n; }
    }
    hasil.skor = Math.round(skorTerbaik * 100) / 100;
    hasil.langkah = kata.map((w) => ({ kata: w, muncul: null }));
    if (skorTerbaik < AMBANG_AR) return { ...hasil, status: "tidak-ditemukan", alasan: "tidak ada teks Arab yang cukup mirip" };
  }

  // perluas ke keluarga riwayat (takhrij) dari hasil terbaik
  // jalur takhrij (kedua arah) tersimpan di baris riwayat terbaik: riwayat.jalur_json
  const jr = await db.prepare("SELECT jalur_json FROM riwayat WHERE n = ?1").bind(terbaik).first();
  const jal = new Map(JSON.parse(jr?.jalur_json || "[]").map(([n, , tingkat]) => [n, tingkat]));
  const kel = (await db.prepare(
    `SELECT r.n, r.kitab_id, r.slug, r.no_tampil, r.tingkat, r.nilai_json, k.nama AS kitab_nama, k.urut AS ku, r.urut
     FROM riwayat r JOIN kitab k ON k.id = r.kitab_id
     WHERE r.n = ?1 OR r.n IN (SELECT value FROM json_each(?2))
        OR r.n IN (SELECT b FROM sumber WHERE a = ?1 AND peringkat <= 12) OR r.n IN (SELECT a FROM sumber WHERE b = ?1)
     ORDER BY k.urut, r.urut`).bind(terbaik, JSON.stringify([...jal.keys()])).all()).results;
  const keluarga = kel.map(({ nilai_json, ...x }) => ({
    ...x, hubungan: x.n === terbaik ? "terbaik" : jal.get(x.n) ?? null, penilaian: nilai(nilai_json) }));
  const adaDi = new Set(keluarga.map((x) => x.kitab_id));
  return {
    ...hasil, status: "ditemukan", terbaik, keluarga,
    klaimHasil: klaim.map((k) => ({ kitab: k, ada: adaDi.has(k), nomor: keluarga.filter((x) => x.kitab_id === k).map((x) => x.no_tampil) })),
  };
}
