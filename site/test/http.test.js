// Uji emas lewat HTTP terhadap situs yang sedang berjalan.
// Jalankan: npm run dev (terminal lain), lalu  BASE_URL=http://127.0.0.1:8787 npm run test:http
import { test } from "node:test";
import assert from "node:assert/strict";

const BASE = process.env.BASE_URL;
const ambil = async (p) => {
  const r = await fetch(BASE + p, { redirect: "manual" });
  return { status: r.status, lokasi: r.headers.get("location"), teks: await r.text() };
};
const opsi = { skip: !BASE && "set BASE_URL untuk menjalankan uji HTTP" };

test("tarawih ditemukan lewat qiyam Ramadhan", opsi, async () => {
  const { teks } = await ambil("/cari?q=" + encodeURIComponent("tolong carikan hadits tentang sholat tarawih"));
  assert.match(teks, /href="\/bukhari\/2009"/);
  assert.match(teks, /href="\/muslim\/759a"/);
  assert.match(teks, /قيام رمضان/);
});

test("rujukan 'muslim 1907' langsung dibuka", opsi, async () => {
  const r = await ambil("/cari?q=muslim%201907");
  assert.equal(r.status, 302);
  assert.match(r.lokasi, /\/muslim\/1907a$/);
});

test("cek hadits niat: ditemukan, atribusi Bukhari & Muslim sesuai", opsi, async () => {
  const { teks } = await ambil("/cek?t=" + encodeURIComponent("Sesungguhnya amalan itu tergantung niatnya dan seseorang akan mendapatkan sesuai dengan apa yang ia niatkan (HR. Bukhari dan Muslim)"));
  assert.match(teks, /DITEMUKAN/);
  assert.match(teks, /Atribusi sesuai/);
  for (const n of ["1", "54", "2529", "3898", "5070", "6689", "6953"]) assert.match(teks, new RegExp(`href="/bukhari/${n}"`));
});

test("cek 'negeri Cina': tidak ditemukan, kata 'cina' disebut", opsi, async () => {
  const { teks } = await ambil("/cek?t=" + encodeURIComponent("Tuntutlah ilmu walau sampai ke negeri Cina"));
  assert.match(teks, /TIDAK DITEMUKAN/);
  assert.match(teks, /“cina”/);
});

test("Bukhari 1: rantai lengkap sampai Rasulullah ﷺ", opsi, async () => {
  const { teks } = await ambil("/bukhari/1");
  for (const nama of ["Rasulullah ﷺ", "Umar bin Al Khaththab", "Alqamah bin Waqash", "Muhammad bin Ibrahim At Taimi", "Sufyan", "Al Humaidi"]) assert.ok(teks.includes(nama), nama);
  assert.match(teks, /Kitab Shahih\. Sumber data kami tidak memuat penilaian per hadits/);
});

test("Tirmidzi 1647: penilaian at-Tirmidzi dari kitabnya + penilai lain", opsi, async () => {
  const { teks } = await ambil("/tirmidzi/1647");
  assert.match(teks, /at-Tirmidzi \(dalam kitabnya\)[\s\S]*حسن صحيح/);
  assert.match(teks, /al-Albani/);
});

test("hadits 'innamal a'malu bin niyyat' tidak ada di Muwaththa' (riwayat Yahya)", opsi, async () => {
  // Kata "niat" memang muncul di riwayat lain Muwaththa' (mis. niat haji); yang diuji adalah HADITS-nya.
  const { teks } = await ambil("/cek?t=" + encodeURIComponent("إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"));
  assert.match(teks, /DITEMUKAN/);
  assert.doesNotMatch(teks, /href="\/malik\//);
});

test("nomor tak dikenal → 404, bukan halaman kosong", opsi, async () => {
  assert.equal((await ambil("/bukhari/999999")).status, 404);
});

test("tema HadeethEnc: daftar tema & saran tema di pencarian", opsi, async () => {
  const daftar = await ambil("/tema");
  for (const t of ["Akidah", "Keutamaan dan Adab", "Sejarah dan Tarikh"]) assert.ok(daftar.teks.includes(t), t);
  const { teks } = await ambil("/cari?q=" + encodeURIComponent("min ada hadist tentang keutamaan sedekah ga"));
  assert.match(teks, /href="\/tema\/511">Sedekah Sunah/);
  const tema = await ambil("/tema/511");
  assert.match(tema.teks, /HadeethEnc\.com/);
  assert.match(tema.teks, /href="\/bukhari\/1442"/);
});

test("Riyadhus Shalihin: terjemah dipasangkan menurut isi, sumber diperiksa", opsi, async () => {
  const r727 = await ambil("/riyadh/727");
  assert.match(r727.teks, /nomor di terjemah: 725/);
  assert.match(r727.teks, /Abu Salamah/);
  const r1 = await ambil("/riyadh/1");
  assert.match(r1.teks, /<b>al-Bukhari<\/b> <span class="num">no\. <a href="\/bukhari\/1">1<\/a>/);
  assert.match(r1.teks, /href="\/muslim\/1907a"/);
  const r = await ambil("/cari?q=" + encodeURIComponent("riyadhus shalihin 918"));
  assert.equal(r.status, 302);
  assert.match((await ambil("/bukhari/1")).teks, /Dikutip dalam[\s\S]*href="\/riyadh\/1"/);
});

test("judul kitab & bab dari teks kitabnya tampil di halaman hadits", opsi, async () => {
  const { teks } = await ambil("/bukhari/2009");
  assert.match(teks, /كتاب صلاة التراويح/);
  assert.match(teks, /Kitab Shalat Tarawih/);
  assert.match(teks, /باب فضل من قام رمضان/);
  assert.match((await ambil("/bukhari/1")).teks, /Permulaan Wahyu/);
});
