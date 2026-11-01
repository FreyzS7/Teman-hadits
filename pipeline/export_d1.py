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
DROP TABLE IF EXISTS riyadh_info; DROP TABLE IF EXISTS sumber; DROP TABLE IF EXISTS judul; DROP TABLE IF EXISTS judul_bab;
DROP TABLE IF EXISTS katalog_kitab; DROP TABLE IF EXISTS katalog; DROP TABLE IF EXISTS katalog_cari;
DROP TABLE IF EXISTS populer; DROP TABLE IF EXISTS populer_katalog; DROP TABLE IF EXISTS populer_riwayat; DROP TABLE IF EXISTS populer_sebut;
DROP TABLE IF EXISTS perawi; DROP TABLE IF EXISTS sanad_perawi;
CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
CREATE TABLE kitab (
  id TEXT PRIMARY KEY, urut INT, nama TEXT, nama_arab TEXT, penyusun TEXT, wafat_h INT, sistem_nomor TEXT,
  jumlah_lidwa INT, jumlah_standar INT, terbit INT, tingkat_a INT, tingkat_b INT, karantina INT, dinilai INT,
  penilai TEXT, edisi TEXT
);
CREATE TABLE bab (kitab_id TEXT, no INT, nama TEXT, jumlah INT, n_awal INT, nama_ar TEXT, nama_en TEXT, nama_id_sumber TEXT,
  PRIMARY KEY (kitab_id, no));
-- judul kitab & bab dari teks OpenITI, unik (riwayat.judul_id); cara per riwayat di riwayat.judul_cara
-- ('teks' = dicocokkan isi, 'urutan' = dari tetangga, 'nomor' = nomor sama, 'koreksi-cetak' = koreksi dari kitab cetak)
CREATE TABLE judul_bab (id INTEGER PRIMARY KEY, kitab_ar TEXT, kitab_nama_id TEXT, bab_ar TEXT);
CREATE TABLE riwayat (
  n INTEGER PRIMARY KEY, id TEXT, kitab_id TEXT, slug TEXT, urut INT, no_tampil TEXT,
  no_standar TEXT, no_arab TEXT, no_lidwa INT, bab_no INT, arab TEXT, terjemah TEXT, rantai_json TEXT,
  kecocokan REAL, tingkat TEXT, alasan TEXT,
  no_edisi TEXT,                -- nomor pada edisi tahqiq (Ahmad: ar-Risalah; Darimi: Asad; Syafi'i: al-Fahl)
  -- Data per riwayat yang dulu tabel terpisah (penilaian, mirip, sanad_perawi, judul) kini kolom JSON di baris ini:
  -- impor menulis jauh lebih sedikit baris dan halaman hadits membaca lebih sedikit baris (docs/12).
  nilai_json TEXT,              -- [[penilai, hukum, kategori], ...] urut penilai
  jalur_json TEXT,              -- takhrij: [[n, skor, tingkat], ...] kedua arah, satu per riwayat ('sama' didahulukan)
  perawi_json TEXT,             -- [[posisi segmen sanad, id perawi], ...] hanya yang pasti
  judul_id INT, judul_cara TEXT
);
CREATE INDEX ix_riwayat_edisi ON riwayat (kitab_id, no_edisi) WHERE no_edisi IS NOT NULL;
CREATE UNIQUE INDEX ix_riwayat_slug ON riwayat (kitab_id, slug);
CREATE INDEX ix_riwayat_urut ON riwayat (kitab_id, urut);
CREATE INDEX ix_riwayat_bab ON riwayat (kitab_id, bab_no, urut);
CREATE TABLE kata_df (kata TEXT PRIMARY KEY, n INT) WITHOUT ROWID;
CREATE VIRTUAL TABLE cari USING fts5 (
  arab_polos, arab_akar, terjemah_polos, perawi, judul,
  content = '', tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE tema (id TEXT PRIMARY KEY, judul TEXT, induk TEXT, jumlah INT);
CREATE TABLE he_hadits (id TEXT PRIMARY KEY, judul TEXT, teks_id TEXT, teks_ar TEXT, atribusi TEXT, derajat TEXT,
  penjelasan TEXT, faedah_json TEXT, url TEXT, boleh_tampil INT);
CREATE TABLE he_tema (he_id TEXT, tema_id TEXT);
CREATE INDEX ix_he_tema ON he_tema (tema_id);
CREATE INDEX ix_he_tema_he ON he_tema (he_id);
CREATE TABLE he_riwayat (he_id TEXT, n INT, skor REAL);
CREATE INDEX ix_he_riwayat_n ON he_riwayat (n);
CREATE INDEX ix_he_riwayat_he ON he_riwayat (he_id);
-- Riyadhus Shalihin: kitab himpunan (an-Nawawi menyebut sumbernya); sumber = tautan ke riwayat di kitab asal
CREATE TABLE riyadh_info (n INTEGER PRIMARY KEY, atribusi_ar TEXT, kitab_atribusi TEXT, catatan_ar TEXT, no_terjemah INT);
CREATE TABLE sumber (a INT, b INT, skor REAL, kitab_disebut INT, sahabat_sama INT, peringkat INT);
CREATE INDEX ix_sumber_a ON sumber (a);
CREATE INDEX ix_sumber_b ON sumber (b);
-- Katalog ucapan populer & palsu dari kitab klasik (pipeline/katalog_palsu.py)
CREATE TABLE katalog_kitab (id TEXT PRIMARY KEY, nama TEXT, nama_ar TEXT, penulis TEXT, wafat INT, edisi TEXT);
CREATE TABLE katalog (k INTEGER PRIMARY KEY, id TEXT UNIQUE, kitab_id TEXT, no INT, judul_ar TEXT, teks_ar TEXT, kata_kunci TEXT);
CREATE VIRTUAL TABLE katalog_cari USING fts5 (judul, content = '', tokenize = 'unicode61 remove_diacritics 2');
CREATE TABLE populer (id TEXT PRIMARY KEY, urut INT, teks_id TEXT, varian TEXT, arab TEXT, catatan TEXT);
CREATE TABLE populer_katalog (populer_id TEXT, katalog_id TEXT, skor REAL);
CREATE TABLE populer_riwayat (populer_id TEXT, n INT, skor REAL);
CREATE TABLE populer_sebut (populer_id TEXT, katalog_id TEXT, kutipan TEXT);
-- Perawi (Taqrib at-Tahdzib + Tahdzib al-Kamal) dan identifikasi per segmen sanad (pipeline/perawi.py, hanya 'pasti')
-- guru_json/murid_json/riwayat_json dihitung di sini supaya halaman perawi hanya membaca 1 baris (batas baca D1 gratis)
CREATE TABLE perawi (id TEXT PRIMARY KEY, taqrib INT, tk_no INT, nama TEXT, teks_taqrib TEXT, penilaian TEXT, tingkat INT,
  tabaqah INT, wafat INT, wafat_ragu INT, rumuz TEXT, n_riwayat INT, guru_json TEXT, murid_json TEXT, riwayat_json TEXT);
CREATE INDEX ix_perawi_n ON perawi (n_riwayat);
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
            if len(v.encode("utf8")) + len(kepala) > MAKS_PERNYATAAN:
                raise ValueError(f"satu baris {tabel} terlalu panjang untuk D1 ({len(v.encode('utf8'))} byte): potong teksnya")
            if buf and (pjg + len(v.encode("utf8")) + 2 > MAKS_PERNYATAAN or len(buf) >= MAKS_BARIS):
                self.tulis(kepala + ",".join(buf) + ";\n")
                buf, pjg = [], len(kepala)
            buf.append(v)
            pjg += len(v.encode("utf8")) + 1
        if buf:
            self.tulis(kepala + ",".join(buf) + ";\n")

    def tutup(self):
        self.f.close()


# Kitab yang di sumber penomoran kita hanya punya satu sumber digital (Lidwa). Edisi tahqiq OpenITI menjadi
# sumber kedua (tingkat A bila >= 90% teks Lidwa ada di blok edisi), sumber judul, dan nomor edisi.
LIDWA_SAJA = {"ahmad": "ar-Risalah (tahqiq Syu'aib al-Arna'uth dkk.)",
              "darimi": "Dar al-Mughni (tahqiq Husain Salim Asad)",
              "syafii": "Ghiras (tahqiq Mahir Yasin al-Fahl)"}
PENILAI_EDISI = {"darimi": "Husain Salim Asad"}


def kategori_ar(t):
    """Kategori kasar penilaian berbahasa Arab, dari klausa PERTAMA (teks lengkap tetap ditampilkan)."""
    n = norm_ar(re.split(r"،|\.|\s(?:و?لكن|غير ان)\s", t or "", maxsplit=1)[0])
    if any(x in n for x in ("موضوع", "باطل", "كذب")):
        return "palsu"
    if "ضعيف" in n:
        return "lemah"
    if any(x in n for x in ("مرسل", "موقوف", "مقطوع", "منقطع", "معضل")):
        return "lainnya"
    if "صحيح" in n and "حسن" in n:
        return "shahih-hasan"
    if "صحيح" in n or "جيد" in n:
        return "shahih"
    if "حسن" in n:
        return "hasan"
    return "lainnya"


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
    bab_path = os.path.join(BUILD, "bab.sqlite")
    judul_rw, nama_bagian = {}, {}
    if os.path.exists(bab_path):
        bj = sqlite3.connect(bab_path)
        bj.row_factory = sqlite3.Row
        judul_rw = {r["riwayat_id"]: dict(r) for r in bj.execute("SELECT * FROM riwayat_bab")}
        nama_bagian = {(r["kitab_id"], r["bab_no"]): (r["nama_ar"], r["nama_id"]) for r in bj.execute("SELECT * FROM kitab_nama")}
    judul_n = {}
    # Bagian (bab_no) untuk kitab Lidwa-saja, diurutkan menurut posisi pertamanya di edisi tahqiq.
    kunci_bagian = lambda kid, j: (j["bab_ar"] or j["kitab_ar"]) if kid == "ahmad" else j["kitab_ar"]
    bagian_lidwa = {}
    for kid in LIDWA_SAJA:
        awal = {}
        for rid, j in judul_rw.items():
            if rid.startswith(kid + ":") and kunci_bagian(kid, j):
                k = kunci_bagian(kid, j)
                awal[k] = min(awal.get(k, 1e12), j["urut_openiti"] if j["urut_openiti"] is not None else 1e12)
        for i, k in enumerate(sorted(awal, key=awal.get), start=1):
            bagian_lidwa[(kid, k)] = i
    pen_edisi = []
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
        j = judul_rw.get(rid)
        no_edisi = None
        if kid in LIDWA_SAJA:
            cocok = j is not None and j["cara"] == "teks" and (j["skor"] or 0) >= 0.9
            k = kunci_bagian(kid, j) if j else None
            babno = bagian_lidwa.get((kid, k), 0) if k else 0
            nama_b = (j["kitab_nama_id"] if (j and kid != "ahmad") else None) or k or "Belum terpetakan ke edisi tahqiq"
            bb = bab.setdefault((kid, babno), [nama_b, 0, n, k, None, None])
            bb[1] += 1
            if cocok:
                tk, kc, no_edisi = "A", j["skor"], (str(j["no_openiti"]) if j["no_openiti"] is not None else None)
                al = f"teks Arab Lidwa tercakup {round(j['skor'] * 100)}% di edisi {LIDWA_SAJA[kid]} (OpenITI); terjemah dari baris Lidwa yang sama"
                if kid in PENILAI_EDISI and j["tahqiq"]:
                    pen_edisi.append((n, PENILAI_EDISI[kid], j["tahqiq"][:400], kategori_ar(j["tahqiq"])))
            else:
                al = (al + "; " if al else "") + f"belum cocok >= 90% dengan edisi {LIDWA_SAJA[kid]}"
        data_riwayat.append((n, rid, kid, slug, urut_dalam[kid], tampil, nos, noa, nol, babno, arab, terj, rantai, kc, tk, al, no_edisi))
        na = norm_ar(arab)
        nama = " ".join(json.loads(rantai)) if rantai else ""
        if j:
            judul_n[n] = (j["kitab_ar"], j["kitab_nama_id"], j["bab_ar"], j["cara"])
        teks_judul = " ".join(x for x in [norm_id(j["kitab_nama_id"] or ""), akar_ar(norm_ar((j["kitab_ar"] or "") + " " + (j["bab_ar"] or "")))] if x) if j else ""
        data_cari.append((n, na, akar_ar(na), norm_id(terj), norm_id(nama), teks_judul))
        if babno is not None and kid not in LIDWA_SAJA:
            b = bab.setdefault((kid, babno), [babnama, 0, n, None, babnama, None])
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
                                 terj if pasti else None, None, None, tk, alasan, None))
            na = norm_ar(arab)
            ar_b, id_b = bab_ry.get(babno, (None, None))
            data_cari.append((n, na, akar_ar(na), norm_id(terj if pasti else ""), "",
                              (norm_id(id_b or "") + " " + akar_ar(norm_ar(ar_b or ""))).strip()))
            data_ry_info.append((n, atr, katr, catatan or None, noter if pasti else None))
            for rid, sk, kd, sh, pk in sumber_ry[u]:
                if rid in n_of:
                    data_sumber.append((n, n_of[rid], sk, kd, sh, pk))
            if babno is not None:
                ar, idn = bab_ry.get(babno, (None, None))
                b = bab.setdefault(("riyadh", babno), [idn or ar, 0, n, ar, None, idn])
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
    # penilaian akhir = fawazahmed0 + muhaqqiq edisi (Asad untuk Darimi)
    penilaian_akhir = [(n_of[r[0]], r[1], r[2], r[3]) for r in q("SELECT riwayat_id, penilai, hukum, kategori FROM penilaian")
                       if r[0] in n_of] + pen_edisi
    kitab_n = {r[0]: r[2] for r in data_riwayat}
    tk_kitab = collections.Counter((r[2], r[14]) for r in data_riwayat)
    dinilai_kitab = collections.defaultdict(set)
    penilai_kitab = collections.defaultdict(set)
    for n_, pnl, _, _ in penilaian_akhir:
        dinilai_kitab[kitab_n[n_]].add(n_)
        penilai_kitab[kitab_n[n_]].add(pnl)
    kit = []
    for kid, nama, nama_ar, penyusun, wafat, sistem, nl, ns in q(
            "SELECT id, nama, nama_arab, penyusun, wafat_h, sistem_nomor, jumlah_lidwa, jumlah_standar FROM kitab"):
        karantina = q("SELECT count(*) FROM riwayat WHERE kitab_id=? AND tingkat='K'", kid)[0][0]
        a_, b_ = tk_kitab[(kid, "A")], tk_kitab[(kid, "B")]
        kit.append((kid, urut_kitab[kid], nama, nama_ar, penyusun, wafat, sistem, nl, ns, a_ + b_, a_, b_, karantina,
                    len(dinilai_kitab[kid]), json.dumps(sorted(penilai_kitab[kid]), ensure_ascii=False), LIDWA_SAJA.get(kid)))
    if ry_kitab:
        kit.append(ry_kitab + (None,))
    w.sisip("kitab", ["id", "urut", "nama", "nama_arab", "penyusun", "wafat_h", "sistem_nomor", "jumlah_lidwa",
                      "jumlah_standar", "terbit", "tingkat_a", "tingkat_b", "karantina", "dinilai", "penilai", "edisi"], kit)
    # Nama bagian kitab: Indonesia (glosarium Teman Hadits, belum ditinjau) > Inggris (fawazahmed0); Arab dari OpenITI.
    baris_bab = []
    for (k, no), v in sorted(bab.items()):
        ar, idn = nama_bagian.get((k, no), (None, None))
        if k == "riyadh" or k in LIDWA_SAJA:
            baris_bab.append((k, no, v[0], v[1], v[2], v[3], None, v[5]))
        else:
            baris_bab.append((k, no, idn or v[0], v[1], v[2], ar, v[4], None))
    w.sisip("bab", ["kitab_id", "no", "nama", "jumlah", "n_awal", "nama_ar", "nama_en", "nama_id_sumber"], baris_bab)
    # --- data per riwayat sebagai kolom JSON (dulu tabel penilaian, mirip, sanad_perawi, judul) ------------------
    # Setiap baris tabel DAN setiap entri indeks dihitung D1 sebagai "baris ditulis" saat impor; tabel-tabel itu
    # (±1 juta tulisan) selalu dibaca per riwayat, jadi cukup disimpan di baris riwayatnya sendiri.
    js = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":")) if x else None
    nilai = collections.defaultdict(list)
    for n_, pnl, hk, kat in sorted(penilaian_akhir, key=lambda x: (x[0], x[1] or "")):
        nilai[n_].append([pnl, hk, kat])
    jalur = collections.defaultdict(dict)
    n_mirip = 0
    tk_path = os.path.join(BUILD, "takhrij.sqlite")
    if os.path.exists(tk_path):
        for a, b, sk, tk in sqlite3.connect(tk_path).execute("SELECT a, b, skor, tingkat FROM mirip"):
            if a not in n_of or b not in n_of:
                continue
            n_mirip += 1
            for x, y in ((n_of[a], n_of[b]), (n_of[b], n_of[a])):
                ada = jalur[x].get(y)     # aturan sama dengan halaman hadits dulu: 'sama' didahulukan, lalu skor tertinggi
                if ada is None or (ada[1] != "sama" and tk == "sama") or (ada[1] == tk and sk > ada[0]):
                    jalur[x][y] = (sk, tk)
    pos_perawi = collections.defaultdict(list)
    n_pr = 0
    pr_path = os.path.join(BUILD, "perawi.sqlite")
    if os.path.exists(pr_path):
        pr0 = sqlite3.connect(pr_path)
        ids0 = {tk: pid for tk, pid in pr0.execute("SELECT tk_id, id FROM perawi")}
        for rid, pos, tk in pr0.execute("SELECT riwayat_id, pos, tk_id FROM sebutan WHERE label='pasti' ORDER BY riwayat_id, pos"):
            if rid in n_of and tk in ids0:
                pos_perawi[n_of[rid]].append([pos, ids0[tk]])
                n_pr += 1
    judul_id = {}
    for n_, (ka, kn, ba, _) in sorted(judul_n.items()):
        judul_id.setdefault((ka, kn, ba), len(judul_id) + 1)
    data_riwayat = [r + (js(nilai.get(r[0])),
                         js([[y, round(sk, 3), tk] for y, (sk, tk) in sorted(jalur[r[0]].items())]) if r[0] in jalur else None,
                         js(pos_perawi.get(r[0])),
                         judul_id[judul_n[r[0]][:3]] if r[0] in judul_n else None,
                         judul_n[r[0]][3] if r[0] in judul_n else None) for r in data_riwayat]
    w.sisip("judul_bab", ["id", "kitab_ar", "kitab_nama_id", "bab_ar"], [(i,) + k for k, i in judul_id.items()])
    # Peta n -> kitab & tingkat untuk pencarian (site/src/cari.js): n sudah urut (urutan kitab, urutan riwayat) dan
    # setiap kitab menempati rentang n yang bersambung, jadi pencarian tidak perlu membaca baris riwayat setiap hasil.
    rentang = []
    for r in data_riwayat:
        if rentang and rentang[-1][0] == r[2] and rentang[-1][2] == r[0] - 1:
            rentang[-1][2] = r[0]
        else:
            assert all(x[0] != r[2] for x in rentang), "rentang n per kitab harus bersambung"
            rentang.append([r[2], r[0], r[0]])
    bit = bytearray(len(data_riwayat) // 8 + 2)
    for r in data_riwayat:
        if r[14] == "B":
            bit[r[0] >> 3] |= 1 << (r[0] & 7)
    import base64
    w.sisip("info", ["kunci", "nilai"], [("peta_n", json.dumps(rentang)), ("bitmap_tingkat_b", base64.b64encode(bytes(bit)).decode())])
    w.sisip("riyadh_info", ["n", "atribusi_ar", "kitab_atribusi", "catatan_ar", "no_terjemah"], data_ry_info)
    w.sisip("sumber", ["a", "b", "skor", "kitab_disebut", "sahabat_sama", "peringkat"], data_sumber)
    w.sisip("riwayat", ["n", "id", "kitab_id", "slug", "urut", "no_tampil", "no_standar", "no_arab", "no_lidwa", "bab_no",
                        "arab", "terjemah", "rantai_json", "kecocokan", "tingkat", "alasan", "no_edisi",
                        "nilai_json", "jalur_json", "perawi_json", "judul_id", "judul_cara"], data_riwayat)
    w.sisip("cari", ["rowid", "arab_polos", "arab_akar", "terjemah_polos", "perawi", "judul"], data_cari)

    # frekuensi kata Indonesia (untuk "cek teks"): berapa riwayat memuat kata (setelah stem ringan)
    df = collections.Counter()
    for _, _, _, terj_polos, _, _ in data_cari:
        df.update({stem_id(x) for x in terj_polos.split()})
    w.sisip("kata_df", ["kata", "n"], sorted(df.items()))

    he_path = os.path.join(BUILD, "hadeethenc.sqlite")
    n_he = 0
    if os.path.exists(he_path):
        h = sqlite3.connect(he_path)
        try:
            w.sisip("tema", ["id", "judul", "induk", "jumlah"], h.execute("SELECT id, judul, induk, jumlah FROM tema"))
            meta = dict(h.execute("SELECT kunci, nilai FROM hadeethenc_meta"))
            # Daftar tema sebagai satu baris info: pencarian & halaman tema dulu membaca 447 baris tema per permintaan
            # dan menormalkan judulnya di Worker. Urutan = urutan baris tabel tema (rowid), judul_norm = norm_id(judul).
            tema_json = json.dumps([[i, j, ind, jml, norm_id(j)] for i, j, ind, jml in
                                    h.execute("SELECT id, judul, induk, jumlah FROM tema ORDER BY rowid")],
                                   ensure_ascii=False, separators=(",", ":"))
            w.sisip("info", ["kunci", "nilai"], [("hadeethenc_versi", meta.get("versi", "")), ("hadeethenc_sumber", meta.get("sumber", "")),
                                                 ("tema_json", tema_json)])
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
    kt_path = os.path.join(BUILD, "katalog.sqlite")
    n_kt = 0
    if os.path.exists(kt_path):
        kt = sqlite3.connect(kt_path)
        w.sisip("katalog_kitab", ["id", "nama", "nama_ar", "penulis", "wafat", "edisi"], kt.execute("SELECT * FROM katalog_kitab"))
        ent = kt.execute("SELECT id, kitab_id, no, judul_ar, teks_ar, kata_kunci FROM katalog").fetchall()
        n_kt = len(ent)
        # Beberapa bab al-Maudhu'at memuat puluhan jalur sanad; batas satu pernyataan D1 ±100 KB.
        potong = lambda t: t if len(t) <= 12000 else t[:12000] + " … [teks dipotong; lihat kitab aslinya]"
        w.sisip("katalog", ["k", "id", "kitab_id", "no", "judul_ar", "teks_ar", "kata_kunci"],
                [(i, e[0], e[1], e[2], e[3], potong(e[4]), e[5]) for i, e in enumerate(ent, 1)])
        w.sisip("katalog_cari", ["rowid", "judul"],
                [(i, akar_ar(norm_ar(e[3] + " " + " ".join(re.sub(r"^حديث\s*:?\s*", "", e[4]).split()[:10])))) for i, e in enumerate(ent, 1)])
        w.sisip("populer", ["id", "urut", "teks_id", "varian", "arab", "catatan"],
                [(r[0], i) + tuple(r[1:]) for i, r in enumerate(kt.execute("SELECT id, teks_id, varian, arab, catatan FROM populer"), 1)])
        w.sisip("populer_katalog", ["populer_id", "katalog_id", "skor"], kt.execute("SELECT * FROM populer_katalog"))
        w.sisip("populer_sebut", ["populer_id", "katalog_id", "kutipan"], kt.execute("SELECT * FROM populer_sebut"))
        w.sisip("populer_riwayat", ["populer_id", "n", "skor"],
                [(p, n_of[r], s_) for p, r, s_ in kt.execute("SELECT * FROM populer_riwayat") if r in n_of])
    if os.path.exists(pr_path):
        pr = sqlite3.connect(pr_path)
        ids = {tk: pid for tk, pid in pr.execute("SELECT tk_id, id FROM perawi")}
        info_p = {pid: (nama, tingkat) for pid, nama, tingkat in pr.execute("SELECT id, nama, tingkat FROM perawi")}
        # guru (posisi +1) & murid (posisi -1) yang SAMA-SAMA pasti di rantai yang sama; daftar riwayat menurut urutan kitab
        posisi = collections.defaultdict(dict)
        for rid, pos, tk in pr.execute("SELECT riwayat_id, pos, tk_id FROM sebutan WHERE label='pasti'"):
            if tk in ids:
                posisi[rid][pos] = ids[tk]
        guru, murid, riw = (collections.defaultdict(collections.Counter) for _ in range(3))
        urut_kitab = {k: i for i, k in enumerate(["bukhari", "muslim", "abudawud", "tirmidzi", "nasai", "ibnumajah"])}
        meta_r = {rid: (kid, slug, tampil, urut) for rid, kid, slug, tampil, urut in
                  ((x[1], x[2], x[3], x[5], x[4]) for x in data_riwayat)}
        for rid, ps in posisi.items():
            if rid not in meta_r:
                continue
            for pos, pid in ps.items():
                kid, slug, tampil, urut = meta_r[rid]
                riw[pid][(urut_kitab.get(kid, 9), urut, kid, slug, tampil)] += 1
                if pos + 1 in ps:
                    guru[pid][ps[pos + 1]] += 1
                if pos - 1 in ps:
                    murid[pid][ps[pos - 1]] += 1
        daftar = lambda c: json.dumps([[q, info_p[q][0], info_p[q][1], n] for q, n in c.most_common(24)], ensure_ascii=False)
        w.sisip("perawi", ["id", "taqrib", "tk_no", "nama", "teks_taqrib", "penilaian", "tingkat", "tabaqah", "wafat", "wafat_ragu",
                           "rumuz", "n_riwayat", "guru_json", "murid_json", "riwayat_json"],
                [row + (daftar(guru[row[0]]), daftar(murid[row[0]]),
                        json.dumps([[k[2], k[3], k[4]] for k in sorted(riw[row[0]])[:80]], ensure_ascii=False))
                 for row in pr.execute("SELECT id, taqrib, tk_no_cetak, nama, teks_taqrib, penilaian, tingkat, tabaqah, wafat, wafat_ragu, rumuz, n_riwayat FROM perawi")])
    w.tutup()
    berkas = sorted(f for f in os.listdir(OUT) if f.endswith(".sql"))
    ukuran = sum(os.path.getsize(os.path.join(OUT, f)) for f in berkas)
    print(f"{len(data_riwayat)} riwayat (termasuk {len(data_ry_info)} Riyadhus Shalihin), {len(data_sumber)} tautan sumber Riyadh, {n_mirip} pasangan takhrij, {n_kt} entri katalog, {n_pr} perawi teridentifikasi di sanad, {n_he} hadits HadeethEnc, {len(df)} kata -> "
          f"{len(berkas)} berkas, {ukuran / 1e6:.0f} MB di build/d1/", file=sys.stderr)


if __name__ == "__main__":
    main()
