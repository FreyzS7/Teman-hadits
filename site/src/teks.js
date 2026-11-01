// Pengolahan teks: normalisasi Arab/Indonesia, lafaz periwayatan, pemisahan sanad-matan, rantai perawi.
// Normalisasi WAJIB identik dengan pipeline/common.py (diuji oleh test/paritas.test.js).

const HARAKAT = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
const HRK = "[\\u064B-\\u0652\\u0670\\u0640]*";
const ALIF = { "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": "" };
const NON_AR = /[^ء-ي\s]/g;
const WS = /\s+/g;

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export function stripHarakat(s) {
  return String(s ?? "").replace(HARAKAT, "");
}

export function normAr(s) {
  let t = String(s ?? "").normalize("NFC").replace(HARAKAT, "");
  t = t.replace(/[أإآٱىةؤئء]/g, (c) => ALIF[c]);
  return t.replace(NON_AR, " ").replace(WS, " ").trim();
}

export function normId(s) {
  let t = String(s ?? "").normalize("NFKD").toLowerCase();
  t = t.replace(/\p{M}/gu, "");
  t = t.replace(/[`'’‘]/g, "");
  t = t.replace(/[^a-z0-9\s]/g, " ");
  return t.replace(WS, " ").trim();
}

const PROKLITIK = ["وبال", "وكال", "فبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل"];
export function stemAr(w) {
  for (const p of PROKLITIK) if (w.startsWith(p) && [...w].length - [...p].length >= 3) return w.slice(p.length);
  return w;
}
export const akarAr = (normalized) => normalized.split(" ").filter(Boolean).map(stemAr).join(" ");

export function stemId(w) {
  for (const s of ["nya", "kan", "lah", "an"]) if (w.endsWith(s) && w.length - s.length >= 4) return w.slice(0, -s.length);
  return w;
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
  "يحدث", "حدثه", "اخبره", "في", "علي", "قالا", "قالوا", "وهو", "ذكر", "عن"]);

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
      if (!bersih || HENTI_NAMA.has(normAr(bersih))) break;
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

export const fmt = (n) => Number(n ?? 0).toLocaleString("id-ID");
