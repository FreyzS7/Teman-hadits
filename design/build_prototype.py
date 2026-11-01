#!/usr/bin/env python3
"""Isi prototipe desain dengan data ASLI dari build/teman-hadits.sqlite.

Tidak ada teks hadits yang diketik tangan: semua kutipan, nomor, dan penilaian diambil dari
database, lalu disisipkan ke design/prototipe.src.html -> design/prototipe.html.

Jalankan (setelah pipeline/build_db.py):  python3 design/build_prototype.py
"""
import base64
import collections
import html
import json
import math
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pipeline"))
from common import DB_PATH, KITAB, norm_ar, norm_id, stem_ar  # noqa: E402

db = sqlite3.connect(DB_PATH)
q = lambda s, *a: db.execute(s, a).fetchall()
NAMA = {k[0]: k[1] for k in KITAB}
URUT = {k[0]: i for i, k in enumerate(KITAB)}
TERBIT = q("SELECT count(*) FROM riwayat WHERE tingkat IN ('A','B')")[0][0]

# --- penyeragaman tampilan nama penilai & label derajat (label asli tetap ditampilkan) -------------
PENILAI = {"Al-Albani": "al-Albani", "Shuaib Al Arnaut": "Syu'aib al-Arna'uth", "Zubair Ali Zai": "Zubair 'Ali Za'i",
           "Muhammad Muhyi Al-Din Abdul Hamid": "Muhyiddin 'Abdul Hamid", "Ahmad Muhammad Shakir": "Ahmad Syakir",
           "Bashar Awad Maarouf": "Basyar 'Awwad Ma'ruf", "Abu Ghuddah": "Abu Ghuddah", "Salim al-Hilali": "Salim al-Hilali",
           "Muhammad Fouad Abd al-Baqi": "Fu'ad 'Abdul Baqi"}


def penilaian(rid):
    return [{"penilai": PENILAI.get(a, a), "hukum": b, "kategori": c}
            for a, b, c in q("SELECT penilai, hukum, kategori FROM penilaian WHERE riwayat_id=? ORDER BY penilai", rid)]


def nomor_tampil(kid, no_standar, no_arab, no_lidwa):
    if kid == "muslim" and no_arab:
        # Muslim lazim dikutip dengan penomoran Fu'ad 'Abdul Baqi; .01/.02 -> a/b
        x = str(no_arab)
        if "." in x:
            base, dec = x.split(".")
            return f"{base}{chr(96 + int(dec))}" if dec.isdigit() and 0 < int(dec) < 27 else x
        return x
    return no_standar or f"L{no_lidwa}"


def ringkas(rid):
    kid = rid.split(":")[0]
    r = q("SELECT no_standar, no_arab, no_lidwa, tingkat, kecocokan FROM riwayat WHERE id=?", rid)[0]
    return {"id": rid, "kitab": kid, "kitabNama": NAMA[kid], "no": nomor_tampil(kid, r[0], r[1], r[2]),
            "noLidwa": r[2], "tingkat": r[3], "kecocokan": r[4], "penilaian": penilaian(rid)}


# --- rak kitab -------------------------------------------------------------------------------------
rak = []
for kid, nama, nama_ar, penyusun, wafat, nl, ns in q(
        "SELECT id, nama, nama_arab, penyusun, wafat_h, jumlah_lidwa, jumlah_standar FROM kitab"):
    t = dict(q("SELECT tingkat, count(*) FROM riwayat WHERE kitab_id=? GROUP BY tingkat", kid))
    dinilai = q("SELECT count(DISTINCT riwayat_id) FROM penilaian WHERE riwayat_id LIKE ?", kid + ":%")[0][0]
    pen = [PENILAI.get(r[0], r[0]) for r in q("SELECT DISTINCT penilai FROM penilaian WHERE riwayat_id LIKE ?", kid + ":%")]
    rak.append({"id": kid, "nama": nama, "arab": nama_ar, "penyusun": penyusun, "wafat": wafat,
                "A": t.get("A", 0), "B": t.get("B", 0), "K": t.get("K", 0), "dinilai": dinilai, "penilai": pen})
rak.append({"id": "riyadh", "nama": "Riyadhus Shalihin", "arab": "رياض الصالحين", "penyusun": "Yahya bin Syaraf an-Nawawi",
            "wafat": 676, "A": 0, "B": 0, "K": 1896, "dinilai": 0, "penilai": [], "karantina": True,
            "alasan": "Data sumber tersimpan per bab dan per halaman, belum per hadits. Sedang dipecah ulang."})

tingkat_total = dict(q("SELECT tingkat, count(*) FROM riwayat GROUP BY tingkat"))


# --- hasil cari "babi" ---------------------------------------------------------------------------
def potong_id(t, kata, lebar=150):
    n = t.lower().find(kata)
    if n < 0:
        return html.escape(t[:lebar * 2]) + "…"
    a, b = max(0, n - lebar), min(len(t), n + len(kata) + lebar)
    s = ("…" if a else "") + html.escape(t[a:n]) + "<mark>" + html.escape(t[n:n + len(kata)]) + "</mark>" + \
        html.escape(t[n + len(kata):b]) + ("…" if b < len(t) else "")
    return s


def potong_ar(t, akar, jendela=7):
    w = t.split()
    for i, x in enumerate(w):
        if any(a in norm_ar(x) for a in akar):
            a, b = max(0, i - jendela), min(len(w), i + jendela + 1)
            return ("… " if a else "") + " ".join(html.escape(y) for y in w[a:i]) + " <mark>" + html.escape(x) + \
                "</mark> " + " ".join(html.escape(y) for y in w[i + 1:b]) + (" …" if b < len(w) else "")
    return html.escape(" ".join(w[:14])) + " …"


hits = [r[0] for r in q("SELECT riwayat_id FROM cari WHERE cari MATCH 'terjemah_polos:babi OR arab_akar:خنزير'")]
per_kitab = collections.Counter(h.split(":")[0] for h in hits)


def relevansi(h):
    # Kueri berbentuk pertanyaan hukum ("makan babi ... haram?"): dahulukan riwayat yang juga
    # memuat kata "haram" dan "makan" (termasuk bentuk mengharamkan/dimakan).
    t = (q("SELECT terjemah FROM riwayat WHERE id=?", h)[0][0] or "").lower()
    return ("haram" in t) + ("makan" in t)


def arab_cocok(h):
    # Hit yang kata Arabnya sendiri memuat خنزير lebih pasti daripada hit dari terjemahan gabungan.
    a = norm_ar(q("SELECT arab FROM riwayat WHERE id=?", h)[0][0])
    return "خنزير" in a or "خنازير" in a


ranked = sorted(hits, key=lambda h: (not arab_cocok(h), -relevansi(h),
                                     q("SELECT tingkat FROM riwayat WHERE id=?", h)[0][0] != "A", URUT[h.split(':')[0]], h))
cari = []
seen_kitab = collections.Counter()
for h in ranked:
    kid = h.split(":")[0]
    if seen_kitab[kid] >= 2:
        continue
    seen_kitab[kid] += 1
    arab, terj = q("SELECT arab, terjemah FROM riwayat WHERE id=?", h)[0]
    d = ringkas(h)
    d["cuplikanId"] = potong_id(terj or "", "babi") if terj else None
    d["cuplikanAr"] = potong_ar(arab, ("خنزير", "خنازير"))
    d["relevansi"] = relevansi(h)
    cari.append(d)
    if len(cari) >= 8:
        break

# --- detail Bukhari no. 1: sanad, matan, rantai, jalur lain ---------------------------------------
HRK = "[ً-ْٰـ]*"


def pola(kata):
    return "".join(re.escape(c) + HRK for c in kata)


SIGHAH = [("حدثنا", "haddatsanā", "menceritakan kepada kami",
           "Lafaz penyampaian langsung: guru membacakan, murid mendengar."),
          ("حدثني", "haddatsanī", "menceritakan kepadaku", "Seperti haddatsana, tetapi murid mendengar sendirian."),
          ("أخبرنا", "akhbaranā", "mengabarkan kepada kami",
           "Penyampaian langsung; banyak ulama memakainya untuk murid yang membaca di hadapan guru."),
          ("أخبرني", "akhbaranī", "mengabarkan kepadaku",
           "Penyampaian langsung; banyak ulama memakainya untuk murid yang membaca di hadapan guru."),
          ("سمعت", "sami'tu", "aku mendengar", "Pernyataan tegas mendengar langsung."),
          ("سمع", "sami'a", "ia mendengar", "Pernyataan tegas mendengar langsung."),
          ("عن", "'an", "dari", "Tidak tegas apakah mendengar langsung; ulama memeriksanya untuk kemungkinan tadlis.")]
# Batas kata Arab harus melewati harakat: "عَنْهُ" (dalam رضي الله عنه) bukan lafaz "عن".
_HUR = "[ء-ي]"
RE_SIGHAH = re.compile("|".join(
    f"(?<![ء-يً-ْ])(?:[وف]{HRK})?{pola(k)}(?!{HRK}{_HUR})" for k, *_ in SIGHAH))


def kunci_sighah(s):
    b = norm_ar(s)
    if b[:1] in ("و", "ف") and len(b) > 2:
        b = b[1:]
    for k, *_ in SIGHAH:
        if norm_ar(k) == b:
            return k
    return None


arab1, terj1, rantai1, bab1, nol1 = q("SELECT arab, terjemah, rantai_json, bab_nama, no_lidwa FROM riwayat WHERE id='bukhari:1'")[0]
sanad_txt, matn_txt = arab1.split('"', 1)
matn_txt = matn_txt.strip().rstrip('"').strip()


def rubrik(t):
    out, last = [], 0
    for m in RE_SIGHAH.finditer(t):
        out.append(html.escape(t[last:m.start()]))
        k = kunci_sighah(m.group())
        cls = "sg sg-an" if k == "عن" else "sg"
        out.append(f'<span class="{cls}" data-k="{html.escape(k)}">{html.escape(m.group())}</span>')
        last = m.end()
    out.append(html.escape(t[last:]))
    return "".join(out)


# Rantai: setiap lafaz periwayatan diikuti nama perawi sampai tanda koma / "رضي".
segs = []
ms = list(RE_SIGHAH.finditer(sanad_txt + " " + matn_txt[:0]))
full = sanad_txt
for i, m in enumerate(ms):
    end = ms[i + 1].start() if i + 1 < len(ms) else len(full)
    nama = re.split(r"،|,|:| " + pola("رضي"), full[m.end():end])[0].strip()
    segs.append({"sighah": kunci_sighah(m.group()), "lafaz": m.group(), "namaAr": nama})
nama_id = json.loads(rantai1)
# Urutan: perawi pertama (guru al-Bukhari) ... sahabat, lalu Nabi ﷺ.
rantai = [{"namaAr": "البخاري", "namaId": "al-Bukhari", "peran": "penyusun kitab"}]
for i, s in enumerate(segs):
    is_nabi = "رسول" in norm_ar(s["namaAr"])
    rantai.append({"namaAr": s["namaAr"] if not is_nabi else "رسول الله ﷺ",
                   "namaId": (nama_id[i] if i < len(nama_id) else "") if not is_nabi else "Rasulullah ﷺ",
                   "sighah": s["sighah"], "lafaz": s["lafaz"],
                   "peran": "Nabi" if is_nabi else ("sahabat" if i == len(segs) - 2 else "perawi")})


def grams(t, n=2):
    w = [stem_ar(x) for x in t.split()]
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


G = grams(norm_ar(matn_txt))
jalur = []
for rid, ar in q("SELECT id, arab FROM riwayat WHERE tingkat IN ('A','B')"):
    c = len(G & grams(norm_ar(ar))) / len(G)
    if c >= 0.4 and rid != "bukhari:1":
        d = ringkas(rid)
        d["kemiripan"] = round(c, 2)
        jalur.append(d)
jalur.sort(key=lambda d: (URUT[d["kitab"]], -d["kemiripan"]))

detail = {"id": "bukhari:1", "kitabNama": NAMA["bukhari"], "no": "1", "noLidwa": nol1, "babSumber": bab1,
          "sanadHtml": rubrik(sanad_txt.strip()), "matnHtml": html.escape(matn_txt),
          "terjemah": terj1, "rantai": rantai,
          "sighah": [{"k": k, "latin": a, "arti": b, "ket": c} for k, a, b, c in SIGHAH], "jalur": jalur}

# --- cek teks tempel -------------------------------------------------------------------------------
STOP = set(("yang dan itu ini dengan akan ia dia ke di dari pada untuk apa sesuai seseorang sesungguhnya kepada "
            "kami telah adalah bahwa atau juga tidak orang dalam saya beliau bersabda berkata hr bukhari muslim "
            "sampai").split())


def st(w):
    for s in ("nya", "kan", "lah", "an"):
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[:-len(s)]
    return w


docs = [(rid, set(st(w) for w in norm_id(t).split() if w not in STOP))
        for rid, t in q("SELECT id, terjemah FROM riwayat WHERE tingkat IN ('A','B') AND terjemah IS NOT NULL")]
df = collections.Counter()
for _, s in docs:
    df.update(s)
N = len(docs)


def cek(teks, klaim):
    toks = [st(w) for w in norm_id(re.sub(r"\(.*?\)", "", teks)).split() if w not in STOP]
    Q = list(dict.fromkeys(toks))
    absen = [w for w in Q if df[w] == 0]
    langkah = [{"kata": w, "muncul": df[w]} for w in Q]
    if absen:
        return {"teks": teks, "klaim": klaim, "langkah": langkah, "ditemukan": False, "absen": absen,
                "dicari": N}
    idf = {w: math.log(N / (1 + df[w])) for w in Q}
    tot = sum(idf.values())
    best = max(docs, key=lambda d: sum(idf[w] for w in d[1] & set(Q)))
    skor = sum(idf[w] for w in best[1] & set(Q)) / tot
    # perluas ke satu "keluarga" riwayat lewat kemiripan matan Arab dari hasil terbaik
    return {"teks": teks, "klaim": klaim, "langkah": langkah, "ditemukan": skor >= 0.75, "skor": round(skor, 2),
            "terbaik": best[0], "dicari": N}


cek1 = cek("Sesungguhnya amalan itu tergantung niatnya dan seseorang akan mendapatkan sesuai dengan apa yang ia "
           "niatkan (HR. Bukhari dan Muslim)", ["bukhari", "muslim"])
fam = [ringkas("bukhari:1")] + jalur
cek1["keluarga"] = fam
cek1["klaimHasil"] = [{"kitab": k, "nama": NAMA[k], "ada": any(f["kitab"] == k for f in fam),
                       "nomor": [f["no"] for f in fam if f["kitab"] == k]} for k in cek1["klaim"]]
cek2 = cek("Tuntutlah ilmu walau sampai ke negeri Cina", [])
cek2["arabDicek"] = "الصين"
cek2["arabMuncul"] = q("SELECT count(*) FROM cari WHERE cari MATCH 'arab_akar:صين'")[0][0]

KATA_BOLEH = ("halal", "boleh", "membolehkan", "dibolehkan", "diperbolehkan", "dihalalkan", "menghalalkan")
boleh = []
for h in hits:
    t = (q("SELECT terjemah FROM riwayat WHERE id=?", h)[0][0] or "").lower()
    found = [k for k in KATA_BOLEH if re.search(r"\b" + k + r"\b", t)]
    if found:
        boleh.append({"id": h, "kitabNama": NAMA[h.split(":")[0]], "no": ringkas(h)["no"], "kata": found,
                      "penilaian": penilaian(h), "tingkat": ringkas(h)["tingkat"],
                      "cuplikan": potong_id(q("SELECT terjemah FROM riwayat WHERE id=?", h)[0][0], found[0], 110)})

DATA = {"terbit": TERBIT, "tingkat": tingkat_total, "rak": rak,
        "cari": {"kueri": "apakah makan babi itu hukumnya haram?", "kata": ["babi", "خنزير"], "total": len(hits),
                 "perKitab": dict(per_kitab), "hasil": cari, "kataBoleh": KATA_BOLEH, "boleh": boleh},
        "detail": detail, "cek": [cek1, cek2]}

src = open(os.path.join(HERE, "prototipe.src.html"), encoding="utf8").read()
emblem = base64.b64encode(open(os.path.join(HERE, "assets", "emblem.webp"), "rb").read()).decode()
logo = base64.b64encode(open(os.path.join(HERE, "assets", "logo.webp"), "rb").read()).decode()
out = (src.replace("__DATA__", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/"))
       .replace("__EMBLEM__", "data:image/webp;base64," + emblem)
       .replace("__LOGO__", "data:image/webp;base64," + logo))
open(os.path.join(HERE, "prototipe.html"), "w", encoding="utf8").write(out)
print(f"design/prototipe.html ({len(out) // 1024} KB); jalur lain={len(jalur)}, hasil babi={len(hits)}, "
      f"rantai={[r['namaId'] for r in rantai]}", file=sys.stderr)
