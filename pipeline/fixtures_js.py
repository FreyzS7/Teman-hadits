#!/usr/bin/env python3
"""Buat site/test/fixtures/paritas.json: masukan + keluaran normalisasi & rencana versi Python,
supaya site/src (JavaScript) diuji menghasilkan hal yang SAMA PERSIS."""
import json
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB_PATH, ROOT, akar_ar, norm_ar, norm_id
from cari import rencana
from sanad import pisah_sanad, rantai_arab

db = sqlite3.connect(DB_PATH)
random.seed(20261101)
ids = [r[0] for r in db.execute("SELECT id FROM riwayat WHERE tingkat IN ('A','B')")]
contoh = random.sample(ids, 300)
teks = []
for rid in contoh:
    ar, tr = db.execute("SELECT arab, terjemah FROM riwayat WHERE id=?", (rid,)).fetchone()
    teks.append({"id": rid, "arab": ar, "terjemah": tr or ""})
TEPI = ["", "   ", "Shalat Jum'at", "SHOLAT  tarawih!!", "Ṣalāt al-‘Īd", "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ", "ﷺ صلى الله عليه وسلم",
        "وَالْخِنْزِيرِ والأصنام", "آمَنَ بِاللَّهِ وَمَلَائِكَتِهِ", "مسند الشافعي 900: أَخْبَرَنَا", "Tuntutlah ilmu walau ke negeri Cina", "Abu Hurairah r.a. berkata:"]
for t in TEPI:
    teks.append({"id": "tepi", "arab": t, "terjemah": t})
KUERI = ["tolong carikan hadits tentang sholat tarawih", "apakah makan babi itu hukumnya haram?", "hadits yang membolehkan makan babi",
         "min ada hadist tentang keutamaan sedekah ga", "niat", "Terawih di bulan Romadhon", "adab makan dan minum", "wudu",
         "muslim 1907", "hr bukhari no 1", "sholat subuh berjamaah", "keutamaan shodaqoh di hari jum'at",
         "birrul walidain", "keutamaan sholat tahajjud", "silaturrahim memperpanjang umur", "apa itu gibah", "hukum isbal",
         "ziarah kubur", "hukum musik", "bayar utang",
         "sholawat nabi", "takziyah", "tawakkal kepada allah", "menjaga lisan", "cara istinjak", "hukum cadar", "hak tetangga", "khitanan",
         "doa", "keutamaan", "doa masuk wc", "doa naik kendaraan", "shalat id", "korupsi", "hukum judi", "jimat",
         "telaga kautsar", "isra' mi'raj", "timbangan mizan", "shirat", "padang mahsyar", "namimah", "tawaduk", "qonaah", "poligami", "khulafaur rasyidin",
         "shalat tahiyatul masjid", "shalat rawatib", "makmum masbuq", "badal haji", "mudharabah", "ghasab tanah", "luqathah", "jual beli gharar", "sutrah", "fidyah puasa", "bughat", "pakaian sutra",
         "habbatus sauda", "minum tiga tegukan", "pengobatan ruqyah", "sutra laki laki",
         "kisah nabi khidhir", "munkar nakir", "asmaul husna", "keutamaan hauqalah", "istirja", "surat yasin", "surat al mulk", "ayat kursi",
         "hukum khalwat", "safar wanita tanpa mahram", "nikah mut'ah", "melamar wanita", "homoseksual", "tasyabbuh", "banci", "hukum kb", "gambar makhluk hidup", "main catur", "pengemis", "orang dzalim", ""]
def _sanad(arab):
    p = pisah_sanad(arab)
    return None if p is None else {"sanad": p[0], "matan": p[1], "rantai": [{"lafaz": x["lafaz"], "sighah": x["sighah"], "namaAr": x["nama_ar"], "nabi": x["nabi"]} for x in rantai_arab(p[0])]}


out = {
    "sanad": [{"id": x["id"], "arab": x["arab"], "hasil": _sanad(x["arab"])} for x in teks],
    "normalisasi": [{"masuk": x, "norm_ar": norm_ar(x["arab"]), "akar_ar": akar_ar(norm_ar(x["arab"])), "norm_id": norm_id(x["terjemah"])} for x in teks],
    "rencana": [{"kueri": k, **{f: rencana(k)[f] for f in ("ejaan", "dibuang", "kata", "maksud", "pertanyaan_hukum")},
                 "konsep": [c["id"] for c in rencana(k)["konsep"]]} for k in KUERI],
}
p = os.path.join(ROOT, "site", "test", "fixtures", "paritas.json")
json.dump(out, open(p, "w"), ensure_ascii=False)
print(f"{p}: {len(out['normalisasi'])} teks, {len(out['rencana'])} kueri ({os.path.getsize(p) // 1024} KB)")
