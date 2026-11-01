// Teman Hadits — Cloudflare Worker. Semua halaman dirender di server dari database D1.
import { cari, akarSorot, kataSorot, NAMA_KITAB } from "./cari.js";
import { cek } from "./cek.js";
import { hukumTirmidzi, normId, pisahKomentar, pisahSanad, rantaiArab, rubrik } from "./teks.js";
import * as T from "./tampilan.js";

const PER_HALAMAN = 50;
const KEAMANAN = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
};

const html = (body, status = 200) => new Response(body, { status, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=300", ...KEAMANAN } });
const alihkan = (lokasi, status = 302) => new Response(null, { status, headers: { Location: lokasi } });
const halamanKe = (url) => Math.max(1, Math.min(1000, parseInt(url.searchParams.get("h") || "1", 10) || 1));

async function semuaKitab(db) {
  return (await db.prepare("SELECT * FROM kitab ORDER BY urut").all()).results;
}
async function infoDb(db) {
  return Object.fromEntries((await db.prepare("SELECT kunci, nilai FROM info").all()).results.map((x) => [x.kunci, x.nilai]));
}

async function cariRiwayat(db, kid, slug) {
  const r = await db.prepare("SELECT * FROM riwayat WHERE kitab_id = ?1 AND slug = ?2").bind(kid, slug).first();
  if (r) return { r };
  // Muslim lazim dikutip tanpa huruf (1907 → 1907a)
  if (kid === "muslim" && /^\d+$/.test(slug)) {
    const alt = await db.prepare("SELECT slug FROM riwayat WHERE kitab_id = 'muslim' AND slug = ?1").bind(slug + "a").first();
    if (alt) return { alih: `/muslim/${alt.slug}` };
  }
  return {};
}

function susunRantai(r, kitab, pisah) {
  if (!pisah) return null;
  const segs = rantaiArab(pisah.sanad);
  if (segs.length < 2) return null;
  const nama = JSON.parse(r.rantai_json || "[]");
  const gabungan = /menggabungkan/.test(r.alasan || "");
  const nonNabi = segs.filter((s) => !s.nabi);
  const selaras = !gabungan && nama.length === nonNabi.length;
  const adaNabi = segs.some((s) => s.nabi);
  let iNama = 0;
  const naik = segs.map((s, i) => ({
    ...s,
    namaId: s.nabi ? "Rasulullah ﷺ" : selaras ? nama[iNama++] : "",
    peran: s.nabi ? "Nabi" : adaNabi && i === segs.length - 2 ? "sahabat" : "",
  }));
  const simpul = [{ namaId: kitab.penyusun, namaAr: "", peran: "penyusun kitab", penyusun: true }, ...naik].reverse();
  simpul.forEach((s, i) => { if (!s.peran) s.peran = `perawi ke-${i}`; });
  return { simpul, selaras, adaNabi };
}

async function halamanHadits(env, url, kid, slug) {
  const db = env.DB;
  const kitab = await db.prepare("SELECT * FROM kitab WHERE id = ?1").bind(kid).first();
  if (!kitab) return null;
  const { r, alih } = await cariRiwayat(db, kid, slug);
  if (alih) return alihkan(alih, 301);
  if (!r) return html(T.layout({ judul: "Tidak ditemukan · Teman Hadits", noindex: true, isi: T.halamanGalat("Nomor tidak ditemukan", `${T.PENDEK[kid] || kid} no. ${slug} tidak ada di data kami. Penomoran bisa berbeda antar-edisi; coba cari dengan kata kunci.`) }), 404);
  const [pen, jalurA, jalurB, penJalur, tetangga, tema, bab] = await db.batch([
    db.prepare("SELECT penilai, hukum, kategori FROM penilaian WHERE n = ?1 ORDER BY penilai").bind(r.n),
    db.prepare("SELECT m.skor, m.tingkat AS tingkat_mirip, x.n, x.kitab_id, x.slug, x.no_tampil, k.nama AS kitab_nama, k.urut AS ku, x.urut FROM mirip m JOIN riwayat x ON x.n = m.b JOIN kitab k ON k.id = x.kitab_id WHERE m.a = ?1").bind(r.n),
    db.prepare("SELECT m.skor, m.tingkat AS tingkat_mirip, x.n, x.kitab_id, x.slug, x.no_tampil, k.nama AS kitab_nama, k.urut AS ku, x.urut FROM mirip m JOIN riwayat x ON x.n = m.a JOIN kitab k ON k.id = x.kitab_id WHERE m.b = ?1").bind(r.n),
    db.prepare("SELECT n, penilai, hukum, kategori FROM penilaian WHERE n IN (SELECT b FROM mirip WHERE a = ?1 UNION SELECT a FROM mirip WHERE b = ?1) ORDER BY penilai").bind(r.n),
    db.prepare("SELECT slug, no_tampil, urut FROM riwayat WHERE kitab_id = ?1 AND urut IN (?2, ?3)").bind(kid, r.urut - 1, r.urut + 1),
    db.prepare("SELECT DISTINCT t.id, t.judul FROM he_riwayat hr JOIN he_tema ht ON ht.he_id = hr.he_id JOIN tema t ON t.id = ht.tema_id WHERE hr.n = ?1 LIMIT 8").bind(r.n),
    db.prepare("SELECT no, nama FROM bab WHERE kitab_id = ?1 AND no = ?2").bind(kid, r.bab_no ?? -1),
  ]);
  const jalurMap = new Map();
  for (const j of [...jalurA.results, ...jalurB.results]) {
    const ada = jalurMap.get(j.n);
    if (!ada || (ada.tingkat_mirip !== "sama" && j.tingkat_mirip === "sama") || (ada.tingkat_mirip === j.tingkat_mirip && j.skor > ada.skor)) jalurMap.set(j.n, j);
  }
  const jalur = [...jalurMap.values()].sort((a, b) => a.ku - b.ku || a.urut - b.urut);
  const jalurPenilaian = new Map();
  for (const p of penJalur.results) (jalurPenilaian.get(p.n) || jalurPenilaian.set(p.n, []).get(p.n)).push(p);
  const pisah = pisahSanad(r.arab);
  if (pisah && kid === "tirmidzi") Object.assign(pisah, pisahKomentar(pisah.matan));
  const kanonik = `${url.origin}/${kid}/${r.slug}`;
  const isi = T.halamanHadits({
    r, kitab, bab: bab.results[0] || null, penilaian: pen.results, jalur, jalurPenilaian, pisah,
    sanadHtml: pisah ? rubrik(pisah.sanad) : "", rantai: susunRantai(r, kitab, pisah),
    tirmidzi: kid === "tirmidzi" ? hukumTirmidzi(r.arab) : null, tema: tema.results,
    sebelum: tetangga.results.find((x) => x.urut === r.urut - 1), sesudah: tetangga.results.find((x) => x.urut === r.urut + 1), kanonik,
  });
  const desk = (r.terjemah || "").replace(/\[|\]/g, "").replace(/\s+/g, " ").slice(0, 155);
  return html(T.layout({ judul: `${kitab.nama} no. ${r.no_tampil} · Teman Hadits`, deskripsi: desk, isi, kanonik }));
}

async function halamanCari(env, url) {
  const db = env.DB;
  const q = (url.searchParams.get("q") || "").trim().slice(0, 200);
  const kitab = await semuaKitab(db);
  if (!q) return html(T.layout({ judul: "Cari hadits · Teman Hadits", aktif: "cari", isi: T.halamanGalat("Cari hadits", "Ketik kata kunci, tema, atau rujukan seperti “muslim 1907”.") }));
  const filter = { k: url.searchParams.get("k") || "", t: url.searchParams.get("t") || "" };
  if (filter.k && !kitab.some((k) => k.id === filter.k)) filter.k = "";
  if (!["", "A", "B"].includes(filter.t)) filter.t = "";
  const halaman = halamanKe(url);
  const out = await cari(db, q, { halaman, kitab: filter.k || null, tingkat: filter.t || null });
  let rujukan = null;
  if (out.rencana.rujukan) {
    const { kitab: kid, no } = out.rencana.rujukan;
    const { r, alih } = await cariRiwayat(db, kid, no);
    const slug = r ? r.slug : alih ? alih.split("/").pop() : null;
    // kueri yang HANYA berisi rujukan ("muslim 1907", "HR Bukhari no 1") langsung dibuka
    const polos = normId(q).replace(/\b(hr|h r|hadits|hadist|hadis|riwayat|no|nomor)\b/g, " ").replace(/\s+/g, " ").trim();
    const hanyaRujukan = NAMA_KITAB.some(([re]) => new RegExp("^" + re.source + "\\s*\\d+[a-z]?$").test(polos));
    if (slug && hanyaRujukan) return alihkan(`/${kid}/${slug}`);
    if (slug) {
      const x = await db.prepare("SELECT r.kitab_id, r.slug, r.no_tampil, k.nama AS kitab_nama, k.jumlah_standar FROM riwayat r JOIN kitab k ON k.id = r.kitab_id WHERE r.kitab_id = ?1 AND r.slug = ?2").bind(kid, slug).first();
      rujukan = { ...x, catatan: x.jumlah_standar ? "penomoran standar" : "penomoran Lidwa" };
    }
  }
  // Tema HadeethEnc yang judulnya memuat kata kunci — kurasi ulama, ditampilkan di atas hasil.
  // Kata inti (konsep & kata sisa, semua varian ejaan) wajib cocok; kata maksud ("keutamaan") hanya menambah skor.
  const r0 = out.rencana;
  const inti = kataSorot({ ...r0, maksud: [] }).map(normId).filter((w) => w.length >= 4);
  const maksud = r0.maksud.map(normId);
  const memuat = (j, w) => (" " + j + " ").includes(" " + w);
  const tema = inti.length ? (await db.prepare("SELECT id, judul, jumlah FROM tema WHERE jumlah > 0").all()).results
    .map((t) => { const j = normId(t.judul); return { ...t, skor: 2 * inti.filter((w) => memuat(j, w)).length + maksud.filter((w) => memuat(j, w)).length, kena: inti.some((w) => memuat(j, w)) }; })
    .filter((t) => t.kena).sort((a, b) => b.skor - a.skor || b.jumlah - a.jumlah).slice(0, 6) : [];
  const isi = T.hasilCari({ q, out, kitab, sorot: kataSorot(out.rencana), akar: akarSorot(out.rencana), filter, rujukan, tema });
  return html(T.layout({ judul: `${q} · Cari · Teman Hadits`, aktif: "cari", isi, noindex: true }));
}

async function halamanKitab(env, url, kid, babNo) {
  const db = env.DB;
  const k = await db.prepare("SELECT * FROM kitab WHERE id = ?1").bind(kid).first();
  if (!k) return null;
  const halaman = halamanKe(url);
  const kolom = "SELECT r.slug, r.no_tampil, substr(r.terjemah, 1, 300) AS terjemah, r.tingkat, (SELECT count(*) FROM penilaian p WHERE p.n = r.n) AS n_nilai FROM riwayat r";
  if (babNo != null) {
    const b = await db.prepare("SELECT * FROM bab WHERE kitab_id = ?1 AND no = ?2").bind(kid, babNo).first();
    if (!b) return null;
    const daftar = (await db.prepare(`${kolom} WHERE r.kitab_id = ?1 AND r.bab_no = ?2 ORDER BY r.urut LIMIT ${PER_HALAMAN} OFFSET ?3`).bind(kid, babNo, (halaman - 1) * PER_HALAMAN).all()).results;
    return html(T.layout({ judul: `${b.nama || "Bab " + b.no} · ${k.nama} · Teman Hadits`, aktif: "kitab", kanonik: `${url.origin}/kitab/${kid}/bab/${babNo}`, isi: T.halamanBab({ k, b, daftar, halaman, halMaks: Math.ceil(b.jumlah / PER_HALAMAN) }) }));
  }
  const bab = (await db.prepare("SELECT no, nama, jumlah FROM bab WHERE kitab_id = ?1 ORDER BY no").bind(kid).all()).results;
  let daftar = [], halMaks = 1;
  if (!bab.length) {
    daftar = (await db.prepare(`${kolom} WHERE r.kitab_id = ?1 ORDER BY r.urut LIMIT ${PER_HALAMAN} OFFSET ?2`).bind(kid, (halaman - 1) * PER_HALAMAN).all()).results;
    halMaks = Math.ceil(k.terbit / PER_HALAMAN);
  }
  return html(T.layout({ judul: `${k.nama} · Teman Hadits`, aktif: "kitab", kanonik: `${url.origin}/kitab/${kid}`, deskripsi: `${k.nama} karya ${k.penyusun}: ${k.terbit} riwayat dengan teks Arab, terjemah, dan penilaian ulama.`, isi: T.halamanKitab({ k, bab, daftar, halaman, halMaks }) }));
}

async function halamanTema(env, url, id) {
  const db = env.DB;
  const versi = (await db.prepare("SELECT nilai FROM info WHERE kunci = 'hadeethenc_versi'").first())?.nilai;
  const semua = (await db.prepare("SELECT id, judul, induk, jumlah FROM tema ORDER BY CAST(id AS INTEGER)").all()).results;
  const akarIdx = (t) => !t.induk || t.induk === "0";
  if (!id) {
    const anak = {};
    for (const t of semua) if (!akarIdx(t)) (anak[t.induk] ||= []).push(t);
    return html(T.layout({ judul: "Tema · Teman Hadits", aktif: "tema", isi: T.daftarTema({ akar: semua.filter(akarIdx), anak, versi }) }));
  }
  const t = semua.find((x) => x.id === id);
  if (!t) return null;
  const hadits = (await db.prepare("SELECT h.* FROM he_tema ht JOIN he_hadits h ON h.id = ht.he_id WHERE ht.tema_id = ?1 ORDER BY CAST(h.id AS INTEGER) LIMIT 100").bind(id).all()).results;
  const link = (await db.prepare("SELECT hr.he_id, r.kitab_id, r.slug, r.no_tampil FROM he_riwayat hr JOIN riwayat r ON r.n = hr.n JOIN kitab k ON k.id = r.kitab_id WHERE hr.he_id IN (SELECT value FROM json_each(?1)) ORDER BY hr.he_id, k.urut, r.urut").bind(JSON.stringify(hadits.map((h) => h.id))).all()).results;
  const per = {};
  for (const l of link) ((per[l.he_id] ||= []).length < 8) && per[l.he_id].push(l);
  return html(T.layout({ judul: `${t.judul} · Tema · Teman Hadits`, aktif: "tema", isi: T.halamanTema({ t, induk: semua.find((x) => x.id === t.induk), sub: semua.filter((x) => x.induk === t.id), hadits: hadits.map((h) => ({ ...h, riwayat: per[h.id] || [] })), versi }) }));
}

async function sitemap(env, url, kid) {
  const db = env.DB;
  const xml = (s) => new Response(s, { headers: { "Content-Type": "application/xml; charset=utf-8", "Cache-Control": "public, max-age=86400" } });
  if (!kid) {
    const kitab = await semuaKitab(db);
    return xml(`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${kitab.map((k) => `<sitemap><loc>${url.origin}/sitemap-${k.id}.xml</loc></sitemap>`).join("\n")}\n</sitemapindex>`);
  }
  const rows = (await db.prepare("SELECT slug FROM riwayat WHERE kitab_id = ?1 ORDER BY urut").bind(kid).all()).results;
  if (!rows.length) return null;
  return xml(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>${url.origin}/kitab/${kid}</loc></url>\n${rows.map((r) => `<url><loc>${url.origin}/${kid}/${encodeURIComponent(r.slug)}</loc></url>`).join("\n")}\n</urlset>`);
}

async function rute(req, env) {
  const url = new URL(req.url);
  const p = decodeURIComponent(url.pathname).replace(/\/+$/, "") || "/";
  const db = env.DB;
  if (req.method !== "GET" && req.method !== "HEAD") return new Response("Metode tidak didukung", { status: 405 });
  if (p === "/") {
    const [kitab, info] = await Promise.all([semuaKitab(db), infoDb(db)]);
    return html(T.layout({ judul: "Teman Hadits · Pustaka hadits: cari, cek, dan lihat sumbernya", aktif: "beranda", kanonik: url.origin + "/", isi: T.beranda({ kitab, info }) }));
  }
  if (p === "/cari") return halamanCari(env, url);
  if (p === "/cek") {
    const t = (url.searchParams.get("t") || "").trim();
    const [kitab, info] = await Promise.all([semuaKitab(db), infoDb(db)]);
    const hasil = t ? await cek(db, t) : null;
    return html(T.layout({ judul: "Cek hadits · Teman Hadits", aktif: "cek", noindex: Boolean(t), isi: T.halamanCek({ t, hasil, kitab, info }) }));
  }
  if (p === "/metode") return html(T.layout({ judul: "Metode · Teman Hadits", aktif: "metode", isi: T.halamanMetode({ info: await infoDb(db) }) }));
  if (p === "/kitab") return html(T.layout({ judul: "Kitab · Teman Hadits", aktif: "kitab", isi: T.daftarKitab({ kitab: await semuaKitab(db) }) }));
  if (p === "/tema") return halamanTema(env, url, null);
  if (p === "/robots.txt") return new Response(`User-agent: *\nAllow: /\nDisallow: /cari\nDisallow: /cek?\nDisallow: /api/\nSitemap: ${url.origin}/sitemap.xml\n`, { headers: { "Content-Type": "text/plain" } });
  if (p === "/sitemap.xml") return sitemap(env, url, null);
  if (p === "/api/cari") {
    const q = (url.searchParams.get("q") || "").trim().slice(0, 200);
    if (!q) return Response.json({ galat: "parameter q kosong" }, { status: 400 });
    const out = await cari(db, q, { halaman: halamanKe(url) });
    return Response.json({
      rencana: { ...out.rencana, konsep: out.rencana.konsep.map((k) => ({ id: k.id, label: k.label })) }, total: out.total,
      hasil: out.hasil.map((h) => ({ id: h.id, url: `${url.origin}/${h.kitab_id}/${h.slug}`, kitab: h.kitab_id, no: h.no_tampil, tingkat: h.tingkat, alasan: h.alasan, penilaian: h.penilaian.map(({ penilai, hukum }) => ({ penilai, hukum })) })),
    });
  }
  let m;
  if ((m = p.match(/^\/sitemap-([a-z]+)\.xml$/))) return sitemap(env, url, m[1]);
  if ((m = p.match(/^\/kitab\/([a-z]+)$/))) return halamanKitab(env, url, m[1], null);
  if ((m = p.match(/^\/kitab\/([a-z]+)\/bab\/(\d+)$/))) return halamanKitab(env, url, m[1], parseInt(m[2], 10));
  if ((m = p.match(/^\/tema\/(\d+)$/))) return halamanTema(env, url, m[1]);
  if ((m = p.match(/^\/([a-z]+)\/([0-9a-z.\-]+)$/))) return halamanHadits(env, url, m[1], m[2]);
  return null;
}

export default {
  async fetch(req, env) {
    try {
      const res = await rute(req, env);
      if (res) return res;
      return html(T.layout({ judul: "Halaman tidak ditemukan · Teman Hadits", noindex: true, isi: T.halamanGalat("Halaman tidak ditemukan", "Alamat ini tidak ada. Coba cari hadits yang Anda maksud.") }), 404);
    } catch (e) {
      console.error(e && e.stack || e);
      return html(T.layout({ judul: "Terjadi kesalahan · Teman Hadits", noindex: true, isi: T.halamanGalat("Terjadi kesalahan", "Maaf, halaman ini gagal dimuat. Coba lagi sebentar lagi.") }), 500);
    }
  },
};
