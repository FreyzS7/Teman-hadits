import { test } from "node:test";
import assert from "node:assert/strict";
import { hukumTirmidzi, normAr, pisahKomentar, pisahSanad, rantaiArab, rubrik } from "../src/teks.js";
import { bacaKlaim } from "../src/cek.js";
import { rencana } from "../src/cari.js";

// Teks Shahih al-Bukhari no. 1 (fawazahmed0), dipotong.
const B1 = 'حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ ، قَالَ : حَدَّثَنَا سُفْيَانُ ، قَالَ : حَدَّثَنَا يَحْيَى بْنُ سَعِيدٍ الْأَنْصَارِيُّ ، قَالَ : أَخْبَرَنِي مُحَمَّدُ بْنُ إِبْرَاهِيمَ التَّيْمِيُّ ، أَنَّهُ سَمِعَ عَلْقَمَةَ بْنَ وَقَّاصٍ اللَّيْثِيَّ ، يَقُولُ : سَمِعْتُ عُمَرَ بْنَ الْخَطَّابِ رَضِيَ اللَّهُ عَنْهُ عَلَى الْمِنْبَرِ، قَالَ : سَمِعْتُ رَسُولَ اللَّهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ، يَقُولُ : " إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى';

test("sanad dan matan Bukhari 1 terpisah di tanda kutip", () => {
  const p = pisahSanad(B1);
  assert.ok(p);
  assert.ok(normAr(p.matan).startsWith("انما الاعمال بالنيات"));
  assert.ok(!normAr(p.sanad).includes("انما الاعمال"));
});

test("rantai Bukhari 1: 6 perawi + Nabi, lafaz periwayatan benar", () => {
  const r = rantaiArab(pisahSanad(B1).sanad);
  assert.deepEqual(r.map((s) => s.sighah), ["حدثنا", "حدثنا", "حدثنا", "أخبرني", "سمع", "سمعت", "سمعت"]);
  assert.deepEqual(r.map((s) => normAr(s.namaAr)).slice(0, 6), ["الحميدي عبد الله بن الزبير", "سفيان", "يحيي بن سعيد الانصاري", "محمد بن ابراهيم التيمي", "علقمه بن وقاص الليثي", "عمر بن الخطاب"]);
  assert.equal(r.at(-1).nabi, true);
});

test("'عنه' dalam رضي الله عنه bukan lafaz 'عن'", () => {
  assert.ok(!rubrik("رَضِيَ اللَّهُ عَنْهُ").includes("sg"));
  assert.ok(rubrik("عَنْ قَتَادَةَ").includes("sg-an"));
});

test("penilaian at-Tirmidzi dibaca dari teksnya", () => {
  assert.equal(hukumTirmidzi("قَالَ أَبُو عِيسَى هَذَا حَدِيثٌ حَسَنٌ صَحِيحٌ"), "حسن صحيح");
  assert.equal(hukumTirmidzi("حَدَّثَنَا قُتَيْبَةُ"), null);
});

test("komentar at-Tirmidzi dipisah dari matan", () => {
  const { matan, komentar } = pisahKomentar("إِنَّمَا الْأَعْمَالُ بِالنِّيَّةِ \" . قَالَ أَبُو عِيسَى هَذَا حَدِيثٌ حَسَنٌ صَحِيحٌ");
  assert.equal(normAr(matan), "انما الاعمال بالنيه");
  assert.ok(normAr(komentar).startsWith("قال ابو عيسي"));
});

test("klaim HR dibaca dari teks tempel", () => {
  assert.deepEqual(bacaKlaim("… apa yang ia niatkan (HR. Bukhari dan Muslim)"), ["bukhari", "muslim"]);
  assert.deepEqual(bacaKlaim("Muttafaq 'alaih"), ["bukhari", "muslim"]);
  assert.deepEqual(bacaKlaim("(HR. Abu Daud no. 2201)"), ["abudawud"]);
  assert.deepEqual(bacaKlaim("tanpa sumber"), []);
});

test("rujukan langsung dikenali", () => {
  assert.deepEqual(rencana("muslim 1907").rujukan, { kitab: "muslim", no: "1907" });
  assert.deepEqual(rencana("HR. Abu Dawud no. 2201").rujukan, { kitab: "abudawud", no: "2201" });
  assert.equal(rencana("sholat tarawih").rujukan, null);
});
