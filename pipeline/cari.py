#!/usr/bin/env python3
"""Pencarian "pintar" tanpa AI: memahami kalimat bebas lewat aturan + kamus konsep yang bisa diaudit.

Contoh:
    python3 pipeline/cari.py "tolong carikan hadits tentang sholat tarawih"

Langkah:
  1. Rapikan ejaan (sholat/solat/salat -> shalat) dan buang kata pengisi (tolong, carikan, tentang, ...).
  2. Kenali konsep dari kamus (tarawih -> قيام رمضان + kitab "Taraweeh" di Bukhari, dst).
  3. Cari: padanan Arab, nama kitab/bab, dan kata Indonesia; setiap hasil membawa ALASAN kenapa ia muncul.
  4. Urutkan: skor alasan, lalu tingkat data A, lalu urutan kitab.
Semua hasil berasal dari database; tidak ada teks yang dikarang.
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DB_PATH, KITAB, akar_ar, norm_ar, norm_id

KAMUS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kamus_konsep.json"), encoding="utf8"))
URUT = {k[0]: i for i, k in enumerate(KITAB)}
PENGISI = set(KAMUS["pengisi"])
MAKSUD = set(KAMUS["kata_maksud"])
VARIAN = {v: grup for grup in KAMUS["varian"] for v in grup}  # tiap varian -> seluruh grupnya
PERTANYAAN_HUKUM = re.compile(r"\b(hukum|hukumnya|halal|haram|boleh|bolehkah|wajib|sunnah|makruh|mubah|membolehkan|melarang|mengharamkan|menghalalkan)\b")


def _fts_frasa(teks_ar):
    return '"' + akar_ar(norm_ar(teks_ar)) + '"'


def rencana(kueri):
    """Ubah kalimat pengguna menjadi rencana pencarian yang bisa ditampilkan apa adanya."""
    kata = norm_id(kueri).split()
    dirapikan = [VARIAN.get(w, [w])[0] for w in kata]
    konsep, sisa, dibuang, maksud = [], [], [], []
    for w in dirapikan:
        k = next((c for c in KAMUS["konsep"] if w in c["pemicu"]), None)
        if k and k not in konsep:
            konsep.append(k)
        elif k:
            continue
        elif w in PENGISI or len(w) < 3:
            dibuang.append(w)
        elif w in MAKSUD:
            maksud.append(w)
        else:
            sisa.append(w)
    if not sisa and not konsep and maksud:  # kueri hanya "doa" / "keutamaan": cari kata itu sendiri
        sisa, maksud = maksud, []
    return {"kueri": kueri, "ejaan": [f"{a}→{b}" for a, b in zip(kata, dirapikan) if a != b],
            "dibuang": dibuang, "konsep": konsep, "kata": sisa, "maksud": maksud,
            "pertanyaan_hukum": bool(PERTANYAAN_HUKUM.search(norm_id(kueri)))}


def cari(kueri, batas=20, db=None):
    db = db or sqlite3.connect(DB_PATH)
    q = lambda s, *a: db.execute(s, a).fetchall()
    r = rencana(kueri)
    skor, alasan = {}, {}

    def tambah(rid, nilai, sebab):
        skor[rid] = skor.get(rid, 0) + nilai
        alasan.setdefault(rid, []).append(sebab)

    for k in r["konsep"]:
        for frasa in k["arab"]:
            for (rid,) in q("SELECT riwayat_id FROM cari WHERE cari MATCH ?", "arab_akar:" + _fts_frasa(frasa)):
                tambah(rid, 3, f"teks Arab memuat {frasa}")
        for kid, bab in k["bab"]:
            for (rid,) in q("SELECT id FROM riwayat WHERE kitab_id=? AND bab_nama=? AND tingkat IN ('A','B')", kid, bab):
                tambah(rid, 3, f"masuk kitab/bab \"{bab}\"")
        for t in k["terjemah"]:
            for (rid,) in q("SELECT riwayat_id FROM cari WHERE cari MATCH ?", f'terjemah_polos:"{norm_id(t)}"'):
                tambah(rid, 2, f"terjemah memuat \"{t}\"")

    def grup_fts(w):
        return "(" + " OR ".join(f'terjemah_polos:"{v}"' for v in VARIAN.get(w, [w])) + ")"

    def ada(teks, w):
        return any(v in teks for v in VARIAN.get(w, [w]))

    if r["kata"] and not r["konsep"]:
        semua = " AND ".join(grup_fts(w) for w in r["kata"])
        r["total_kata"] = q("SELECT count(*) FROM cari WHERE cari MATCH ?", semua)[0][0]
        rows = q("SELECT riwayat_id, bm25(cari) FROM cari WHERE cari MATCH ? ORDER BY bm25(cari) LIMIT 400", semua)
        mode = "semua kata"
        if not rows:
            rows = q("SELECT riwayat_id, bm25(cari) FROM cari WHERE cari MATCH ? ORDER BY bm25(cari) LIMIT 400",
                     " OR ".join(grup_fts(w) for w in r["kata"]))
            mode = "sebagian kata"
        for i, (rid, _) in enumerate(rows):
            # bobot 1 + sedikit bonus urutan bm25 (FTS5), supaya yang paling padat kata kuncinya naik
            tambah(rid, 1 + (len(rows) - i) / (10 * len(rows)), f"terjemah memuat {mode}: {', '.join(r['kata'])}")

    # Kata sisa (bila ada konsep) dan kata maksud: hanya menaikkan peringkat, tidak mewajibkan.
    penguat = (r["kata"] if r["konsep"] else []) + r["maksud"]
    if penguat:
        for rid in list(skor):
            t = (q("SELECT terjemah FROM riwayat WHERE id=?", rid)[0][0] or "").lower()
            for w in penguat:
                if ada(t, w):
                    tambah(rid, 1, f"terjemah memuat \"{w}\"")

    def kunci(rid):
        kid = rid.split(":")[0]
        t = q("SELECT tingkat FROM riwayat WHERE id=?", rid)[0][0]
        nomor = re.sub(r"\D", "", rid.split(":")[1]) or "0"
        return (-round(skor[rid], 3), t != "A", URUT.get(kid, 99), int(nomor))

    urut = sorted(skor, key=kunci)
    hasil = []
    for rid in urut[:batas]:
        kid = rid.split(":")[0]
        no, no_ar, no_l, tk, terj = q("SELECT no_standar, no_arab, no_lidwa, tingkat, terjemah FROM riwayat WHERE id=?", rid)[0]
        pen = q("SELECT penilai, hukum FROM penilaian WHERE riwayat_id=?", rid)
        hasil.append({"id": rid, "kitab": kid, "no": no or f"L{no_l}", "no_arab": no_ar, "no_lidwa": no_l,
                      "tingkat": tk, "skor": skor[rid], "alasan": alasan[rid], "penilaian": pen,
                      "cuplikan": (terj or "")[:220]})
    return {"rencana": {**r, "konsep": [{"id": k["id"], "label": k["label"], "catatan": k["catatan"]} for k in r["konsep"]]},
            "total": max(len(skor), r.get("total_kata", 0)), "hasil": hasil}


def main():
    kueri = " ".join(sys.argv[1:]) or "tolong carikan hadits tentang sholat tarawih"
    out = cari(kueri, batas=12)
    r = out["rencana"]
    print(f"Kueri      : {r['kueri']}")
    print(f"Ejaan      : {', '.join(r['ejaan']) or '-'}")
    print(f"Kata maksud: {', '.join(r['maksud']) or '-'} (menaikkan peringkat, tidak diwajibkan)")
    print(f"Dibuang    : {', '.join(r['dibuang']) or '-'}")
    print(f"Konsep     : {', '.join(k['label'] for k in r['konsep']) or '-'}")
    for k in r["konsep"]:
        print(f"  catatan  : {k['catatan']}")
    print(f"Kata lain  : {', '.join(r['kata']) or '-'}")
    if r["pertanyaan_hukum"]:
        print("Catatan    : ini pertanyaan hukum; situs menampilkan riwayat, bukan fatwa.")
    print(f"Ditemukan  : {out['total']} riwayat\n")
    for h in out["hasil"]:
        print(f"[{h['tingkat']}] {h['id']:<16} skor {h['skor']:.1f}  ·  {'; '.join(dict.fromkeys(h['alasan']))}")
        print(f"     {h['cuplikan'][:160]}…")


if __name__ == "__main__":
    main()
