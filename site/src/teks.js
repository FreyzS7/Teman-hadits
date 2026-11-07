// Pengolahan teks: normalisasi Arab/Indonesia, lafaz periwayatan, pemisahan sanad-matan, rantai perawi.
// Normalisasi WAJIB identik dengan pipeline/common.py (diuji oleh test/paritas.test.js).

const HARAKAT = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
const HRK = "[\\u064B-\\u0652\\u0670\\u0640]*";
const ALIF = { "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": "" };
const WS = /\s+/g;

const ENTITAS = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ENTITAS[c]);

export function stripHarakat(s) {
  return String(s ?? "").replace(HARAKAT, "");
}

// Definisi normAr (sama dengan norm_ar di Python):
//   t.normalize("NFC").replace(HARAKAT, "").replace(/[أإآٱىةؤئء]/g, (c) => ALIF[c]).replace(NON_AR, " ").replace(WS, " ").trim()
// Ditulis sebagai satu putaran per karakter karena inilah bagian terberat "cek teks" Arab (80 teks kandidat per
// permintaan; diukur ±3,5x lebih cepat). Hasilnya identik: diuji pada semua teks Arab di database + uji acak
// (test/teks.test.js). NFC hanya dijalankan bila ada hamzah/madd penggabung (U+0653–U+0655): hanya itulah yang dapat
// bergabung dengan huruf ء-ي; selebihnya NFC cuma menata ulang/menggabung tanda & huruf non-Arab, yang tetap dibuang
// (harakat) atau menjadi satu spasi.
const PETA_AR = new Uint16Array(0x0672 - 0x0620);
for (const [a, b] of Object.entries(ALIF)) if (b) PETA_AR[a.charCodeAt(0) - 0x0620] = b.charCodeAt(0);
const harakat = (c) => (c >= 0x064b && c <= 0x065f) || (c >= 0x0610 && c <= 0x061a) || c === 0x0670 || c === 0x0640 || (c >= 0x06d6 && c <= 0x06ed);
export function normAr(s) {
  let t = String(s ?? "");
  if (/[ٓ-ٕ]/.test(t)) t = t.normalize("NFC");
  const kode = [];
  let spasi = false;
  for (let i = 0; i < t.length; i++) {
    let c = t.charCodeAt(i);
    if (c === 0x0621 || harakat(c)) continue; // harakat & hamzah lepas dibuang tanpa spasi
    if (c >= 0x0620 && c < 0x0672 && PETA_AR[c - 0x0620]) c = PETA_AR[c - 0x0620];
    if (c >= 0x0621 && c <= 0x064a) {
      if (spasi && kode.length) kode.push(32);
      spasi = false;
      kode.push(c);
    } else spasi = true;
  }
  let out = "";
  for (let i = 0; i < kode.length; i += 8192) out += String.fromCharCode.apply(null, kode.slice(i, i + 8192));
  return out;
}

/** Langkah awal normId: huruf kecil, tanpa diakritik & tanda kutip (belum memisah kata). */
export function dasarId(s) {
  let t = String(s ?? "").normalize("NFKD").toLowerCase();
  t = t.replace(/\p{M}/gu, "");
  return t.replace(/[`'’‘]/g, "");
}

export function normId(s) {
  return dasarId(s).replace(/[^a-z0-9\s]/g, " ").replace(WS, " ").trim();
}

// semua awalan di BMP, jadi [...p].length === p.length; panjang kata dihitung per code point seperti len() Python
const PROKLITIK = ["وبال", "وكال", "فبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل"];
const panjangKode = (w) => {
  let n = w.length;
  for (let i = 0; i < w.length - 1; i++) {
    const c = w.charCodeAt(i), d = w.charCodeAt(i + 1);
    if (c >= 0xd800 && c <= 0xdbff && d >= 0xdc00 && d <= 0xdfff) { n--; i++; }
  }
  return n;
};
export function stemAr(w) {
  for (const p of PROKLITIK) if (w.startsWith(p) && panjangKode(w) - p.length >= 3) return w.slice(p.length);
  return w;
}
export const akarAr = (normalized) => normalized.split(" ").filter(Boolean).map(stemAr).join(" ");

const AKHIRAN_ID = ["nya", "kan", "lah", "an"];
export function stemId(w) {
  for (const s of AKHIRAN_ID) if (w.endsWith(s) && w.length - s.length >= 4) return w.slice(0, -s.length);
  return w;
}

const alnum = (c) => (c >= 97 && c <= 122) || (c >= 48 && c <= 57);
/**
 * Kata kueri Q (sudah di-stem) yang menjadi awalan suatu kata ber-stem di teks. Sama dengan
 *   Q.filter((w) => [...new Set(normId(teks).split(" ").map(stemId))].some((k) => k.startsWith(w)))
 * tetapi tanpa membuat string per kata (dipakai "cek teks" untuk 120 terjemah kandidat). Kata = deretan [a-z0-9] di
 * dasarId(teks); stemId(kata) selalu awalan kata itu, jadi cukup periksa kata.startsWith(w) lalu panjang stem-nya.
 */
/**
 * Liputan terbaik dalam satu jendela: jumlah bobot kata kueri (Q, sudah di-stem; aturan cocok sama dengan awalanId)
 * yang muncul bersama dalam `jendela` kata berurutan, beserta rentangnya (jarak kata pertama-terakhir; makin kecil
 * makin rapat). `kunci` (opsional): ejaan -> kunci grupnya, supaya "sholat" dan "shalat" dihitung sebagai satu kata. Dipakai Cek Hadits supaya kata-kata yang tersebar jauh di
 * riwayat panjang tidak dianggap satu kalimat.
 */
export function liputanJendela(teks, Q, bobot, jendela, kunci = null) {
  const t = dasarId(teks), kena = [];
  const awal = new Uint8Array(128);
  for (const w of Q) awal[w.charCodeAt(0) & 127] = 1;
  let pos = 0;
  for (let i = 0; i < t.length;) {
    if (!alnum(t.charCodeAt(i))) { i++; continue; }
    let e = i + 1;
    while (e < t.length && alnum(t.charCodeAt(e))) e++;
    if (awal[t.charCodeAt(i)]) {
      const L = e - i;
      let st = L;
      for (const s of AKHIRAN_ID) if (L - s.length >= 4 && t.startsWith(s, e - s.length)) { st = L - s.length; break; }
      for (const w of Q) if (st >= w.length && t.startsWith(w, i)) kena.push([pos, kunci ? kunci.get(w) ?? w : w]);
    }
    pos++;
    i = e;
  }
  const hitung = new Map();
  let terbaik = 0, rentang = Infinity, jumlah = 0, kiri = 0;
  for (let kanan = 0; kanan < kena.length; kanan++) {
    const [p, w] = kena[kanan];
    hitung.set(w, (hitung.get(w) || 0) + 1);
    if (hitung.get(w) === 1) jumlah += bobot.get(w);
    while (p - kena[kiri][0] >= jendela) {
      const v = kena[kiri][1];
      hitung.set(v, hitung.get(v) - 1);
      if (hitung.get(v) === 0) jumlah -= bobot.get(v);
      kiri++;
    }
    // geser kiri selama kata paling kiri masih ada di sisi kanan: jendela terpendek untuk liputan ini
    while (kiri < kanan && hitung.get(kena[kiri][1]) > 1) { hitung.set(kena[kiri][1], hitung.get(kena[kiri][1]) - 1); kiri++; }
    const r = p - kena[kiri][0];
    if (jumlah > terbaik + 1e-9 || (Math.abs(jumlah - terbaik) <= 1e-9 && r < rentang)) { terbaik = jumlah; rentang = r; }
  }
  return { skor: terbaik, rentang };
}

export function awalanId(teks, Q) {
  const t = dasarId(teks), ada = new Set();
  const awal = new Uint8Array(128);
  for (const w of Q) awal[w.charCodeAt(0) & 127] = 1;
  for (let i = 0; i < t.length && ada.size < Q.length;) {
    if (!alnum(t.charCodeAt(i))) { i++; continue; }
    let e = i + 1;
    while (e < t.length && alnum(t.charCodeAt(e))) e++;
    if (awal[t.charCodeAt(i)]) {
      const L = e - i;
      let st = L;
      for (const s of AKHIRAN_ID) if (L - s.length >= 4 && t.startsWith(s, e - s.length)) { st = L - s.length; break; }
      for (const w of Q) if (st >= w.length && !ada.has(w) && t.startsWith(w, i)) ada.add(w);
    }
    i = e;
  }
  return ada;
}

export const adaArab = (s) => (String(s).match(/[ء-ي]/g) || []).length >= 8;

// ---------------------------------------------------------------------------------------------
// Lafaz periwayatan (sighah) dan rantai sanad
// ---------------------------------------------------------------------------------------------
export const SIGHAH = [
  { k: "حدثنا", latin: "haddatsanā", arti: "menceritakan kepada kami", ket: "Lafaz penyampaian langsung: guru membacakan, murid mendengar." },
  { k: "حدثني", latin: "haddatsanī", arti: "menceritakan kepadaku", ket: "Seperti haddatsanā, tetapi murid mendengar sendirian." },
  { k: "أخبرنا", latin: "akhbaranā", arti: "mengabarkan kepada kami", ket: "Penyampaian langsung; banyak ulama memakainya untuk murid yang membaca di hadapan guru." },
  { k: "أخبرني", latin: "akhbaranī", arti: "mengabarkan kepadaku", ket: "Penyampaian langsung; banyak ulama memakainya untuk murid yang membaca di hadapan guru." },
  { k: "سمعت", latin: "sami'tu", arti: "aku mendengar", ket: "Pernyataan tegas mendengar langsung." },
  { k: "سمع", latin: "sami'a", arti: "ia mendengar", ket: "Pernyataan tegas mendengar langsung." },
  { k: "عن", latin: "'an", arti: "dari", ket: "Tidak tegas apakah mendengar langsung; ulama memeriksanya untuk kemungkinan tadlis." },
];
export const SIGHAH_MAP = Object.fromEntries(SIGHAH.map((s) => [s.k, s]));

const VARIAN_HURUF = { "ا": "[اأإآٱ]", "ي": "[يى]", "ه": "[هة]" };
function pola(kata, toleran = false) {
  return [...kata].map((c) => (c === " " ? "\\s+" : (toleran && VARIAN_HURUF[c]) || c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) + (c === " " ? "" : HRK)).join("");
}
const HUR = "[\\u0621-\\u064A]";
// batas kata harus melewati harakat: "عَنْهُ" (رضي الله عنه) bukan lafaz "عن"
const RE_SIGHAH = new RegExp(
  SIGHAH.map((s) => `(?<![\\u0621-\\u064A\\u064B-\\u0652])(?:[وف]${HRK})?${pola(s.k)}(?!${HRK}${HUR})`).join("|"),
  "g",
);

export function kunciSighah(lafaz) {
  let b = normAr(lafaz);
  if ((b[0] === "و" || b[0] === "ف") && b.length > 2) b = b.slice(1);
  for (const s of SIGHAH) if (normAr(s.k) === b) return s.k;
  return null;
}

/** Tandai lafaz periwayatan dengan <span class="sg"> (teks di-escape). */
export function rubrik(teks) {
  let out = "", last = 0;
  for (const m of teks.matchAll(RE_SIGHAH)) {
    out += esc(teks.slice(last, m.index));
    const k = kunciSighah(m[0]);
    const g = SIGHAH_MAP[k];
    const cls = k === "عن" ? "sg sg-an" : "sg";
    const judul = g ? ` title="${esc(`${g.latin}: “${g.arti}”. ${g.ket}`)}" tabindex="0"` : "";
    out += `<span class="${cls}"${judul}>${esc(m[0])}</span>`;
    last = m.index + m[0].length;
  }
  return out + esc(teks.slice(last));
}

const RE_SALAWAT = new RegExp(`(?:${pola("صلي الله عليه وسلم", true)}|ﷺ)`);
const RE_SETELAH = new RegExp(`^\\s*[،,]?\\s*(?:(?:${pola("قال", true)}|${pola("يقول", true)}|${pola("فقال", true)})\\s*:?)?\\s*`);

/** Pisahkan sanad dan matan. Kembalikan {sanad, matan} atau null bila tidak bisa dipisahkan dengan yakin. */
export function pisahSanad(arab) {
  const t = String(arab ?? "").trim();
  for (const tanda of ['"', "«", "“"]) {
    const i = t.indexOf(tanda);
    if (i > 10) {
      const matan = t.slice(i + 1).replace(/["»”‏\s.]+$/u, "").trim();
      if (matan.split(/\s+/).length >= 4) return { sanad: t.slice(0, i).replace(/[‏\s]+$/u, ""), matan };
    }
  }
  const m = t.match(RE_SALAWAT);
  if (m) {
    const akhir = m.index + m[0].length;
    const sisa = t.slice(akhir);
    const s = sisa.match(RE_SETELAH);
    const potong = akhir + (s ? s[0].length : 0);
    const matan = t.slice(potong).trim();
    if (matan.split(/\s+/).length >= 4) return { sanad: t.slice(0, potong).trim(), matan };
  }
  return null;
}

// Komentar penyusun yang ikut tertulis setelah matan (at-Tirmidzi: "قال أبو عيسى …"). Bukan bagian matan.
const RE_KOMENTAR = new RegExp(`(?:${pola("قال", true)}\\s+)?${pola("ابو عيسي", true)}`);
export function pisahKomentar(matan) {
  const m = String(matan ?? "").match(RE_KOMENTAR);
  if (!m || m.index < 10) return { matan, komentar: null };
  return { matan: matan.slice(0, m.index).replace(/["»”\u200f\s.،]+$/u, "").trim(), komentar: matan.slice(m.index).trim() };
}

const HENTI_NAMA = new Set(["قال", "قالت", "ان", "انه", "انها", "يقول", "تقول", "رضي", "يرفعه", "يبلغ", "به", "نحوه", "مثله",
  "يحدث", "حدثه", "اخبره", "في", "قالا", "قالوا", "وهو", "ذكر", "عن"]);
// "عَلَى" (huruf jar, alif maqshurah) menghentikan nama; "عَلِيّ" (nama) tidak. Setelah normalisasi keduanya "علي".
const HURUF_JAR_ALA = "على";

/** Rantai dari teks Arab sanad: [{lafaz, sighah, namaAr, nabi}] urut dari guru penyusun ke atas. */
export function rantaiArab(sanad) {
  const ms = [...sanad.matchAll(RE_SIGHAH)];
  const segs = [];
  ms.forEach((m, i) => {
    const akhir = i + 1 < ms.length ? ms[i + 1].index : sanad.length;
    const kata = sanad.slice(m.index + m[0].length, akhir).trim().split(/\s+/);
    const nama = [];
    for (const w of kata) {
      const bersih = w.replace(/[،,:؛.‏"]+$/u, "");
      if (!bersih || HENTI_NAMA.has(normAr(bersih)) || stripHarakat(bersih) === HURUF_JAR_ALA) break;
      nama.push(bersih);
      if (bersih !== w) break; // ada tanda baca di akhir kata: nama selesai
    }
    if (!nama.length) return;
    const namaAr = nama.join(" ");
    const n = normAr(namaAr);
    segs.push({ lafaz: m[0], sighah: kunciSighah(m[0]), namaAr, nabi: /^(رسول الله|النبي|نبي الله)/.test(n) });
  });
  // berhenti di Nabi ﷺ: segmen sesudahnya (bila ada) bagian dari matan
  const iNabi = segs.findIndex((s) => s.nabi);
  return iNabi >= 0 ? segs.slice(0, iNabi + 1) : segs;
}

/** Penilaian at-Tirmidzi sendiri yang tertulis di dalam Jami'-nya: "قال أبو عيسى: هذا حديث حسن صحيح". */
export function hukumTirmidzi(arab) {
  const n = normAr(arab);
  const m = n.match(/قال ابو عيسي\s+(?:و)?هذا حديث((?:\s+(?:حسن|صحيح|غريب|ضعيف|منكر|مرسل|مضطرب)){1,4})/);
  return m ? m[1].trim() : null;
}

/** Potongan teks di sekitar salah satu kata (case-insensitive), dengan <mark>. */
export function cuplik(teks, kata, lebar = 150) {
  const t = String(teks ?? "");
  const kecil = t.toLowerCase();
  let pos = -1, panjang = 0;
  for (const k of kata) {
    if (!k) continue;
    const i = kecil.indexOf(k.toLowerCase());
    if (i >= 0 && (pos < 0 || i < pos)) { pos = i; panjang = k.length; }
  }
  if (pos < 0) return esc(t.slice(0, lebar * 2)) + (t.length > lebar * 2 ? "…" : "");
  const a = Math.max(0, pos - lebar), b = Math.min(t.length, pos + panjang + lebar);
  const tandai = (s) => {
    let out = esc(s);
    for (const k of kata) if (k && k.length >= 3) out = out.replace(new RegExp(esc(k).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), (x) => `<mark>${x}</mark>`);
    return out;
  };
  return (a ? "…" : "") + tandai(t.slice(a, b)) + (b < t.length ? "…" : "");
}

/** Potongan teks Arab di sekitar kata yang (setelah normalisasi) memuat salah satu akar. */
export function cuplikAr(arab, akar, jendela = 8) {
  const w = String(arab ?? "").split(/\s+/);
  const cari = akar.map((a) => normAr(a)).filter(Boolean);
  for (let i = 0; i < w.length; i++) {
    const nw = normAr(w[i]);
    if (cari.some((a) => nw.includes(a))) {
      const a = Math.max(0, i - jendela), b = Math.min(w.length, i + jendela + 1);
      return (a ? "… " : "") + w.slice(a, i).map(esc).join(" ") + ` <mark>${esc(w[i])}</mark> ` + w.slice(i + 1, b).map(esc).join(" ") + (b < w.length ? " …" : "");
    }
  }
  return w.slice(0, 16).map(esc).join(" ") + (w.length > 16 ? " …" : "");
}

// sama dengan Number(n).toLocaleString("id-ID"), tetapi formatter dibuat sekali (toLocaleString membuatnya tiap panggilan)
const ANGKA_ID = new Intl.NumberFormat("id-ID");
export const fmt = (n) => ANGKA_ID.format(Number(n ?? 0));

/** Cuplikan matan untuk meta description / pratinjau tautan. Terjemah Lidwa diawali sanad («Telah menceritakan kepada
 *  kami [A] dari [B] ...»); cuplikan dimulai sesudah nama perawi terakhir sebelum kutipan pertama. */
export function cuplikMatan(t, maks = 155) {
  t = String(t || "");
  const kutip = t.search(/["“]/);
  const akhirSanad = t.lastIndexOf("]", kutip > 0 ? kutip : Math.floor(t.length * 0.6));
  let awal = akhirSanad >= 0 ? akhirSanad + 1 : 0;
  if (kutip > awal) {                     // mulai dari klausa terakhir sebelum kutipan: «saya mendengar Rasulullah ... bersabda: "...»
    const jeda = Math.max(...[";", ",", "."].map((c) => t.lastIndexOf(c, kutip - 2)));
    if (jeda > awal) awal = jeda + 1;
  }
  let s = t.slice(awal).replace(/[[\]]/g, "").replace(/\s+/g, " ").replace(/^[\s,;:."“”']+/, "").trim();
  s = s.charAt(0).toUpperCase() + s.slice(1);
  if (s.length < 40) s = t.replace(/[[\]]/g, "").replace(/\s+/g, " ").trim();
  if (s.length <= maks) return s;
  const potong = s.slice(0, maks - 1);
  return potong.slice(0, Math.max(potong.lastIndexOf(" "), maks - 20)).replace(/[\s,;:]+$/, "") + "…";
}
