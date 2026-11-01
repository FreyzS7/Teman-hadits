// Ukur waktu CPU Worker per halaman (paket gratis Cloudflare: 10 ms CPU per permintaan; waktu menunggu D1 TIDAK dihitung).
// Worker dijalankan di Node dengan tiruan D1 di atas berkas SQLite lokal (hasil `npm run impor`); waktu yang dihabiskan
// di dalam SQLite dikurangkan, jadi angkanya = CPU kode Worker sendiri (sesudah pemanasan, seperti isolate yang sudah hangat).
// Waktu diukur dengan jam dinding thread utama (tiruan D1 sinkron, tanpa I/O), dikurangi waktu di SQLite: termasuk jeda GC
// di thread utama, tetapi BUKAN thread GC/JIT latar belakang (process.cpuUsage dulu ikut menghitungnya), seperti hitungan
// CPU isolate di Cloudflare. (process.threadCpuUsage terlalu kasar di Linux: ±4 ms per tik.) Hasil kueri di-round-trip JSON di luar waktu DB, karena di produksi Worker
// harus mengurai respons D1 (JSON) sendiri.
// Jalankan:  node scripts/ukur-cpu.mjs
import { DatabaseSync } from "node:sqlite";
import { readdirSync } from "node:fs";
import { performance } from "node:perf_hooks";
import worker from "../src/index.js";

const dir = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject";
const file = readdirSync(dir).find((f) => f.endsWith(".sqlite") && f !== "metadata.sqlite");
const sql = new DatabaseSync(`${dir}/${file}`, { readOnly: true });
let waktuDb = 0;

function stmt(q, args = []) {
  const jalankan = () => {
    const t = performance.now();
    const s = sql.prepare(q);
    const rows = s.all(...args);
    waktuDb += performance.now() - t;
    return JSON.parse(JSON.stringify(rows));
  };
  return {
    q, args,
    bind: (...a) => stmt(q, a),
    all: async () => ({ results: jalankan(), meta: { rows_read: 0 } }),
    run: async () => ({ results: jalankan(), meta: { rows_read: 0 } }),
    first: async (kol) => { const r = jalankan()[0]; return r === undefined ? null : kol ? r[kol] : r; },
    raw: async () => jalankan().map((r) => Object.values(r)),
  };
}
const env = {
  DB: { prepare: (q) => stmt(q), batch: async (xs) => Promise.all(xs.map((x) => x.all())) },
  TERJEMAH_RIYADH: "tampil",
};

const RUTE = ["/", "/bukhari/1", "/muslim/1907a", "/tirmidzi/1647", "/ahmad/1", "/riyadh/1", "/kitab/bukhari", "/kitab/bukhari/bab/1",
  "/tema", "/populer", "/populer/ilmu-negeri-cina", "/perawi", "/perawi/t2451", "/perawi/t8426", "/metode",
  "/cari?q=" + encodeURIComponent("tolong carikan hadits tentang sholat tarawih"), "/cari?q=niat", "/cari?q=muslim%201907",
  "/cek?t=" + encodeURIComponent("Sesungguhnya amalan itu tergantung niatnya (HR. Bukhari dan Muslim)"),
  "/cek?t=" + encodeURIComponent("Tuntutlah ilmu walau sampai ke negeri Cina"), "/cek?t=" + encodeURIComponent("حب الوطن من الإيمان")];

const ULANG = 20;
const hasil = [];
for (const r of RUTE) {
  const req = () => new Request("http://127.0.0.1:8787" + r);
  for (let i = 0; i < 3; i++) await (await worker.fetch(req(), env)).text();          // pemanasan JIT
  const sampel = [];
  for (let i = 0; i < ULANG; i++) {
    waktuDb = 0;
    const c0 = performance.now();
    const res = await worker.fetch(req(), env);
    await res.text();
    sampel.push(performance.now() - c0 - waktuDb);
  }
  sampel.sort((a, b) => a - b);
  hasil.push({ rute: r.length > 60 ? r.slice(0, 57) + "..." : r, median_ms: +sampel[ULANG >> 1].toFixed(2), p90_ms: +sampel[Math.floor(ULANG * 0.9)].toFixed(2) });
}
console.table(hasil);
const lewat = hasil.filter((h) => h.p90_ms > 10);
console.log(lewat.length ? `MELEWATI 10 ms (p90): ${lewat.map((h) => h.rute).join(", ")}` : "Semua rute di bawah 10 ms CPU (p90).");
