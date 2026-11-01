#!/usr/bin/env python3
"""Riyadhus Shalihin: pecah per hadits, pasangkan Arab<->terjemah MENURUT ISI, hubungkan ke sumbernya.

Masukan : sources/lidwa-carihadis/riyadhus-shalihin.sql (1 baris = 1 bab; kolom arab & terjemah HTML)
Keluaran: build/riyadh.sqlite

Kenapa tidak dipasangkan menurut nomor: penomoran terjemah Indonesia di sumber ini mengikuti edisi lain
(selisih 0–4 dari nomor Arab, berubah-ubah sepanjang kitab), ada nomor salah ketik ("5" di antara 14 dan 16)
dan nomor ayat Al-Qur'an yang terbaca seperti nomor hadits. Memasangkan menurut nomor akan menempelkan
terjemah ke hadits yang salah.

Cara memasangkan: penjajaran urutan (Needleman–Wunsch, berpita) atas seluruh kitab dengan skor dari
  (1) kerangka konsonan nama sahabat  ("وعن جابر" ~ "Dari Jabir"),
  (2) atribusi an-Nawawi             ("متفق عليه" ~ "(Muttafaq 'alaih)"),
  (3) rasio panjang teks.
Terjemah hanya dipasang bila nama sahabat cocok DAN atribusi tidak bertentangan ("pasti").

Sumber (takhrij): matan «...» dicocokkan ke riwayat kita (2-gram berbobot IDF, seperti HadeethEnc).
Uji silang: atribusi an-Nawawi vs kitab hasil pencocokan — saksi independen.

Jalankan:  python3 pipeline/riyadh.py
"""
import collections
import difflib
import json
import math
import os
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, SRC, clean_html, norm_ar, norm_id, read_mysql_dump
from hadeethenc import _KURUNG, _SISIPAN, grams, kitab_atribusi

OUT = os.path.join(BUILD, "riyadh.sqlite")
BERKAS = os.path.join(SRC, "lidwa-carihadis", "riyadhus-shalihin.sql")

# ------------------------------------------------------------------------------------------------
# 1. Pecah teks Arab
# ------------------------------------------------------------------------------------------------
_NOMOR_AR = re.compile(r"^\s*(\d{1,4})\s*[-–]\s*(.*)$")
_KITAB_AR = re.compile(r"^\s*\(\s*(\d{1,2})\s*\)\s*[-–]\s*(.*)$")


def pecah_arab(rows):
    hadits, bab, kitab_ar = [], {}, None
    bab_no = None
    for _id, _k, arab, _t in rows:
        cur = None
        for baris in clean_html(arab).split("\n"):   # sebagian baris dipisah <br>, bukan baris baru
            b = baris.strip()
            if not b:
                continue
            mk = _KITAB_AR.match(b)
            if mk and norm_ar(mk.group(2)).startswith("كتاب"):
                kitab_ar = mk.group(2).strip()
                cur = None
                continue
            m = _NOMOR_AR.match(b)
            if m and norm_ar(m.group(2)).startswith("كتاب"):     # "19 - كتاب الاستغفار" (tanpa kurung)
                kitab_ar = m.group(2).strip()
                cur = None
                continue
            if m and norm_ar(m.group(2)).startswith("باب"):
                bab_no = int(m.group(1))
                bab[bab_no] = {"nama_ar": m.group(2).strip(), "kitab_ar": kitab_ar}
                cur = None
                continue
            if m and hadits and cur is not None and int(m.group(1)) < hadits[-1]["tertulis"] - 50:
                # daftar bernomor di dalam catatan (mis. "1 - لباس الزينة") — bukan hadits baru
                cur["arab"] += "\n" + b
            elif m:
                cur = {"tertulis": int(m.group(1)), "arab": m.group(2).strip(), "bab": bab_no}
                hadits.append(cur)
            elif cur is not None:
                cur["arab"] += "\n" + b
    return hadits, bab


def koreksi_nomor(hadits):
    """Nomor tertulis bisa salah ketik/ganda. Tentukan nomor dari urutan; catat setiap koreksi."""
    prev = 0
    for i, h in enumerate(hadits):
        w = h["tertulis"]
        nxt = hadits[i + 1]["tertulis"] if i + 1 < len(hadits) else None
        if w == prev + 1 or (w > prev and (nxt is None or nxt > w)):
            h["no"], h["koreksi"] = w, None                       # normal, atau ada nomor yang hilang di data
        elif nxt is not None and nxt == prev + 2:
            h["no"], h["koreksi"] = prev + 1, f"nomor tertulis {w}, dikoreksi menjadi {prev + 1} menurut urutan"
        else:
            h["no"], h["koreksi"] = None, f"nomor tertulis {w} tidak sesuai urutan (sebelumnya {prev})"
        if h["no"]:
            prev = h["no"]
    return hadits


_ATRIBUSI_AR = re.compile(r"(متفق\s*علي|رواه|أخرجه|اخرجه)")
_HRK = re.compile(r"[\u064B-\u0652\u0670\u0640]")


def pisah_catatan(teks):
    """Teks digital ini memuat catatan kaki edisi cetaknya di bawah garis "__________": syarah (mis. Ibnu
    'Utsaimin) dan takhrij muhaqqiq ("(2) أخرجه: البخاري 2/ 99 (1281)"). Itu BUKAN teks an-Nawawi, jadi
    dipisah sebagai catatan. Semua yang di atas garis (termasuk hadits yang ditulis beberapa baris,
    riwayat tambahan "وفي رواية…", dan penjelasan kata "قوله…" dari an-Nawawi) tetap teks Riyadhus Shalihin."""
    baris = [b.strip() for b in clean_html(teks).split("\n") if b.strip()]
    potong = next((i for i, b in enumerate(baris) if re.match(r"^_{3,}", b) or re.match(r"^\(\d{1,2}\)\s", b)), len(baris))
    catatan = [b for b in baris[potong:] if not re.match(r"^_{3,}$", b)]
    return "\n".join(baris[:potong]), "\n".join(catatan)


def atribusi_arab(teks):
    """Kalimat atribusi an-Nawawi: dari kemunculan PERTAMA 'رواه'/'متفق عليه'/'أخرجه' sampai akhir barisnya."""
    for baris in _HRK.sub("", teks).split("\n"):
        m = _ATRIBUSI_AR.search(baris)
        if m:
            return baris[m.start():].strip()[:240]
    return ""


def teks_utama(teks):
    """Teks sampai akhir baris atribusi pertama (tanpa penjelasan kata sesudahnya) — untuk pencocokan sumber."""
    baris = teks.split("\n")
    for i, b in enumerate(baris):
        if _ATRIBUSI_AR.search(_HRK.sub("", b)):
            return "\n".join(baris[:i + 1])
    return teks


# ------------------------------------------------------------------------------------------------
# 2. Pecah terjemah Indonesia
# ------------------------------------------------------------------------------------------------
_NOMOR_ID = re.compile(r"(?:^|(?<=[\s\)\.\"']))(\d{1,4})\.\s*(?:[A-Z][a-z]+\s*:\s*)?(?=(?:Dan\s*)?(?:[Dd]ari|Diriwayatkan))")
_BAB_ID = re.compile(r"Bab\s*(\d{1,3})\s*\.\s*(.{3,200}?)(?=\s{2,}|Allah Ta|Firman|$)")


def pecah_indonesia(rows):
    hadits, bab = [], {}
    for _id, _k, _a, terjemah in rows:
        t = clean_html(terjemah).replace("\t", " ")
        mb = _BAB_ID.search(t[:400])
        bab_no = int(mb.group(1)) if mb else None
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", terjemah, re.S | re.I)
        if h1:  # judul bab utuh dari tag <h1>
            judul = re.sub(r"\s+", " ", clean_html(h1.group(1))).strip()
            mj = re.match(r"Bab\s*(\d{1,3})\s*\.\s*(.*)$", judul)
            if mj:
                bab_no, judul = int(mj.group(1)), mj.group(2)
            bab[bab_no] = judul
        elif mb:  # cadangan: potong sebelum ayat pembuka ("Allah Ta'ala berfirman", "Firman Allah")
            judul = re.split(r"Allah\s*Ta|Firman|Rasulullah", re.sub(r"\s+", " ", t[mb.start(2):mb.start(2) + 300]))[0]
            bab[bab_no] = judul.strip(" .")
        ms = list(_NOMOR_ID.finditer(t))
        for i, m in enumerate(ms):
            akhir = ms[i + 1].start() if i + 1 < len(ms) else len(t)
            isi = re.sub(r"\s+", " ", t[m.end():akhir]).strip()
            hadits.append({"no_id": int(m.group(1)), "teks": isi, "bab": bab_no})
    return hadits, bab


NAMA_ID = [(r"\bmuttafaq", {"bukhari", "muslim"}), (r"\bbukhari\b", {"bukhari"}), (r"\bmuslim\b", {"muslim"}),
           (r"\babu ?da(?:w|u)u?d\b", {"abudawud"}), (r"\btirmidzi\b", {"tirmidzi"}), (r"\bnasa ?i\b", {"nasai"}),
           (r"\bibnu? ?majah\b", {"ibnumajah"}), (r"\bimam malik\b|\bmalik\b(?! bin)", {"malik"}),
           (r"\bahmad\b(?! bin)", {"ahmad"}), (r"\bdarimi\b", {"darimi"})]


def atribusi_indonesia(teks):
    ekor = norm_id(teks[-260:])
    m = list(re.finditer(r"\b(riwayat|diriwayatkan|muttafaq|hr)\b", ekor))
    if not m:
        return set(), ""
    bagian = ekor[m[-1].start():]
    out = set()
    for pola, k in NAMA_ID:
        if re.search(pola, bagian):
            out |= k
    return out, bagian


# ------------------------------------------------------------------------------------------------
# 3. Kerangka konsonan nama sahabat (Arab dan Latin dipetakan ke kelas yang sama)
# ------------------------------------------------------------------------------------------------
_AR2 = {"ب": "b", "ت": "t", "ث": "s", "ج": "j", "ح": "h", "خ": "h", "د": "d", "ذ": "d", "ر": "r", "ز": "z", "س": "s",
        "ش": "s", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "غ": "g", "ف": "f", "ق": "k", "ك": "k", "ل": "l", "م": "m",
        "ن": "n", "ه": "h"}
_ABAI_AR = {"ابي", "ابو", "ام", "ابن", "بن", "بنت", "امير", "المومنين", "امير المومنين", "ال"}
_ABAI_ID = {"abu", "abi", "ummu", "ibnu", "bin", "binti", "amirul", "mu", "minin", "yaitu", "yakni", "dari", "dan", "al", "an", "ash", "as", "ad", "ar", "az", "at"}


_UMUM = {"bd", "lh", "lln", "rhmn", "mhmd", "hmd"}   # عبد، الله، الرحمن، محمد، أحمد: terlalu umum untuk membedakan


def _latin_kerangka(w):
    for a, b in (("kh", "h"), ("sy", "s"), ("sh", "s"), ("ts", "s"), ("dz", "d"), ("dh", "d"), ("th", "t"), ("zh", "z"),
                 ("gh", "g"), ("q", "k"), ("x", "ks")):
        w = w.replace(a, b)
    return re.sub(r"[aeiouwy\s']", "", w)


def kerangka_ar(nama):
    """Daftar kerangka konsonan kata-kata khas dalam nama (maks. 5)."""
    out = []
    for w in norm_ar(nama).split():
        if w in _ABAI_AR:
            continue
        k = "".join(_AR2.get(c, "") for c in (w[2:] if w.startswith("ال") else w))
        if len(k) >= 2 and k not in _UMUM:
            out.append(k)
    return out[:5]


def kerangka_id(nama):
    s = re.sub(r"\b(" + "|".join(_ABAI_ID) + r")\b", " ", norm_id(nama))
    out = []
    for w in s.split():
        w = re.sub(r"^(al|as|ash|ad|ar|az|at|an)(?=[a-z]{3})", "", w) if False else w
        k = _latin_kerangka(w)
        if len(k) >= 2 and k not in _UMUM:
            out.append(k)
    return out[:8]


def kemiripan_nama(ka, ki):
    """Bagian kata khas nama Arab yang punya padanan (rasio >= 0.75) di nama Latin."""
    if not ka or not ki:
        return 0.0
    cocok = sum(1 for x in ka if max(difflib.SequenceMatcher(None, x, y).ratio() for y in ki) >= 0.75)
    return cocok / len(ka)


_ORDINAL = r"^(?:[\u0621-\u064A]+\s*)?"  # "الخامس: عن ..." (tanda baca sudah hilang setelah normalisasi)


def nama_sahabat_ar(teks):
    """Nama sahabat; "وعنه/وعنها/وعنهما" (= sahabat hadits sebelumnya) dikembalikan sebagai "<ganti>"."""
    n = norm_ar(teks)
    if re.match(_ORDINAL + r"و?عن(?:ه|ها|هما|هم)(?:\s|$)", n[:40]):
        return "<ganti>"
    m = re.search(r"(?:^|\s)و?عن\s+(.{2,240}?)(?:\s+رضي|\s+قال|\s+قالت|\s+ان\s|\s+انه|$)", n[:320])
    return m.group(1) if m else ""


def nama_sahabat_id(teks):
    if re.match(r"(?:Dan\s*)?[Dd]ari(?:pada)?\s*nya\b|(?:Dan\s*)?[Dd]ari\s+beliau\b", teks):
        return "<ganti>"
    m = re.match(r"(?:Dan\s*)?[Dd]ari\s*(.{2,260}?)(?:\s+r\.a|\s+radhi|\s+katanya|\s+berkata|\s+bahwa|\s+ia\b|,\s+(?:katanya|berkata|bahwa|ia)|$)", teks)
    return m.group(1) if m else ""


def skor_pasangan(a, i):
    nama = kemiripan_nama(a["kerangka"], i["kerangka"])
    sa, si = a["kitab_atr"], i["kitab_atr"]
    if sa and si:
        atr = 1.0 if sa == si else (0.4 if sa & si else -1.5)
    else:
        atr = 0.0
    rasio = len(i["teks"]) / max(1, len(a["arab"]))
    panjang = 0.0 if 0.7 <= rasio <= 6 else -1.0
    return 3 * nama + atr + panjang, nama, atr


def jajarkan(A, I, pita=160):
    """Needleman–Wunsch berpita. Kembalikan daftar (ia, ii)."""
    n, m = len(A), len(I)
    CELAH = -0.6
    NEG = -1e9
    skor = {}
    asal = {}
    skor[(0, 0)] = 0.0
    for x in range(0, n + 1):
        lo, hi = max(0, x - pita), min(m, x + pita)
        for y in range(lo, hi + 1):
            if x == 0 and y == 0:
                continue
            best, dari = NEG, None
            if x > 0 and y > 0 and (x - 1, y - 1) in skor:
                s = skor[(x - 1, y - 1)] + skor_pasangan(A[x - 1], I[y - 1])[0] - 1.5
                if s > best:
                    best, dari = s, "d"
            if x > 0 and (x - 1, y) in skor and skor[(x - 1, y)] + CELAH > best:
                best, dari = skor[(x - 1, y)] + CELAH, "a"
            if y > 0 and (x, y - 1) in skor and skor[(x, y - 1)] + CELAH > best:
                best, dari = skor[(x, y - 1)] + CELAH, "i"
            skor[(x, y)], asal[(x, y)] = best, dari
    x, y, pasang = n, m, []
    while x > 0 or y > 0:
        d = asal[(x, y)]
        if d == "d":
            pasang.append((x - 1, y - 1))
            x, y = x - 1, y - 1
        elif d == "a":
            x -= 1
        else:
            y -= 1
    return pasang[::-1]


# ------------------------------------------------------------------------------------------------
# 4. Takhrij: matan Riyadh -> riwayat kita
# ------------------------------------------------------------------------------------------------
_GUILLEMET = re.compile(r"«([^«»]+)»")


def matan_riyadh(arab, atribusi):
    t = arab.replace(atribusi, " ") if atribusi else arab
    kutip = _GUILLEMET.findall(t)
    if kutip and sum(len(k) for k in kutip) > 25:
        t = " ".join(kutip)
    t = _KURUNG.sub(" ", t)
    t = _SISIPAN.sub(" ", t)
    return t


def main():
    t0 = time.time()
    rows = list(read_mysql_dump(BERKAS))
    A, bab_ar = pecah_arab(rows)
    A = koreksi_nomor(A)
    I, bab_id = pecah_indonesia(rows)
    sebelum = ([], [])
    for a in A:
        a["hadits_ar"], a["catatan_ar"] = pisah_catatan(a["arab"])
        a["atribusi"] = atribusi_arab(a["hadits_ar"])
        a["kitab_atr"] = kitab_atribusi(a["atribusi"])
        nama = nama_sahabat_ar(a["arab"])
        if nama == "<ganti>":
            a["kerangka"], a["sahabat_kata"] = sebelum
        else:
            a["kerangka"] = kerangka_ar(nama)
            a["sahabat_kata"] = [w for w in norm_ar(nama).split()
                                 if w not in _ABAI_AR and w not in ("عبد", "الله", "رسول") and len(w) >= 3][:4]
        sebelum = (a["kerangka"], a["sahabat_kata"])
    sebelum = ""
    for i in I:
        i["kitab_atr"], i["atribusi"] = atribusi_indonesia(i["teks"])
        nama = nama_sahabat_id(i["teks"])
        i["kerangka"] = sebelum if nama == "<ganti>" else kerangka_id(nama)
        sebelum = i["kerangka"]
    print(f"Arab {len(A)} hadits, terjemah {len(I)} entri ({time.time() - t0:.0f}s)", file=sys.stderr)

    pasang = jajarkan(A, I)
    status = collections.Counter()
    for ia, ii in pasang:
        s, nama, atr = skor_pasangan(A[ia], I[ii])
        a = A[ia]
        if nama >= 0.6 and atr >= 0:
            a["terjemah"], a["no_terjemah"], a["skor_pasangan"], a["status_terjemah"] = I[ii]["teks"], I[ii]["no_id"], round(s, 2), "pasti"
            status["pasti"] += 1
        else:
            a["kandidat"] = (I[ii]["no_id"], round(nama, 2), atr)
            status["ragu (tidak dipasang)"] += 1
    print(f"penjajaran: {dict(status)} ({time.time() - t0:.0f}s)", file=sys.stderr)

    # takhrij
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    riw = src.execute("SELECT id, arab FROM riwayat WHERE tingkat IN ('A','B')").fetchall()
    teks, df = {}, collections.Counter()
    for rid, ar in riw:
        teks[rid] = norm_ar(ar)
        df.update(grams(teks[rid]))
    N = len(teks)
    post = collections.defaultdict(list)
    for rid, nrm in teks.items():
        for g in grams(nrm):
            if df[g] <= 300:
                post[g].append(rid)
    for a in A:
        m = grams(norm_ar(matan_riyadh(teks_utama(a["hadits_ar"]), a["atribusi"])))
        a["sumber"] = []
        if len(m) < 4:
            continue
        langka = sorted((g for g in m if 0 < df[g] <= 300), key=lambda g: df[g])[:16]
        cand = collections.Counter()
        for g in langka:
            for rid in post[g]:
                cand[rid] += 1
        bobot = {g: math.log(N / (1 + df[g])) if df[g] else math.log(N) for g in m}
        total = sum(bobot.values())
        hasil = []
        for rid, _ in cand.most_common(200):
            c = sum(bobot[g] for g in m & grams(teks[rid])) / total
            if c >= 0.6:
                hasil.append((round(c, 3), rid))
        # Urutan: kitab yang disebut an-Nawawi & sahabat yang sama didahulukan, baru skor kemiripan matan.
        def kunci(x):
            c, rid = x
            kid = rid.split(":")[0]
            t = teks[rid]
            sahabat = any(re.search(r"(?<![\u0621-\u064A])" + w + r"(?![\u0621-\u064A])", t) for w in a["sahabat_kata"])
            return (kid not in a["kitab_atr"], not sahabat, -c, rid)
        a["sumber"] = [(c, rid, kid_ok, sh_ok) for (c, rid) in sorted(hasil, key=kunci)[:40]
                       for kid_ok, sh_ok in [(rid.split(":")[0] in a["kitab_atr"],
                                              not kunci((c, rid))[1])]]
    print(f"takhrij selesai ({time.time() - t0:.0f}s)", file=sys.stderr)

    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE riyadh_bab (no INT PRIMARY KEY, nama_ar TEXT, nama_id TEXT, kitab_ar TEXT);
    CREATE TABLE riyadh (urut INT PRIMARY KEY, no INT, no_tertulis INT, koreksi TEXT, bab_no INT, arab TEXT, catatan_ar TEXT,
      atribusi_ar TEXT, kitab_atribusi TEXT, terjemah TEXT, no_terjemah INT, skor_pasangan REAL, status_terjemah TEXT,
      kandidat TEXT);
    CREATE TABLE riyadh_sumber (urut INT, riwayat_id TEXT, skor REAL, kitab_disebut INT, sahabat_sama INT, peringkat INT);
    CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
    """)
    for no, b in sorted(bab_ar.items()):
        db.execute("INSERT INTO riyadh_bab VALUES (?,?,?,?)", (no, b["nama_ar"], bab_id.get(no), b["kitab_ar"]))
    for u, a in enumerate(A, 1):
        db.execute("INSERT INTO riyadh VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (u, a.get("no"), a["tertulis"], a.get("koreksi"), a["bab"], a["hadits_ar"], a["catatan_ar"], a["atribusi"],
                    json.dumps(sorted(a["kitab_atr"])), a.get("terjemah"), a.get("no_terjemah"), a.get("skor_pasangan"),
                    a.get("status_terjemah", "tidak"), json.dumps(a.get("kandidat"))))
        db.executemany("INSERT INTO riyadh_sumber VALUES (?,?,?,?,?,?)",
                       [(u, rid, c, int(k), int(sh), p) for p, (c, rid, k, sh) in enumerate(a["sumber"], 1)])

    # uji silang atribusi an-Nawawi vs pencocokan
    dicek = cocok = 0
    for a in A:
        sebut = a["kitab_atr"]
        kit = {x[1].split(":")[0] for x in a["sumber"]}
        if sebut and kit:
            dicek += 1
            cocok += bool(sebut & kit)
    info = {"hadits_arab": len(A), "entri_terjemah": len(I), "terjemah_pasti": status["pasti"],
            "punya_sumber": sum(1 for a in A if a["sumber"]), "uji_silang_dicek": dicek, "uji_silang_cocok": cocok,
            "nomor_dikoreksi": sum(1 for a in A if a.get("koreksi") and a.get("no")),
            "nomor_tak_pasti": sum(1 for a in A if not a.get("no"))}
    db.executemany("INSERT INTO info VALUES (?,?)", [(k, str(v)) for k, v in info.items()])
    db.commit()
    print(json.dumps(info, ensure_ascii=False), file=sys.stderr)
    print(f"uji silang atribusi an-Nawawi: {cocok}/{dicek} = {cocok / max(1, dicek):.1%}", file=sys.stderr)


if __name__ == "__main__":
    main()
