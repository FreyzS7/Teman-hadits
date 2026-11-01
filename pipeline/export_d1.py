#!/usr/bin/env python3
"""Ekspor database build ke berkas SQL untuk Cloudflare D1 (lokal maupun nanti online).

Masukan : build/teman-hadits.sqlite, build/takhrij.sqlite, build/hadeethenc.sqlite (opsional)
Keluaran: build/d1/000-skema.sql, build/d1/NNN-data.sql (dipecah per ~40 MB)

Versi D1 lebih ramping dari database build:
  - hanya riwayat tingkat A/B (karantina tidak dikirim ke situs);
  - tanpa kolom pembanding arab_lidwa;
  - indeks pencarian FTS5 "contentless" (hanya indeks; teks diambil dari tabel riwayat);
  - kunci bilangan bulat `n` agar join & indeks hemat.

Jalankan:  python3 pipeline/export_d1.py
"""
import collections
import datetime
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, KITAB, akar_ar, norm_ar, norm_id

OUT = os.path.join(BUILD, "d1")
MAKS_PERNYATAAN = 90_000      # D1 membatasi panjang satu pernyataan SQL (~100 KB)
MAKS_BERKAS = 40_000_000
MAKS_BARIS = 500              # baris per INSERT; VALUES majemuk yang terlalu panjang -> SQLITE_NOMEM di D1 lokal

SKEMA = """
DROP TABLE IF EXISTS info; DROP TABLE IF EXISTS kitab; DROP TABLE IF EXISTS bab; DROP TABLE IF EXISTS riwayat;
DROP TABLE IF EXISTS penilaian; DROP TABLE IF EXISTS mirip; DROP TABLE IF EXISTS kata_df; DROP TABLE IF EXISTS cari;
DROP TABLE IF EXISTS tema; DROP TABLE IF EXISTS he_hadits; DROP TABLE IF EXISTS he_tema; DROP TABLE IF EXISTS he_riwayat;
DROP TABLE IF EXISTS riyadh_info; DROP TABLE IF EXISTS sumber;
CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
CREATE TABLE kitab (
  id TEXT PRIMARY KEY, urut INT, nama TEXT, nama_arab TEXT, penyusun TEXT, wafat_h INT, sistem_nomor TEXT,
  jumlah_lidwa INT, jumlah_standar INT, terbit INT, tingkat_a INT, tingkat_b INT, karantina INT, dinilai INT,
  penilai TEXT
);
CREATE TABLE bab (kitab_id TEXT, no INT, nama TEXT, jumlah INT, n_awal INT, nama_ar TEXT, PRIMARY KEY (kitab_id, no));
CREATE TABLE riwayat (
  n INTEGER PRIMARY KEY, id TEXT UNIQUE, kitab_id TEXT, slug TEXT, urut INT, no_tampil TEXT,
  no_standar TEXT, no_arab TEXT, no_lidwa INT, bab_no INT, arab TEXT, terjemah TEXT, rantai_json TEXT,
  kecocokan REAL, tingkat TEXT, alasan TEXT
);
CREATE UNIQUE INDEX ix_riwayat_slug ON riwayat (kitab_id, slug);
CREATE INDEX ix_riwayat_urut ON riwayat (kitab_id, urut);
CREATE INDEX ix_riwayat_bab ON riwayat (kitab_id, bab_no, urut);
CREATE TABLE penilaian (n INT, penilai TEXT, hukum TEXT, kategori TEXT);
CREATE INDEX ix_penilaian_n ON penilaian (n);
CREATE TABLE mirip (a INT, b INT, skor REAL, tingkat TEXT);
CREATE INDEX ix_mirip_a ON mirip (a);
CREATE TABLE kata_df (kata TEXT PRIMARY KEY, n INT) WITHOUT ROWID;
CREATE VIRTUAL TABLE cari USING fts5 (
  arab_polos, arab_akar, terjemah_polos, perawi,
  content = '', tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE tema (id TEXT PRIMARY KEY, judul TEXT, induk TEXT, jumlah INT);
CREATE TABLE he_hadits (id TEXT PRIMARY KEY, judul TEXT, teks_id TEXT, teks_ar TEXT, atribusi TEXT, derajat TEXT,
  penjelasan TEXT, faedah_json TEXT, url TEXT, boleh_tampil INT);
CREATE TABLE he_tema (he_id TEXT, tema_id TEXT);
CREATE INDEX ix_he_tema ON he_tema (tema_id);
CREATE TABLE he_riwayat (he_id TEXT, n INT, skor REAL);
CREATE INDEX ix_he_riwayat_n ON he_riwayat (n);
CREATE INDEX ix_he_riwayat_he ON he_riwayat (he_id);
-- Riyadhus Shalihin: kitab himpunan (an-Nawawi menyebut sumbernya); sumber = tautan ke riwayat di kitab asal
CREATE TABLE riyadh_info (n INTEGER PRIMARY KEY, atribusi_ar TEXT, kitab_atribusi TEXT, catatan_ar TEXT, no_terjemah INT);
CREATE TABLE sumber (a INT, b INT, skor REAL, kitab_disebut INT, sahabat_sama INT, peringkat INT);
CREATE INDEX ix_sumber_a ON sumber (a);
CREATE INDEX ix_sumber_b ON sumber (b);
"""

# Stem Indonesia ringan untuk tabel frekuensi kata (dipakai fitur "cek teks"); harus sama dengan site/src/teks.js
def stem_id(w):
    for s in ("nya", "kan", "lah", "an"):
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[:-len(s)]
    return w


def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v).replace("\r\n", "\n").replace("\r", "\n")
    # Baris baru di dalam literal membingungkan pemecah pernyataan `wrangler d1 execute`;
    # tulis sebagai char(10) supaya isi teks tetap sama persis.
    return " || char(10) || ".join("'" + bagian.replace("'", "''") + "'" for bagian in s.split("\n"))


class Penulis:
    def __init__(self):
        os.makedirs(OUT, exist_ok=True)
        for f in os.listdir(OUT):
            if f.endswith(".sql"):
                os.remove(os.path.join(OUT, f))
        self.no, self.f, self.ukuran = 0, None, 0
        self._buka()

    def _buka(self):
        if self.f:
            self.f.close()
        self.no += 1
        self.f = open(os.path.join(OUT, f"{self.no:03d}-data.sql"), "w", encoding="utf8")
        self.ukuran = 0

    def tulis(self, s):
        if self.ukuran + len(s) > MAKS_BERKAS:
            self._buka()
        self.f.write(s)
        self.ukuran += len(s.encode("utf8"))

    def sisip(self, tabel, kolom, baris):
        kepala = f"INSERT INTO {tabel} ({', '.join(kolom)}) VALUES "
        buf, pjg = [], len(kepala)
        for b in baris:
            v = "(" + ",".join(sql_val(x) for x in b) + ")"
            if buf and (pjg + len(v.encode("utf8")) + 2 > MAKS_PERNYATAAN or len(buf) >= MAKS_BARIS):
                self.tulis(kepala + ",".join(buf) + ";\n")
                buf, pjg = [], len(kepala)
            buf.append(v)
            pjg += len(v.encode("utf8")) + 1
        if buf:
            self.tulis(kepala + ",".join(buf) + ";\n")

    def tutup(self):
        self.f.close()


def slug_muslim(no_arab, no_standar):
    if not no_arab:
        return f"s{no_standar}"
    x = str(no_arab)
    if "." in x:
        base, dec = x.split(".")
        if dec.isdigit() and 0 < int(dec) < 27:
            return f"{base}{chr(96 + int(dec))}"
    return x


def main():
    src = sqlite3.connect(DB_PATH)
    q = lambda s, *a: src.execute(s, a).fetchall()
    w = Penulis()
    with open(os.path.join(OUT, "000-skema.sql"), "w", encoding="utf8") as f:
        f.write(SKEMA)

    urut_kitab = {k[0]: i for i, k in enumerate(KITAB)}
    rows = q("SELECT id, kitab_id, no_standar, no_arab, no_lidwa, bab_no, bab_nama, arab, terjemah, rantai_json, "
             "kecocokan, tingkat, alasan FROM riwayat WHERE tingkat IN ('A','B')")

    def kunci_urut(r):
        kid = r[1]
        if r[2] is not None:
            try:
                return (urut_kitab[kid], float(r[2]))
            except ValueError:
                pass
        return (urut_kitab[kid], float(r[4] or 0))

    rows.sort(key=kunci_urut)
    n_of = {}
    data_riwayat, data_cari = [], []
    urut_dalam = collections.Counter()
    slug_dipakai = set()
    bab = {}
    for n, r in enumerate(rows, start=1):
        rid, kid, nos, noa, nol, babno, babnama, arab, terj, rantai, kc, tk, al = r
        n_of[rid] = n
        urut_dalam[kid] += 1
        if kid == "muslim":
            slug = slug_muslim(noa, nos)
            tampil = slug
        elif nos is not None:
            slug = tampil = nos
        else:
            slug = tampil = str(nol)
        if (kid, slug) in slug_dipakai:
            slug = f"{slug}-{n}"
        slug_dipakai.add((kid, slug))
        data_riwayat.append((n, rid, kid, slug, urut_dalam[kid], tampil, nos, noa, nol, babno, arab, terj, rantai, kc, tk, al))
        na = norm_ar(arab)
        nama = " ".join(json.loads(rantai)) if rantai else ""
        data_cari.append((n, na, akar_ar(na), norm_id(terj), norm_id(nama)))
        if babno is not None:
            b = bab.setdefault((kid, babno), [babnama, 0, n, None])
            b[1] += 1

    # --- Riyadhus Shalihin (build/riyadh.sqlite, dari pipeline/riyadh.py) -------------------------
    ry_path = os.path.join(BUILD, "riyadh.sqlite")
    data_ry_info, data_sumber, ry_kitab, ry_info = [], [], None, {}
    if os.path.exists(ry_path):
        ry = sqlite3.connect(ry_path)
        bab_ry = {no: (ar, idn) for no, ar, idn in ry.execute("SELECT no, nama_ar, nama_id FROM riyadh_bab")}
        sumber_ry = collections.defaultdict(list)
        for u, rid, sk, kd, sh, pk in ry.execute("SELECT urut, riwayat_id, skor, kitab_disebut, sahabat_sama, peringkat FROM riyadh_sumber"):
            sumber_ry[u].append((rid, sk, kd, sh, pk))
        n = len(rows)
        hit = collections.Counter()
        for u, no, babno, arab, catatan, atr, katr, terj, noter, st in ry.execute(
                "SELECT urut, no, bab_no, arab, catatan_ar, atribusi_ar, kitab_atribusi, terjemah, no_terjemah, "
                "status_terjemah FROM riyadh ORDER BY no"):
            n += 1
            src_ok = any(kd for _, _, kd, _, _ in sumber_ry[u])
            pasti = st == "pasti"
            tk = "A" if (pasti and src_ok) else "B"
            alasan = "; ".join(x for x in [
                None if pasti else "terjemah belum terpasang: pasangannya di sumber terjemah tidak pasti",
                None if sumber_ry[u] else "sumbernya belum ditemukan di kitab-kitab kami",
                None if (src_ok or not sumber_ry[u]) else "sumber yang ditemukan bukan kitab yang disebut an-Nawawi"] if x) or None
            hit[tk] += 1
            data_riwayat.append((n, f"riyadh:{no}", "riyadh", str(no), no, str(no), str(no), None, None, babno, arab,
                                 terj if pasti else None, None, None, tk, alasan))
            na = norm_ar(arab)
            data_cari.append((n, na, akar_ar(na), norm_id(terj if pasti else ""), ""))
            data_ry_info.append((n, atr, katr, catatan or None, noter if pasti else None))
            for rid, sk, kd, sh, pk in sumber_ry[u]:
                if rid in n_of:
                    data_sumber.append((n, n_of[rid], sk, kd, sh, pk))
            if babno is not None:
                ar, idn = bab_ry.get(babno, (None, None))
                b = bab.setdefault(("riyadh", babno), [idn or ar, 0, n, ar])
                b[1] += 1
        ry_info = dict(ry.execute("SELECT kunci, nilai FROM info"))
        ry_kitab = ("riyadh", len(KITAB), "Riyadhus Shalihin", "رياض الصالحين", "Yahya bin Syaraf an-Nawawi", 676,
                    "Riyadhus Shalihin (1–1896)", int(ry_info.get("entri_terjemah", 0)), 1896, hit["A"] + hit["B"],
                    hit["A"], hit["B"], 0, 0, "[]")

    # info + kitab
    total = dict(q("SELECT tingkat, count(*) FROM riwayat GROUP BY tingkat"))
    tk_total = collections.Counter(r[14] for r in data_riwayat)
    info = {"dibangun": datetime.date.today().isoformat(), "terbit": str(len(data_riwayat)),
            "tingkat_a": str(tk_total["A"]), "tingkat_b": str(tk_total["B"]), "karantina": str(total.get("K", 0))}
    info.update({f"riyadh_{k}": v for k, v in ry_info.items()})
    lock = json.load(open(os.path.join(os.path.dirname(DB_PATH), "..", "pipeline", "sources.lock.json"), encoding="utf8"))
    info["sumber"] = json.dumps(sorted({(k.split('/')[0], v["commit"][:7]) for k, v in lock.items()}))
    w.sisip("info", ["kunci", "nilai"], info.items())
    kit = []
    for kid, nama, nama_ar, penyusun, wafat, sistem, nl, ns in q(
            "SELECT id, nama, nama_arab, penyusun, wafat_h, sistem_nomor, jumlah_lidwa, jumlah_standar FROM kitab"):
        t = dict(q("SELECT tingkat, count(*) FROM riwayat WHERE kitab_id=? GROUP BY tingkat", kid))
        dinilai = q("SELECT count(DISTINCT riwayat_id) FROM penilaian WHERE riwayat_id LIKE ?", kid + ":%")[0][0]
        pen = [r[0] for r in q("SELECT DISTINCT penilai FROM penilaian WHERE riwayat_id LIKE ? ORDER BY 1", kid + ":%")]
        kit.append((kid, urut_kitab[kid], nama, nama_ar, penyusun, wafat, sistem, nl, ns, t.get("A", 0) + t.get("B", 0),
                    t.get("A", 0), t.get("B", 0), t.get("K", 0), dinilai, json.dumps(pen, ensure_ascii=False)))
    if ry_kitab:
        kit.append(ry_kitab)
    w.sisip("kitab", ["id", "urut", "nama", "nama_arab", "penyusun", "wafat_h", "sistem_nomor", "jumlah_lidwa",
                      "jumlah_standar", "terbit", "tingkat_a", "tingkat_b", "karantina", "dinilai", "penilai"], kit)
    w.sisip("bab", ["kitab_id", "no", "nama", "jumlah", "n_awal", "nama_ar"],
            [(k, no, v[0], v[1], v[2], v[3]) for (k, no), v in sorted(bab.items())])
    w.sisip("riyadh_info", ["n", "atribusi_ar", "kitab_atribusi", "catatan_ar", "no_terjemah"], data_ry_info)
    w.sisip("sumber", ["a", "b", "skor", "kitab_disebut", "sahabat_sama", "peringkat"], data_sumber)
    w.sisip("riwayat", ["n", "id", "kitab_id", "slug", "urut", "no_tampil", "no_standar", "no_arab", "no_lidwa", "bab_no",
                        "arab", "terjemah", "rantai_json", "kecocokan", "tingkat", "alasan"], data_riwayat)
    w.sisip("cari", ["rowid", "arab_polos", "arab_akar", "terjemah_polos", "perawi"], data_cari)
    w.sisip("penilaian", ["n", "penilai", "hukum", "kategori"],
            [(n_of[r[0]], r[1], r[2], r[3]) for r in q("SELECT riwayat_id, penilai, hukum, kategori FROM penilaian")
             if r[0] in n_of])

    # frekuensi kata Indonesia (untuk "cek teks"): berapa riwayat memuat kata (setelah stem ringan)
    df = collections.Counter()
    for _, _, _, terj_polos, _ in data_cari:
        df.update({stem_id(x) for x in terj_polos.split()})
    w.sisip("kata_df", ["kata", "n"], sorted(df.items()))

    tk_path = os.path.join(BUILD, "takhrij.sqlite")
    n_mirip = 0
    if os.path.exists(tk_path):
        t = sqlite3.connect(tk_path)
        m = [(n_of[a], n_of[b], s, tk) for a, b, s, tk in t.execute("SELECT a, b, skor, tingkat FROM mirip")
             if a in n_of and b in n_of]
        n_mirip = len(m)
        w.sisip("mirip", ["a", "b", "skor", "tingkat"], m)
    he_path = os.path.join(BUILD, "hadeethenc.sqlite")
    n_he = 0
    if os.path.exists(he_path):
        h = sqlite3.connect(he_path)
        try:
            w.sisip("tema", ["id", "judul", "induk", "jumlah"], h.execute("SELECT id, judul, induk, jumlah FROM tema"))
            meta = dict(h.execute("SELECT kunci, nilai FROM hadeethenc_meta"))
            w.sisip("info", ["kunci", "nilai"], [("hadeethenc_versi", meta.get("versi", "")), ("hadeethenc_sumber", meta.get("sumber", ""))])
            he = h.execute("SELECT id, judul, teks_id, teks_ar, atribusi, derajat, penjelasan, faedah_json, url, "
                           "boleh_tampil FROM he_hadits").fetchall()
            n_he = len(he)
            w.sisip("he_hadits", ["id", "judul", "teks_id", "teks_ar", "atribusi", "derajat", "penjelasan", "faedah_json",
                                  "url", "boleh_tampil"], he)
            w.sisip("he_tema", ["he_id", "tema_id"], h.execute("SELECT he_id, tema_id FROM he_tema"))
            w.sisip("he_riwayat", ["he_id", "n", "skor"],
                    [(a, n_of[b], s) for a, b, s in h.execute("SELECT he_id, riwayat_id, skor FROM he_riwayat")
                     if b in n_of])
        except sqlite3.Error as e:
            print("hadeethenc.sqlite belum lengkap, dilewati:", e, file=sys.stderr)
    w.tutup()
    berkas = sorted(f for f in os.listdir(OUT) if f.endswith(".sql"))
    ukuran = sum(os.path.getsize(os.path.join(OUT, f)) for f in berkas)
    print(f"{len(data_riwayat)} riwayat (termasuk {len(data_ry_info)} Riyadhus Shalihin), {len(data_sumber)} tautan sumber Riyadh, {n_mirip} pasangan takhrij, {n_he} hadits HadeethEnc, {len(df)} kata -> "
          f"{len(berkas)} berkas, {ukuran / 1e6:.0f} MB di build/d1/", file=sys.stderr)


if __name__ == "__main__":
    main()
