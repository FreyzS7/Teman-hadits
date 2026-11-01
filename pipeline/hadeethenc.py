#!/usr/bin/env python3
"""Impor tema & hadits HadeethEnc (Ensiklopedia Terjemahan Hadis-hadis Nabi) dan petakan ke riwayat kita.

Hasil: build/hadeethenc.sqlite (terpisah dari build/teman-hadits.sqlite, yang hanya DIBACA).

Langkah:
  1. Unduh (sopan, ≤ 3 permintaan/detik, cache per berkas, bisa dilanjutkan) ke sources/hadeethenc/:
     kategori -> daftar hadits per kategori -> detail tiap hadits (bahasa Indonesia).
  2. Simpan tema, hadits, dan relasi tema-hadits.
  3. Petakan matan Arab HadeethEnc ke teks Arab riwayat tingkat A/B (2-gram setelah normalisasi
     dan pemotongan awalan). Skor = bagian 2-gram matan HadeethEnc (berbobot IDF) yang ada di teks
     riwayat; disimpan bila ≥ 0,6, maksimal 40 pasangan per hadits.
  4. Uji silang: atribusi HadeethEnc ("متفق عليه", "رواه مسلم", ...) dibandingkan dengan kitab
     pasangan hasil pemetaan kita. Atribusi itu dibuat penyusun HadeethEnc, jadi ia saksi independen.

Syarat pemakaian HadeethEnc (modal "Terms and Policies" di hadeethenc.com, dibaca 2026-11-01):
terjemahan boleh diunduh dan diterbitkan ulang asalkan tidak diubah, sumber disebut jelas
(HadeethEnc.com), nomor versi disebut, catatan dilaporkan ke sumber, diperbarui mengikuti versi
terbaru, dan tidak ditampilkan bersama iklan yang tidak pantas. Lihat docs/07-hadeethenc.md.

Jalankan:
    python3 -I pipeline/hadeethenc.py unduh [--maks-detik 500]   # boleh diulang sampai lengkap
    python3 -I pipeline/hadeethenc.py bangun                      # tulis build/hadeethenc.sqlite
"""
import collections
import datetime
import json
import math
import os
import random
import re
import sqlite3
import sys
import subprocess
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, SRC, norm_ar, stem_ar  # noqa: E402

API = "https://hadeethenc.com/api/v1"
BAHASA = "id"
DIR = os.path.join(SRC, "hadeethenc")
OUT = os.path.join(BUILD, "hadeethenc.sqlite")
JEDA = 0.34  # detik antar permintaan (≈ 3/detik)
_terakhir = [0.0]


# ---------------------------------------------------------------------------
# Unduh
# ---------------------------------------------------------------------------
def ambil(url, tujuan):
    """Unduh JSON ke berkas cache; lewati bila sudah ada. Retry dengan backoff saat gagal.

    Memakai curl biasa (identitas bawaan curl, tidak dipalsukan). Server HadeethEnc menolak
    identitas bawaan urllib Python, dan kita tidak menyamar sebagai peramban.
    """
    if os.path.exists(tujuan):
        return json.load(open(tujuan, encoding="utf8"))
    os.makedirs(os.path.dirname(tujuan), exist_ok=True)
    galat = None
    for coba, tunggu in enumerate((0, 2, 4, 8, 16)):
        time.sleep(max(0.0, JEDA - (time.time() - _terakhir[0])) + tunggu)
        _terakhir[0] = time.time()
        r = subprocess.run(["curl", "-sS", "-m", "60", "-o", tujuan + ".part", "-w", "%{http_code}", url],
                           capture_output=True, text=True)
        kode = r.stdout.strip()
        if r.returncode == 0 and kode == "200":
            try:
                obj = json.load(open(tujuan + ".part", encoding="utf8"))
            except json.JSONDecodeError as e:
                galat = e
                continue
            os.replace(tujuan + ".part", tujuan)
            return obj
        galat = RuntimeError(f"{url}: curl exit {r.returncode}, HTTP {kode} {r.stderr.strip()[:200]}")
        if kode not in ("000", "429", "500", "502", "503", "504"):
            break
    if os.path.exists(tujuan + ".part"):
        os.remove(tujuan + ".part")
    raise galat


def unduh(maks_detik):
    mulai = time.time()
    kats = ambil(f"{API}/categories/list/?language={BAHASA}", os.path.join(DIR, f"categories_{BAHASA}.json"))
    ids = set()
    for k in kats:
        hal = 1
        while True:
            if time.time() - mulai > maks_detik:
                print(f"batas waktu tercapai di daftar kategori {k['id']}; jalankan lagi untuk melanjutkan",
                      file=sys.stderr)
                return False
            d = ambil(f"{API}/hadeeths/list/?language={BAHASA}&category_id={k['id']}&page={hal}&per_page=100",
                      os.path.join(DIR, "list", f"cat{k['id']}_p{hal}.json"))
            ids.update(h["id"] for h in d["data"])
            if hal >= int(d["meta"]["last_page"]):
                break
            hal += 1
    print(f"{len(kats)} kategori, {len(ids)} id hadits unik", file=sys.stderr)
    for n, hid in enumerate(sorted(ids, key=int)):
        if time.time() - mulai > maks_detik:
            print(f"batas waktu tercapai ({n}/{len(ids)} detail); jalankan lagi untuk melanjutkan", file=sys.stderr)
            return False
        ambil(f"{API}/hadeeths/one/?language={BAHASA}&id={hid}", os.path.join(DIR, "one", f"{hid}.json"))
    tanggal = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    meta = os.path.join(DIR, "unduhan.json")
    if not os.path.exists(meta):
        json.dump({"api": API, "bahasa": BAHASA, "tanggal_ambil_utc": tanggal, "jumlah_hadits": len(ids),
                   "jumlah_kategori": len(kats)}, open(meta, "w"), indent=1)
    print("unduhan lengkap", file=sys.stderr)
    return True


# ---------------------------------------------------------------------------
# Pemetaan ke riwayat
# ---------------------------------------------------------------------------
def grams(teks_norm):
    w = [stem_ar(x) for x in teks_norm.split()]
    return {zlib.crc32(" ".join(w[i:i + 2]).encode()) for i in range(len(w) - 1)}


_KUTIP = re.compile(r"[«»\"“”]")
_DALAM_KUTIP = re.compile(r"«([^«»]+)»")
_KURUNG = re.compile(r"\([^()]{0,200}\)")           # catatan editor: (ولمسلم: ...), (وفي رواية: ...)
_SISIPAN = re.compile(r"-[^-\n]{1,60}-")              # -رضي الله عنه-, -أو قال: امرأ-
_PEMBUKA = re.compile(r"^\s*عن\s+[^:«]{0,120}?(?:رضي الله عن(?:ه|ها|هما|هم)\s*)?(?:مرفوعا|مرفوعًا|قال|قالت|أن|أنه)?\s*[:،]?\s*")


def matan_he(h):
    """Matan HadeethEnc tanpa pembuka sanad ringkas ("عن ... قال:") dan tanpa catatan editor.

    Urutan: bila ada kutipan «...», ambil semua isinya; bila tidak, buang hadeeth_intro_ar atau pola
    pembuka "عن ... رضي الله عنه قال". Lalu buang catatan dalam kurung dan sisipan bertanda minus.
    """
    ar, intro = (h.get("hadeeth_ar") or "").strip(), (h.get("hadeeth_intro_ar") or "").strip()
    kutip = _DALAM_KUTIP.findall(ar)
    if kutip and sum(len(k) for k in kutip) > 25:
        ar = " ".join(kutip)
    elif intro and ar.startswith(intro):
        ar = ar[len(intro):]
    else:
        ar = _PEMBUKA.sub("", strip_harakat_ringan(ar), count=1)
    ar = _KURUNG.sub(" ", ar)
    ar = _SISIPAN.sub(" ", ar)
    return _KUTIP.sub(" ", ar)


def strip_harakat_ringan(s):
    # pola pembuka ditulis tanpa harakat; buang harakat dulu agar cocok
    return re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)


# Nama penyusun dalam atribusi Arab -> id kitab kita. Kitab lain (Baihaqi, Thabrani, Hakim, ...)
# tidak ada di koleksi kita sehingga tidak ikut uji silang.
PENYUSUN = [("البخاري", "bukhari"), ("مسلم", "muslim"), ("أبو داود", "abudawud"), ("ابو داود", "abudawud"),
            ("الترمذي", "tirmidzi"), ("النسائي", "nasai"), ("ابن ماجه", "ibnumajah"), ("مالك", "malik"),
            ("أحمد", "ahmad"), ("احمد", "ahmad"), ("الدارمي", "darimi"), ("الشافعي", "syafii")]


def kitab_atribusi(attr_ar):
    s = (attr_ar or "").replace("ـ", "")
    s = re.sub(r"[ً-ْ]", "", s)
    out = set()
    if re.search("متفق علي(?:ه|ها)", s):  # "متفق عليه" / "متفق عليها" (riwayat ...)
        out |= {"bukhari", "muslim"}
    # "حديث أنس بن مالك" adalah nama sahabat, bukan al-Muwaththa'; buang "بن/ابن + nama" dulu.
    s = re.sub(r"(?:ابن|بن)\s+(?:مالك|أحمد|احمد)", " ", s)
    for nama, kid in PENYUSUN:
        # kata utuh, boleh diawali kata sambung و ("والترمذي", "وأحمد")
        if re.search("(?<![\u0621-\u064A])و?" + nama + "(?![\u0621-\u064A])", s):
            out.add(kid)
    return out


def bangun():
    meta = json.load(open(os.path.join(DIR, "unduhan.json"), encoding="utf8"))
    kats = json.load(open(os.path.join(DIR, f"categories_{BAHASA}.json"), encoding="utf8"))
    hs = [json.load(open(os.path.join(DIR, "one", f), encoding="utf8"))
          for f in sorted(os.listdir(os.path.join(DIR, "one")), key=lambda x: int(x.split(".")[0]))]

    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE tema (id TEXT PRIMARY KEY, judul TEXT, induk TEXT, jumlah INT);
    CREATE TABLE he_hadits (id TEXT PRIMARY KEY, judul TEXT, teks_id TEXT, teks_ar TEXT, atribusi TEXT,
      atribusi_ar TEXT, derajat TEXT, derajat_ar TEXT, penjelasan TEXT, faedah_json TEXT, url TEXT,
      boleh_tampil INT);
    CREATE TABLE he_tema (he_id TEXT, tema_id TEXT);
    CREATE TABLE he_riwayat (he_id TEXT, riwayat_id TEXT, skor REAL, metode TEXT);
    CREATE TABLE hadeethenc_meta (kunci TEXT PRIMARY KEY, nilai TEXT);
    CREATE INDEX ix_he_tema ON he_tema(tema_id);
    CREATE INDEX ix_he_riwayat_r ON he_riwayat(riwayat_id);
    CREATE INDEX ix_he_riwayat_h ON he_riwayat(he_id);
    """)
    for k in kats:
        db.execute("INSERT INTO tema VALUES(?,?,?,?)", (k["id"], k["title"], k["parent_id"], int(k["hadeeths_count"])))
    # Syarat HadeethEnc mengizinkan terbit ulang dengan atribusi & tanpa perubahan -> boleh_tampil = 1.
    # Situs WAJIB menampilkan: "Sumber: HadeethEnc.com", versi/tanggal ambil, dan teks tanpa diubah.
    for h in hs:
        db.execute("INSERT INTO he_hadits VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   (h["id"], h.get("title"), h.get("hadeeth"), h.get("hadeeth_ar"), h.get("attribution"),
                    h.get("attribution_ar"), h.get("grade"), h.get("grade_ar"), h.get("explanation"),
                    json.dumps(h.get("hints") or [], ensure_ascii=False),
                    f"https://hadeethenc.com/{BAHASA}/browse/hadith/{h['id']}", 1))
        for c in h.get("categories") or []:
            db.execute("INSERT INTO he_tema VALUES(?,?)", (h["id"], str(c)))
    for k, v in [("sumber", "HadeethEnc.com — Ensiklopedia Terjemahan Hadis-hadis Nabi"), ("api", meta["api"]),
                 ("bahasa", meta["bahasa"]), ("tanggal_ambil_utc", meta["tanggal_ambil_utc"]),
                 ("versi", f"API v1, diambil {meta['tanggal_ambil_utc']} (API tidak menyediakan nomor versi terjemah)"),
                 ("syarat", "Boleh diterbitkan ulang tanpa diubah, dengan menyebut HadeethEnc.com dan versinya, "
                            "tanpa iklan yang tidak pantas; catatan dilaporkan ke sumber; ikuti versi terbaru.")]:
        db.execute("INSERT INTO hadeethenc_meta VALUES(?,?)", (k, v))

    # --- pemetaan -----------------------------------------------------------------------------
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    riw = src.execute("SELECT id, arab FROM riwayat WHERE tingkat IN ('A','B')").fetchall()
    teks = {}
    df = collections.Counter()
    for rid, ar in riw:
        n = norm_ar(ar)
        teks[rid] = n
        df.update(grams(n))
    N = len(teks)
    LANGKA = 300
    post = collections.defaultdict(list)
    for rid, n in teks.items():
        for g in grams(n):
            if df[g] <= LANGKA:
                post[g].append(rid)

    t0 = time.time()
    statistik = collections.Counter()
    for h in hs:
        m = grams(norm_ar(matan_he(h)))
        if len(m) < 4:
            statistik["matan terlalu pendek"] += 1
            continue
        langka = sorted((g for g in m if 0 < df[g] <= LANGKA), key=lambda g: df[g])[:16]
        cand = collections.Counter()
        for g in langka:
            for rid in post[g]:
                cand[rid] += 1
        # Skor berbobot IDF: 2-gram umum (رسول الله، صلى الله عليه وسلم، كان رسول) hampir tak berbobot,
        # sehingga kecocokan ditentukan oleh bagian matan yang khas. Tanpa ini, matan pendek bisa
        # "cocok" dengan hadits lain hanya karena frasa umum (kasus HE 10940 -> abudawud:1130).
        bobot = {g: math.log(N / (1 + df[g])) if df[g] else math.log(N) for g in m}
        total = sum(bobot.values())
        hasil = []
        for rid, _ in cand.most_common(200):
            c = sum(bobot[g] for g in m & grams(teks[rid])) / total
            if c >= 0.6:
                hasil.append((c, rid))
        hasil.sort(key=lambda x: (-x[0], x[1]))
        for c, rid in hasil[:40]:
            db.execute("INSERT INTO he_riwayat VALUES(?,?,?,?)",
                       (h["id"], rid, round(c, 3), "2gram-idf-matan>=0.6"))
        statistik["terpetakan" if hasil else "tidak terpetakan"] += 1
    db.commit()
    print(f"pemetaan {time.time() - t0:.0f}s: {dict(statistik)}", file=sys.stderr)
    return db, src, hs


def laporan(db, src, hs, seed=20261101):
    q = lambda s, *a: db.execute(s, a).fetchall()
    total = len(hs)
    terpetakan = q("SELECT count(DISTINCT he_id) FROM he_riwayat")[0][0]
    print(f"tema={q('SELECT count(*) FROM tema')[0][0]} hadits={total} terpetakan={terpetakan} "
          f"({100 * terpetakan / total:.1f}%) pasangan={q('SELECT count(*) FROM he_riwayat')[0][0]}")

    # uji silang atribusi
    semua = penuh = sebagian = tanpa = 0
    contoh_gagal = []
    for h in hs:
        harap = kitab_atribusi(h.get("attribution_ar"))
        if not harap:
            continue
        semua += 1
        dapat = {r[0].split(":")[0] for r in q("SELECT riwayat_id FROM he_riwayat WHERE he_id=?", h["id"])}
        if harap <= dapat:
            penuh += 1
        elif harap & dapat:
            sebagian += 1
        else:
            tanpa += 1
            if len(contoh_gagal) < 8:
                contoh_gagal.append((h["id"], h.get("attribution_ar"), sorted(dapat)))
    print(f"uji silang atribusi: {semua} hadits beratribusi ke kitab kita; semua kitab cocok={penuh} "
          f"({100 * penuh / max(1, semua):.1f}%), sebagian={sebagian}, tidak satu pun={tanpa}")
    for c in contoh_gagal:
        print("  contoh tidak cocok:", c)

    # sampel acak untuk cek manual
    rnd = random.Random(seed)
    ids = [r[0] for r in q("SELECT DISTINCT he_id FROM he_riwayat ORDER BY he_id")]
    for hid in rnd.sample(ids, 10):
        h = next(x for x in hs if x["id"] == hid)
        rid, skor = q("SELECT riwayat_id, skor FROM he_riwayat WHERE he_id=? ORDER BY skor DESC, riwayat_id LIMIT 1", hid)[0]
        ar = src.execute("SELECT arab FROM riwayat WHERE id=?", (rid,)).fetchone()[0]
        print(f"\n[sampel] HE {hid} ({h.get('attribution_ar')}) -> {rid} skor {skor}")
        print("  HE :", norm_ar(matan_he(h))[:200])
        print("  KITA:", norm_ar(ar)[-260:])


if __name__ == "__main__":
    perintah = sys.argv[1] if len(sys.argv) > 1 else "bangun"
    if perintah == "unduh":
        maks = float(sys.argv[sys.argv.index("--maks-detik") + 1]) if "--maks-detik" in sys.argv else 1e9
        sys.exit(0 if unduh(maks) else 3)
    elif perintah == "bangun":
        laporan(*bangun())
    else:
        print(__doc__)
