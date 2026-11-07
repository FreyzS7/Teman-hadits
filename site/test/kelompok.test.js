import { test } from "node:test";
import assert from "node:assert/strict";
import { kelompokkan, miripMatan } from "../src/cari.js";

const sanad = "حَدَّثَنَا قُتَيْبَةُ، حَدَّثَنَا اللَّيْثُ، عَنْ نَافِعٍ، عَنِ ابْنِ عُمَرَ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ ";
const r = (n, matan, extra = {}) => ({ n, id: "x:" + n, kitab_id: "muslim", slug: String(n), no_tampil: String(n), arab: sanad + "\"" + matan + "\"", ...extra });

test("riwayat dengan matan sama dilipat, yang berbeda tidak", () => {
  const h = kelompokkan([
    r(1, "إِذَا دَخَلَ أَحَدُكُمُ الْمَسْجِدَ فَلْيَقُلِ اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ"),
    r(2, "لاَ يَشْرَبَنَّ أَحَدٌ مِنْكُمْ قَائِمًا فَمَنْ نَسِيَ فَلْيَسْتَقِئْ"),
    r(3, "إِذَا دَخَلَ أَحَدُكُمُ الْمَسْجِدَ فَلْيَقُلِ اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ"),
  ]);
  assert.deepEqual(h.map((x) => x.n), [1, 2]);
  assert.deepEqual(h[0].serupa.map((x) => x.no_tampil), ["3"]);
  assert.equal(h[1].serupa.length, 0);
  assert.equal("jalur_json" in h[0], false);
});

test("tautan takhrij 'sama' melipat walau lafaz berbeda; 'mirip' tidak", () => {
  const h = kelompokkan([
    r(1, "الدِّينُ النَّصِيحَةُ قُلْنَا لِمَنْ قَالَ لِلَّهِ وَلِكِتَابِهِ"),
    r(2, "إِنَّ الدِّينَ النَّصِيحَةُ ثَلاَثًا قَالُوا لِمَنْ يَا رَسُولَ اللَّهِ", { jalur_json: JSON.stringify([[1, 0.9, "sama"]]) }),
    r(3, "مَنْ غَشَّنَا فَلَيْسَ مِنَّا وَالْمَكْرُ وَالْخِدَاعُ فِي النَّارِ", { jalur_json: JSON.stringify([[1, 0.5, "mirip"]]) }),
  ]);
  assert.deepEqual(h.map((x) => x.n), [1, 3]);
  assert.deepEqual(h[0].serupa.map((x) => x.no_tampil), ["2"]);
});

test("matan terlalu pendek tidak dibandingkan", () => {
  assert.equal(miripMatan(new Set(["ا", "ب", "ج"]), new Set(["ا", "ب", "ج"])), 0);
});
