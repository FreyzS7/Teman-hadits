// Jalankan banyak kueri sekaligus terhadap D1 LOKAL dan laporkan yang lemah (hasil 0, hanya "sebagian kata", atau
// < 3 riwayat). Dipakai untuk mencari istilah yang perlu entri kamus sebelum ada pengguna sungguhan.
//   node scripts/uji-kueri.mjs berkas-kueri.txt      (satu kueri per baris)
import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import { cari } from "../src/cari.js";

const d = new URL("../.wrangler/state/v3/d1/miniflare-D1DatabaseObject/", import.meta.url);
const f = fs.readdirSync(d).find((x) => x.endsWith(".sqlite") && !x.startsWith("metadata"));
const raw = new DatabaseSync(new URL(f, d), { readOnly: true });
const urut = (s, a) => { const m = [...s.matchAll(/\?(\d+)/g)]; return m.length ? m.map((x) => a[+x[1] - 1]) : a; };
const db = { prepare: (s) => { let a = []; const o = { bind: (...x) => { a = x; return o; },
  all: async () => ({ results: raw.prepare(s.replace(/\?(\d+)/g, "?")).all(...urut(s, a)) }),
  first: async () => raw.prepare(s.replace(/\?(\d+)/g, "?")).get(...urut(s, a)) }; return o; } };
const kueri = fs.readFileSync(process.argv[2], "utf8").split("\n").map((x) => x.trim()).filter((x) => x && !/[؀-ۿ]/.test(x));
let lemah = 0;
for (const q of kueri) {
  const r = await cari(db, q, { perHalaman: 1, abaikanIdRiyadh: true });
  const alasan = r.total === 0 ? "kosong" : r.modeKata === "sebagian kata" ? "sebagian" : r.total < 3 ? "sedikit" : null;
  if (alasan) { lemah++; console.log(`${alasan}\t${r.total}\t${q}`); }
}
console.error(`${kueri.length} kueri, ${lemah} lemah`);
