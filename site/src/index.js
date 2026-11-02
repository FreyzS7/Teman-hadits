// Teman Hadits — Cloudflare Worker. Semua halaman dirender di server dari database D1.
import { cari, akarSorot, kataSorot, NAMA_KITAB, nilai } from "./cari.js";
import { cek } from "./cek.js";
import { hukumTirmidzi, normId, pisahKomentar, pisahSanad, rantaiArab, rubrik } from "./teks.js";
import * as T from "./tampilan.js";
import { cocokKatalogArab, cocokPopuler, dataPopuler, daftarPopuler, entriKatalog } from "./katalog.js";
import { dataPerawi, daftarPerawi, perawiSanad } from "./perawi.js";
import { adaArab } from "./teks.js";

const PER_HALAMAN = 50;
const KEAMANAN = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
  "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
};

// Cache-Control diisi di fetch() (cache tepi untuk 200; 404 sebentar; galat tidak disimpan)
const html = (body, status = 200) => new Response(body, { status, headers: { "Content-Type": "text/html; charset=utf-8", ...KEAMANAN } });
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

function susunRantai(r, kitab, pisah, perawi = new Map()) {
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
    perawi: s.nabi ? null : perawi.get(i) || null,   // posisi i = nomor segmen yang sama dengan pipeline/perawi.py
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
  // takhrij, penilaian, perawi, dan judul tersimpan di baris riwayat (kolom *_json, judul_id): lihat pipeline/export_d1.py
  const jal = JSON.parse(r.jalur_json || "[]");
  const [anggota, tetangga, tema, bab, dikutip, judul] = await db.batch([
    db.prepare("SELECT x.n, x.kitab_id, x.slug, x.no_tampil, x.urut, x.nilai_json, k.nama AS kitab_nama, k.urut AS ku FROM riwayat x JOIN kitab k ON k.id = x.kitab_id WHERE x.n IN (SELECT value FROM json_each(?1))").bind(JSON.stringify(jal.map(([n]) => n))),
    db.prepare("SELECT slug, no_tampil, urut FROM riwayat WHERE kitab_id = ?1 AND urut IN (?2, ?3)").bind(kid, r.urut - 1, r.urut + 1),
    db.prepare("SELECT DISTINCT t.id, t.judul FROM he_riwayat hr JOIN he_tema ht ON ht.he_id = hr.he_id JOIN tema t ON t.id = ht.tema_id WHERE hr.n = ?1 LIMIT 8").bind(r.n),
    db.prepare("SELECT no, nama FROM bab WHERE kitab_id = ?1 AND no = ?2").bind(kid, r.bab_no ?? -1),
    db.prepare("SELECT x.slug, x.no_tampil FROM sumber s JOIN riwayat x ON x.n = s.a WHERE s.b = ?1 ORDER BY x.urut").bind(r.n),
    db.prepare("SELECT kitab_ar, kitab_nama_id, bab_ar, catatan FROM judul_bab WHERE id = ?1").bind(r.judul_id ?? -1),
  ]);
  const pen = { results: nilai(r.nilai_json) };
  const per = new Map(anggota.results.map((x) => [x.n, x]));
  const jalur = jal.filter(([n]) => per.has(n))
    .map(([n, skor, tingkat_mirip]) => { const { nilai_json, ...x } = per.get(n); return { ...x, skor, tingkat_mirip }; })
    .sort((a, b) => a.ku - b.ku || a.urut - b.urut);
  const jalurPenilaian = new Map();
  for (const x of anggota.results) { const p = nilai(x.nilai_json); if (p.length) jalurPenilaian.set(x.n, p); }
  if (kid === "riyadh") return halamanRiyadh(env, url, kitab, r);
  const pisah = pisahSanad(r.arab);
  if (pisah && kid === "tirmidzi") Object.assign(pisah, pisahKomentar(pisah.matan));
  const perawi = pisah ? await perawiSanad(db, r.perawi_json) : new Map();
  const kanonik = `${url.origin}/${kid}/${r.slug}`;
  const isi = T.halamanHadits({
    r, kitab, bab: bab.results[0] || null, penilaian: pen.results, jalur, jalurPenilaian, pisah,
    sanadHtml: pisah ? rubrik(pisah.sanad) : "", rantai: susunRantai(r, kitab, pisah, perawi),
    tirmidzi: kid === "tirmidzi" ? hukumTirmidzi(r.arab) : null, tema: tema.results,
    sebelum: tetangga.results.find((x) => x.urut === r.urut - 1), sesudah: tetangga.results.find((x) => x.urut === r.urut + 1), kanonik,
    dikutip: dikutip.results, judul: judul.results[0] ? { ...judul.results[0], cara: r.judul_cara } : null,
  });
  const desk = (r.terjemah || "").replace(/\[|\]/g, "").replace(/\s+/g, " ").slice(0, 155);
  return html(T.layout({ judul: `${kitab.nama} no. ${r.no_tampil} · Teman Hadits`, deskripsi: desk, isi, kanonik }));
}

async function halamanRiyadh(env, url, kitab, r) {
  const db = env.DB;
  const [info, sumber, tetangga, tema, bab] = await db.batch([
    db.prepare("SELECT * FROM riyadh_info WHERE n = ?1").bind(r.n),
    db.prepare("SELECT s.skor, s.kitab_disebut, s.sahabat_sama, s.peringkat, x.n, x.kitab_id, x.slug, x.no_tampil, x.nilai_json, k.nama AS kitab_nama FROM sumber s JOIN riwayat x ON x.n = s.b JOIN kitab k ON k.id = x.kitab_id WHERE s.a = ?1 ORDER BY s.peringkat").bind(r.n),
    db.prepare("SELECT slug, no_tampil, urut FROM riwayat WHERE kitab_id = 'riyadh' AND urut IN (?1, ?2)").bind(r.urut - 1, r.urut + 1),
    db.prepare("SELECT DISTINCT t.id, t.judul FROM he_riwayat hr JOIN he_tema ht ON ht.he_id = hr.he_id JOIN tema t ON t.id = ht.tema_id WHERE hr.n IN (SELECT b FROM sumber WHERE a = ?1 AND peringkat <= 3) LIMIT 8").bind(r.n),
    db.prepare("SELECT no, nama, nama_ar FROM bab WHERE kitab_id = 'riyadh' AND no = ?1").bind(r.bab_no ?? -1),
  ]);
  const penilaianSumber = new Map();
  for (const x of sumber.results) { const p = nilai(x.nilai_json); if (p.length) penilaianSumber.set(x.n, p); delete x.nilai_json; }
  const kanonik = `${url.origin}/riyadh/${r.slug}`;
  const isi = T.halamanRiyadh({
    r, kitab, bab: bab.results[0] || null, info: info.results[0] || null, sumber: sumber.results, penilaianSumber, tema: tema.results,
    sebelum: tetangga.results.find((x) => x.urut === r.urut - 1), sesudah: tetangga.results.find((x) => x.urut === r.urut + 1), kanonik,
    sembunyiTerjemah: env.TERJEMAH_RIYADH === "sembunyi",
  });
  const desk = (env.TERJEMAH_RIYADH === "sembunyi" ? "" : (r.terjemah || "")).replace(/\s+/g, " ").slice(0, 155) || `Riyadhus Shalihin no. ${r.no_tampil}: teks Arab, sumber menurut an-Nawawi, dan riwayat sumbernya.`;
  return html(T.layout({ judul: `Riyadhus Shalihin no. ${r.no_tampil} · Teman Hadits`, deskripsi: desk, isi, kanonik }));
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
    const polos = normId(q).replace(/\b(hr|h r|hadits|hadist|hadis|riwayat|no|nomor)\b/g, " ").replace(/\s+/g, " ").trim();
    const hanyaRujukan = NAMA_KITAB.some(([re]) => new RegExp("^" + re.source + "\\s*\\d+[a-z]?$").test(polos));
    const k = await db.prepare("SELECT nama, jumlah_standar, edisi FROM kitab WHERE id = ?1").bind(kid).first();
    let calon = [];
    if (k?.edisi) {
      // Ahmad/Darimi/Syafi'i: nomor bisa berarti penomoran Lidwa ATAU penomoran edisi tahqiq yang lazim dikutip
      // nomor edisi bisa berupa rentang («47–48»: satu riwayat Lidwa = dua hadits edisi), dicari lewat edisi_alias
      calon = (await db.prepare("SELECT slug, no_tampil, no_edisi FROM riwayat WHERE kitab_id = ?1 AND (slug = ?2 OR no_edisi = ?2 "
        + "OR n IN (SELECT n FROM edisi_alias WHERE kitab_id = ?1 AND no = ?2))").bind(kid, no).all()).results
        .map((x) => {
          const edisi = x.no_edisi === no || (x.no_edisi || "").split("–").includes(no);
          return { kitab_id: kid, slug: x.slug, kitab_nama: k.nama, no_tampil: edisi ? x.no_edisi : x.no_tampil,
            catatan: edisi ? `menurut edisi ${k.edisi}${x.slug !== no ? ` (= no. ${x.no_tampil} Lidwa)` : ""}` : `menurut penomoran Lidwa${x.no_edisi ? ` (= no. ${x.no_edisi} edisi tahqiq)` : ""}` };
        });
      calon = [...new Map(calon.map((c) => [c.slug, c])).values()];
    } else {
      const { r, alih } = await cariRiwayat(db, kid, no);
      const slug = r ? r.slug : alih ? alih.split("/").pop() : null;
      if (slug) {
        const x = await db.prepare("SELECT slug, no_tampil FROM riwayat WHERE kitab_id = ?1 AND slug = ?2").bind(kid, slug).first();
        calon = [{ kitab_id: kid, slug: x.slug, kitab_nama: k.nama, no_tampil: x.no_tampil, catatan: k.jumlah_standar ? "penomoran standar" : "penomoran Lidwa" }];
      }
    }
    // kueri yang HANYA berisi rujukan langsung dibuka — kecuali nomornya ambigu antara dua sistem penomoran
    if (calon.length === 1 && hanyaRujukan) return alihkan(`/${kid}/${calon[0].slug}`);
    if (calon.length) rujukan = calon;
  }
  // Tema HadeethEnc yang judulnya memuat kata kunci — kurasi ulama, ditampilkan di atas hasil.
  // Kata inti (konsep & kata sisa, semua varian ejaan) wajib cocok; kata maksud ("keutamaan") hanya menambah skor.
  const r0 = out.rencana;
  const inti = kataSorot({ ...r0, maksud: [] }).map(normId).filter((w) => w.length >= 4);
  const maksud = r0.maksud.map(normId);
  // judul memuat kata w di awal kata: (" " + judul + " ").includes(" " + w); string berspasi dibuat sekali saja
  const intiS = inti.map((w) => " " + w), maksudS = maksud.map((w) => " " + w);
  const tema = inti.length ? (await semuaTema(db)).daftar.filter((t) => t.jumlah > 0)
    .map(({ judul_norm, induk, ...t }) => {
      const j = " " + judul_norm + " ";
      const nInti = intiS.filter((w) => j.includes(w)).length;
      return { ...t, skor: 2 * nInti + maksudS.filter((w) => j.includes(w)).length, kena: nInti > 0 };
    })
    .filter((t) => t.kena).sort((a, b) => b.skor - a.skor || b.jumlah - a.jumlah).slice(0, 6) : [];
  const isi = T.hasilCari({ q, out, kitab, sorot: kataSorot(out.rencana), akar: akarSorot(out.rencana), filter, rujukan, tema, sembunyiRiyadh: env.TERJEMAH_RIYADH === "sembunyi" });
  return html(T.layout({ judul: `${q} · Cari · Teman Hadits`, aktif: "cari", isi, noindex: true }));
}

async function halamanKitab(env, url, kid, babNo) {
  const db = env.DB;
  const k = await db.prepare("SELECT * FROM kitab WHERE id = ?1").bind(kid).first();
  if (!k) return null;
  const halaman = halamanKe(url);
  const kolom = "SELECT r.slug, r.no_tampil, substr(r.terjemah, 1, 300) AS terjemah, r.tingkat, coalesce(json_array_length(r.nilai_json), 0) AS n_nilai FROM riwayat r";
  if (babNo != null) {
    const b = await db.prepare("SELECT * FROM bab WHERE kitab_id = ?1 AND no = ?2").bind(kid, babNo).first();
    if (!b) return null;
    const daftar = (await db.prepare(`${kolom} WHERE r.kitab_id = ?1 AND r.bab_no = ?2 ORDER BY r.urut LIMIT ${PER_HALAMAN} OFFSET ?3`).bind(kid, babNo, (halaman - 1) * PER_HALAMAN).all()).results;
    return html(T.layout({ judul: `${b.nama || "Bab " + b.no} · ${k.nama} · Teman Hadits`, aktif: "kitab", kanonik: `${url.origin}/kitab/${kid}/bab/${babNo}`, isi: T.halamanBab({ k, b, daftar, halaman, halMaks: Math.ceil(b.jumlah / PER_HALAMAN) }) }));
  }
  const bab = (await db.prepare("SELECT no, nama, nama_ar, jumlah FROM bab WHERE kitab_id = ?1 ORDER BY no").bind(kid).all()).results;
  let daftar = [], halMaks = 1;
  if (!bab.length) {
    daftar = (await db.prepare(`${kolom} WHERE r.kitab_id = ?1 ORDER BY r.urut LIMIT ${PER_HALAMAN} OFFSET ?2`).bind(kid, (halaman - 1) * PER_HALAMAN).all()).results;
    halMaks = Math.ceil(k.terbit / PER_HALAMAN);
  }
  return html(T.layout({ judul: `${k.nama} · Teman Hadits`, aktif: "kitab", kanonik: `${url.origin}/kitab/${kid}`, deskripsi: `${k.nama} karya ${k.penyusun}: ${k.terbit} riwayat dengan teks Arab, terjemah, dan penilaian ulama.`, isi: T.halamanKitab({ k, bab, daftar, halaman, halMaks }) }));
}

/** Semua tema HadeethEnc dari SATU baris info (tema_json; pipeline/export_d1.py), urut baris tabel tema. */
async function semuaTema(db) {
  const info = Object.fromEntries((await db.prepare("SELECT kunci, nilai FROM info WHERE kunci IN ('tema_json', 'hadeethenc_versi')").all()).results.map((x) => [x.kunci, x.nilai]));
  const daftar = JSON.parse(info.tema_json || "[]").map(([id, judul, induk, jumlah, judul_norm]) => ({ id, judul, induk, jumlah, judul_norm }));
  return { daftar, versi: info.hadeethenc_versi };
}

async function halamanTema(env, url, id) {
  const db = env.DB;
  const { daftar, versi } = await semuaTema(db);
  const semua = daftar.map(({ judul_norm, ...t }) => t).sort((a, b) => Number(a.id) - Number(b.id));
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
    return xml(`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${kitab.map((k) => `<sitemap><loc>${url.origin}/sitemap-${k.id}.xml</loc></sitemap>`).join("\n")}\n<sitemap><loc>${url.origin}/sitemap-perawi.xml</loc></sitemap>\n</sitemapindex>`);
  }
  if (kid === "perawi") {
    const ids = (await db.prepare("SELECT id FROM perawi ORDER BY n_riwayat DESC").all()).results;
    return xml(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>${url.origin}/perawi</loc></url>\n${ids.map((r) => `<url><loc>${url.origin}/perawi/${r.id}</loc></url>`).join("\n")}\n</urlset>`);
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
    const [kitab, info, populer] = await Promise.all([semuaKitab(db), infoDb(db), daftarPopuler(db)]);
    return html(T.layout({ judul: "Teman Hadits · Pustaka hadits: cari, cek, dan lihat sumbernya", aktif: "beranda", kanonik: url.origin + "/", isi: T.beranda({ kitab, info, populer }) }));
  }
  if (p === "/cari") return halamanCari(env, url);
  if (p === "/cek") {
    const t = (url.searchParams.get("t") || "").trim();
    const [kitab, info] = await Promise.all([semuaKitab(db), infoDb(db)]);
    const hasil = t ? await cek(db, t) : null;
    let katalog = "";
    if (t) {
      // ucapan populer (teks Indonesia) atau entri katalog (teks Arab) -> pembahasan ulama
      const pop = adaArab(t) ? null : await cocokPopuler(db, t);
      if (pop) {
        const p = await dataPopuler(db, pop.id);
        katalog = T.kotakKatalog({ populer: p, entri: p.entri, riwayat: p.riwayat });
      } else if (adaArab(t)) {
        const ids = await cocokKatalogArab(db, t);
        if (ids.length) katalog = T.kotakKatalog({ entri: await entriKatalog(db, ids) });
      }
    }
    return html(T.layout({ judul: "Cek hadits · Teman Hadits", aktif: "cek", noindex: Boolean(t), isi: T.halamanCek({ t, hasil, kitab, info, katalog }) }));
  }
  if (p === "/metode") return html(T.layout({ judul: "Metode · Teman Hadits", aktif: "metode", isi: T.halamanMetode({ info: await infoDb(db) }) }));
  if (p === "/kitab") return html(T.layout({ judul: "Kitab · Teman Hadits", aktif: "kitab", isi: T.daftarKitab({ kitab: await semuaKitab(db) }) }));
  if (p === "/tema") return halamanTema(env, url, null);
  if (p === "/populer") return html(T.layout({ judul: "Sering beredar, benarkah hadits? · Teman Hadits", aktif: "populer", kanonik: url.origin + "/populer", deskripsi: "Ucapan yang sering disebut hadits di masyarakat, dengan pembahasan ulama dari kitab-kitab tentang hadits populer dan palsu.", isi: T.halamanPopulerDaftar({ daftar: await daftarPopuler(db) }) }));
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
  if (p === "/perawi") return html(T.layout({ judul: "Perawi hadits · Teman Hadits", aktif: "perawi", kanonik: url.origin + "/perawi", deskripsi: "Biodata perawi hadits dari Taqrib at-Tahdzib (Ibnu Hajar): penilaian, tabaqah, tahun wafat, guru dan murid.", isi: T.halamanPerawiDaftar({ daftar: await daftarPerawi(db) }) }));
  if ((m = p.match(/^\/perawi\/([tk]\d+)$/))) {
    const pr = await dataPerawi(db, m[1]);
    if (!pr) return html(T.layout({ judul: "Tidak ditemukan · Teman Hadits", noindex: true, isi: T.halamanGalat("Perawi tidak ditemukan", "Perawi ini belum teridentifikasi di sanad mana pun dalam data kami.") }), 404);
    return html(T.layout({ judul: `${pr.nama} · Perawi hadits · Teman Hadits`, aktif: "perawi", kanonik: `${url.origin}/perawi/${pr.id}`, deskripsi: `Biodata ${pr.nama}${pr.penilaian ? `: ${pr.penilaian}` : ""} (Taqrib at-Tahdzib${pr.taqrib ? " no. " + pr.taqrib : ""}).`, isi: T.halamanPerawi({ p: pr }) }));
  }
  if ((m = p.match(/^\/kitab\/([a-z]+)$/))) return halamanKitab(env, url, m[1], null);
  if ((m = p.match(/^\/kitab\/([a-z]+)\/bab\/(\d+)$/))) return halamanKitab(env, url, m[1], parseInt(m[2], 10));
  if ((m = p.match(/^\/tema\/(\d+)$/))) return halamanTema(env, url, m[1]);
  if ((m = p.match(/^\/populer\/([a-z0-9-]+)$/))) {
    const pp = await dataPopuler(db, m[1]);
    if (!pp) return null;
    return html(T.layout({ judul: `“${pp.teks_id}”: benarkah hadits? · Teman Hadits`, aktif: "populer", kanonik: `${url.origin}/populer/${pp.id}`, deskripsi: `Pembahasan ulama tentang ucapan “${pp.teks_id}” (${pp.arab}).`, isi: T.halamanPopuler({ p: pp }) }));
  }
  if ((m = p.match(/^\/([a-z]+)\/([0-9a-z.\-]+)$/))) return halamanHadits(env, url, m[1], m[2]);
  return null;
}

/** Bungkus binding D1 untuk menghitung baris yang dibaca (D1 gratis: 5 juta baris/hari). Hasilnya dikirim di header
 *  X-D1-Baris supaya beban tiap halaman bisa dipantau. Semantik first()/all()/run() tetap sama. */
function hitungD1(db) {
  const hit = { baris: 0, kueri: 0 };
  const catat = (meta) => { hit.kueri++; hit.baris += (meta && meta.rows_read) || 0; };
  const bungkus = (st) => ({
    asli: st,
    bind: (...a) => bungkus(st.bind(...a)),
    all: async () => { const r = await st.all(); catat(r.meta); return r; },
    run: async () => { const r = await st.run(); catat(r.meta); return r; },
    raw: (...a) => st.raw(...a),
    first: async (kol) => {
      const r = await st.all(); catat(r.meta);
      const baris = r.results[0];
      return baris === undefined ? null : kol ? baris[kol] : baris;
    },
  });
  const batch = async (xs) => { const rs = await db.batch(xs.map((x) => x.asli || x)); rs.forEach((r) => catat(r.meta)); return rs; };
  return { db: { prepare: (q) => bungkus(db.prepare(q)), batch }, hit };
}


/** Lama simpan di cache tepi (detik). Halaman data berubah hanya saat data dibangun ulang; kunci cache memuat VERSI_DATA,
 *  jadi impor data baru (dengan VERSI_DATA baru) otomatis memakai cache baru. */
function lamaCache(p) {
  if (p.startsWith("/api/") || p === "/cari" || p === "/cek") return 3600;
  return 86400;
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const bolehCache = req.method === "GET" && typeof caches !== "undefined" && !url.searchParams.has("segar");
    const kunci = bolehCache ? new Request(`${url.origin}${url.pathname}?${url.searchParams.toString()}&__v=${env.VERSI_DATA || "lokal"}`) : null;
    if (bolehCache) {
      const ada = await caches.default.match(kunci);
      if (ada) { const r = new Response(ada.body, ada); r.headers.set("X-Cache", "HIT"); r.headers.set("X-D1-Baris", "0; cache"); return r; }
    }
    const { db, hit } = hitungD1(env.DB);
    env = { ...env, DB: db };
    const beri = (res) => {
      const r = new Response(res.body, res);
      r.headers.set("X-D1-Baris", `${hit.baris}; kueri=${hit.kueri}`);
      for (const [k, v] of Object.entries(KEAMANAN)) if (!r.headers.has(k)) r.headers.set(k, v);
      if (bolehCache && r.status === 200 && !r.headers.has("Cache-Control")) {
        r.headers.set("Cache-Control", `public, max-age=300, s-maxage=${lamaCache(url.pathname)}`);
        r.headers.set("X-Cache", "MISS");
        const simpan = r.clone();
        const tugas = caches.default.put(kunci, simpan).catch(() => {});
        if (ctx && ctx.waitUntil) ctx.waitUntil(tugas);
      } else if (!r.headers.has("Cache-Control")) {
        r.headers.set("Cache-Control", r.status === 404 ? "public, max-age=60" : r.status >= 500 ? "no-store" : "public, max-age=300");
      }
      return r;
    };
    try {
      const res = await rute(req, env);
      if (res) return beri(res);
      return beri(html(T.layout({ judul: "Halaman tidak ditemukan · Teman Hadits", noindex: true, isi: T.halamanGalat("Halaman tidak ditemukan", "Alamat ini tidak ada. Coba cari hadits yang Anda maksud.") }), 404));
    } catch (e) {
      console.error(e && e.stack || e);
      return beri(html(T.layout({ judul: "Terjadi kesalahan · Teman Hadits", noindex: true, isi: T.halamanGalat("Terjadi kesalahan", "Maaf, halaman ini gagal dimuat. Coba lagi sebentar lagi.") }), 500));
    }
  },
};
