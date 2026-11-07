// Ukur ketepatan Cek Hadits (teks Indonesia) terhadap database D1 LOKAL (npm run impor dulu).
// 100 riwayat tingkat A acak (biji tetap) -> potongan 8-15 kata dari kutipan sabda di terjemahnya -> cek().
// "tepat" = riwayat asal; "keluarga" = sekelompok (riwayat.grup) atau ada di keluarga takhrij hasil; "lain" = riwayat
// lain (bisa sah: potongan umum atau riwayat saudara dengan teks sama, lihat docs/06). Butuh Node >= 22.5 (node:sqlite).
//   node scripts/uji-cek.mjs          (teks Indonesia)
//   node scripts/uji-cek.mjs arab     (potongan 6-12 kata matan Arab, berharakat, tanpa sanad)
//   "wa" = potongan gaya pesan WhatsApp (pembuka "Rasulullah SAW bersabda:", singkatan yg/dgn/utk, emoji, "(HR. Bukhari)");
//   "pendek" = potongan 4-6 kata. Tambahkan "rinci" untuk mencetak setiap kasus "lain"; "ejaan" untuk potongan yang ejaannya diganti varian lain; "dasar" untuk kata berawalan diganti kata dasarnya
import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import { cek } from "../src/cek.js";
import { pisahSanad } from "../src/teks.js";
const ARAB = process.argv.includes("arab"), RINCI = process.argv.includes("rinci"), EJAAN = process.argv.includes("ejaan"), DASAR = process.argv.includes("dasar");
const WA = process.argv.includes("wa"), PENDEK = process.argv.includes("pendek");
// mode wa: potongan dibungkus seperti pesan berantai WhatsApp (pembuka, singkatan, emoji, penutup "HR. ...", huruf acak besar/kecil)
const SINGKAT = { yang: "yg", dengan: "dgn", untuk: "utk", tidak: "tdk", karena: "krn", orang: "org", sudah: "sdh", kepada: "kpd", dari: "dr", seperti: "spt", juga: "jg", belum: "blm", dalam: "dlm", pada: "pd", tersebut: "tsb", allah: "Allah SWT", bisa: "bs" };
const PEMBUKA = ["Rasulullah SAW bersabda: ", "Nabi Muhammad saw bersabda, ", "Hadits: ", "📿 Dari Abu Hurairah ra, Rasulullah ﷺ bersabda:\n", "Sabda Nabi s.a.w : ", ""];
const PENUTUP = [" (HR. Bukhari)", " (HR Muslim)", " 🤲🤲", "\nSemoga bermanfaat 🙏", " #sharing", " (HR. Bukhari & Muslim) Aamiin"];
const keWa = (kata) => PEMBUKA[Math.floor(acak() * PEMBUKA.length)] + "“" + kata.map((w) => { const k = w.toLowerCase().replace(/[^a-z]/g, ""); return SINGKAT[k] && acak() < 0.7 ? SINGKAT[k] : (acak() < 0.15 ? w.toUpperCase() : w); }).join(" ") + "”" + PENUTUP[Math.floor(acak() * PENUTUP.length)];
// mode dasar: kata berawalan di potongan diganti kata dasarnya, seperti ketikan orang ("membaca" -> "baca")
const keDasar = (w) => { const m = w.toLowerCase().match(/^(ber|di|ter)([a-z]{4,})$/) || w.toLowerCase().match(/^(mem)([bf][a-z]{3,})$/) || w.toLowerCase().match(/^(men)([dcj][a-z]{3,})$/) || w.toLowerCase().match(/^(meng)([aiueogh][a-z]{3,})$/); return m ? m[2] : null; };
// mode ejaan: hanya potongan yang memuat kata dari grup ejaan kamus, lalu kata itu diganti varian lain (sholat, shodaqoh, ...)
const KAMUS = JSON.parse(fs.readFileSync(new URL("../../pipeline/kamus_konsep.json", import.meta.url)));
const GANTI = new Map(KAMUS.varian.flatMap((g) => g.map((v, i) => [v, g[(i + 1) % g.length]])));

const d = new URL("../.wrangler/state/v3/d1/miniflare-D1DatabaseObject/", import.meta.url);
const f = fs.readdirSync(d).find((x) => x.endsWith(".sqlite") && !x.startsWith("metadata"));
if (!f) { console.error("D1 lokal kosong: jalankan npm run impor"); process.exit(1); }
const raw = new DatabaseSync(new URL(f, d), { readOnly: true });
const urut = (s, a) => { const m = [...s.matchAll(/\?(\d+)/g)]; return m.length ? m.map((x) => a[+x[1] - 1]) : a; };
const db = { prepare: (s) => { let a = []; const o = { bind: (...x) => { a = x; return o; },
  all: async () => ({ results: raw.prepare(s.replace(/\?(\d+)/g, "?")).all(...urut(s, a)) }),
  first: async () => raw.prepare(s.replace(/\?(\d+)/g, "?")).get(...urut(s, a)) }; return o; } };

let biji = 20261107;
const acak = () => (biji = (biji * 1103515245 + 12345) % 2147483648) / 2147483648;
const semua = raw.prepare("SELECT n, arab, terjemah, grup FROM riwayat WHERE tingkat = 'A' AND kitab_id <> 'riyadh' AND terjemah IS NOT NULL").all();
const sampel = [], dipakai = new Set();
while (sampel.length < 100) {
  const r = semua[Math.floor(acak() * semua.length)];
  if (dipakai.has(r.n)) continue;
  if (ARAB) {
    const p = pisahSanad(r.arab);
    const kata = p ? p.matan.split(/\s+/).filter(Boolean) : [];
    if (kata.length < 10) continue;
    const mulai = Math.floor(acak() * Math.max(1, kata.length - 12));
    sampel.push({ ...r, teks: kata.slice(mulai, mulai + 6 + Math.floor(acak() * 7)).join(" ") });
    dipakai.add(r.n);
    continue;
  }
  const kutip = [...r.terjemah.replace(/\[[^\]]*\]/g, " ").matchAll(/"([^"]{40,400})"/g)].map((m) => m[1]);
  if (!kutip.length) continue;
  const kata = kutip[0].split(/\s+/).filter(Boolean);
  if (kata.length < 10) continue;
  const mulai = Math.floor(acak() * Math.max(1, kata.length - 12));
  let potong = PENDEK ? kata.slice(mulai, mulai + 4 + Math.floor(acak() * 3)) : kata.slice(mulai, mulai + 8 + Math.floor(acak() * 8));
  if (DASAR) {
    if (!potong.some((w) => keDasar(w))) continue;
    potong = potong.map((w) => keDasar(w) || w);
  }
  if (EJAAN) {
    const bersih = (w) => w.toLowerCase().replace(/[^a-z']/g, "").replace(/'/g, "");
    if (!potong.some((w) => GANTI.has(bersih(w)))) continue;
    potong = potong.map((w) => (GANTI.has(bersih(w)) ? GANTI.get(bersih(w)) : w));
  }
  sampel.push({ ...r, teks: WA ? keWa(potong) : potong.join(" ") });
  dipakai.add(r.n);
}
const hasil = { tepat: 0, keluarga: 0, lain: 0, tidak: 0 };
for (const s of sampel) {
  const h = await cek(db, s.teks);
  if (h.status !== "ditemukan") { hasil.tidak++; if (RINCI) console.log(`tidak: ${h.status} | ${s.teks.slice(0, 110).replace(/\n/g, " ")}`); continue; }
  const t = raw.prepare("SELECT n, grup FROM riwayat WHERE n = ?").get(h.terbaik);
  if (t.n === s.n) hasil.tepat++;
  else if ((s.grup && t.grup === s.grup) || h.keluarga.some((k) => k.n === s.n)) hasil.keluarga++;
  else {
    hasil.lain++;
    if (RINCI) {
      const a = raw.prepare("SELECT id FROM riwayat WHERE n = ?").get(s.n).id, b = raw.prepare("SELECT id, arab, terjemah FROM riwayat WHERE n = ?").get(h.terbaik);
      const asli = (ARAB ? b.arab : b.terjemah || "");
      console.log(`lain: asal ${a} -> ${b.id} (skor ${h.skor}) | ${s.teks.slice(0, 90)}`);
    }
  }
}
console.log(hasil, `-> riwayat asal atau keluarganya: ${hasil.tepat + hasil.keluarga}/100`);
