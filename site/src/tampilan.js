// Template HTML. Semua teks dari database melewati esc() kecuali yang sudah dibangun aman (rubrik, cuplik).
import { cuplik, cuplikAr, esc, fmt, normAr, SIGHAH_MAP } from "./teks.js";
import { RUMUZ, TABAQAH, TINGKAT } from "./perawi.js";

const HR = { riyadh: "an-Nawawi, Riyadhus Shalihin", bukhari: "al-Bukhari", muslim: "Muslim", abudawud: "Abu Dawud", tirmidzi: "at-Tirmidzi", nasai: "an-Nasa'i", ibnumajah: "Ibnu Majah", malik: "Malik (al-Muwaththa')", ahmad: "Ahmad", darimi: "ad-Darimi", syafii: "asy-Syafi'i" };
export const PENDEK = { riyadh: "Riyadhus Shalihin", bukhari: "Bukhari", muslim: "Muslim", abudawud: "Abu Dawud", tirmidzi: "Tirmidzi", nasai: "Nasa'i", ibnumajah: "Ibnu Majah", malik: "Malik", ahmad: "Ahmad", darimi: "Darimi", syafii: "Syafi'i" };
const KITAB_SHAHIH = new Set(["bukhari", "muslim"]);
const PENILAI = {
  "Al-Albani": "al-Albani", "Shuaib Al Arnaut": "Syu'aib al-Arna'uth", "Zubair Ali Zai": "Zubair 'Ali Za'i",
  "Muhammad Muhyi Al-Din Abdul Hamid": "Muhyiddin 'Abdul Hamid", "Ahmad Muhammad Shakir": "Ahmad Syakir",
  "Bashar Awad Maarouf": "Basyar 'Awwad Ma'ruf", "Abu Ghuddah": "Abu Ghuddah", "Salim al-Hilali": "Salim al-Hilali",
  "Muhammad Fouad Abd al-Baqi": "Fu'ad 'Abdul Baqi",
};
// Alih aksara istilah derajat ke ejaan Indonesia. Label asli tetap ada di atribut title.
const ISTILAH = [[/\bSahih\b/g, "Shahih"], [/\bDaif\b/g, "Dha'if"], [/\bIsnaa?d\b/g, "Sanadnya"], [/\bLighairihi\b/gi, "li ghairihi"],
  [/\bAgreed Upon\b/g, "Muttafaq 'alaih"], [/\bMaudu'?\b/g, "Maudhu'"], [/\bMawdu'?\b/g, "Maudhu'"], [/\bJayyid\b/g, "Jayyid"]];
export const namaPenilai = (p) => PENILAI[p] || p;
export const hukumTampil = (h) => ISTILAH.reduce((s, [re, ganti]) => s.replace(re, ganti), String(h));

export const lencana = (t) => `<span class="tk tk-${esc(t)}" title="${t === "A" ? "Teks Arab cocok di 2 sumber digital" : t === "B" ? "Baru 1 sumber digital" : "Karantina"}">${t === "K" ? "karantina" : "tingkat " + esc(t)}</span>`;

export function bukuBesar(pen, kitab, tambahan = []) {
  const baris = [...tambahan, ...(pen || []).map((p) => ({ siapa: namaPenilai(p.penilai), hukum: hukumTampil(p.hukum), asli: p.hukum, kategori: p.kategori }))];
  if (!baris.length) {
    return KITAB_SHAHIH.has(kitab)
      ? `<p class="tanpa-nilai">Kitab Shahih. Sumber data kami tidak memuat penilaian per hadits untuk kitab ini, dan kami tidak mengisinya sendiri.</p>`
      : `<p class="tanpa-nilai">Belum ada penilaian ulama yang tercatat di sumber kami.</p>`;
  }
  return `<ul class="buku-besar">${baris.map((b) => /[\u0600-\u06FF]/.test(b.hukum)
    ? `<li class="k-${esc(b.kategori)} arab"><span class="siapa">${esc(b.siapa)}</span><span class="hukum ar">${esc(b.hukum)}</span></li>`
    : `<li class="k-${esc(b.kategori)}"><span class="siapa">${esc(b.siapa)}</span><span class="titik"></span><span class="hukum"${b.asli ? ` title="label asli: ${esc(b.asli)}"` : ""}>${esc(b.hukum)}</span></li>`).join("")}</ul>`;
}

const SVG_BINTANG = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0l2.6 6.3L21 3l-3.3 6.4L24 12l-6.3 2.6L21 21l-6.4-3.3L12 24l-2.6-6.3L3 21l3.3-6.4L0 12l6.3-2.6L3 3l6.4 3.3z"/></svg>`;

export function layout({ judul, deskripsi, isi, aktif = "", kanonik = "", noindex = false }) {
  const nav = [["/", "Beranda", "beranda"], ["/cari", "Cari", "cari"], ["/cek", "Cek Hadits", "cek"], ["/kitab", "Kitab", "kitab"], ["/tema", "Tema", "tema"], ["/populer", "Populer", "populer"], ["/perawi", "Perawi", "perawi"], ["/metode", "Metode", "metode"]];
  return `<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(judul)}</title>
<meta name="description" content="${esc(deskripsi || "Pustaka hadits berbahasa Indonesia: cari hadits, cek teks yang beredar, lihat sanad dan penilaian ulama beserta sumbernya.")}">
${kanonik ? `<link rel="canonical" href="${esc(kanonik)}">` : ""}${noindex ? '<meta name="robots" content="noindex">' : ""}
<link rel="icon" href="/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0E3F2F">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,500;0,700;0,800;1,400&family=Alegreya+Sans:wght@400;500;700&family=Alegreya+Sans+SC:wght@500;700&family=Amiri:wght@400;700&display=swap">
<link rel="stylesheet" href="/assets/th.css">
<script src="/assets/th.js"></script>
</head>
<body>
<header class="kepala">
  <div class="wrap">
    <a class="merek" href="/" aria-label="Teman Hadits, ke beranda"><img src="/assets/emblem.webp" alt="" width="46" height="38"><span><b>Teman Hadits</b><small>cek dulu sumbernya, baru sebarkan</small></span></a>
    <nav class="nav" aria-label="Utama">${nav.map(([h, t, k]) => `<a href="${h}"${k === aktif ? ' aria-current="page"' : ""}>${t}</a>`).join("")}</nav>
    <div class="alat">
      <button id="btn-harakat" class="ar-btn" aria-pressed="true" title="Tampilkan / sembunyikan harakat">حَـ</button>
      <button id="btn-kecil" title="Perkecil teks Arab" aria-label="Perkecil teks Arab">A−</button>
      <button id="btn-besar" title="Perbesar teks Arab" aria-label="Perbesar teks Arab">A+</button>
      <button id="btn-tema" title="Ganti tema terang/gelap" aria-label="Ganti tema terang atau gelap"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg></button>
    </div>
  </div>
</header>
<main class="wrap">${isi}</main>
<footer class="kaki"><div class="wrap">
  <p><b>Teman Hadits</b> adalah layanan umum tanpa iklan. Teks Arab: fawazahmed0/hadith-api dan Lidwa Pusaka; judul kitab &amp; bab serta kitab katalog hadits palsu: OpenITI (<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>). Terjemahan: Lidwa Pusaka (digunakan dengan izin), via carihadis.com. Penilaian derajat selalu disertai nama ulama penilainya.</p>
  <p>Teman Hadits menampilkan riwayat, bukan fatwa. Untuk hukum suatu perkara, tanyakan kepada ulama yang Anda percaya. <a href="/metode">Cara kami menjaga kebenaran data</a> · <a href="/metode#sumber">Sumber dan lisensi</a>.</p>
</div></footer>
</body>
</html>`;
}

// ------------------------------------------------------------------------------------------------
// BERANDA
// ------------------------------------------------------------------------------------------------
export function beranda({ kitab, info, populer = [] }) {
  const terbit = Number(info.terbit);
  const maks = Math.max(...kitab.map((k) => k.terbit));
  const rak = kitab.map((k) => {
    const pen = JSON.parse(k.penilai || "[]");
    const w = Math.round(34 + 60 * Math.sqrt(k.terbit / maks));
    return `<a class="punggung" style="--w:${w}px" href="/kitab/${esc(k.id)}" title="${esc(k.nama)}: ${fmt(k.terbit)} riwayat${pen.length ? ", " + pen.length + " ulama penilai" : ""}"><span class="pita-emas">${pen.map(() => "<i></i>").join("")}</span><span class="judul">${esc(PENDEK[k.id] || k.nama)}</span></a>`;
  }).join("");
  const contoh = [
    ["/cari?q=" + encodeURIComponent("tolong carikan hadits tentang sholat tarawih"), "tolong carikan hadits tentang sholat tarawih"],
    ["/cari?q=" + encodeURIComponent("apakah makan babi itu hukumnya haram?"), "apakah makan babi itu hukumnya haram?"],
    ["/cari?q=" + encodeURIComponent("muslim 1907"), "muslim 1907"],
    ["/cek?t=" + encodeURIComponent("Sesungguhnya amalan itu tergantung niatnya dan seseorang akan mendapatkan sesuai dengan apa yang ia niatkan (HR. Bukhari dan Muslim)"), "“Sesungguhnya amalan itu tergantung niatnya…” (HR. Bukhari dan Muslim)"],
  ];
  const ket = {
    A: "Teks Arab cocok di dua sumber digital berbeda dan terjemahannya terpasang pada teks yang sama.",
    B: "Baru ada di satu sumber digital, atau belum menemukan pasangan terjemahan yang pasti. Tetap tampil, dengan label.",
    K: "Data kosong, terpotong, atau tersimpan per bab/halaman. Tidak tampil sampai diperbaiki.",
  };
  const angka = { A: info.tingkat_a, B: info.tingkat_b, K: info.karantina };
  return `
  <div class="pembuka">
    <img class="logo" src="/assets/logo.webp" alt="Logo Teman Hadits" width="300" height="274">
    <div>
      <h1>Sebelum dibagikan, <em>cek dulu sumbernya.</em></h1>
      <p class="lead">Ketik kata kunci, tema, atau tempel teks hadits yang beredar. Teman Hadits menunjukkan kitab, nomor, rantai sanad, dan penilaian para ulama, lengkap dengan sumbernya. Bila tidak ditemukan, kami katakan tidak ditemukan.</p>
    </div>
  </div>
  <div class="mihrab">
    <svg class="lengkung" viewBox="0 0 1000 64" preserveAspectRatio="none" aria-hidden="true"><path d="M0 64 V44 C150 44 330 40 420 22 C455 15 480 8 500 0 C520 8 545 15 580 22 C670 40 850 44 1000 44 V64"/></svg>
    <div class="mihrab-isi">
      <div class="mode"><a class="tombol-mode aktif" href="/cari" aria-current="page">Cari kata atau tema</a><a class="tombol-mode" href="/cek">Cek teks yang beredar</a></div>
      <form class="kolom-cari" action="/cari" method="get" role="search">
        <label class="sembunyi" for="q-beranda">Kata kunci</label>
        <input id="q-beranda" name="q" type="search" placeholder="mis. sholat tarawih, keutamaan sedekah, muslim 1907" autocomplete="off" required>
        <button class="tombol" type="submit">Cari</button>
      </form>
      <div class="contoh"><span class="label">contoh</span>${contoh.map(([h, t]) => `<a href="${h}">${esc(t)}</a>`).join("")}</div>
      <p class="cakupan">Mencari di <b>${kitab.length} kitab</b> · <b>${fmt(terbit)}</b> riwayat · teks Arab dan terjemah Indonesia.</p>
    </div>
  </div>
  ${bagianPopulerBeranda(populer)}
  <section class="bagian" aria-labelledby="h-rak">
    <header><h2 id="h-rak">Rak kitab</h2><p>Lebar punggung = banyaknya riwayat. Pita emas = jumlah ulama penilai yang datanya sudah kami miliki untuk kitab itu. Ketuk untuk membuka.</p></header>
    <div class="rak">${rak}</div>
    <div class="legenda"><span><i></i> 1 pita = 1 ulama penilai</span></div>
  </section>
  <section class="bagian" aria-labelledby="h-tingkat">
    <header><h2 id="h-tingkat">Seberapa yakin kami pada datanya</h2><p>Tingkat menilai <b>data digitalnya</b>, bukan derajat haditsnya. Derajat hadits selalu ditulis atas nama ulama yang menilainya.</p></header>
    <div class="tingkat-grid">${["A", "B", "K"].map((t) => `<div>${lencana(t)}<b>${fmt(angka[t])}</b><p>${ket[t]}</p></div>`).join("")}</div>
  </section>`;
}

// ------------------------------------------------------------------------------------------------
// HASIL CARI
// ------------------------------------------------------------------------------------------------
export function hasilCari({ q, out, kitab, sorot, akar, filter, rujukan, tema = [], sembunyiRiyadh = false }) {
  const r = out.rencana;
  const urlDengan = (ubah) => {
    const p = new URLSearchParams({ q, ...filter, ...ubah });
    for (const [k, v] of [...p]) if (!v) p.delete(k);
    if (p.get("h") === "1") p.delete("h");
    return "/cari?" + p.toString();
  };
  const bacaan = `<div class="rencana">
    <div class="baris"><span>Kami membaca:</span>
      ${r.konsep.map((k) => `<span class="chip">${esc(k.label)}</span>`).join("")}
      ${r.kata.map((w) => `<span class="chip">${esc(w)}</span>`).join("")}
      ${r.maksud.map((w) => `<span class="chip" title="kata maksud: menaikkan peringkat, tidak diwajibkan">${esc(w)}?</span>`).join("")}
      ${!r.konsep.length && !r.kata.length ? "<span>(tidak ada kata kunci yang tersisa)</span>" : ""}</div>
    ${r.ejaan.length ? `<div class="baris"><span>Ejaan diseragamkan:</span> ${r.ejaan.map(esc).join(", ")}</div>` : ""}
    ${r.dibuang.length ? `<div class="baris"><span>Diabaikan:</span> <del>${r.dibuang.map(esc).join(" ")}</del></div>` : ""}
  </div>`;
  const catatan = [];
  for (const k of r.konsep) catatan.push(`<b>${esc(k.label)}.</b> ${esc(k.catatan)}`);
  if (r.pertanyaanHukum) catatan.push(`Pertanyaan Anda menyangkut hukum. Teman Hadits menampilkan riwayat, bukan fatwa.${r.klaim.length ? ` Kata <b>${r.klaim.map(esc).join(", ")}</b> dipakai untuk mengurutkan dan disorot di bawah, tetapi pencarian kata tidak bisa membuktikan isi sebuah hadits. Baca kalimat lengkapnya.` : ""}`);
  const daftarRujuk = rujukan ? (Array.isArray(rujukan) ? rujukan : [rujukan]) : [];
  const rujuk = daftarRujuk.length ? `<div class="rujukan-langsung"><span>${daftarRujuk.length > 1 ? "Nomor ini ada di dua sistem penomoran:" : "Rujukan langsung:"}</span>${daftarRujuk.map((x) => `<a href="/${esc(x.kitab_id)}/${esc(x.slug)}">${esc(x.kitab_nama)} no. ${esc(x.no_tampil)} →</a><span class="kecil">${esc(x.catatan)}</span>`).join("")}</div>` : "";
  const maksPK = Math.max(1, ...Object.values(out.perKitab));
  const sebaran = kitab.map((k) => {
    const n = out.perKitab[k.id] || 0;
    const aktif = filter.k === k.id;
    return n ? `<a href="${urlDengan({ k: aktif ? "" : k.id, h: "" })}" aria-current="${aktif}"><div><span>${esc(PENDEK[k.id])}</span><span class="batang"><i style="width:${((n / maksPK) * 100).toFixed(1)}%"></i></span><span class="n">${fmt(n)}</span></div></a>` : "";
  }).join("");
  const daftar = out.hasil.map((h) => `
    <li class="hasil">
      <header><span class="rujukan"><a href="/${esc(h.kitab_id)}/${esc(h.slug)}">${esc(kitab.find((k) => k.id === h.kitab_id)?.nama)} <span class="num">no. ${esc(h.no_tampil)}</span></a>${h.no_lidwa && h.kitab_id !== "ahmad" && h.kitab_id !== "darimi" && h.kitab_id !== "syafii" ? `<small class="num">Lidwa ${h.no_lidwa}</small>` : ""}</span>${lencana(h.tingkat)}</header>
      ${h.terjemah && !(sembunyiRiyadh && h.kitab_id === "riyadh") ? `<p class="id">${cuplik(h.terjemah.replace(/\[|\]/g, ""), sorot)}</p>` : `<p class="tanpa-nilai">Terjemahan belum ditampilkan untuk nomor ini.</p>`}
      <p class="ar">${cuplikAr(h.arab, akar)}</p>
      <p class="alasan">Muncul karena: ${h.alasan.map((a) => `<b>${esc(a)}</b>`).join(" · ")}</p>
      <footer>${bukuBesar(h.penilaian, h.kitab_id)}</footer>
    </li>`).join("");
  const halMaks = Math.ceil(out.tampil / out.perHalaman);
  const nav = halMaks > 1 ? `<nav class="halaman-nav" aria-label="Halaman hasil">${out.halaman > 1 ? `<a href="${urlDengan({ h: out.halaman - 1 })}">← Sebelumnya</a>` : `<span class="nonaktif">← Sebelumnya</span>`}<span class="kecil">Halaman ${out.halaman} dari ${halMaks}</span>${out.halaman < halMaks ? `<a href="${urlDengan({ h: out.halaman + 1 })}">Berikutnya →</a>` : `<span class="nonaktif">Berikutnya →</span>`}</nav>` : "";
  const kosong = !out.hasil.length ? `<div class="catatan">Tidak ditemukan riwayat yang cocok di ${kitab.length} kitab yang kami muat. Coba ejaan lain atau kata yang lebih umum. Bila Anda punya teks lengkap haditsnya, gunakan <a href="/cek?t=${encodeURIComponent(q)}">Cek Hadits</a>.</div>` : "";
  return `
  <h1 class="sembunyi">Hasil pencarian: ${esc(q)}</h1>
  <form class="kolom-cari" action="/cari" method="get" role="search">
    <label class="sembunyi" for="q-cari">Kata kunci</label>
    <input id="q-cari" name="q" type="search" value="${esc(q)}" autocomplete="off" required>
    <button class="tombol" type="submit">Cari</button>
  </form>
  ${bacaan}
  <div class="dua-kolom">
    <div>
      ${rujuk}
      ${tema.length ? `<div class="rujukan-langsung"><span>Tema terkait (kurasi HadeethEnc):</span>${tema.map((t) => `<a href="/tema/${esc(t.id)}">${esc(t.judul)} <span class="kecil">${fmt(t.jumlah)} hadits</span></a>`).join("")}</div>` : ""}
      ${catatan.length ? `<div class="catatan">${catatan.join("<br><br>")}</div>` : ""}
      ${out.hasil.length ? `<p class="kecil" style="margin-top:14px">${fmt(out.total)} riwayat ditemukan${filter.k || filter.t ? `, ${fmt(out.tampil)} sesuai saringan` : ""}. Diurutkan menurut kekuatan alasan, lalu tingkat data, lalu urutan kitab.</p>` : kosong}
      <ol class="daftar-hasil">${daftar}</ol>
      ${nav}
    </div>
    <aside class="panel-samping" aria-labelledby="h-sebaran">
      <h3 id="h-sebaran">Sebaran per kitab</h3>
      <div class="sebaran">${sebaran || '<p class="kecil">Belum ada hasil.</p>'}</div>
      ${filter.k ? `<a class="kecil" href="${urlDengan({ k: "", h: "" })}">Tampilkan semua kitab</a>` : '<p class="label">ketuk kitab untuk menyaring</p>'}
      <h3>Tingkat data</h3>
      <div class="saring">${[["", "Semua"], ["A", "Hanya tingkat A"], ["B", "Hanya tingkat B"]].map(([t, l]) => `<a href="${urlDengan({ t, h: "" })}" aria-current="${(filter.t || "") === t}">${l}</a>`).join("")}</div>
    </aside>
  </div>`;
}

// ------------------------------------------------------------------------------------------------
// HALAMAN HADITS
// ------------------------------------------------------------------------------------------------
export function halamanHadits(d) {
  const { r, kitab, bab, penilaian, jalur, jalurPenilaian, pisah, sanadHtml, rantai, tirmidzi, tema, sebelum, sesudah, kanonik, dikutip = [], judul = null } = d;
  const judulHtml = judul && (judul.kitab_ar || judul.bab_ar) ? `<div class="judul-bab">
      ${judul.kitab_ar ? `<p class="ar" style="font-size:calc(1.15rem * var(--ar));color:var(--tinta-2)">${esc(judul.kitab_ar)}${judul.kitab_nama_id ? ` <span class="kecil" style="direction:ltr;unicode-bidi:isolate">· ${esc(judul.kitab_nama_id)}</span>` : ""}</p>` : ""}
      ${judul.bab_ar ? `<p class="ar" style="font-size:calc(1.3rem * var(--ar));color:var(--zamrud);font-weight:700;line-height:1.9">${esc(judul.bab_ar)}${judul.bab_ar.trim() === "باب" ? ` <span class="kecil" style="font-family:var(--f-ui);font-weight:400">(bab tanpa judul)</span>` : ""}</p>` : ""}
      <p class="label">judul kitab & bab dari teks kitabnya${judul.cara === "urutan" ? " · disimpulkan dari urutan hadits sebelum & sesudahnya" : ""}${judul.cara === "nomor" ? " · dicocokkan lewat nomor hadits yang sama (isi teksnya ikut diperiksa)" : ""}${judul.cara === "koreksi-cetak" ? " · dikoreksi sesuai kitab cetaknya (lihat Metode)" : ""}${judul.cara === "catatan-cetak" ? " · dengan catatan dari kitab cetaknya (lihat Metode)" : ""}</p>${judul.catatan ? `
      <p class="kecil catatan-bab"><b>Catatan cetakan:</b> ${esc(judul.catatan)}</p>` : ""}</div>` : "";
  const tambahan = tirmidzi ? [{ siapa: "at-Tirmidzi (dalam kitabnya)", hukum: tirmidzi, kategori: /ضعيف|منكر/.test(tirmidzi) ? "lemah" : /صحيح/.test(tirmidzi) ? "shahih" : /حسن/.test(tirmidzi) ? "hasan" : "lainnya" }] : [];
  const kelompok = {};
  for (const j of jalur) (kelompok[j.kitab_id] ||= { nama: j.kitab_nama, xs: [] }).xs.push(j);
  const adaSama = jalur.some((j) => j.tingkat_mirip === "sama");
  const penJalur = jalur.filter((j) => j.tingkat_mirip === "sama" && jalurPenilaian.has(j.n)).slice(0, 6);
  const terjemahHtml = r.terjemah ? esc(r.terjemah).replace(/\[([^\]]+)\]/g, '<span class="perawi">$1</span>') : null;
  const gabungan = (r.alasan || "").startsWith("teks ini tercakup utuh");
  const rujukanTeks = `HR. ${HR[kitab.id] || kitab.nama} no. ${r.no_edisi ? `${r.no_edisi} (edisi ${kitab.edisi}; no. ${r.no_tampil} penomoran Lidwa)` : r.no_tampil + (kitab.jumlah_standar ? "" : " (penomoran Lidwa)")}. Sumber: Teman Hadits, ${kanonik}`;
  const rantaiHtml = rantai && rantai.simpul.length >= 3 ? `
  <section class="rantai-wrap" aria-labelledby="h-rantai">
    <h2 id="h-rantai" style="color:var(--zamrud);font-size:1.7rem">Rantai sanad</h2>
    <p style="color:var(--tinta-2);max-width:66ch;font-size:1rem;margin-top:6px">Dibaca dari atas: ${rantai.adaNabi ? "Rasulullah ﷺ menyampaikan kepada sahabat, lalu" : "riwayat"} turun dari guru ke murid sampai ke penyusun kitab. Di antara dua nama tertulis lafaz yang dipakai murid saat menerima.</p>
    <ol class="rantai">${rantai.simpul.map((s, i, arr) => {
      const bawah = arr[i + 1];
      const g = SIGHAH_MAP[s.sighah];
      const mata = bawah && s.sighah ? `<div class="mata"><span>${esc(bawah.namaId || bawah.namaAr)} menerima dengan lafaz</span><span class="ar">${esc(s.lafaz)}</span><em>${g ? esc(`${g.latin}, “${g.arti}”`) : ""}</em></div>` : "";
      return `<li class="simpul${s.nabi ? " nabi" : ""}" style="animation-delay:${i * 60}ms"><span class="manik" aria-hidden="true">${s.nabi ? "ﷺ" : s.penyusun ? "✦" : i}</span>
        <div class="orang"><span class="peran">${esc(s.peran)}</span><b>${esc(s.namaId || "")}</b><span class="ar">${esc(s.namaAr || "")}</span>${s.perawi ? ringkasPerawi(s.perawi) : ""}</div>${mata}</li>`;
    }).join("")}</ol>
    <p class="kotak-info" style="max-width:640px;margin:18px auto 0">${rantai.selaras ? "Nama Latin diambil dari terjemah Lidwa dan dipasangkan dengan nama Arab karena jumlah dan urutannya sama." : "Rantai dibaca otomatis dari teks Arab; nama Latin tidak dipasangkan karena jumlahnya tidak sama dengan terjemah."} Perawi yang meriwayatkan bersamaan (“dan …”) belum ditampilkan terpisah. ${rantai.simpul.some((x) => x.perawi)
      ? `Identitas perawi ditetapkan dari daftar guru-murid <i>Tahdzib al-Kamal</i> (al-Mizzi) untuk kitab ini, dan hanya ditampilkan bila <b>pasti</b>; ringkasan penilaian dari <i>Taqrib at-Tahdzib</i> (Ibnu Hajar). Perawi tanpa ringkasan belum dapat dipastikan. <a href="/metode#perawi">Caranya</a>.`
      : "Identitas perawi di rantai ini belum dapat dipastikan, jadi biodatanya tidak ditampilkan."}</p>
  </section>` : "";
  return `
  <nav class="remah" aria-label="Lokasi"><a href="/kitab">Kitab</a> › <a href="/kitab/${esc(kitab.id)}">${esc(kitab.nama)}</a>${bab ? ` › <a href="/kitab/${esc(kitab.id)}/bab/${bab.no}">${esc(bab.nama || "Bab " + bab.no)}</a>` : ""} › <span>No. ${esc(r.no_tampil)}</span></nav>
  <div class="judul-hadits"><h1>${esc(kitab.nama)} <span class="num">no. ${esc(r.no_tampil)}</span></h1></div>
  <div class="meta">${lencana(r.tingkat)}${r.no_lidwa && kitab.jumlah_standar ? `<span class="chip num">nomor Lidwa ${r.no_lidwa}</span>` : ""}${!kitab.jumlah_standar ? `<span class="chip">penomoran Lidwa</span>` : ""}${r.no_edisi ? `<span class="chip num" title="nomor yang lazim dikutip dari edisi tahqiq ini">no. ${esc(r.no_edisi)} di edisi ${esc(kitab.edisi)}</span>` : ""}${r.kecocokan != null ? `<span class="chip">teks Arab cocok ${Math.round(r.kecocokan * 100)}% ${kitab.edisi ? "dengan edisi tahqiq" : "di 2 sumber"}</span>` : ""}</div>
  ${r.alasan ? `<p class="kotak-info" style="margin-top:12px">${esc(r.alasan)}</p>` : ""}
  <article class="halaman">
    <div class="lembar">
      ${judulHtml}
      ${pisah ? `
      <div class="label">sanad · rantai periwayat <span style="text-transform:none;letter-spacing:0;font-family:var(--f-ui);font-weight:400">(lafaz periwayatan bertinta merah; sentuh untuk artinya)</span></div>
      <p class="ar sanad" id="teks-sanad">${sanadHtml}</p>
      <div class="pemisah" aria-hidden="true">${SVG_BINTANG}</div>
      <div class="label">matan · isi hadits</div>
      <p class="ar matan" id="teks-matan">${esc(pisah.matan)}</p>
      ${pisah.komentar ? `<div class="label">komentar ${esc(kitab.id === "tirmidzi" ? "at-Tirmidzi" : "penyusun")} · bukan bagian matan</div><p class="ar sanad">${esc(pisah.komentar)}</p>` : ""}` : `
      <div class="label">teks lengkap · sanad dan matan belum dipisahkan otomatis</div>
      <p class="ar teks-utuh" id="teks-matan">${esc(r.arab)}</p>`}
      <div class="pemisah" aria-hidden="true">${SVG_BINTANG}</div>
      <div class="label">terjemahan · Lidwa Pusaka${gabungan ? " · mencakup beberapa riwayat yang digabung" : ""}</div>
      ${terjemahHtml ? `<p class="terjemah">${terjemahHtml}</p>` : `<p class="tanpa-nilai">Terjemahan belum terpasang untuk nomor ini, karena pasangannya di sumber Lidwa belum ditemukan dengan pasti. Kami tidak menampilkan terjemahan yang belum pasti.</p>`}
      <div class="aksi">
        <button type="button" data-salin="${esc(rujukanTeks)}" data-pesan="Rujukan tersalin.">Salin rujukan</button>
        <button type="button" data-salin="1" data-salin-dari="${pisah ? "#teks-sanad" : "#teks-matan"}" data-pesan="Teks Arab tersalin.">Salin teks Arab</button>
        <a href="https://github.com/FreyzS7/Teman-hadits/issues/new?title=${encodeURIComponent("Laporan: " + r.id)}&body=${encodeURIComponent("Halaman: " + kanonik + "\n\nApa yang keliru:\n\nRujukan pembanding (kitab cetak, halaman):\n")}" rel="noopener">Laporkan kesalahan</a>
      </div>
      <p class="label" id="status-salin" aria-live="polite"></p>
    </div>
    <aside class="hamisy" aria-label="Catatan pinggir">
      <section><h2>Derajat</h2>${bukuBesar(penilaian, kitab.id, tambahan)}
        ${penJalur.length ? `<p style="margin:12px 0 6px;font:500 .9rem/1.4 var(--f-ui)">Penilaian ulama atas jalur lain yang matannya sama:</p>${penJalur.map((j) => `<div style="margin-top:10px"><div class="label" style="margin-bottom:4px"><a href="/${esc(j.kitab_id)}/${esc(j.slug)}">${esc(PENDEK[j.kitab_id])} no. ${esc(j.no_tampil)}</a></div>${bukuBesar(jalurPenilaian.get(j.n), j.kitab_id)}</div>`).join("")}` : ""}
      </section>
      <section><h2>Diriwayatkan juga oleh</h2>
        ${jalur.length ? `<div class="jalur">${Object.entries(kelompok).map(([k, g]) => `<div><span class="kitab">${esc(g.nama)}</span><div class="nomor">${g.xs.map((j) => `<a class="${j.tingkat_mirip === "mirip" ? "mirip" : ""}" href="/${esc(j.kitab_id)}/${esc(j.slug)}" title="${j.tingkat_mirip === "sama" ? "matan sama" : "matan mirip, periksa sendiri"} (${Math.round(j.skor * 100)}%)">${esc(j.no_tampil)}</a>`).join("")}</div></div>`).join("")}</div>
        <p class="kecil" style="margin-top:8px">Kotak utuh = matan sama. Kotak putus-putus = mirip, periksa sendiri. Dicocokkan otomatis lewat kemiripan matan Arab.</p>`
        : `<p class="tanpa-nilai">${pisah ? "Belum ditemukan riwayat lain dengan matan yang sama di kitab-kitab kami." : "Belum dihitung, karena matannya belum bisa dipisahkan otomatis dari sanad."}</p>`}
      </section>
      ${dikutip.length ? `<section><h2>Dikutip dalam</h2><p class="kecil" style="margin-bottom:6px">Riyadhus Shalihin (an-Nawawi)</p><div class="jalur"><div class="nomor">${dikutip.map((x) => `<a href="/riyadh/${esc(x.slug)}">no. ${esc(x.no_tampil)}</a>`).join("")}</div></div></section>` : ""}
      ${tema.length ? `<section><h2>Tema</h2><div class="nomor" style="display:flex;flex-wrap:wrap;gap:6px">${tema.map((t) => `<a class="chip" href="/tema/${esc(t.id)}">${esc(t.judul)}</a>`).join("")}</div><p class="kecil" style="margin-top:6px">Tema dari HadeethEnc.com</p></section>` : ""}
      <section><h2>Asal data</h2><div class="asal">
        <span>Teks Arab: ${kitab.jumlah_standar ? "fawazahmed0/hadith-api" : "Lidwa Pusaka via carihadis.com"}</span>
        ${kitab.edisi ? `<span>Teks pembanding & judul: edisi ${esc(kitab.edisi)} (OpenITI, <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>)</span>` : `<span>Judul kitab & bab: OpenITI (<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>)</span>`}
        ${r.terjemah ? "<span>Terjemah: Lidwa Pusaka via carihadis.com</span>" : ""}
        ${r.kecocokan != null ? `<span>Kecocokan teks Arab 2 sumber: <b class="num">${r.kecocokan.toFixed(2).replace(".", ",")}</b></span>` : "<span>Baru 1 sumber digital</span>"}
        <span>ID data: <code>${esc(r.id)}</code></span>
      </div></section>
    </aside>
  </article>
  ${rantaiHtml}
  <nav class="navigasi-hadits" aria-label="Hadits sebelum dan sesudah">${sebelum ? `<a href="/${esc(kitab.id)}/${esc(sebelum.slug)}" rel="prev">← No. ${esc(sebelum.no_tampil)}</a>` : "<span></span>"}${sesudah ? `<a href="/${esc(kitab.id)}/${esc(sesudah.slug)}" rel="next">No. ${esc(sesudah.no_tampil)} →</a>` : ""}</nav>`;
}

// ------------------------------------------------------------------------------------------------
// KITAB
// ------------------------------------------------------------------------------------------------
export function daftarKitab({ kitab }) {
  return `<h1 class="halaman-judul">Kitab</h1><p class="sub">Kitab-kitab yang sudah dimuat. Riyadhus Shalihin adalah kitab himpunan: an-Nawawi mengutip hadits dari kitab-kitab lain dan menyebut sumbernya.</p>
  <div class="tema-daftar" style="margin-top:22px">${kitab.map((k) => `<a href="/kitab/${esc(k.id)}"><span style="color:var(--tinta)"><b>${esc(k.nama)}</b><br><span class="ar" style="color:var(--zamrud);font-size:1.2rem">${esc(k.nama_arab)}</span></span><span>${fmt(k.terbit)}</span></a>`).join("")}</div>`;
}

function ringkasKitab(k) {
  const pen = JSON.parse(k.penilai || "[]").map(namaPenilai);
  return `<div class="ringkas-kitab">
    <div><b>${fmt(k.terbit)}</b><span>riwayat tampil</span></div>
    <div><b>${fmt(k.tingkat_a)}</b><span>${lencana("A")} cocok di 2 sumber</span></div>
    <div><b>${fmt(k.tingkat_b)}</b><span>${lencana("B")} baru 1 sumber</span></div>
    <div><b>${fmt(k.karantina)}</b><span>karantina (tidak tampil)</span></div>
    <div><b>${fmt(k.dinilai)}</b><span>${pen.length ? "punya penilaian: " + pen.map(esc).join(", ") : KITAB_SHAHIH.has(k.id) ? "kitab Shahih, tanpa penilaian per hadits di sumber" : "belum ada data penilaian"}</span></div>
  </div>`;
}

export function halamanKitab({ k, bab, daftar, halaman, halMaks }) {
  const kepala = `<nav class="remah"><a href="/kitab">Kitab</a> › <span>${esc(k.nama)}</span></nav>
  <h1 class="halaman-judul" style="margin-top:10px">${esc(k.nama)}</h1>
  <p class="ar" style="font-size:1.8rem;color:var(--zamrud);text-align:left;direction:rtl">${esc(k.nama_arab)}</p>
  <p class="sub">${esc(k.penyusun)} (w. ${k.wafat_h} H). Penomoran: ${k.id === "riyadh" ? "nomor hadits Riyadhus Shalihin pada teks Arab (1–1896); terjemah memakai penomoran edisinya sendiri, ditampilkan sebagai pembanding" : k.jumlah_standar ? "standar (fawazahmed0), dengan nomor Lidwa sebagai pembanding" : k.edisi ? `Lidwa Pusaka (alamat halaman); nomor edisi ${esc(k.edisi)} ditampilkan di setiap hadits yang teksnya cocok` : "Lidwa Pusaka"}.</p>
  ${ringkasKitab(k)}`;
  if (bab.length) {
    const ket = k.id === "riyadh" ? "Nama bab Indonesia dari terjemahnya; nama Arab dari teks an-Nawawi."
      : "Nama Arab dari teks kitabnya (korpus OpenITI). Nama Indonesia disusun Teman Hadits dan belum ditinjau ahli; nama Inggris dari fawazahmed0.";
    return kepala + `<section class="bagian" style="margin-top:34px"><header><h2>Daftar bab</h2><p>${ket}</p></header>
      <ol class="daftar-bab">${bab.map((b) => `<li><a href="/kitab/${esc(k.id)}/bab/${b.no}">${b.no}. ${esc(b.nama || "Riwayat tanpa nomor kitab di sumber penomoran (campuran)")}${b.nama_ar ? `<br><span class="ar" style="font-size:1.05rem;color:var(--tinta-2);display:block;text-align:left">${esc(b.nama_ar)}</span>` : ""}${b.nama_en && b.nama_en !== b.nama ? `<span class="kecil" style="display:block">${esc(b.nama_en)}</span>` : ""}</a><span class="nb">${fmt(b.jumlah)}</span></li>`).join("")}</ol></section>`;
  }
  return kepala + `<section class="bagian" style="margin-top:34px"><header><h2>Daftar riwayat</h2><p>Kitab ini belum punya pembagian bab di sumber kami.</p></header>${daftarRiwayat(k.id, daftar)}${navHalaman(`/kitab/${k.id}`, halaman, halMaks)}</section>`;
}

export function halamanBab({ k, b, daftar, halaman, halMaks }) {
  return `<nav class="remah"><a href="/kitab">Kitab</a> › <a href="/kitab/${esc(k.id)}">${esc(k.nama)}</a> › <span>${esc(b.nama || "Bab " + b.no)}</span></nav>
  <h1 class="halaman-judul" style="margin-top:10px">${esc(b.nama || "Bab " + b.no)}</h1>${b.nama_ar ? `<p class="ar" style="font-size:1.5rem;color:var(--zamrud);text-align:left;direction:rtl;margin-top:6px">${esc(b.nama_ar)}</p>` : ""}
  ${b.nama_en && b.nama_en !== b.nama ? `<p class="kecil">${esc(b.nama_en)} (fawazahmed0)</p>` : ""}
  <p class="sub">${esc(k.nama)} · bagian ke-${b.no} · ${fmt(b.jumlah)} riwayat</p>
  ${daftarRiwayat(k.id, daftar)}${navHalaman(`/kitab/${k.id}/bab/${b.no}`, halaman, halMaks)}`;
}

function daftarRiwayat(kid, daftar) {
  return `<ol class="daftar-riwayat">${daftar.map((d) => `<li><span class="no"><a href="/${esc(kid)}/${esc(d.slug)}">${esc(d.no_tampil)}</a></span><div>${d.terjemah ? `<p>${esc(d.terjemah.replace(/\[|\]/g, "").slice(0, 260))}${d.terjemah.length > 260 ? "…" : ""}</p>` : `<p class="tanpa-nilai">Terjemahan belum terpasang.</p>`}<p class="kecil" style="margin-top:4px">${lencana(d.tingkat)} ${d.n_nilai ? `· ${d.n_nilai} penilaian ulama` : ""}</p></div></li>`).join("")}</ol>`;
}

function navHalaman(dasar, halaman, halMaks) {
  if (halMaks <= 1) return "";
  return `<nav class="halaman-nav" aria-label="Halaman">${halaman > 1 ? `<a href="${dasar}?h=${halaman - 1}">← Sebelumnya</a>` : `<span class="nonaktif">← Sebelumnya</span>`}<span class="kecil">Halaman ${halaman} dari ${halMaks}</span>${halaman < halMaks ? `<a href="${dasar}?h=${halaman + 1}">Berikutnya →</a>` : `<span class="nonaktif">Berikutnya →</span>`}</nav>`;
}

// ------------------------------------------------------------------------------------------------
// CEK
// ------------------------------------------------------------------------------------------------
export function halamanCek({ t, hasil, kitab, info, katalog = "" }) {
  const nama = (id) => kitab.find((k) => k.id === id)?.nama || id;
  const contoh = [
    ["Hadits niat", "Sesungguhnya amalan itu tergantung niatnya dan seseorang akan mendapatkan sesuai dengan apa yang ia niatkan (HR. Bukhari dan Muslim)"],
    ["“Tuntutlah ilmu walau ke negeri Cina”", "Tuntutlah ilmu walau sampai ke negeri Cina"],
    ["Teks Arab", "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"],
  ];
  let vonis = "";
  if (hasil) {
    const langkah = hasil.langkah ? `<div><div class="label" style="margin-bottom:8px">cara kami mencocokkan · kata kunci${hasil.mode === "indonesia" ? " khas dan jumlah riwayat yang memuatnya" : " Arab yang dicari"}</div><div class="langkah">${hasil.langkah.map((l) => `<span class="chip${l.muncul === 0 ? " nol" : ""}">${hasil.mode === "arab" ? `<span class="ar">${esc(l.kata)}</span>` : esc(l.kata)}${l.muncul != null ? ` <b>${fmt(l.muncul)}</b>` : ""}</span>`).join("")}</div></div>` : "";
    if (hasil.status === "kosong") {
      vonis = `<div class="catatan" style="margin-top:20px">Teksnya terlalu pendek atau hanya berisi kata umum. Tempel kalimat hadits yang lebih lengkap.</div>`;
    } else if (hasil.status === "ditemukan") {
      const grup = {};
      for (const f of hasil.keluarga) (grup[f.kitab_id] ||= []).push(f);
      const klaim = hasil.klaimHasil.length ? `<div class="klaim"><div class="label">klaim di teks Anda</div>
        ${hasil.klaimHasil.map((k) => `<div><span class="tanda ${k.ada ? "ya" : "tidak"}">${k.ada ? "✓" : "✗"}</span><b>${esc(nama(k.kitab))}</b><span class="num">${k.ada ? "no. " + k.nomor.map(esc).join(", ") : "tidak ditemukan di keluarga riwayat ini"}</span></div>`).join("")}
        <p style="font:500 1rem/1.4 var(--f-ui);color:${hasil.klaimHasil.every((k) => k.ada) ? "var(--terima)" : "var(--palsu)"}">${hasil.klaimHasil.every((k) => k.ada) ? "Atribusi sesuai." : "Sebagian atribusi tidak ditemukan. Periksa kembali sumbernya."}</p></div>` : `<p class="kecil">Teks Anda tidak menyebut sumber (“HR. …”). Berikut kitab-kitab yang memuatnya.</p>`;
      vonis = `<section class="vonis"><header><span class="stempel ok">DITEMUKAN</span><p>Teks ini cocok dengan hadits yang tercatat di <b>${Object.keys(grup).length} kitab</b>, dalam <b>${hasil.keluarga.length} riwayat</b>. Kemiripan terbaik ${Math.round(hasil.skor * 100)}%.</p></header>
        <div class="isi">${klaim}${langkah}
          ${katalog}
          <div><div class="label" style="margin-bottom:10px">semua riwayat yang ditemukan</div><div class="keluarga">${Object.entries(grup).map(([k, fs]) => `<article><h4>${esc(nama(k))}</h4><div class="nomor">${fs.map((f) => `<a href="/${esc(f.kitab_id)}/${esc(f.slug)}" title="${f.hubungan === "terbaik" ? "paling cocok dengan teks Anda" : f.hubungan === "sama" ? "matan sama" : "matan mirip"}"${f.hubungan === "terbaik" ? ' style="border-color:var(--zamrud);border-width:2px"' : f.hubungan === "mirip" ? ' style="border-style:dashed"' : ""}>${esc(f.no_tampil)}</a>`).join("")}</div>${bukuBesar(fs.find((f) => f.penilaian.length)?.penilaian, k)}</article>`).join("")}</div></div>
        </div></section>`;
    } else {
      vonis = `<section class="vonis"><header><span class="stempel tidak">TIDAK DITEMUKAN</span><p>Kalimat ini <b>tidak ditemukan</b> di ${kitab.length} kitab yang kami muat (${fmt(info.terbit)} riwayat).</p></header>
        <div class="isi">${langkah}
          ${hasil.absen?.length ? `<p>Kata <b>“${hasil.absen.map(esc).join("”, “")}”</b> tidak muncul dalam satu pun terjemahan riwayat kami. Periksa ejaannya. Bila ejaannya benar, kalimat ini bukan hadits dari kitab-kitab tersebut.</p>` : `<p>${esc(hasil.alasan || "")}.</p>`}
          <p style="color:var(--tinta-2)">Tidak ditemukan di kitab-kitab hadits ini belum membuktikan kalimat tersebut palsu. Para ulama membahas ucapan-ucapan populer dalam kitab khusus; bila ada, pembahasan mereka tampil di bawah.</p>
          ${katalog || `<div class="slot-kosong"><b>Catatan ulama hadits tentang kalimat ini</b><span>Kalimat ini juga tidak ditemukan di empat kitab tentang hadits populer & palsu yang kami muat (al-Maqashid al-Hasanah, Kasyf al-Khafa', al-Asrar al-Marfu'ah, al-Maudhu'at).</span></div>`}
        </div></section>`;
    }
  }
  return `<h1 class="halaman-judul">Cek teks hadits yang beredar</h1>
  <p class="sub">Tempel teks dari pesan berantai, poster, atau ceramah, dalam bahasa Indonesia atau Arab. Kami cari padanannya di kitab-kitab hadits dan memeriksa klaim “HR. …” di belakangnya.</p>
  <form class="kolom-cari" action="/cek" method="get" style="margin-top:18px">
    <label class="sembunyi" for="teks-cek">Teks yang ingin dicek</label>
    <textarea id="teks-cek" name="t" maxlength="2000" required>${esc(t || "")}</textarea>
    <button class="tombol" type="submit">Cek</button>
  </form>
  <div class="contoh"><span class="label">contoh</span>${contoh.map(([l, x]) => `<a href="/cek?t=${encodeURIComponent(x)}">${esc(l)}</a>`).join("")}</div>
  ${vonis}`;
}

// ------------------------------------------------------------------------------------------------
// TEMA, METODE, GALAT
// ------------------------------------------------------------------------------------------------
export function daftarTema({ akar, anak, versi }) {
  if (!akar.length) return `<h1 class="halaman-judul">Tema</h1><div class="catatan" style="margin-top:18px">Daftar tema (dari HadeethEnc.com, disusun dan ditinjau ulama) sedang disiapkan. Sementara itu, gunakan <a href="/cari">pencarian</a>.</div>`;
  return `<h1 class="halaman-judul">Tema</h1><p class="sub">Tema berbahasa Indonesia dari HadeethEnc.com, disusun dan ditinjau tim ulama mereka. Setiap hadits di tema dihubungkan ke riwayat di kitab-kitab kami bila teks Arabnya cocok. Versi data: ${esc(versi || "-")}.</p>
  ${akar.map((a) => `<section class="bagian" style="margin-top:30px"><header><h2><a href="/tema/${esc(a.id)}" style="text-decoration:none">${esc(a.judul)}</a></h2><p>${fmt(a.jumlah)} hadits</p></header>
    <div class="tema-daftar">${(anak[a.id] || []).map((t) => `<a href="/tema/${esc(t.id)}">${esc(t.judul)}<span>${fmt(t.jumlah)}</span></a>`).join("")}</div></section>`).join("")}`;
}

export function halamanTema({ t, induk, sub, hadits, versi }) {
  return `<nav class="remah"><a href="/tema">Tema</a>${induk ? ` › <a href="/tema/${esc(induk.id)}">${esc(induk.judul)}</a>` : ""} › <span>${esc(t.judul)}</span></nav>
  <h1 class="halaman-judul" style="margin-top:10px">${esc(t.judul)}</h1>
  ${sub.length ? `<div class="tema-daftar" style="margin-top:18px">${sub.map((s) => `<a href="/tema/${esc(s.id)}">${esc(s.judul)}<span>${fmt(s.jumlah)}</span></a>`).join("")}</div>` : ""}
  <p class="kecil" style="margin-top:14px">Teks terjemah, derajat, dan penjelasan di halaman ini dari <a href="https://hadeethenc.com" rel="noopener">HadeethEnc.com</a> (Ensiklopedia Terjemahan Hadis-hadis Nabi), ditampilkan tanpa diubah. Versi: ${esc(versi || "-")}.</p>
  <div style="display:grid;gap:14px;margin-top:22px">${hadits.map((h) => `<article class="he">
    <h2 style="font-size:1.15rem;color:var(--zamrud)">${esc(h.judul)}</h2>
    ${h.boleh_tampil && h.teks_id ? `<p>${esc(h.teks_id)}</p>` : ""}
    ${h.teks_ar ? `<p class="ar">${esc(h.teks_ar)}</p>` : ""}
    <p class="kecil">${h.atribusi ? esc(h.atribusi) + " · " : ""}${h.derajat ? "Derajat menurut HadeethEnc: <b>" + esc(hukumTampil(h.derajat)) + "</b> · " : ""}<a href="${esc(h.url)}" rel="noopener">lihat di HadeethEnc.com</a></p>
    ${h.penjelasan ? `<details><summary class="kecil" style="cursor:pointer">Penjelasan (HadeethEnc)</summary><p style="margin-top:8px">${esc(h.penjelasan)}</p></details>` : ""}
    ${h.riwayat.length ? `<p class="kecil">Di kitab kami: ${h.riwayat.map((r) => `<a href="/${esc(r.kitab_id)}/${esc(r.slug)}">${esc(PENDEK[r.kitab_id])} ${esc(r.no_tampil)}</a>`).join(" · ")}</p>` : `<p class="kecil">Belum terhubung ke riwayat di kitab kami.</p>`}
  </article>`).join("")}</div>`;
}

function chipTingkat(t) {
  if (!t || !TINGKAT[t]) return "";
  return `<span class="chip kk-${TINGKAT[t][1]}" title="tingkatan ke-${t} dari 12 dalam muqaddimah Taqrib">${esc(TINGKAT[t][0])}</span>`;
}

function wafatTeks(p) {
  return p.wafat ? `w. ${p.wafat} H${p.wafat_ragu ? " (ada pendapat lain)" : ""}` : "";
}

function ringkasPerawi(p) {
  const info = [p.tabaqah ? `tabaqah ${p.tabaqah}` : "", wafatTeks(p)].filter(Boolean).join(" · ");
  return `<a class="perawi-ringkas" href="/perawi/${esc(p.id)}">${p.penilaian ? `<span class="ar">${esc(p.penilaian)}</span>` : ""}
    <span class="perawi-meta">${chipTingkat(p.tingkat)}${info ? `<span>${esc(info)}</span>` : ""}<span class="lanjut">biodata →</span></span></a>`;
}

export function halamanPerawi({ p }) {
  const rumuz = (p.rumuz || "").split(" ").filter(Boolean);
  const daftarOrang = (xs, kosong) => xs.length
    ? `<ul class="daftar-orang">${xs.map((x) => `<li><a href="/perawi/${esc(x.id)}"><span class="ar">${esc(x.nama)}</span></a> ${chipTingkat(x.tingkat)} <span class="kecil num">${fmt(x.n)} riwayat</span></li>`).join("")}</ul>`
    : `<p class="kecil">${kosong}</p>`;
  return `<nav class="remah"><a href="/perawi">Perawi</a> › <span class="ar" style="display:inline">${esc(p.nama)}</span></nav>
  <h1 class="halaman-judul ar" style="margin-top:10px;font-size:calc(2rem * var(--ar))">${esc(p.nama)}</h1>
  <div class="meta" style="margin-top:8px">${chipTingkat(p.tingkat)}${p.tabaqah ? `<span class="chip">tabaqah ${p.tabaqah}</span>` : ""}${p.wafat ? `<span class="chip num">${esc(wafatTeks(p))}</span>` : ""}<span class="chip num">${fmt(p.n_riwayat)} riwayat di data kami</span></div>
  <section class="bagian" style="margin-top:22px"><header><h2>Ringkasan Ibnu Hajar</h2><p>${p.taqrib ? `<i>Taqrib at-Tahdzib</i> no. ${p.taqrib} (edisi Muhammad 'Awwamah, Dar ar-Rasyid; teks OpenITI, <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>)` : "Perawi ini tidak ditemukan di <i>Taqrib at-Tahdzib</i> dengan pasti; data dari <i>Tahdzib al-Kamal</i>."}</p></header>
    ${p.teks_taqrib ? `<p class="ar kutipan-ulama">${esc(p.teks_taqrib)}${rumuz.length ? ` <span class="kode">${esc(rumuz.join(" "))}</span>` : ""}</p>` : ""}
    <dl class="fakta">
      ${p.penilaian ? `<dt>Penilaian</dt><dd><span class="ar" style="display:inline">${esc(p.penilaian)}</span> ${chipTingkat(p.tingkat)}<br><span class="kecil">Padanan Indonesia hanya alat bantu baca; Ibnu Hajar menyusun 12 tingkatan di muqaddimah Taqrib.</span></dd>` : ""}
      ${p.tabaqah ? `<dt>Tabaqah</dt><dd>${p.tabaqah}: ${esc(TABAQAH[p.tabaqah] || "")}</dd>` : ""}
      ${p.wafat ? `<dt>Wafat</dt><dd>${esc(wafatTeks(p))}. <span class="kecil">Dibaca dari teks di atas; bila Ibnu Hajar tidak menulis abadnya, abad dilengkapi dengan kaidah di muqaddimah Taqrib (tabaqah 1–2 sebelum 100 H, 3–8 sesudah 100 H, 9–12 sesudah 200 H).</span></dd>` : ""}
      ${rumuz.length ? `<dt>Riwayatnya ada di</dt><dd>${rumuz.map((k) => esc(RUMUZ[k] || k)).join(", ")}</dd>` : ""}
      ${p.tk_no ? `<dt>Tahdzib al-Kamal</dt><dd>biografi no. ${p.tk_no} (teks digital; berisi daftar guru dan murid yang dipakai untuk identifikasi)</dd>` : ""}
    </dl>
  </section>
  <section class="bagian" style="margin-top:26px"><header><h2>Guru dan murid di sanad kami</h2><p>Dihitung dari rantai yang perawinya teridentifikasi pasti. Bukan daftar lengkap; daftar lengkap ada di <i>Tahdzib al-Kamal</i>.</p></header>
    <div class="dua-kolom"><div><h3 class="kecil-judul">Meriwayatkan dari (guru)</h3>${daftarOrang(p.guru, "Belum ada guru yang teridentifikasi pasti.")}</div>
    <div><h3 class="kecil-judul">Diriwayatkan oleh (murid)</h3>${daftarOrang(p.murid, "Belum ada murid yang teridentifikasi pasti.")}</div></div>
  </section>
  <section class="bagian" style="margin-top:26px"><header><h2>Riwayat</h2><p>${fmt(p.n_riwayat)} riwayat di enam kitab ${p.n_riwayat > p.riwayat.length ? `(ditampilkan ${p.riwayat.length} pertama)` : ""}.</p></header>
    <div class="nomor" style="display:flex;flex-wrap:wrap;gap:6px">${p.riwayat.map((r) => `<a class="chip num" href="/${esc(r.kitab_id)}/${esc(r.slug)}">${esc(PENDEK[r.kitab_id])} ${esc(r.no_tampil)}</a>`).join("")}</div>
  </section>`;
}

export function halamanPerawiDaftar({ daftar }) {
  return `<h1 class="halaman-judul">Perawi hadits</h1>
  <p class="sub">Perawi yang identitasnya ditetapkan dengan pasti di sanad enam kitab (al-Bukhari, Muslim, Abu Dawud, at-Tirmidzi, an-Nasa'i, Ibnu Majah), dengan ringkasan Ibnu Hajar dari <i>Taqrib at-Tahdzib</i>. Diurutkan menurut jumlah riwayat.</p>
  <ol class="daftar-perawi">${daftar.map((p) => `<li><a href="/perawi/${esc(p.id)}"><span class="ar">${esc(p.nama)}</span></a>
    <span class="baris-status">${chipTingkat(p.tingkat)}${p.tabaqah ? `<span class="kecil">tabaqah ${p.tabaqah}</span>` : ""}${p.wafat ? `<span class="kecil">w. ${p.wafat} H</span>` : ""}<span class="kecil num">${fmt(p.n_riwayat)} riwayat</span></span></li>`).join("")}</ol>`;
}

export function halamanMetode({ info }) {
  const sumber = JSON.parse(info.sumber || "[]");
  return `<div class="prosa">
    <h1 class="halaman-judul">Cara kami menjaga kebenaran data</h1>
    <p>Teman Hadits tidak menilai hadits sendiri. Kami mengumpulkan teks dari kitab, mencocokkannya antar sumber, dan menampilkan penilaian ulama apa adanya, atas nama ulama tersebut.</p>
    <h2>Tingkat data</h2>
    <ul>
      <li>${lencana("A")} <b class="num">${fmt(info.tingkat_a)}</b> riwayat: teks Arab cocok di dua sumber digital dan terjemahannya terpasang pada teks yang sama.</li>
      <li>${lencana("B")} <b class="num">${fmt(info.tingkat_b)}</b> riwayat: baru satu sumber digital, atau pasangan terjemahannya belum pasti.</li>
      <li>${lencana("K")} <b class="num">${fmt(info.karantina)}</b> riwayat: data kosong/terpotong; tidak ditampilkan.</li>
    </ul>
    <h2>Yang tidak akan kami lakukan</h2>
    <ul>
      <li>Membuat “nilai akhir” sendiri bila para ulama berbeda pendapat. Semua penilaian ditampilkan berdampingan.</li>
      <li>Menerjemahkan, meringkas, atau menilai hadits dengan AI.</li>
      <li>Menampilkan hadits yang datanya rusak, terpotong, atau belum jelas nomornya.</li>
      <li>Menyatakan sebuah hadits “tidak ada” hanya karena tidak ada di koleksi kami. Kami selalu menyebut cakupan pencarian.</li>
    </ul>
    <h2>Pencarian</h2>
    <p>Pencarian memahami kalimat bebas dengan aturan yang bisa diperiksa: ejaan diseragamkan (shalat/sholat/salat), kata pengisi diabaikan, dan istilah awam dipetakan ke istilah dalam hadits. Contohnya, “tarawih” dicari sebagai <span class="ar">قيام رمضان</span>, karena kata “tarawih” tidak ada di teks Arab hadits. Setiap hasil menunjukkan alasan kemunculannya.</p>
    <h2 id="perawi">Identitas perawi</h2>
    <p>Sebuah nama di sanad, misalnya “Sufyan”, bisa merujuk ke beberapa orang. Seperti cara para ahli hadits membedakannya, kami melihat <b>siapa murid dan gurunya</b> di rantai itu. <i>Tahdzib al-Kamal</i> (al-Mizzi) mencatat untuk setiap perawi enam kitab daftar guru dan muridnya, lengkap dengan kode kitab tempat hubungan itu ada. Sebuah nama baru kami tampilkan sebagai <b>pasti</b> bila satu orang unggul mutlak atas semua kemungkinan lain dan hubungannya dengan perawi di atas dan di bawahnya tercatat untuk kitab tersebut. Ringkasan penilaian, tabaqah, dan tahun wafat diambil dari <i>Taqrib at-Tahdzib</i> (Ibnu Hajar). Hasilnya diuji terhadap identifikasi kurator Ifta' Sunnah (Arab Saudi): 99,8% sama pada lebih dari 45 ribu posisi yang bisa dibandingkan.</p>
    <h2 id="cetak">Dicocokkan dengan kitab cetak</h2>
    <p>Sampel acak isi yang tampil di situs (ringkasan Ibnu Hajar dari <i>Taqrib at-Tahdzib</i>, judul dan kata kunci <i>al-Maqashid al-Hasanah</i> dan <i>Kasyf al-Khafa'</i>) dibandingkan dengan teks hasil pindai kitab cetaknya dari edisi yang sama, lewat archive.org. Dari 122 entri yang terbaca di hasil pindai, tidak ditemukan satu pun perbedaan isi; semua selisih ternyata salah baca mesin pemindai. Pemeriksaan gambar halaman (50 entri Taqrib, nomor entri ikut dicek) menemukan dua kekurangan yang sudah diperbaiki: penilaian «كذبوه» yang tidak terbaca, dan bab tanpa judul yang terlewat di teks digital Shahih al-Bukhari. Seluruh daftar isi rinci (fihris) 9 juz cetakan Dar Thauq an-Najah sudah dibaca dari gambarnya; 47 rentang judul bab dikoreksi. Untuk Shahih Muslim, fihris dan halaman isi cetakan Fu'ad 'Abd al-Baqi menunjukkan 59 judul tambahan teks digital (kini dibuang) dan 5 judul yang berbeda (kini sesuai cetakan). Fihris Sunan Ibnu Majah (cetakan al-Halabi) memperlihatkan 121 bab yang terlewat karena format teks digitalnya; kini terbaca. Fihris Sunan an-Nasa'i (Abu Ghuddah) dan Sunan Abu Dawud (Muhyiddin 'Abd al-Hamid) memperlihatkan judul yang terpotong atau tidak lengkap; kini diperbaiki. Fihris Jami' at-Tirmidzi (Basyar 'Awwad Ma'ruf, 6 jilid) dibandingkan dengan semua judul bab; judul yang berbeda dicek di halaman isinya. Hasilnya: satu judul kitab yang terlewat («Nadzar dan Sumpah»), 4 judul bab yang dikoreksi, judul yang terpotong kini utuh, dan satu bab tambahan edisi Ahmad Syakir (hadits 611–612) yang kini diberi catatan. Fihris dan halaman isi al-Muwaththa' (Fu'ad 'Abd al-Baqi) dan Sunan ad-Darimi (Husain Salim Asad) masing-masing menghasilkan satu koreksi judul; di ad-Darimi juga dua judul bab yang terlewat format teks digitalnya, kini terbaca. Seluruh daftar isi Musnad asy-Syafi'i (al-Fahl) juga sudah dibaca dari gambarnya; 2 judul bab dikoreksi menurut halaman isi. Untuk Musnad Ahmad (ar-Risalah), pemeriksaan cetakan menemukan ±700 hadits bertanda (zawa'id Abdullah bin Ahmad, wijadah) yang dulu terbaca sebagai bagian hadits sebelumnya, sehingga riwayatnya tampil dengan nomor edisi yang salah; kini diperbaiki, dan sampel acak nomor yang berubah dicek di halaman cetak. Riwayat Lidwa yang teksnya mencakup dua hadits edisi berurutan kini diberi rentang nomor (mis. «47–48») bila kedua sanadnya ada di teks itu, tanpa penilaian muhaqqiq satu hadits. Pemeriksaan Tirmidzi juga menemukan 13 riwayat di beberapa kitab yang teksnya diulang penyusun di bab lain dan dulu tampil di tempat yang salah; kini diletakkan menurut nomornya. Setiap koreksi mencantumkan halaman buktinya. Teks dan nomor hadits Bukhari belum dicocokkan halaman per halaman.</p>
    <h2>Hadits populer &amp; palsu</h2>
    <p>Untuk ucapan yang sering beredar sebagai hadits, kami menampilkan pembahasan ulama dari empat kitab khusus: <i>al-Maudhu'at</i> (Ibnul Jauzi), <i>al-Maqashid al-Hasanah</i> (as-Sakhawi), <i>al-Asrar al-Marfu'ah</i> (Mulla 'Ali al-Qari), dan <i>Kasyf al-Khafa'</i> (al-'Ajluni). Kata kunci penilaian seperti <span class="ar" style="display:inline">باطل</span> (batil) dicari otomatis dan selalu ditampilkan bersama kalimat aslinya. Kami memilih aturan yang hati-hati: kata <i>shahih</i> atau <i>hasan</i> hanya ditandai bila jelas berupa penilaian (mis. <span class="ar" style="display:inline">إسناده صحيح</span>), bukan bagian dari judul kitab atau isi hadits. Bila sebuah ucapan hanya disebut di tengah pembahasan ucapan lain, penilaian entri itu tidak kami tempelkan padanya.</p>
    <h2 id="sumber">Sumber dan lisensi</h2>
    <p>Teman Hadits menyusun ulang data dari sumber-sumber berikut. Hak atas teks dan terjemahan tetap milik pemiliknya masing-masing.</p>
    <ul>
      <li><b>Terjemah Indonesia dan teks Arab 9 kitab + Musnad asy-Syafi'i:</b> <i>Ensiklopedi Hadits Kitab 9 Imam</i>, Lidwa Pusaka, <b>digunakan dengan izin Lidwa Pusaka</b>. Data diambil lewat carihadis.com dan repositori <a href="https://github.com/irsyadulibad/hadits-database" rel="noopener">irsyadulibad/hadits-database</a>.</li>
      <li><b>Teks Arab bernomor standar dan penilaian derajat atas nama ulama (7 kitab):</b> <a href="https://github.com/fawazahmed0/hadith-api" rel="noopener">fawazahmed0/hadith-api</a>, berlisensi Unlicense (domain publik).</li>
      <li><b>Judul kitab &amp; bab, teks edisi tahqiq (Musnad Ahmad, Sunan ad-Darimi, Musnad asy-Syafi'i), empat kitab hadits populer &amp; palsu, <i>Taqrib at-Tahdzib</i>, <i>Tahdzib al-Kamal</i>:</b> korpus OpenITI (Open Islamicate Texts Initiative), dilisensikan <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>. Sitasi: Nigst, L., Romanov, M., Savant, S. B., Seydi, M. &amp; Verkinderen, P., <i>OpenITI: a Machine-Readable Corpus of Islamicate Texts</i>, Zenodo, <a href="https://doi.org/10.5281/zenodo.3082463" rel="noopener">doi:10.5281/zenodo.3082463</a> (kami memakai repositori GitHub-nya pada commit yang tercantum di “Versi data”). Kitab-kitab ini karya ulama abad ke-3 sampai ke-12 H; edisi cetak yang menjadi dasar teks digitalnya disebut di setiap halaman kitab.
        <br><b>Perubahan kami:</b> teks dinormalisasi, dipotong per hadits/entri, dipetakan ke riwayat Lidwa, dan sebagian judul bab serta nomor edisi dikoreksi menurut kitab cetak (lihat bagian di atas). <b>Bagian situs yang memuat teks OpenITI</b> (judul kitab &amp; bab, nomor dan penilaian edisi tahqiq, ringkasan Ibnu Hajar, kutipan pembahasan ulama di katalog) kami bagikan dengan lisensi yang sama, <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>, untuk keperluan nonkomersial.</li>
      <li><b>Tema, terjemah yang ditinjau, derajat, dan penjelasan di halaman Tema:</b> <a href="https://hadeethenc.com" rel="noopener">HadeethEnc.com</a> (Ensiklopedia Terjemahan Hadits Nabi), ditampilkan tanpa diubah${info.hadeethenc_versi ? `, versi ${esc(info.hadeethenc_versi)}` : ""}.</li>
      <li><b>Pemeriksaan dengan kitab cetak:</b> hasil pindai kitab di <a href="https://archive.org" rel="noopener">archive.org</a> dipakai hanya untuk mencocokkan data (lihat bagian di atas). Gambarnya tidak ditampilkan ulang di situs ini.</li>
      <li><b>Versi data:</b> ${sumber.map(([s, c]) => `<code>${esc(s)}@${esc(c)}</code>`).join(", ")}, dibangun ${esc(info.dibangun)}.</li>
    </ul>
    <p class="kecil">Pemilik hak atas salah satu sumber di atas yang keberatan dengan cara datanya ditampilkan dapat menghubungi kami lewat tombol “Laporkan kesalahan”. Kami akan menanggapinya dan, bila perlu, menurunkan bagian itu.</p>
    <h2 id="privasi">Privasi</h2>
    <p>Situs ini tidak memakai cookie, iklan, atau analitik pihak ketiga. Teks yang Anda tempel di Cek Hadits dan kata yang Anda cari dikirim sebagai bagian alamat halaman, supaya hasilnya bisa dibagikan. Karena itu, hasilnya bisa tersimpan di cache server Cloudflare selama sekitar 1 jam. Jangan menempel data pribadi di kolom itu.</p>
    <h2>Laporkan kesalahan</h2>
    <p>Setiap halaman hadits punya tombol “Laporkan kesalahan”. Laporan diperiksa terhadap kitab cetak sebelum data diubah, dan setiap perubahan tercatat di riwayat kode.</p>
  </div>`;
}

export const halamanGalat = (judul, pesan) => `<div class="galat"><h1 class="halaman-judul">${esc(judul)}</h1><p>${pesan}</p><form class="kolom-cari" action="/cari" method="get"><label class="sembunyi" for="q-galat">Cari</label><input id="q-galat" name="q" type="search" placeholder="Cari hadits…"><button class="tombol" type="submit">Cari</button></form></div>`;

// ------------------------------------------------------------------------------------------------
// RIYADHUS SHALIHIN: kitab himpunan — an-Nawawi menyebut sahabat & sumbernya, tanpa sanad lengkap
// ------------------------------------------------------------------------------------------------
const NAMA_SUMBER = { bukhari: "al-Bukhari", muslim: "Muslim", abudawud: "Abu Dawud", tirmidzi: "at-Tirmidzi", nasai: "an-Nasa'i", ibnumajah: "Ibnu Majah", malik: "Malik", ahmad: "Ahmad", darimi: "ad-Darimi", syafii: "asy-Syafi'i" };

export function halamanRiyadh(d) {
  const { r, kitab, bab, info, sumber, penilaianSumber, tema, sebelum, sesudah, kanonik, sembunyiTerjemah } = d;
  const disebut = JSON.parse(info?.kitab_atribusi || "[]");
  const kelompok = {};
  for (const s of sumber) (kelompok[s.kitab_id] ||= { nama: s.kitab_nama, xs: [] }).xs.push(s);
  const cek = disebut.map((k) => {
    const xs = (kelompok[k]?.xs || []);
    return `<div><span class="tanda ${xs.length ? "ya" : "tidak"}">${xs.length ? "✓" : "–"}</span><b>${esc(NAMA_SUMBER[k] || k)}</b> <span class="num">${xs.length ? "no. " + xs.slice(0, 6).map((x) => `<a href="/${esc(x.kitab_id)}/${esc(x.slug)}">${esc(x.no_tampil)}</a>`).join(", ") : "belum ditemukan di kitab kami"}</span></div>`;
  }).join("");
  const dinilai = sumber.filter((s) => penilaianSumber.has(s.n)).slice(0, 4);
  const terjemah = r.terjemah && !sembunyiTerjemah;
  const rujukanTeks = `Riyadhus Shalihin no. ${r.no_tampil} (${info?.atribusi_ar || ""}). Sumber: Teman Hadits, ${kanonik}`;
  return `
  <nav class="remah" aria-label="Lokasi"><a href="/kitab">Kitab</a> › <a href="/kitab/riyadh">Riyadhus Shalihin</a>${bab ? ` › <a href="/kitab/riyadh/bab/${bab.no}">${esc(bab.nama || "Bab " + bab.no)}</a>` : ""} › <span>No. ${esc(r.no_tampil)}</span></nav>
  <div class="judul-hadits"><h1>Riyadhus Shalihin <span class="num">no. ${esc(r.no_tampil)}</span></h1></div>
  <div class="meta">${lencana(r.tingkat)}${info?.no_terjemah && String(info.no_terjemah) !== String(r.no_tampil) ? `<span class="chip num">nomor di terjemah: ${info.no_terjemah}</span>` : ""}<span class="chip">kitab himpunan an-Nawawi</span></div>
  ${r.alasan ? `<p class="kotak-info" style="margin-top:12px">${esc(r.alasan)}</p>` : ""}
  <article class="halaman">
    <div class="lembar">
      <div class="label">teks Riyadhus Shalihin · an-Nawawi menyebut sahabatnya, tanpa sanad lengkap</div>
      <p class="ar teks-utuh" id="teks-matan">${esc(r.arab)}</p>
      <div class="pemisah" aria-hidden="true">${SVG_BINTANG}</div>
      <div class="label">terjemahan Riyadhus Shalihin · bukan dari Lidwa Pusaka</div>
      ${terjemah ? `<p class="terjemah">${esc(r.terjemah)}</p>` : `<p class="tanpa-nilai">${r.terjemah ? "Terjemahan Riyadhus Shalihin belum ditampilkan sampai izin penerjemahnya dipastikan." : "Terjemahan belum terpasang untuk nomor ini, karena pasangannya di sumber terjemah tidak pasti."} Terjemahan riwayat sumbernya bisa dibaca lewat tautan di samping.</p>`}
      ${info?.catatan_ar ? `<details><summary class="kecil" style="cursor:pointer">Catatan kaki dalam teks digital ini (bukan teks an-Nawawi)</summary><p class="ar sanad" style="margin-top:8px">${esc(info.catatan_ar)}</p></details>` : ""}
      <div class="aksi">
        <button type="button" data-salin="${esc(rujukanTeks)}" data-pesan="Rujukan tersalin.">Salin rujukan</button>
        <button type="button" data-salin="1" data-salin-dari="#teks-matan" data-pesan="Teks Arab tersalin.">Salin teks Arab</button>
        <a href="https://github.com/FreyzS7/Teman-hadits/issues/new?title=${encodeURIComponent("Laporan: " + r.id)}&body=${encodeURIComponent("Halaman: " + kanonik + "\n\nApa yang keliru:\n\nRujukan pembanding (kitab cetak, halaman):\n")}" rel="noopener">Laporkan kesalahan</a>
      </div>
      <p class="label" id="status-salin" aria-live="polite"></p>
    </div>
    <aside class="hamisy" aria-label="Catatan pinggir">
      <section><h2>Sumber menurut an-Nawawi</h2>
        ${info?.atribusi_ar ? `<p class="ar" style="font-size:calc(1.25rem * var(--ar));line-height:1.8">${esc(info.atribusi_ar)}</p>` : `<p class="tanpa-nilai">Kalimat atribusi tidak ditemukan pada teks ini.</p>`}
        ${cek ? `<div class="klaim" style="margin-top:8px">${cek}</div><p class="kecil" style="margin-top:6px">✓ = riwayat dengan matan yang sama ditemukan di kitab tersebut dalam koleksi kami.</p>` : ""}
      </section>
      <section><h2>Derajat</h2>
        ${dinilai.length ? `<p style="margin:0 0 6px;font:500 .9rem/1.4 var(--f-ui)">${disebut.some((k) => k === "bukhari" || k === "muslim") ? `Riwayat ${disebut.filter((k) => k === "bukhari" || k === "muslim").map((k) => NAMA_SUMBER[k]).join(" dan ")} ada di kitab Shahih, yang di sumber kami tidak punya penilaian per hadits. Penilaian di bawah untuk jalur lain dengan matan yang sama:` : "Penilaian ulama atas riwayat sumbernya:"}</p>${dinilai.map((s) => `<div style="margin-top:10px"><div class="label" style="margin-bottom:4px"><a href="/${esc(s.kitab_id)}/${esc(s.slug)}">${esc(PENDEK[s.kitab_id])} no. ${esc(s.no_tampil)}</a></div>${bukuBesar(penilaianSumber.get(s.n), s.kitab_id)}</div>`).join("")}`
          : disebut.some((k) => k === "bukhari" || k === "muslim") ? `<p class="tanpa-nilai">Bersumber dari kitab Shahih menurut an-Nawawi. Sumber data kami tidak memuat penilaian per hadits untuk kitab Shahih, dan kami tidak mengisinya sendiri.</p>`
          : `<p class="tanpa-nilai">Belum ada penilaian ulama yang tercatat untuk riwayat sumbernya.</p>`}
      </section>
      <section><h2>Ditemukan di kitab kami</h2>
        ${sumber.length ? `<div class="jalur">${Object.entries(kelompok).map(([k, g]) => `<div><span class="kitab">${esc(g.nama)}</span><div class="nomor">${g.xs.map((x) => `<a class="${x.sahabat_sama ? "" : "mirip"}" href="/${esc(x.kitab_id)}/${esc(x.slug)}" title="matan ${Math.round(x.skor * 100)}% cocok${x.sahabat_sama ? ", sahabat sama" : ", sahabat berbeda"}">${esc(x.no_tampil)}</a>`).join("")}</div></div>`).join("")}</div>
        <p class="kecil" style="margin-top:8px">Kotak utuh = sahabat sama. Kotak putus-putus = matan sama dari sahabat lain.</p>` : `<p class="tanpa-nilai">Belum ditemukan riwayat dengan matan yang sama di kitab-kitab kami.</p>`}
      </section>
      ${tema.length ? `<section><h2>Tema</h2><div style="display:flex;flex-wrap:wrap;gap:6px">${tema.map((t) => `<a class="chip" href="/tema/${esc(t.id)}">${esc(t.judul)}</a>`).join("")}</div></section>` : ""}
      <section><h2>Asal data</h2><div class="asal">
        <span>Teks Arab dan terjemah: Riyadhus Shalihin via carihadis.com (irsyadulibad/hadits-database)</span>
        ${info?.no_terjemah ? "<span>Terjemah dipasangkan menurut isi (nama sahabat & atribusi), bukan menurut nomor</span>" : ""}
        <span>ID data: <code>${esc(r.id)}</code></span>
      </div></section>
    </aside>
  </article>
  <nav class="navigasi-hadits" aria-label="Hadits sebelum dan sesudah">${sebelum ? `<a href="/riyadh/${esc(sebelum.slug)}" rel="prev">← No. ${esc(sebelum.no_tampil)}</a>` : "<span></span>"}${sesudah ? `<a href="/riyadh/${esc(sesudah.slug)}" rel="next">No. ${esc(sesudah.no_tampil)} →</a>` : ""}</nav>`;
}

// ------------------------------------------------------------------------------------------------
// KATALOG UCAPAN POPULER & HADITS PALSU
// ------------------------------------------------------------------------------------------------
// Kelas warna (palsu/lemah/terima/lain) ditentukan pipeline (katalog_palsu.py) bersama daftar kata kuncinya.
const chipKunci = ([g, kelas]) => `<span class="chip kk-${esc(kelas || "lain")}">${esc(g)}</span>`;
const NAMA_KITAB_KATALOG = { maqashid: "al-Maqashid al-Hasanah", kasyf: "Kasyf al-Khafa'", asrar: "al-Asrar al-Marfu'ah", maudhuat: "al-Maudhu'at" };

function sorotKunci(konteks, kunci) {
  const t = esc(konteks);
  const k = esc(kunci);
  const i = t.indexOf(k);
  return i < 0 ? t : t.slice(0, i) + `<mark>${k}</mark>` + t.slice(i + k.length);
}

export function kartuEntri(e) {
  return `<article class="he">
    <h3 style="font-size:1.05rem;color:var(--zamrud);margin:0">${esc(e.kitab_nama)} <span class="num">no. ${e.no}</span> <span class="kecil">· ${esc(e.penulis)} (w. ${e.wafat} H)</span></h3>
    <p class="ar" style="font-weight:700">${esc(e.judul_ar)}</p>
    ${e.kata_kunci.length ? `<ul class="kunci-ulama">${e.kata_kunci.map(([k, g, ctx, kelas]) => `<li>${chipKunci([g, kelas])} <span class="ar">${sorotKunci(ctx, k)}</span></li>`).join("")}</ul>`
      : `<p class="kecil">Tidak ada kata kunci penilaian yang dikenali otomatis. Baca teks lengkapnya.</p>`}
    <details><summary class="kecil" style="cursor:pointer">Teks lengkap ${esc(e.penulis)}</summary><p class="ar" style="margin-top:8px">${esc(e.teks_ar)}</p></details>
  </article>`;
}

export function kotakKatalog({ populer, entri, riwayat = [] }) {
  if (!populer && !entri.length) return "";
  return `<section class="katalog-kotak">
    <h3>Dibahas ulama dalam kitab tentang hadits populer & palsu</h3>
    ${populer ? `<p>Teks Anda cocok dengan ucapan yang sering beredar: <b>“${esc(populer.teks_id)}”</b> <span class="ar" style="display:inline">${esc(populer.arab)}</span>. <a href="/populer/${esc(populer.id)}">Lihat pembahasan lengkap →</a></p>` : ""}
    ${riwayat.length ? `<p>Lafaz Arab ini juga ada di kitab hadits kami: ${riwayat.map((r) => `<a href="/${esc(r.kitab_id)}/${esc(r.slug)}">${esc(PENDEK[r.kitab_id])} ${esc(r.no_tampil)}</a>`).join(" · ")}</p>` : ""}
    ${entri.length ? `<div style="display:grid;gap:12px">${entri.map(kartuEntri).join("")}</div>` : `<p class="tanpa-nilai">Lafaz ini tidak ditemukan sebagai judul entri di keempat kitab katalog kami.</p>`}
    <p class="kecil">Kata kunci (mis. <span class="ar" style="display:inline">باطل</span> = batil) dicari otomatis di teks ulama dan ditampilkan bersama kalimat aslinya. Kata seperti <i>shahih</i> atau <i>hasan</i> sering merujuk riwayat lain yang dibahas di entri yang sama. Teman Hadits tidak membuat vonis sendiri; para ulama kadang berbeda pendapat, jadi bacalah kalimat lengkapnya.</p>
  </section>`;
}

export function halamanPopulerDaftar({ daftar }) {
  return `<h1 class="halaman-judul">Sering beredar, benarkah hadits?</h1>
  <p class="sub">Ucapan yang sering disebut “hadits” di masyarakat, dihubungkan ke pembahasan ulama dalam kitab-kitab khusus tentang hadits populer dan palsu: <i>al-Maqashid al-Hasanah</i> (as-Sakhawi), <i>Kasyf al-Khafa'</i> (al-'Ajluni), <i>al-Asrar al-Marfu'ah</i> (Mulla 'Ali al-Qari), dan <i>al-Maudhu'at</i> (Ibnul Jauzi). Beberapa di antaranya justru hadits yang memang ada di kitab hadits; itu juga ditunjukkan.</p>
  <p class="kecil" style="margin-top:8px">Daftar kalimat Indonesia dan lafaz Arabnya disusun Teman Hadits dan belum ditinjau ahli. Penilaian yang tampil selalu kutipan dari kitab ulama atau kitab hadits.</p>
  <ol class="daftar-populer">${daftar.map((p) => `<li><a href="/populer/${esc(p.id)}"><b>“${esc(p.teks_id)}”</b></a>
    <span class="ar">${esc(p.arab)}</span>
    <span class="baris-status">${p.riwayat ? `<span class="chip kk-terima">ada di kitab hadits kami (${p.riwayat} riwayat)</span>` : `<span class="chip kk-lain">tidak ada di 11 kitab hadits kami</span>`}
      ${p.kitab.length ? `<span class="kecil">dibahas di ${p.kitab.map((k) => esc(NAMA_KITAB_KATALOG[k])).join(", ")}</span>` : `<span class="kecil">tidak ditemukan di 4 kitab katalog</span>`}</span>
    ${p.kunci.length ? `<span class="baris-status"><span class="kecil">kata kunci di teks ulama:</span> ${p.kunci.slice(0, 6).map(chipKunci).join(" ")}</span>` : ""}</li>`).join("")}</ol>`;
}

export function halamanPopuler({ p }) {
  return `<nav class="remah"><a href="/populer">Sering beredar</a> › <span>${esc(p.teks_id)}</span></nav>
  <h1 class="halaman-judul" style="margin-top:10px">“${esc(p.teks_id)}”</h1>
  <p class="ar" style="font-size:calc(1.6rem * var(--ar));color:var(--zamrud);margin-top:6px">${esc(p.arab)}</p>
  <div class="catatan" style="margin-top:16px">${p.riwayat.length
    ? `<b>Ada di kitab hadits kami</b> dengan lafaz yang cocok: ${p.riwayat.map((r) => `<a href="/${esc(r.kitab_id)}/${esc(r.slug)}">${esc(r.kitab_nama)} no. ${esc(r.no_tampil)}</a>`).join(" · ")}. Bukalah untuk melihat sanad dan penilaian ulama.`
    : `<b>Tidak ditemukan</b> dengan lafaz ini di 11 kitab hadits kami (${"Bukhari, Muslim, Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah, Malik, Ahmad, Darimi, Syafi'i, Riyadhus Shalihin"}). Ini sendiri belum membuktikan palsu; lihat pembahasan ulama di bawah.`}</div>
  <section class="bagian" style="margin-top:26px"><header><h2>Pembahasan ulama</h2><p>Kutipan dari kitab-kitab tentang hadits populer dan palsu (teks OpenITI, <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.id" rel="license noopener">CC BY-NC-SA 4.0</a>; <a href="/metode#sumber">sumber</a>).</p></header>
    ${p.entri.length ? `<div style="display:grid;gap:14px">${p.entri.map(kartuEntri).join("")}</div>` : `<p class="tanpa-nilai">Lafaz ini tidak ditemukan sebagai judul entri di keempat kitab katalog kami. Mungkin ia dikenal dengan lafaz lain, atau memang tidak dibahas di kitab-kitab ini.</p>`}
  </section>
  ${p.sebut?.length ? `<section class="bagian" style="margin-top:26px"><header><h2>Disebut dalam pembahasan entri lain</h2><p>Lafaz ini muncul persis di tengah pembahasan ucapan lain. Kata kunci penilaian entri-entri itu <b>tidak</b> ditampilkan karena belum tentu tentang lafaz ini; bacalah kalimatnya.</p></header>
    <ul class="kunci-ulama">${p.sebut.map((x) => `<li><span class="kecil"><b>${esc(x.kitab_nama)} no. ${x.no}</b> (${esc(x.penulis)}), entri <span class="ar" style="display:inline">${esc(x.judul_ar.slice(0, 80))}</span></span><span class="ar">${sorotKunci(x.kutipan, normAr(p.arab))}</span></li>`).join("")}</ul>
  </section>` : ""}
  <p class="kecil" style="margin-top:18px">Kalimat Indonesia dan lafaz Arabnya disusun Teman Hadits (belum ditinjau). ${p.varian.length ? "Juga dikenal sebagai: " + p.varian.map((v) => `“${esc(v)}”`).join(", ") + "." : ""}</p>`;
}

export function bagianPopulerBeranda(daftar) {
  if (!daftar.length) return "";
  return `<section class="bagian" aria-labelledby="h-populer">
    <header><h2 id="h-populer">Sering beredar, benarkah hadits?</h2><p>Ucapan populer yang sering disebut hadits, beserta pembahasan ulama tentangnya. <a href="/populer">Lihat semua →</a></p></header>
    <div class="tema-daftar">${daftar.slice(0, 6).map((p) => `<a href="/populer/${esc(p.id)}" style="display:grid;gap:6px"><span>“${esc(p.teks_id)}”</span>${p.riwayat ? `<span class="chip kk-terima" style="justify-self:start">ada di kitab hadits</span>` : p.kunci.length ? `<span style="display:flex;gap:4px;flex-wrap:wrap">${p.kunci.slice(0, 3).map(chipKunci).join("")}</span>` : ""}</a>`).join("")}</div>
  </section>`;
}
