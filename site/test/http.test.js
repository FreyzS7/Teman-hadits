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

test("istilah awam dipetakan ke lafaz Arabnya (kamus konsep)", opsi, async () => {
  const birr = (await ambil("/cari?q=" + encodeURIComponent("birrul walidain") + "&z=" + Date.now())).teks;
  assert.match(birr, /href="\/bukhari\/5970"/);
  assert.match(birr, /بر الوالدين/);
  const tahajud = (await ambil("/cari?q=tahajud&z=" + Date.now())).teks;
  assert.match(tahajud, /href="\/bukhari\/1136"/);
  const utang = (await ambil("/cari?q=utang&z=" + Date.now())).teks;
  assert.match(utang, /utang→hutang/);
});

test("riwayat yang lafaz matannya sama dilipat, tetap tertaut", opsi, async () => {
  const { teks } = await ambil("/cari?q=niat&z=" + Date.now());
  assert.match(teks, /Riwayat serupa di halaman ini/);
  assert.match(teks, /href="\/bukhari\/1"/);
  assert.match(teks, /href="\/muslim\/1907a"/);
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
  // produksi: TERJEMAH_RIYADH="sembunyi" (izin penerjemah belum pasti) -> terjemah tidak tampil, diganti keterangan
  if (/belum ditampilkan sampai izin penerjemahnya dipastikan/.test(r727.teks)) assert.doesNotMatch(r727.teks, /Abu Salamah/);
  else assert.match(r727.teks, /Abu Salamah/);
  const r1 = await ambil("/riyadh/1");
  assert.match(r1.teks, /<b>al-Bukhari<\/b> <span class="num">no\. <a href="\/bukhari\/1">1<\/a>/);
  assert.match(r1.teks, /href="\/muslim\/1907a"/);
  const r = await ambil("/cari?q=" + encodeURIComponent("riyadhus shalihin 918"));
  assert.equal(r.status, 302);
  assert.match((await ambil("/bukhari/1")).teks, /Dikutip dalam[\s\S]*href="\/riyadh\/1"/);
});

test("mode sembunyi: terjemah Riyadh tidak ikut dicari, nama bab Indonesianya tidak tampil", opsi, async () => {
  const sembunyi = /belum ditampilkan sampai izin penerjemahnya dipastikan/.test((await ambil("/riyadh/727")).teks);
  if (!sembunyi) return;
  const { teks } = await ambil("/cari?q=sabar&z=" + Date.now());
  assert.doesNotMatch(teks, /href="\/riyadh\/\d+"/);
  const kitab = (await ambil("/kitab/riyadh?z=" + Date.now())).teks;
  assert.match(kitab, /Nama bab Indonesia belum ditampilkan/);
  assert.match(kitab, />1\. Bab 1</);
});

test("judul kitab & bab dari teks kitabnya tampil di halaman hadits", opsi, async () => {
  const { teks } = await ambil("/bukhari/2009");
  assert.match(teks, /كتاب صلاة التراويح/);
  assert.match(teks, /Kitab Shalat Tarawih/);
  assert.match(teks, /باب فضل من قام رمضان/);
  assert.match((await ambil("/bukhari/1")).teks, /Permulaan Wahyu/);
});

test("Ahmad/Darimi/Syafi'i: nomor edisi tahqiq, penilaian Asad, nomor ambigu", opsi, async () => {
  const d4 = (await ambil("/darimi/4")).teks;
  assert.match(d4, /no\. 4 di edisi Dar al-Mughni/);
  assert.match(d4, /Husain Salim Asad[\s\S]*عباد بن منصور/);
  const r = await ambil("/cari?q=" + encodeURIComponent("darimi 2468"));
  assert.equal(r.status, 200);                       // tidak langsung dibuka: nomornya ambigu
  assert.match(r.teks, /Nomor ini ada di dua sistem penomoran/);
  assert.match((await ambil("/ahmad/163")).teks, /di edisi ar-Risalah/);
});

test("katalog populer: 'negeri Cina' → al-Maqashid no. 125 (batil), al-Maudhu'at, tanpa riwayat", opsi, async () => {
  const { status, teks } = await ambil("/populer/ilmu-negeri-cina");
  assert.equal(status, 200);
  assert.match(teks, /al-Maqashid al-Hasanah <span class="num">no\. 125/);
  assert.match(teks, /al-Maudhu&#39;at <span class="num">no\. 71/);
  assert.match(teks, /class="chip kk-palsu">batil</);
  assert.match(teks, /Tidak ditemukan<\/b> dengan lafaz ini di 11 kitab hadits kami/);
  // cek dengan teks Indonesia ikut memunculkan kotak katalog
  const cek = (await ambil("/cek?t=" + encodeURIComponent("Tuntutlah ilmu walau sampai ke negeri Cina"))).teks;
  assert.match(cek, /cocok dengan ucapan yang sering beredar/);
});

test("katalog: 'حب الوطن من الإيمان' tidak diberi chip shahih/hasan", opsi, async () => {
  const { teks } = await ambil("/cek?t=" + encodeURIComponent("حب الوطن من الإيمان"));
  for (const k of ["al-Maqashid al-Hasanah <span class=\"num\">no. 386", "Kasyf al-Khafa&#39; <span class=\"num\">no. 1102", "al-Asrar al-Marfu&#39;ah <span class=\"num\">no. 164"]) assert.ok(teks.includes(k), k);
  assert.doesNotMatch(teks, /kk-terima">(shahih|hasan)</);
  assert.match(teks, /kk-lain">maknanya benar/);
});

test("katalog: kontrol shahih ditunjukkan ada di kitab hadits; 'disebut' dipisah", opsi, async () => {
  const { teks } = await ambil("/populer/ulama-pewaris-nabi");
  assert.match(teks, /href="\/tirmidzi\/2682"/);
  assert.match(teks, /href="\/abudawud\/3641"/);
  const tidur = (await ambil("/populer/tidur-puasa-ibadah")).teks;
  assert.match(tidur, /Disebut dalam pembahasan entri lain/);
  assert.match(tidur, /al-Asrar al-Marfu&#39;ah no\. 567/);
  assert.equal((await ambil("/populer/tidak-ada")).status, 404);
});

test("perawi: Bukhari 1 — setiap perawi teridentifikasi pasti dengan ringkasan Ibnu Hajar", opsi, async () => {
  const { teks } = await ambil("/bukhari/1");
  for (const id of ["t3320", "t2451", "t7559", "t5691", "t4685", "t4888"]) assert.match(teks, new RegExp(`href="/perawi/${id}"`), id);
  assert.match(teks, /ثقة حافظ فقيه إمام حجة/);            // Sufyan bin 'Uyainah
  assert.match(teks, /tabaqah 8 · w\. 198 H/);
  assert.match(teks, /Tahdzib al-Kamal/);
});

test("perawi: halaman biodata Sufyan bin 'Uyainah (Taqrib no. 2451)", opsi, async () => {
  const { status, teks } = await ambil("/perawi/t2451");
  assert.equal(status, 200);
  assert.match(teks, /Taqrib at-Tahdzib<\/i> no\. 2451/);
  assert.match(teks, /sangat terpercaya/);
  assert.match(teks, /tabaqah 8/);
  assert.match(teks, /href="\/bukhari\/1"/);
  assert.match(teks, /href="\/perawi\/t3320"/);           // al-Humaidi sebagai murid
  assert.equal((await ambil("/perawi/t999999")).status, 404);
});

test("perawi: wafat dengan pendapat lain & daftar perawi", opsi, async () => {
  const ah = (await ambil("/perawi/t8426")).teks;          // Abu Hurairah
  assert.match(ah, /w\. 57 H \(ada pendapat lain\)/);
  assert.match(ah, /sahabat Nabi/);
  const d = (await ambil("/perawi")).teks;
  assert.match(d, /href="\/perawi\/t8426"/);
});

test("catatan cetakan tampil hanya di riwayat yang sudah dicek", opsi, async () => {
  const a = await ambil("/bukhari/5323");
  assert.match(a.teks, /Catatan cetakan:<\/b>[^<]*في قولها/);
  const b = await ambil("/darimi/247");
  assert.match(b.teks, /Catatan cetakan:<\/b>[^<]*فتعلّموا/);
  const c = await ambil("/bukhari/1");
  assert.doesNotMatch(c.teks, /Catatan cetakan:/);
});
