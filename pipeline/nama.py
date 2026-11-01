#!/usr/bin/env python3
"""Model nama Arab perawi: ism + rantai nasab (بن/بنت), kunyah (أبو/أم ...), nisbah/laqab (kata ber-ال),
dan rujukan nasab ("ابن عمر", "ابن شهاب" = salah satu leluhur).

urai(nama) -> Nama(rantai, kunyah, atribut, leluhur)
cocok(sebutan, entri) -> True bila sebutan di sanad bisa merujuk ke entri kitab rijal itu.
"""
import re
from dataclasses import dataclass, field

from common import norm_ar

KUNYAH = {"ابو", "ابي", "ابا", "ام"}
PEMISAH = {"بن", "ابن", "بنت", "ابنه"}
_GELAR = {"رسول", "النبي", "امير", "المومنين", "مولي", "مولاهم", "مولاه", "رضي", "صاحب", "القاضي", "الامام", "الحافظ",
          "الشيخ", "يعني", "هو", "وهو", "قاضي", "نزيل", "اخو", "اخي", "والد", "خال", "عم", "زوج", "جد", "امام", "الفقيه"}


def _tanpa_al(w):
    return w[2:] if w.startswith("ال") and len(w) > 4 else w


def satuan(w):
    """Bentuk pembanding satu nama: tanpa ال, 'ابي/ابا' -> 'ابو'."""
    p = w.split(" ")
    if p[0] in ("ابي", "ابا"):
        p[0] = "ابو"
    return " ".join(_tanpa_al(x) for x in p)


@dataclass
class Nama:
    rantai: list = field(default_factory=list)      # [ism, ayah, kakek, ...] dalam bentuk satuan()
    kunyah: list = field(default_factory=list)      # ["ابو سعيد"]
    atribut: list = field(default_factory=list)     # ["الانصاري", "الزهري"]
    leluhur: list = field(default_factory=list)     # rujukan "ابن X [بن Y]": [X, Y]
    alias_leluhur: list = field(default_factory=list)  # nasab lain dalam biografi: "أبو بكر بن أبي شيبة" -> [ابو شيبه]
    maula: list = field(default_factory=list)       # "نافع مولى ابن عمر" -> [عمر]

    def kosong(self):
        return not (self.rantai or self.kunyah or self.atribut or self.leluhur)


RELATIF = {"ابيه", "ابي", "ابوه", "عمه", "عمي", "جده", "جدي", "امه", "امي", "اخيه", "اخي", "خاله", "خالي", "رجل", "رجلا",
           "بعض", "شيخ", "فلان", "مولي", "مولاه", "امراه", "اهل", "اصحابه", "اصحابنا"}
GELAR_KUNYAH = {"ام مومنين"}      # "أم المؤمنين" adalah gelar, bukan kunyah


# kata hubungan di depan nama dalam daftar Tahdzib al-Kamal: "ومولاه عبد الله بن عمر", "وأبيه عمر بن ..."
DEPAN_RELASI = {"مولاه", "مولاته", "مولاهم", "ابيه", "عمه", "جده", "اخيه", "امه", "خاله", "ابنه", "زوجته", "زوجها", "ابن_عمه",
                "اخته", "جدته", "ابنته", "ابن", "صهره", "مولي", "خالته", "عمته", "اخيها", "ابيها", "امها", "زوجه", "خالتها",
                "عمتها", "جدها", "جدتها", "ابنها", "ابنتها", "مولاتها", "سيده", "سيدته", "اخوه", "اخواته", "ابني"}
_TANWIN_ALIF = re.compile(r"(?:\u064B\u0627|\u0627\u064B)(?=[\s،,.:]|$)")   # "كُرَيْبًا" -> "كريب"


def _token(nama):
    t = norm_ar(_TANWIN_ALIF.sub("", re.sub(r"\([^)]*\)", " ", nama))).split()
    while len(t) > 1 and (t[0] in DEPAN_RELASI or (t[0][:1] == "و" and t[0][1:] in DEPAN_RELASI)) and t[0] not in ("ابن", "مولي"):
        t = t[1:]
    out, i = [], 0
    while i < len(t):
        w = t[i]
        if w in ("عبد", "عبيد") and i + 1 < len(t) and t[i + 1] not in PEMISAH and (w == "عبد" or t[i + 1] == "الله"):
            out.append(w + " " + t[i + 1]); i += 2; continue
        if w in KUNYAH and i + 1 < len(t) and t[i + 1] not in PEMISAH:
            if t[i + 1] in ("عبد", "عبيد") and i + 2 < len(t):
                out.append(w + " " + t[i + 1] + " " + t[i + 2]); i += 3; continue
            out.append(w + " " + t[i + 1]); i += 2; continue
        out.append(w); i += 1
    return out


def _runs(tok):
    """Kelompokkan token menjadi 'run' nasab: U (بن U)*, dan kata lepas."""
    runs, cur, i = [], None, 0
    while i < len(tok):
        w = tok[i]
        if w in PEMISAH:
            if cur is not None and i + 1 < len(tok) and tok[i + 1] not in PEMISAH:
                cur.append(tok[i + 1]); i += 2; continue
            if cur is None and i + 1 < len(tok):          # "ابن X" di awal
                cur = ["@ابن", tok[i + 1]]; runs.append(cur); i += 2; continue
            i += 1; continue
        cur = [w]; runs.append(cur); i += 1
    return runs


def urai(nama):
    tok = _token(nama)
    n = Nama()
    if len(tok) == 1 and tok[0] in RELATIF:
        return n
    if "مولي" in tok:                                  # "X مولى Y": Y = tuan/kabilah, pembeda yang kuat
        k = tok.index("مولي")
        n.maula = kata_maula(tok[k + 1:])
        tok = tok[:k]
    for run in _runs(tok):
        kepala = run[0]
        if kepala in _GELAR:
            break
        if kepala == "@ابن":
            if not n.rantai and not n.leluhur:
                n.leluhur = [satuan(x) for x in run[1:]]
            else:
                n.alias_leluhur += [satuan(x) for x in run[1:]]
            continue
        kunyah = kepala.split(" ")[0] in KUNYAH and " " in kepala
        if kunyah:
            if satuan(kepala) not in GELAR_KUNYAH:
                n.kunyah.append(satuan(kepala))
            elif "ام_المومنين" not in n.atribut:
                n.atribut.append("ام_المومنين")         # gelar istri Nabi ﷺ: pembeda (عائشة أم المؤمنين ≠ عائشة بنت طلحة)
            # "أبو بكر بن أبي شيبة": kunyah + leluhur (nama keluarga)
            if len(run) > 1:
                if not n.rantai and not n.leluhur and not n.alias_leluhur:
                    n.leluhur = [satuan(x) for x in run[1:]]
                else:
                    n.alias_leluhur += [satuan(x) for x in run[1:]]
            continue
        if len(run) == 1 and kepala.startswith("ال") and (n.rantai or n.kunyah or n.leluhur or not _ism_ber_al(kepala)):
            n.atribut.append(kepala)
            continue
        if not n.rantai and not n.leluhur:
            n.rantai = [satuan(x) for x in run]
        elif len(run) > 1:
            n.alias_leluhur += [satuan(x) for x in run[1:]]
        else:
            n.atribut.append(kepala)                       # laqab tanpa ال (mis. "بندار")
    return n


# ism yang memang memakai ال: "الحسن", "الحارث" ... (sebutan tunggal "الحسن" = ism, bukan nisbah)
ISM_AL = {"الحسن", "الحسين", "الحارث", "الزبير", "العباس", "الفضل", "القاسم", "المغيره", "النعمان", "الوليد", "المنذر",
          "السايب", "الحكم", "الربيع", "العلا", "الليث", "الاسود", "المسيب", "الاوزاعي_", "المقداد", "البرا", "الاحنف",
          "المطلب", "الهيثم", "الصلت", "المعتمر", "المفضل", "المثني", "الجراح", "الاشعث", "الضحاك", "الحجاج", "النضر",
          "الاعمش_", "الخليل", "العوام", "الحميدي_"}


def _ism_ber_al(w):
    return w in ISM_AL


_BUKAN_MAULA = {"بن", "ابن", "بني", "ال", "عبد", "الله", "ابي", "ابو", "ام", "بنت", "رسول", "النبي", "صلي", "عليه", "وسلم",
                "مولاهم", "مولي", "امراه", "من"}


def kata_maula(tok):
    out = []
    for w in tok[:5]:
        for x in w.split(" "):
            x = _tanpa_al(x)
            if x not in _BUKAN_MAULA and len(x) > 2:
                out.append(x)
    return out


def _mirip(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    # jarak edit <= 1 ("حيويل" ~ "حيوييل")
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    p, q = (a, b) if len(a) < len(b) else (b, a)
    return any(q[:i] + q[i + 1:] == p for i in range(len(q)))


def cocok(s, e, atribut_entri):
    """s: Nama sebutan di sanad. e: Nama entri rijal. atribut_entri: himpunan semua kata di biografi singkat entri."""
    if s.kosong():
        return False
    if s.rantai:
        if e.rantai[:min(2, len(s.rantai))] != s.rantai[:2]:
            return False
        # leluhur sesudah ayah: boleh melompati ("أحمد بن عمرو بن السرح" = kakek buyut), urutan tetap, ejaan selisih <= 1
        sisa = e.rantai[2:] + e.alias_leluhur
        j = 0
        for x in s.rantai[2:]:
            while j < len(sisa) and not _mirip(sisa[j], x):
                j += 1
            if j == len(sisa):
                return False
            j += 1
    if s.leluhur:
        ok = False
        for r in (e.rantai[1:], e.alias_leluhur):
            if any(r[j:j + len(s.leluhur)] == s.leluhur for j in range(len(r))):
                ok = True
        if not ok:
            return False
    for k in s.kunyah:
        if k not in e.kunyah:
            return False
    for a in s.atribut:
        if a not in atribut_entri and _tanpa_al(a) not in atribut_entri:
            return False
    if s.maula and e.maula and not (set(s.maula) & set(e.maula)):
        return False                                    # "مولى أبي بكر بن حزم" bukan "مولى بني ليث"
    return True
