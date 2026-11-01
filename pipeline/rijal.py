#!/usr/bin/env python3
"""Kitab rijal: Taqrib at-Tahdzib (Ibnu Hajar, w. 852 H) dan Tahdzib al-Kamal (al-Mizzi, w. 742 H).

Taqrib  : satu entri ringkas per perawi: nama, penilaian Ibnu Hajar, tabaqah, tahun wafat, kode kitab (rumuz).
          Edisi Muhammad 'Awwamah (Dar ar-Rasyid); nomornya nomor standar yang dikutip para peneliti.
Tahdzib : biografi lengkap, termasuk daftar guru ("روى عن") dan murid ("روى عنه") beserta kode kitab untuk
          SETIAP hubungan guru-murid. Inilah bukti yang dipakai untuk mengenali siapa perawi di sebuah sanad.
          Edisi Basyar 'Awwad Ma'ruf (ar-Risalah).

Keluaran: build/rijal.sqlite (tabel taqrib, tk, tk_relasi, tk_taqrib).   Jalankan:  python3 -I pipeline/rijal.py
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, SRC, norm_ar

OUT = os.path.join(BUILD, "rijal.sqlite")
F_TAQRIB = os.path.join(SRC, "openiti-0875AH", "0852IbnHajarCasqalani.TaqribTahdhib.JK000121-ara1.completed")
F_TK = os.path.join(SRC, "openiti-0750AH", "0742Mizzi.TahdhibKamal.Shamela0003722-ara1.mARkdown")

# Kode kitab dari muqaddimah Taqrib (baris "فالبخاري في صحيحه خ ...")
RUMUZ = {"خ", "خت", "بخ", "عخ", "ر", "ي", "م", "مق", "د", "مد", "صد", "خد", "قد", "ف", "ل", "كد", "ت", "تم", "س", "عس", "كن",
         "ص", "ق", "فق", "ع", "4", "سي", "ز"}
_RUMUZ_PANJANG = sorted(RUMUZ, key=len, reverse=True)


def pecah_kode(tok):
    """'د' -> ['د'], 'دس' (tanpa spasi) -> ['د','س'], 'مدت' -> ['مد','ت'], '(تمييز)' -> ['تمييز'], '(1)' -> [] (catatan kaki).
    Kembalikan None bila token bukan kode sama sekali."""
    t = tok.strip("()[]")
    if t == "تمييز":
        return ["تمييز"]
    if t.isdigit() and tok.startswith("("):
        return []
    if t == "سى":
        t = "سي"
    out, i = [], 0
    while i < len(t):
        for k in _RUMUZ_PANJANG:
            if t.startswith(k, i):
                out.append(k); i += len(k); break
        else:
            return None
    return out or None
# kode yang menandakan perawi ada di KITAB UTAMA tertentu ("ع" = keenamnya, "4" = empat Sunan)
KODE_KITAB = {"bukhari": {"خ", "ع"}, "muslim": {"م", "ع"}, "abudawud": {"د", "ع", "4"}, "tirmidzi": {"ت", "ع", "4"},
              "nasai": {"س", "ع", "4"}, "ibnumajah": {"ق", "ع", "4"}}

_SAMPAH = re.compile(r"ms\d+|PageV\d+P\d+|\|")
_SPASI = re.compile(r"\s+")

TABAQAH = {"الاولي": 1, "الثانيه": 2, "الثالثه": 3, "الرابعه": 4, "الخامسه": 5, "السادسه": 6, "السابعه": 7,
           "الثامنه": 8, "التاسعه": 9, "العاشره": 10, "الحاديه عشره": 11, "الثانيه عشره": 12}
_RE_TABAQAH = re.compile(r"من (?:(?:رووس|روس|كبار|صغار|اوساط|اواسط|اواخر|اوايل)\s+)?(?:الطبقه\s+)?(الحاديه عشره|الثانيه عشره|الاولي|الثانيه|الثالثه|الرابعه|الخامسه|السادسه|السابعه|الثامنه|التاسعه|العاشره)(?![ء-ي])")

SATUAN = {"واحد": 1, "احدي": 1, "احد": 1, "اثنتين": 2, "اثنين": 2, "ثنتين": 2, "اثنتي": 2, "اثني": 2, "ثلاث": 3, "ثلاثه": 3, "اربع": 4, "اربعه": 4,
          "خمس": 5, "خمسه": 5, "ست": 6, "سته": 6, "سبع": 7, "سبعه": 7, "ثمان": 8, "ثماني": 8, "ثمانيه": 8, "تسع": 9, "تسعه": 9}
PULUHAN = {"عشر": 10, "عشره": 10, "عشرين": 20, "ثلاثين": 30, "اربعين": 40, "خمسين": 50, "ستين": 60, "سبعين": 70,
           "ثمانين": 80, "تسعين": 90}
RATUSAN = {"مايه": 100, "ميه": 100, "مايتين": 200, "ميتين": 200, "ثلاثمايه": 300, "ثلاث مايه": 300}


def bersih(t):
    return _SPASI.sub(" ", _SAMPAH.sub(" ", t)).strip()


SAHABAT = (r"صحابي|صحابيه|له صحبه|لها صحبه|له ولابيه صحبه|ام المومنين|شهد بدرا|شهد بدر|من الصحابه|حافظ الصحابه|"
           r"المكثرين من الصحابه|فقهاء الصحابه|ريحانته|سبط رسول الله|خادم رسول الله|خادم النبي|"
           r"امير المومنين(?! في الحديث)|احد العشره|الخليفه الراشد")
# 12 tingkatan Ibnu Hajar (muqaddimah Taqrib). Dicocokkan dari yang paling khusus ke yang umum.
TINGKAT = [
    (12, r"كذاب|وضاع|يضع الحديث|كذبوه"), (11, r"متهم بالكذب|متهم بالوضع|اتهم"), (10, r"متروك|واهي الحديث|ساقط|واه"),
    (9, r"مجهول(?! الحال)|مجهوله|لا يعرف(?! حاله)|لا تعرف"), (7, r"مستور|مستوره|مجهول الحال|لا يعرف حاله"), (8, r"ضعيف|ضعيفه"),
    (6, r"مقبول|مقبوله|لين الحديث|فيه لين"),
    (5, r"صدوق (?:سيي الحفظ|يهم|له اوهام|يخطي|ربما وهم|ربما اخطا|تغير|اختلط|رمي|يدلس|فيه)|صدوق [^م]{0,20}(?:يهم|يخطي|اوهام|تغير|اختلط|رمي|يدلس)"),
    (2, r"ثقه ثقه|ثقه ثبت|ثقه حافظ|ثقه متقن|اوثق الناس|امام حجه|حافظ حجه|ثقه امام|امير المومنين في الحديث|"
        r"متفق علي جلالته|متفق علي اتقانه|متفق علي توثيقه|راس المتقنين|كبير المتثبتين|امام دار الهجره"),
    (3, r"ثقه|متقن|ثبت|عدل"), (4, r"صدوق|لا باس به|ليس به باس"),
    (1, SAHABAT),
]
_RE_TINGKAT = [(t, re.compile(f"(?<![ء-ي])(?:{p})(?![ء-ي])")) for t, p in TINGKAT]
_RE_AWAL_VONIS = re.compile(r"(?<![ء-ي])(ثقه|صدوق|مقبول|مقبوله|ضعيف|ضعيفه|متروك|مجهول|مجهوله|مستور|مستوره|لين|كذاب|متهم|"
                            r"اوثق|امام|حافظ|الحافظ|ثبت|فيه لين|لا يعرف|لا تعرف|واهي|ساقط|وضاع|لا باس به|ليس به باس|"
                            r"متفق علي جلالته|امام دار الهجره|وثقه|فيه ضعف|لا يثبت حديثه|مختلف في صحبته|" + SAHABAT + r")(?![ء-ي])")


def penilaian_ibnu_hajar(isi):
    """Frasa penilaian Ibnu Hajar (teks asli) + nomor tingkatnya (1-12) atau None.
    Frasa = dari kata penilaian pertama sampai sebelum tabaqah/wafat/kode."""
    n = norm_ar(isi)
    m = _RE_AWAL_VONIS.search(n)
    if not m:
        return None, None
    akhir = len(n)
    for pola in (_RE_TABAQAH, re.compile(r"(?<![ء-ي])و?(?:مات|ماتت|قتل|استشهد|توفي)(?![ء-ي])")):
        x = pola.search(n, m.start())
        if x:
            akhir = min(akhir, x.start())
    frasa_n = " ".join(n[m.start():akhir].split()[:16])
    tingkat = next((t for t, p in _RE_TINGKAT if p.search(frasa_n)), None)
    # kembalikan potongan teks ASLI (berharakat/berhamzah) yang sepadan: petakan lewat jumlah kata
    kata_asli = isi.split()
    awal = len(n[:m.start()].split())
    while frasa_n.split() and frasa_n.split()[-1] in ("وهو", "وهي", "وكان", "و", "من"):
        frasa_n = " ".join(frasa_n.split()[:-1])
    frasa = " ".join(kata_asli[awal:awal + len(frasa_n.split())])
    return frasa + (" …" if len(n[m.start():akhir].split()) > 16 else ""), tingkat


def tahun_wafat(n, tabaqah):
    """'مات سنه احدي وعشرين' + tabaqah 9 -> 221 (kaidah muqaddimah Taqrib: tabaqah 1-2 sebelum 100, 3-8 sesudah 100,
    9-12 sesudah 200). Kembalikan (tahun|None, teks, ragu). Yang diambil pendapat PERTAMA Ibnu Hajar; ragu=1 bila
    sesudahnya ada pendapat lain ("وقيل", "او", "ويقال", "قبل/بعد ذلك"). Tahun None bila teksnya tidak pasti (بضع)."""
    m = re.search(r"(?<![ء-ي])و?(?:مات|ماتت|قتل|قتلت|استشهد|توفي|توفيت)(?:\s+(?!سنه|عام)\S+){0,3}?\s+(?:سنه|عام)\s+((?:\S+\s*){1,8})", n)
    if not m:
        return None, None, 0
    kata = m.group(1).split()
    angka = {**SATUAN, **PULUHAN, **RATUSAN}
    dipakai, nilai, ada_ratus = 0, 0, False
    for w in kata:
        b = w[1:] if w.startswith("و") and w[1:] in angka else w
        if b not in angka:
            break
        nilai += angka[b]
        ada_ratus |= b in RATUSAN
        dipakai += 1
    # "سنة سبع وقيل ثمان وقيل تسع وخمسين": puluhan/ratusan ditulis sekali di akhir dan berlaku untuk semua pendapat
    if dipakai and nilai < 10:
        for w in kata[dipakai:dipakai + 8]:
            b = w[1:] if w.startswith("و") and w[1:] in angka else w
            if b in PULUHAN or b in RATUSAN:
                nilai += angka[b]
                ada_ratus |= b in RATUSAN
            elif b not in SATUAN and b not in ("وقيل", "قيل", "او", "ويقال", "سنه"):
                break
    teks = (n[m.start():m.start(1)] + " ".join(kata[:dipakai])).strip()
    if not dipakai or "بضع" in m.group(0) or "نيف" in m.group(0):
        return None, teks, 0
    sisa = " ".join(kata[dipakai:dipakai + 3])
    ragu = 1 if re.match(r"^(او|وقيل|ويقال|قيل|بعد|قبل|وقيل|علي الصحيح)", sisa) and not sisa.startswith("علي الصحيح") else 0
    if not ada_ratus:
        if not tabaqah:
            return None, teks, ragu
        nilai += 0 if tabaqah <= 2 else (100 if tabaqah <= 8 else 200)
    return nilai, teks, ragu


def urai_taqrib():
    entri, cur = [], None
    for baris in open(F_TAQRIB, encoding="utf8"):
        baris = baris.rstrip("\n")
        m = re.match(r"^### \$+(?:[A-Z_]+\$)? (\d+) (.*)", baris)       # "$$" = bagian perawi perempuan
        if m:
            cur = {"no": int(m.group(1)), "teks": [m.group(2)]}
            entri.append(cur)
            continue
        if baris.startswith("###") or baris.startswith("#META"):
            cur = None
            continue
        if cur is not None and baris.startswith("~~"):
            cur["teks"].append(baris[2:])
    out, lihat = [], set()
    for e in entri:
        if e["no"] in lihat:
            continue
        lihat.add(e["no"])
        teks = bersih(" ".join(e["teks"]))
        kata = teks.split()
        rumuz = []
        while kata and (kata[-1] in RUMUZ or kata[-1] == "تمييز"):
            rumuz.insert(0, kata.pop())
        isi = " ".join(kata)
        n = norm_ar(isi)
        mt = _RE_TABAQAH.search(n)
        tabaqah = TABAQAH[mt.group(1)] if mt else (1 if re.search(f"(?<![ء-ي])(?:{SAHABAT}|بدري|زوج النبي)(?![ء-ي])", n) else None)
        wafat, wafat_teks, ragu = tahun_wafat(n, tabaqah)
        penilaian, tingkat = penilaian_ibnu_hajar(isi)
        out.append({"no": e["no"], "teks": isi, "rumuz": rumuz, "tabaqah": tabaqah, "wafat": wafat, "wafat_teks": wafat_teks,
                    "wafat_ragu": ragu, "penilaian": penilaian, "tingkat": tingkat})
    return out


# "### $ 6836 - ع: nama", "### $ 17-ع: nama", "### $ (601) س: nama", "### $ 1767 - (أ) - م د ت: nama", "### $ 5684 - nama"
_RE_KEPALA_TK = re.compile(r"^### \${1,2} \(?(\d+)\)?\s*-?\s*(?:\([^)]{1,3}\)\s*-\s*)?(?:([^:]{0,24}):)?\s*(.*)")


def urai_tk():
    """Tahdzib al-Kamal: entri bernomor '### $ N - kode: nama ...'. Daftar guru/murid diambil apa adanya."""
    entri, cur = [], None
    for baris in open(F_TK, encoding="utf8"):
        baris = baris.rstrip("\n")
        if baris.startswith("### $"):
            baris = re.sub(r"\s*ms\d+\s*", " ", baris)
        m = _RE_KEPALA_TK.match(baris)
        if m:
            pecah = [pecah_kode(k) for k in (m.group(2) or "").split()]
            if any(x is None for x in pecah):                           # ":" bagian dari nama, bukan pemisah kode
                kode, isi = [], baris[m.end(1):].lstrip(" )-")
            else:
                kode, isi = [k for x in pecah for k in x], m.group(3)
            cur = {"no": int(m.group(1)), "rumuz": kode, "teks": [isi]}
            entri.append(cur)
            continue
        if baris.startswith("###") or baris.startswith("#META"):
            cur = None
            continue
        if cur is not None and (baris.startswith("# ") or baris.startswith("~~")):
            cur["teks"].append(baris[2:])
        elif cur is not None and re.match(r"^PageV\d+P\d+$", baris.strip()):
            continue
    out = []
    for e in entri:
        teks = bersih(" ".join(e["teks"]))
        i_an = teks.find("روى عن:")
        i_anhu = teks.find("روى عنه:")
        kepala = teks[:i_an if i_an >= 0 else (i_anhu if i_anhu >= 0 else 400)]
        guru = teks[i_an + 7:i_anhu] if 0 <= i_an < i_anhu else ""
        murid = ""
        if i_anhu >= 0:
            sisa = teks[i_anhu + 8:]
            akhir = re.search(r"\.\s+(?=(?:و?قال|و?ذكره|و?كان|و?روى له|و?مات|و?ولد|و?قيل|و?سئل|قلت|و?اخبرنا|و?أخبرنا|و?حدثنا|و?أنبأنا|و?قرأت)[\s:])", sisa)
            murid = sisa[:akhir.start()] if akhir else sisa[:4000]
        out.append({"urut": len(out) + 1, "no": e["no"], "rumuz": [r for r in e["rumuz"] if r in RUMUZ], "kepala": kepala.strip(),
                    "guru": urai_daftar(guru), "murid": urai_daftar(murid), "teks_len": len(teks)})
    return out


_RE_KODE = re.compile(r"\(([^()]*)\)")


def urai_daftar(t):
    """'إسحاق بن عبد الله (س) ، وأنس ابن مالك (خ م ت س ق) ، ...' -> [(nama, [kode])]."""
    out = []
    for bag in re.split(r"\s*[،,]\s*", t):
        bag = bag.strip(" .")
        if not bag:
            continue
        kode = []
        for m in _RE_KODE.finditer(bag):
            pecah = [pecah_kode(k) for k in m.group(1).split()]
            if pecah and all(x is not None for x in pecah):
                kode += [k for x in pecah for k in x]
        nama = _RE_KODE.sub(" ", bag)
        nama = re.sub(r"^و(?=[ء-ي])", "", nama.strip())
        nama = re.split(r"\s+(?:وهو|وهي|ومات|ان كان|إن كان|فيما|قاله|على خلاف|ولم يسمعه|ولم يسمع|إن صح|ان صح)\s", nama)[0]
        nama = _SPASI.sub(" ", nama).strip(" .")
        if 2 <= len(nama) <= 120:
            out.append((nama, kode))
    return out


def main():
    os.makedirs(BUILD, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE taqrib (no INTEGER PRIMARY KEY, teks TEXT, rumuz TEXT, tabaqah INT, wafat INT, wafat_teks TEXT, wafat_ragu INT,
                         penilaian TEXT, tingkat INT);
    -- id = urutan entri di teks digital; no_cetak = nomor tertulis (di teks digital ada nomor ganda, jadi bukan kunci)
    CREATE TABLE tk (id INTEGER PRIMARY KEY, no_cetak INT, rumuz TEXT, kepala TEXT, n_guru INT, n_murid INT);
    CREATE TABLE tk_relasi (tk_id INT, arah TEXT, nama TEXT, kode TEXT);   -- arah: guru|murid
    CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
    """)
    tq = urai_taqrib()
    db.executemany("INSERT INTO taqrib VALUES (?,?,?,?,?,?,?,?,?)",
                   [(e["no"], e["teks"], " ".join(e["rumuz"]), e["tabaqah"], e["wafat"], e["wafat_teks"], e["wafat_ragu"],
                     e["penilaian"], e["tingkat"]) for e in tq])
    tk = urai_tk()
    db.executemany("INSERT INTO tk VALUES (?,?,?,?,?,?)", [(e["urut"], e["no"], " ".join(e["rumuz"]), e["kepala"], len(e["guru"]), len(e["murid"])) for e in tk])
    db.executemany("INSERT INTO tk_relasi VALUES (?,?,?,?)",
                   [(e["urut"], arah, nama, " ".join(kode)) for e in tk for arah in ("guru", "murid") for nama, kode in e[arah]])
    info = {"taqrib_entri": len(tq), "taqrib_tingkat": sum(1 for e in tq if e["tingkat"]), "taqrib_tabaqah": sum(1 for e in tq if e["tabaqah"]), "taqrib_wafat": sum(1 for e in tq if e["wafat"]),
            "taqrib_rumuz": sum(1 for e in tq if e["rumuz"]), "tk_entri": len(tk), "tk_dengan_guru": sum(1 for e in tk if e["guru"]),
            "tk_relasi": sum(len(e["guru"]) + len(e["murid"]) for e in tk)}
    db.executemany("INSERT INTO info VALUES (?,?)", [(k, str(v)) for k, v in info.items()])
    db.commit()
    print(json.dumps(info), file=sys.stderr)


if __name__ == "__main__":
    main()
