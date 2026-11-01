#!/usr/bin/env python3
"""Katalog "hadits" populer & palsu dari kitab-kitab klasik, ditambah daftar ucapan populer berbahasa Indonesia.

Sumber (OpenITI, commit terkunci di sources.json):
  - al-Maqashid al-Hasanah (as-Sakhawi, w. 902 H): "hadits" yang masyhur di lisan orang, dengan penilaiannya
  - Kasyf al-Khafa' wa Muzil al-Ilbas (al-'Ajluni, w. 1162 H): perluasan al-Maqashid
  - al-Asrar al-Marfu'ah (Mulla 'Ali al-Qari, w. 1014 H): hadits-hadits palsu
  - al-Maudhu'at (Ibnul Jauzi, w. 597 H): hadits yang ia nilai palsu, per bab

Prinsip: situs TIDAK membuat vonis sendiri. Yang ditampilkan adalah teks ulama apa adanya, ditambah daftar
kata kunci penilaian yang muncul di teks itu (mis. "باطل" = batil) berikut kalimat tempatnya muncul.

Daftar ucapan populer berbahasa Indonesia (pipeline/hadits_populer.json) disusun Teman Hadits dan belum
ditinjau; ia hanya menghubungkan kalimat Indonesia ke lafaz Arabnya. Hubungan lafaz Arab -> entri kitab
dan -> riwayat di kitab-kitab kita dihitung otomatis (kemiripan 2-gram).

Keluaran: build/katalog.sqlite.   Jalankan:  python3 pipeline/katalog_palsu.py
"""
import collections
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, ROOT, SRC, norm_ar, stem_ar

OUT = os.path.join(BUILD, "katalog.sqlite")
KITAB = [
    # id, nama, nama Arab, penulis, wafat, berkas, cara urai
    ("maqashid", "al-Maqashid al-Hasanah", "المقاصد الحسنة في بيان كثير من الأحاديث المشتهرة على الألسنة", "as-Sakhawi", 902,
     "openiti-0925AH/0902Sakhawi.MaqasidHasana.Shamela0023177-ara1", "nomor"),
    ("kasyf", "Kasyf al-Khafa'", "كشف الخفاء ومزيل الإلباس عما اشتهر من الأحاديث على ألسنة الناس", "al-'Ajluni", 1162,
     "openiti-1175AH/1162IbnMuammadAbuFidaCajluni.KashfKhafa.Shamela0000856-ara1", "nomor"),
    ("asrar", "al-Asrar al-Marfu'ah", "الأسرار المرفوعة في الأخبار الموضوعة", "Mulla 'Ali al-Qari", 1014,
     "openiti-1025AH/1014MullaCaliQari.AsrarMarfuca.Shamela0006056-ara1", "nomor"),
    ("maudhuat", "al-Maudhu'at", "الموضوعات", "Ibnul Jauzi", 597,
     "openiti-0600AH/0597IbnJawzi.Mawducat.Shamela0000882-ara1", "bab"),
]

# Kata kunci penilaian -> (padanan Indonesia, kelas warna). Urutan = urutan tampil.
# Kelas: palsu (merah) = pernyataan tegas palsu/tak berasal; lemah (kuning); terima (hijau); lain (netral).
# "tidak saya temukan" / "tidak saya kenal" diterjemahkan apa adanya (orang pertama): pembicaranya bisa penulis kitab
# ATAU ulama yang ia kutip; kalimat aslinya selalu ditampilkan.
KATA_KUNCI = [
    ("موضوع", "maudhu' (palsu)", "palsu"), ("مكذوب", "didustakan atas nama Nabi", "palsu"), ("كذب", "dusta", "palsu"),
    ("باطل", "batil", "palsu"), ("لا اصل له", "tidak ada asalnya", "palsu"), ("ليس له اصل", "tidak ada asalnya", "palsu"),
    ("ليس بحديث", "bukan hadits", "palsu"),
    ("لم اقف عليه", "“tidak saya temukan”", "lemah"), ("لا اعرفه", "“tidak saya kenal”", "lemah"),
    ("منكر الحديث", "munkar al-hadits (kritik terhadap perawi)", "lemah"), ("منكر", "munkar", "lemah"), ("ضعيف جدا", "sangat lemah", "lemah"), ("ضعيف", "dha'if (lemah)", "lemah"),
    ("لا يصح", "tidak sahih", "lemah"), ("لا يثبت", "tidak tsabit (tidak sahih)", "lemah"),
    ("ليس بثابت", "tidak tsabit (tidak sahih)", "lemah"),
    ("من كلام", "disebut perkataan orang, bukan sabda Nabi", "lain"),
    ("معناه صحيح", "maknanya benar (bukan penilaian sanad)", "lain"),
    ("صحيح المعني", "maknanya benar (bukan penilaian sanad)", "lain"),
    ("حسن", "hasan", "terima"), ("صحيح", "shahih", "terima"),
]
_HUR = "ء-ي"
# Kata boleh diawali huruf sambung و/ف ("ومعناه صحيح", "فهو باطل"), tapi tidak boleh menempel pada huruf lain.
_POLA_KK = [(norm_ar(k), g, kl, re.compile(f"(?<![{_HUR}])[وف]?{re.escape(norm_ar(k))}(?![{_HUR}])")) for k, g, kl in KATA_KUNCI]
_SAMPAH = re.compile(r"ms\d+|PageV\d+P\d+|\[ص:\s*\d+\]")
# "shahih"/"hasan" hanya dihitung dalam susunan penilaian: "إسناده صحيح", "حديث حسن", "بسند صحيح", "حسن صحيح", "وهو حسن".
_DEPAN_NILAI = {"حديث", "اسناده", "اسنادها", "اسناد", "سنده", "سندها", "سند", "هو", "هذا", "طريق", "حسن", "صحيح", "رجاله"}
_BELAKANG_NILAI = {"صحيح", "حسن", "غريب", "لغيره", "لذاته", "الاسناد", "السند", "علي"}
_BUKAN_NILAI = {"بن", "ابن", "مسلم", "البخاري"}            # "صحيح مسلم", "صحيح ابن حبان", "حسن بن علي"
_lepas = lambda w: w[1:] if len(w) > 3 and w[0] in "وفب" else w


def _penilaian_positif(n, m):
    """True bila "صحيح"/"حسن" pada posisi m adalah penilaian, bukan bagian dari matan/nama/judul kitab."""
    lima = n[:m.start()].split()[-5:]
    depan = [_lepas(w) for w in lima[-1:]]
    belakang = n[m.end():].split()[:1]
    if any(_lepas(w) in ("ليس", "لا", "لم") for w in lima):
        return False                                       # "ليس في فضل الأضحية حديث صحيح", "لا يصح فيه حديث صحيح"
    if depan and depan[0] in ("معناه", "معناها", "معني", "في"):
        return False                                       # "ومعناه صحيح", "في صحيح مسلم"
    if belakang and (belakang[0] in _BUKAN_NILAI or (belakang[0].startswith("ال") and belakang[0] not in _BELAKANG_NILAI)):
        return False                                       # "حسن العهد", "حسن الخلق", "صحيح البخاري"
    return bool((depan and depan[0] in _DEPAN_NILAI) or (belakang and belakang[0] in _BELAKANG_NILAI))


def kata_kunci(teks):
    """[(kunci, padanan, kalimat, kelas)] — kalimat = potongan teks ulama tempat kata itu pertama muncul."""
    n = norm_ar(teks)
    out, dipakai = [], set()
    for k, g, kl, p in _POLA_KK:
        if g in dipakai:
            continue
        m = None
        for x in p.finditer(n):
            sebelum, sesudah = n[:x.start()].split()[-1:], n[x.end():].split()[:1]
            if k == "كذب" and (sebelum in (["من"], ["ولا"], ["لا"]) or sesudah in (["علي"], ["عليه"], ["من"])):
                continue                                   # "من كذب علي متعمدا" (matan), "وكذب من قال" (bantahan pendapat)
            if k == "منكر" and sesudah == ["الحديث"]:
                continue                                   # sudah tercakup "منكر الحديث" (kritik perawi)
            if k == "ضعيف" and sesudah == ["جدا"]:
                continue                                   # sudah tercakup "ضعيف جدا"
            if k == "من كلام" and sesudah and _lepas(sesudah[0]) in ("النبي", "رسول", "الرسول", "نبي", "النبوه"):
                continue                                   # "من كلام النبي" justru sebaliknya
            if k in ("صحيح", "حسن") and not _penilaian_positif(n, x):
                continue
            m = x
            break
        if not m:
            continue
        a, b = max(0, m.start() - 60), min(len(n), m.end() + 60)
        out.append((k, g, ("… " if a else "") + n[a:b] + (" …" if b < len(n) else ""), kl))
        dipakai.add(g)
    return out


def judul_entri(teks):
    t = teks.strip()
    m = re.match(r"^\((.{3,200}?)\)", t)                 # Kasyf: "(اطلبوا العلم ولو بالصين ...)"
    if m:
        return m.group(1)
    m = re.match(r"^حديث\s*:\s*(.{3,200}?)(?:،|\.|$)", t)  # Maqashid: "حديث: اطلبوا العلم ..."
    if m:
        return m.group(1)
    m = re.match(r"^حديث\s+(.{3,200}?)\s*//", t)            # al-Asrar: "حديث العلماء ورثة الأنبياء // ..."
    if m:
        return m.group(1)
    return " ".join(t.split()[:16])


def urai_nomor(path):
    entri, cur = [], None
    for baris in open(path, encoding="utf8"):
        baris = baris.rstrip("\n")
        if baris.startswith("#META#") or baris.startswith("######"):
            continue
        m = re.match(r"^### \|+ ([0-9]+) ?-\s*$", baris)
        if m:
            cur = {"no": int(m.group(1)), "teks": []}
            entri.append(cur)
            continue
        if baris.startswith("### "):
            if cur is not None and "[ص:" not in baris:
                cur = None                                 # judul huruf/bab: entri sebelumnya selesai
            continue
        if cur is not None and (baris.startswith("# ") or baris.startswith("~~")):
            isi = _SAMPAH.sub(" ", baris.lstrip("#~ ")).strip()
            if isi:
                cur["teks"].append(isi)
    return [{"no": e["no"], "teks": " ".join(e["teks"])} for e in entri if e["teks"]]


def urai_bab(path):
    """al-Maudhu'at: setiap "باب ..." = satu entri (judul = nama bab sebelum sanad dimulai)."""
    entri, cur, kitab, no = [], None, None, 0
    for baris in open(path, encoding="utf8"):
        baris = baris.rstrip("\n")
        if baris.startswith("#META#") or baris.startswith("######"):
            continue
        if baris.startswith("### "):
            t = _SAMPAH.sub(" ", baris[4:].lstrip("|$ ")).strip()
            if t.startswith("كتاب"):
                kitab = t
            continue
        if baris.startswith("# ") or baris.startswith("~~"):
            isi = _SAMPAH.sub(" ", baris.lstrip("#~ ")).strip()
            if not isi:
                continue
            if baris.startswith("# باب"):
                no += 1
                cur = {"no": no, "kitab": kitab, "teks": [isi]}
                entri.append(cur)
            elif cur is not None:
                cur["teks"].append(isi)
    out = []
    for e in entri:
        teks = " ".join(e["teks"])
        j = re.split(r"\s(?:أنبأنا|أخبرنا|حدثنا|روى|رواه|قال)\s", teks, maxsplit=1)[0]
        out.append({"no": e["no"], "teks": teks, "judul": re.sub(r"^باب\s*", "", j)[:200]})
    return out


def grams(t):
    w = [stem_ar(x) for x in norm_ar(t).split()]
    return {w[i] + " " + w[i + 1] for i in range(len(w) - 1)} or set(w)


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE katalog_kitab (id TEXT PRIMARY KEY, nama TEXT, nama_ar TEXT, penulis TEXT, wafat INT, edisi TEXT);
    CREATE TABLE katalog (id TEXT PRIMARY KEY, kitab_id TEXT, no INT, judul_ar TEXT, teks_ar TEXT, kata_kunci TEXT);
    CREATE TABLE populer (id TEXT PRIMARY KEY, teks_id TEXT, varian TEXT, arab TEXT, catatan TEXT);
    CREATE TABLE populer_katalog (populer_id TEXT, katalog_id TEXT, skor REAL);
    CREATE TABLE populer_riwayat (populer_id TEXT, riwayat_id TEXT, skor REAL);
    CREATE TABLE populer_sebut (populer_id TEXT, katalog_id TEXT, kutipan TEXT);
    CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
    """)
    semua = []
    for kid, nama, nama_ar, penulis, wafat, rel, cara in KITAB:
        path = os.path.join(SRC, rel)
        head = open(path, encoding="utf8").read(8000)
        edisi = " — ".join(x for x in [re.search(r"EdEDITOR\s*::\s*(.*)", head).group(1).strip() if re.search(r"EdEDITOR\s*::\s*(.*)", head) else "",
                                       re.search(r"EdPUBLISHER\s*::\s*(.*)", head).group(1).strip() if re.search(r"EdPUBLISHER\s*::\s*(.*)", head) else ""]
                           if x and x != "NODATA")
        db.execute("INSERT INTO katalog_kitab VALUES (?,?,?,?,?,?)", (kid, nama, nama_ar, penulis, wafat, edisi))
        entri = urai_nomor(path) if cara == "nomor" else urai_bab(path)
        dipakai_id = set()
        for e in entri:
            judul = e.get("judul") or judul_entri(e["teks"])
            kk = kata_kunci(e["teks"])
            eid = f"{kid}:{e['no']}"
            k = 2
            while eid in dipakai_id:            # penomoran bisa berulang (mis. bagian pengantar al-Asrar)
                eid, k = f"{kid}:{e['no']}-{k}", k + 1
            dipakai_id.add(eid)
            db.execute("INSERT INTO katalog VALUES (?,?,?,?,?,?)",
                       (eid, kid, e["no"], judul, e["teks"], json.dumps(kk, ensure_ascii=False)))
            kepala = re.sub(r"^حديث\s*:?\s*", "", e["teks"])
            semua.append((eid, grams(judul) | grams(" ".join(kepala.split()[:10])), norm_ar(e["teks"])))
        print(f"{kid:9s} {len(entri):5d} entri", file=sys.stderr)

    # --- ucapan populer berbahasa Indonesia -> entri kitab & riwayat --------------------------------
    pop = json.load(open(os.path.join(ROOT, "pipeline", "hadits_populer.json"), encoding="utf8"))
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    riwayat = [(rid, grams(ar)) for rid, ar in src.execute("SELECT id, arab FROM riwayat WHERE tingkat IN ('A','B')")]
    stat = collections.Counter()
    for p in pop["ucapan"]:
        db.execute("INSERT INTO populer VALUES (?,?,?,?,?)", (p["id"], p["teks"], json.dumps(p.get("varian", []), ensure_ascii=False),
                                                              p["arab"], p.get("catatan")))
        g = grams(p["arab"])
        # entri kitab: lafaz harus ada di JUDUL entri. Ucapan yang hanya DISEBUT dalam pembahasan entri lain
        # tidak ditautkan, karena kata kunci penilaian entri itu berlaku untuk ucapan lain.
        lafaz, sebut = norm_ar(p["arab"]), 0
        pola_lafaz = re.compile(f"(?<![{_HUR}]){re.escape(lafaz)}(?![{_HUR}])")
        for eid, gj, teks_n in semua:
            s = len(g & gj) / len(g)
            persis = bool(pola_lafaz.search(teks_n))
            # Tautan judul: judul (+10 kata pertama) memuat >= 75% 2-gram lafaz, ATAU lafaz ada persis di teks entri
            # dan judulnya memuat >= 50% (judul bab al-Maudhu'at sering parafrase: "طلب العلم ولو بالصين").
            if s >= 0.75 or (persis and s >= 0.5):
                db.execute("INSERT INTO populer_katalog VALUES (?,?,?)", (p["id"], eid, round(s, 2)))
                stat["tautan_katalog"] += 1
            elif sebut < 8 and persis:
                # lafaz persis DISEBUT di pembahasan entri lain: ditampilkan terpisah, TANPA kata kunci entri itu
                i = teks_n.find(lafaz)
                a, b = max(0, i - 160), min(len(teks_n), i + len(lafaz) + 160)
                db.execute("INSERT INTO populer_sebut VALUES (?,?,?)", (p["id"], eid, ("… " if a else "") + teks_n[a:b] + (" …" if b < len(teks_n) else "")))
                stat["sebut_di_entri_lain"] += 1
                sebut += 1
        hits = sorted(((len(g & gr) / len(g), rid) for rid, gr in riwayat if len(g & gr) / len(g) >= 0.8), reverse=True)[:20]
        for s, rid in hits:
            db.execute("INSERT INTO populer_riwayat VALUES (?,?,?)", (p["id"], rid, round(s, 2)))
        stat["ada_di_kitab_hadits" if hits else "tidak_ada_di_kitab_hadits"] += 1
    info = {"ucapan_populer": len(pop["ucapan"]), **stat, "ditinjau": str(pop.get("ditinjau", False))}
    db.executemany("INSERT INTO info VALUES (?,?)", [(k, str(v)) for k, v in info.items()])
    db.commit()
    print(json.dumps(info, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
