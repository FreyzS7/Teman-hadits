// Versi JavaScript (situs) harus menormalkan teks & memahami kueri PERSIS seperti versi Python (pipeline).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { akarAr, normAr, normId } from "../src/teks.js";
import { rencana } from "../src/cari.js";

const F = JSON.parse(readFileSync(new URL("./fixtures/paritas.json", import.meta.url), "utf8"));

test("normalisasi Arab & Indonesia identik dengan Python", () => {
  let beda = [];
  for (const x of F.normalisasi) {
    if (normAr(x.masuk.arab) !== x.norm_ar) beda.push(["norm_ar", x.masuk.id]);
    if (akarAr(normAr(x.masuk.arab)) !== x.akar_ar) beda.push(["akar_ar", x.masuk.id]);
    if (normId(x.masuk.terjemah) !== x.norm_id) beda.push(["norm_id", x.masuk.id, normId(x.masuk.terjemah).slice(0, 80), x.norm_id.slice(0, 80)]);
  }
  assert.deepEqual(beda, []);
});

test("rencana pencarian identik dengan Python", () => {
  for (const x of F.rencana) {
    const r = rencana(x.kueri);
    assert.deepEqual(
      { ejaan: r.ejaan, dibuang: r.dibuang, kata: r.kata, maksud: r.maksud, pertanyaan_hukum: r.pertanyaanHukum, konsep: r.konsep.map((k) => k.id) },
      { ejaan: x.ejaan, dibuang: x.dibuang, kata: x.kata, maksud: x.maksud, pertanyaan_hukum: x.pertanyaan_hukum, konsep: x.konsep },
      x.kueri,
    );
  }
});
