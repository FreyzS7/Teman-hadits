import { test } from "node:test";
import assert from "node:assert/strict";
import { bentukKata, lipat } from "../src/cari.js";

test("riwayat sekelompok dilipat di bawah riwayat pertamanya, urutan peringkat dipertahankan", () => {
  const grup = new Map([[5, 1], [9, 1], [7, 2], [3, 2]]);
  assert.deepEqual(lipat([5, 7, 8, 9, 3, 4], grup), [{ n: 5, serupa: [9] }, { n: 7, serupa: [3] }, { n: 8, serupa: [] }, { n: 4, serupa: [] }]);
});

test("di luar jendela, riwayat tidak dilipat", () => {
  const grup = new Map([[1, 1], [2, 1], [3, 1]]);
  assert.deepEqual(lipat([1, 2, 3], grup, 2), [{ n: 1, serupa: [2] }, { n: 3, serupa: [] }]);
});

test("tanpa data kelompok (database lama), satu riwayat satu kartu", () => {
  assert.deepEqual(lipat([4, 2], new Map()), [{ n: 4, serupa: [] }, { n: 2, serupa: [] }]);
});

test("kata dasar juga dicari dengan awalan me-/di-/ber-/ter- (peluluhan lazim)", () => {
  const b = (w) => bentukKata(w);
  assert.ok(b("baca").includes("membaca") && b("baca").includes("dibaca"));
  assert.ok(b("puasa").includes("berpuasa"));
  assert.ok(b("pukul").includes("memukul"));
  assert.ok(b("tulis").includes("menulis"));
  assert.ok(b("sapu").includes("menyapu"));
  assert.ok(b("kirim").includes("mengirim"));
  assert.ok(b("doa").includes("berdoa"));
  assert.ok(!b("riba").includes("ribath"));
});
