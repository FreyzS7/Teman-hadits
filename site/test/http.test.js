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
