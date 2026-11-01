// Katalog ucapan populer & "hadits" palsu: menghubungkan teks yang beredar ke pembahasan ulama di kitab klasik
// (al-Maqashid al-Hasanah, Kasyf al-Khafa', al-Asrar al-Marfu'ah, al-Maudhu'at). Situs tidak membuat vonis:
// yang ditampilkan adalah teks ulama dan kata kunci penilaian yang muncul di dalamnya.
import { akarAr, normAr, normId, stemAr, stemId } from "./teks.js";

const STOP = new Set(("yang dan itu ini dengan akan ia dia ke di dari pada untuk apa adalah bahwa atau juga tidak orang dalam " +
  "hr hadits hadis sabda nabi rasulullah saw shallallahu alaihi wasallam kalian kamu engkau mu nya").split(" "));
const tokenId = (t) => new Set(normId(t).split(" ").filter((w) => w.length >= 3 && !STOP.has(w)).map(stemId));

/** Cocokkan teks Indonesia ke daftar ucapan populer. Kembalikan {id, skor} terbaik atau null. */
export async function cocokPopuler(db, teks) {
  const Q = tokenId(teks);
  if (Q.size < 2) return null;
  const rows = (await db.prepare("SELECT id, teks_id, varian FROM populer").all()).results;
  let terbaik = null;
  for (const r of rows) {
    for (const v of [r.teks_id, ...JSON.parse(r.varian || "[]")]) {
      const V = tokenId(v);
      const sama = [...V].filter((w) => Q.has(w)).length;
      const skor = sama / Math.max(1, V.size);
      if (sama >= 2 && skor >= 0.6 && (!terbaik || skor > terbaik.skor)) terbaik = { id: r.id, skor };
    }
  }
  return terbaik;
}

/** Sama dengan s.split(/\s+/).slice(0, n).join(" "), tanpa memecah seluruh teks (entri katalog bisa ribuan huruf). */
function awalKata(s, n) {
  const re = /\s+/g;
  for (let m, k = 0; (m = re.exec(s));) if (++k === n) return s.slice(0, m.index).split(/\s+/).join(" ");
  return s.split(/\s+/).join(" ");
}

/** Cari entri katalog untuk teks Arab (judul entri harus memuat >= 75% 2-gram teks). */
export async function cocokKatalogArab(db, teks) {
  const kata = akarAr(normAr(teks)).split(" ").filter((w) => w.length >= 2);
  if (kata.length < 2) return [];
  const g = new Set(kata.slice(0, -1).map((w, i) => w + " " + kata[i + 1]));
  const match = "judul:(" + [...new Set(kata)].filter((w) => w.length >= 3).slice(0, 12).map((w) => `"${w}"`).join(" OR ") + ")";
  const cand = (await db.prepare("SELECT k.k, k.id, k.kitab_id, k.no, k.judul_ar, k.teks_ar FROM katalog k WHERE k.k IN (SELECT rowid FROM katalog_cari WHERE katalog_cari MATCH ?1 ORDER BY rank LIMIT 60)").bind(match).all()).results;
  const out = [];
  for (const c of cand) {
    const kepala = akarAr(normAr(c.judul_ar + " " + awalKata(c.teks_ar.replace(/^حديث\s*:?\s*/, ""), 10))).split(" ");
    const gk = new Set(kepala.slice(0, -1).map((w, i) => w + " " + kepala[i + 1]));
    const skor = [...g].filter((x) => gk.has(x)).length / g.size;
    if (skor >= 0.75) out.push({ id: c.id, skor });
  }
  return out.sort((a, b) => b.skor - a.skor).slice(0, 6).map((x) => x.id);
}

/** Data lengkap entri-entri katalog (dengan nama kitab & penulis). */
export async function entriKatalog(db, ids) {
  if (!ids.length) return [];
  const rows = (await db.prepare(`SELECT k.id, k.kitab_id, k.no, k.judul_ar, k.teks_ar, k.kata_kunci, b.nama AS kitab_nama, b.nama_ar AS kitab_nama_ar, b.penulis, b.wafat, b.edisi
    FROM katalog k JOIN katalog_kitab b ON b.id = k.kitab_id WHERE k.id IN (SELECT value FROM json_each(?1))`).bind(JSON.stringify(ids)).all()).results;
  const urut = { maqashid: 1, kasyf: 2, asrar: 3, maudhuat: 4 };
  return rows.map((r) => ({ ...r, kata_kunci: JSON.parse(r.kata_kunci || "[]") })).sort((a, b) => (urut[a.kitab_id] - urut[b.kitab_id]) || (a.no - b.no));
}

/** Ucapan populer + entri katalog + riwayat di kitab hadits kita. */
export async function dataPopuler(db, id) {
  const p = await db.prepare("SELECT * FROM populer WHERE id = ?1").bind(id).first();
  if (!p) return null;
  const ids = (await db.prepare("SELECT katalog_id FROM populer_katalog WHERE populer_id = ?1").bind(id).all()).results.map((x) => x.katalog_id);
  const riwayat = (await db.prepare(`SELECT r.kitab_id, r.slug, r.no_tampil, r.tingkat, k.nama AS kitab_nama, k.urut AS ku FROM populer_riwayat pr
    JOIN riwayat r ON r.n = pr.n JOIN kitab k ON k.id = r.kitab_id WHERE pr.populer_id = ?1 ORDER BY k.urut, r.urut`).bind(id).all()).results;
  // lafaz yang hanya DISEBUT di pembahasan entri lain: tanpa kata kunci (penilaian entri itu tentang ucapan lain)
  const sebut = (await db.prepare(`SELECT s.katalog_id AS id, s.kutipan, k.no, k.judul_ar, k.kitab_id, b.nama AS kitab_nama, b.penulis FROM populer_sebut s
    JOIN katalog k ON k.id = s.katalog_id JOIN katalog_kitab b ON b.id = k.kitab_id WHERE s.populer_id = ?1 ORDER BY b.wafat, k.no`).bind(id).all()).results;
  return { ...p, varian: JSON.parse(p.varian || "[]"), entri: await entriKatalog(db, ids), riwayat, sebut };
}

export async function daftarPopuler(db) {
  const rows = (await db.prepare("SELECT * FROM populer ORDER BY urut").all()).results;
  const kk = (await db.prepare("SELECT pk.populer_id, k.kitab_id, k.kata_kunci FROM populer_katalog pk JOIN katalog k ON k.id = pk.katalog_id").all()).results;
  const rw = (await db.prepare("SELECT populer_id, count(*) AS n FROM populer_riwayat GROUP BY populer_id").all()).results;
  const nRiwayat = Object.fromEntries(rw.map((x) => [x.populer_id, x.n]));
  const per = {};
  for (const x of kk) {
    const o = (per[x.populer_id] ||= { kitab: new Set(), kunci: [] });
    o.kitab.add(x.kitab_id);
    for (const [, g, , kelas] of JSON.parse(x.kata_kunci || "[]")) if (!o.kunci.some(([h]) => h === g)) o.kunci.push([g, kelas]);
  }
  // ringkasan: pernyataan paling tegas dulu (palsu, lemah, netral, terima)
  const berat = { palsu: 0, lemah: 1, lain: 2, terima: 3 };
  const urutKunci = (k) => k.sort((a, b) => (berat[a[1]] ?? 2) - (berat[b[1]] ?? 2));
  return rows.map((r) => ({ ...r, kitab: [...(per[r.id]?.kitab || [])], kunci: urutKunci(per[r.id]?.kunci || []), riwayat: nRiwayat[r.id] || 0 }));
}

export { stemAr };
