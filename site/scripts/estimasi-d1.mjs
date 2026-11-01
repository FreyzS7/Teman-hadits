// Perkiraan beban D1 untuk impor penuh ke Cloudflare, dihitung dari database LOKAL (sesudah `npm run impor`).
// D1 menghitung setiap baris tabel DAN setiap entri indeks sebagai "baris ditulis" (paket gratis: 100.000/hari).
// Jalankan:  node scripts/estimasi-d1.mjs
import { DatabaseSync } from "node:sqlite";
import { readdirSync, statSync } from "node:fs";

const dir = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject";
const file = readdirSync(dir).find((f) => f.endsWith(".sqlite") && f !== "metadata.sqlite");
const db = new DatabaseSync(`${dir}/${file}`, { readOnly: true });
const tabel = db.prepare("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%'").all();
const indeks = db.prepare("SELECT tbl_name, count(*) AS n FROM sqlite_master WHERE type='index' GROUP BY tbl_name").all();
const nIdx = Object.fromEntries(indeks.map((x) => [x.tbl_name, x.n]));
let baris = 0, tulis = 0;
const rinci = [];
for (const t of tabel) {
  if (/VIRTUAL TABLE/i.test(t.sql || "")) continue;            // tabel FTS: isinya dihitung lewat tabel bayangannya
  const n = db.prepare(`SELECT count(*) AS c FROM "${t.name}"`).get().c;
  const w = n * (1 + (nIdx[t.name] || 0));
  baris += n; tulis += w;
  rinci.push({ tabel: t.name, baris: n, indeks: nIdx[t.name] || 0, ditulis: w });
}
rinci.sort((a, b) => b.ditulis - a.ditulis);
console.table(rinci.slice(0, 15));
const mb = statSync(`${dir}/${file}`).size / 1e6;
console.log(`Ukuran database: ${mb.toFixed(0)} MB`);
console.log(`Baris tabel: ${baris.toLocaleString("id")}; perkiraan baris DITULIS saat impor penuh: ${tulis.toLocaleString("id")}`);
console.log(`Paket gratis (100.000 tulis/hari): ±${Math.ceil(tulis / 100000)} hari. Paket Workers Paid (50 juta tulis/bulan termasuk): sekali jalan.`);
