// Versi cepat fungsi teks (ditulis ulang demi batas CPU Worker) harus memberi hasil PERSIS sama dengan definisi
// aslinya yang berbasis regex. Definisi asli ditulis ulang di sini sebagai acuan.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { awalanId, fmt, normAr, normId, stemAr, stemId } from "../src/teks.js";

const F = JSON.parse(readFileSync(new URL("./fixtures/paritas.json", import.meta.url), "utf8"));
const ALIF = { "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": "" };
const acuanNormAr = (s) => String(s ?? "").normalize("NFC").replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, "")
  .replace(/[أإآٱىةؤئء]/g, (c) => ALIF[c]).replace(/[^ء-ي\s]/g, " ").replace(/\s+/g, " ").trim();
const acuanStemAr = (w) => {
  for (const p of ["وبال", "وكال", "فبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل"]) {
    if (w.startsWith(p) && [...w].length - [...p].length >= 3) return w.slice(p.length);
  }
  return w;
};
const acuanAwalan = (teks, Q) => {
  const kata = [...new Set(normId(teks).split(" ").map(stemId))];
  return Q.filter((w) => kata.some((k) => k === w || k.startsWith(w)));
};

let benih = 20261101;
const acak = () => ((benih = (benih * 1103515245 + 12345) % 2147483648) / 2147483648);
const pilih = (xs) => xs[Math.floor(acak() * xs.length)];

test("normAr cepat = definisi regex (teks uji + 100.000 string acak)", () => {
  for (const x of F.normalisasi) assert.equal(normAr(x.masuk.arab), acuanNormAr(x.masuk.arab), x.masuk.id);
  // huruf yang bisa digabung NFC (ا و ي ه ە ہ ے + hamzah/madd U+0653–0655), harakat, tatwil, hamzah lepas,
  // spasi Unicode, huruf Latin + tanda gabung, angka Arab, bentuk penyajian, surrogate
  const kode = [0x627, 0x648, 0x64a, 0x647, 0x6d5, 0x6c1, 0x6d2, 0x653, 0x654, 0x655, 0x651, 0x64e, 0x650, 0x652, 0x640,
    0x621, 0x623, 0x625, 0x622, 0x671, 0x629, 0x649, 0x624, 0x626, 0x6c0, 0x610, 0x61a, 0x61b, 0x670, 0x6d6, 0x6ed, 0x660,
    0x6f0, 0x20, 0xa0, 0x9, 0xa, 0x2028, 0x3000, 0xfeff, 0x41, 0x65, 0x301, 0x300, 0xfdf2, 0xfe8e, 0xd83d, 0xde00, 0x631, 0x628];
  for (let i = 0; i < 100000; i++) {
    let s = "";
    for (let j = 1 + Math.floor(acak() * 12); j > 0; j--) s += String.fromCharCode(pilih(kode));
    assert.equal(normAr(s), acuanNormAr(s), JSON.stringify([...s].map((c) => c.codePointAt(0).toString(16))));
  }
  assert.equal(normAr(null), "");
});

test("stemAr menghitung panjang per code point seperti len() Python", () => {
  for (const w of ["الرحمن", "الله", "ولد", "والد", "بالله", "ال😀😀", "ال😀😀😀", "و\ud83d", "لل\ude00ab", "كتاب"]) assert.equal(stemAr(w), acuanStemAr(w), w);
  for (const x of F.normalisasi) for (const w of normAr(x.masuk.arab).split(" ")) assert.equal(stemAr(w), acuanStemAr(w));
});

test("awalanId = pencocokan awalan per kata ber-stem (teks uji + kalimat acak)", () => {
  for (const x of F.normalisasi) {
    const kata = normId(x.masuk.terjemah).split(" ").filter((w) => w.length >= 3);
    for (let k = 0; k < 5 && kata.length; k++) {
      const Q = [...new Set([0, 1, 2].flatMap(() => { const w = pilih(kata); return [w, stemId(w), w.slice(0, 3), w.slice(0, -1), w + "x"]; }).filter((w) => w.length >= 3))];
      assert.deepEqual([...awalanId(x.masuk.terjemah, Q)].sort(), acuanAwalan(x.masuk.terjemah, Q).sort(), x.masuk.id);
    }
  }
  const potongan = ["ka", "kan", "an", "nya", "lah", "a", "m", "ma", "ta", "'", "’", "é", "-", " ", "1", "la", "h", "n", "y", "Ä"];
  for (let i = 0; i < 50000; i++) {
    let s = "";
    for (let j = 1 + Math.floor(acak() * 10); j > 0; j--) s += pilih(potongan);
    const Q = [...new Set(normId(s).split(" ").flatMap((w) => [w, stemId(w), w.slice(0, 3), w.slice(0, -1)]).filter((w) => w.length >= 3))];
    assert.deepEqual([...awalanId(s, Q)].sort(), acuanAwalan(s, Q).sort(), s);
  }
});

test("fmt = toLocaleString('id-ID')", () => {
  for (const n of [0, 7, 1234, 60000, 1234567, 12.5, null, undefined, "4521"]) assert.equal(fmt(n), Number(n ?? 0).toLocaleString("id-ID"));
});
