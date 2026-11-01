#!/usr/bin/env python3
"""Pemisahan sanad-matan dan rantai perawi dari teks Arab: port SETIA dari site/src/teks.js
(pisahSanad, rantaiArab). Keduanya harus menghasilkan segmen yang sama persis (diuji paritas), karena
identifikasi perawi disimpan per nomor segmen dan ditempelkan situs ke segmen yang ia tampilkan."""
import re
import unicodedata

from common import norm_ar, strip_harakat

HRK = "[ً-ْٰـ]*"
HUR = "[ء-ي]"
SIGHAH = ["حدثنا", "حدثني", "أخبرنا", "أخبرني", "سمعت", "سمع", "عن"]
_VARIAN = {"ا": "[اأإآٱ]", "ي": "[يى]", "ه": "[هة]"}


def _pola(kata, toleran=False):
    out = []
    for c in kata:
        if c == " ":
            out.append(r"\s+")
        else:
            out.append(((toleran and _VARIAN.get(c)) or re.escape(c)) + HRK)
    return "".join(out)


RE_SIGHAH = re.compile("|".join(
    f"(?<![ء-يً-ْ])(?:[وف]{HRK})?{_pola(s)}(?!{HRK}{HUR})" for s in SIGHAH))
_SIGHAH_NORM = {norm_ar(s): s for s in SIGHAH}


def kunci_sighah(lafaz):
    b = norm_ar(lafaz)
    if b[:1] in ("و", "ف") and len(b) > 2:
        b = b[1:]
    return _SIGHAH_NORM.get(b)


RE_SALAWAT = re.compile(f"(?:{_pola('صلي الله عليه وسلم', True)}|ﷺ)")
RE_SETELAH = re.compile(rf"^\s*[،,]?\s*(?:(?:{_pola('قال', True)}|{_pola('يقول', True)}|{_pola('فقال', True)})\s*:?)?\s*")


def _kata(s):
    return s.split()


def pisah_sanad(arab):
    """Sama dengan pisahSanad (JS). Kembalikan (sanad, matan) atau None."""
    t = (arab or "").strip()
    for tanda in ('"', "«", "“"):
        i = t.find(tanda)
        if i > 10:
            matan = re.sub(r'["»”‏\s.]+$', "", t[i + 1:]).strip()
            if len(_kata(matan)) >= 4:
                return re.sub(r"[‏\s]+$", "", t[:i]), matan
    m = RE_SALAWAT.search(t)
    if m:
        akhir = m.end()
        s = RE_SETELAH.match(t[akhir:])
        potong = akhir + (len(s.group(0)) if s else 0)
        matan = t[potong:].strip()
        if len(_kata(matan)) >= 4:
            return t[:potong].strip(), matan
    return None


HENTI_NAMA = {"قال", "قالت", "ان", "انه", "انها", "يقول", "تقول", "رضي", "يرفعه", "يبلغ", "به", "نحوه", "مثله",
              "يحدث", "حدثه", "اخبره", "في", "قالا", "قالوا", "وهو", "ذكر", "عن"}
HURUF_JAR_ALA = "على"   # "عَلَى" menghentikan nama; "عَلِيّ" (nama) tidak
_TANDA_AKHIR = re.compile(r'[،,:؛.‏"]+$')


def rantai_arab(sanad):
    """Sama dengan rantaiArab (JS): [{lafaz, sighah, nama_ar, nabi}] urut dari guru penyusun ke atas."""
    ms = list(RE_SIGHAH.finditer(sanad))
    segs = []
    for i, m in enumerate(ms):
        akhir = ms[i + 1].start() if i + 1 < len(ms) else len(sanad)
        kata = sanad[m.end():akhir].strip().split()
        nama = []
        for w in kata:
            bersih = _TANDA_AKHIR.sub("", w)
            if not bersih or norm_ar(bersih) in HENTI_NAMA or strip_harakat(bersih) == HURUF_JAR_ALA:
                break
            nama.append(bersih)
            if bersih != w:
                break
        if not nama:
            continue
        nama_ar = " ".join(nama)
        n = norm_ar(nama_ar)
        segs.append({"lafaz": m.group(0), "sighah": kunci_sighah(m.group(0)), "nama_ar": nama_ar,
                     "nabi": bool(re.match(r"^(رسول الله|النبي|نبي الله)", n))})
    i_nabi = next((i for i, s in enumerate(segs) if s["nabi"]), -1)
    return segs[:i_nabi + 1] if i_nabi >= 0 else segs


def rantai_riwayat(arab):
    p = pisah_sanad(arab)
    return rantai_arab(p[0]) if p else []
