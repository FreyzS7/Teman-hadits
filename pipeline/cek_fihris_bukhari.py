#!/usr/bin/env python3
"""Cari bab TANPA JUDUL yang terlewat di teks digital Shahih al-Bukhari, dengan fihris cetak Dar Thauq an-Najah.

Fihris cetakan itu mencatat bab tanpa judul sebagai «باب: حدثنا <perawi pertama>» tepat sebelum bab bertajuk
berikutnya. Skrip ini membaca OCR fihris (scan archive.org), lalu untuk setiap entri:
  1. mencari bab bertajuk berikutnya di data kita (maju sesuai urutan kitab);
  2. di bab tepat sebelumnya mencari hadits yang diawali «حدثنا <perawi>» (harus TEPAT SATU);
  3. melaporkan bila hadits itu belum berada di bab tanpa judul (= terlewat di teks digital).
Hasilnya kandidat; koreksi hanya dimasukkan ke pipeline/koreksi_bab.json sesudah diperiksa (docs/13).

Jalankan:  python3 -I pipeline/cek_fihris_bukhari.py   -> build/cek_fihris_bukhari.json
"""
import collections
import gzip
import json
import os
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bab_openiti import urai
from common import BUILD, SRC, norm_ar

ITEM = "alfirdwsiy2018_gmail_2698_201808"
LEAF_FIHRIS = range(4, 81)
DIR = os.path.join(BUILD, "cetak")


def unduh():
    os.makedirs(DIR, exist_ok=True)
    meta = json.loads(subprocess.run(["curl", "-sf", f"https://archive.org/metadata/{ITEM}"], capture_output=True, check=True).stdout)
    out = {}
    for akhiran, nama in (("_hocr_searchtext.txt.gz", "bukhari_st.txt.gz"), ("_hocr_pageindex.json.gz", "bukhari_pi.json.gz")):
        p = os.path.join(DIR, nama)
        if not os.path.exists(p):
            f = next(x["name"] for x in meta["files"] if x["name"].endswith(akhiran))
            subprocess.run(["curl", "-sfL", "-o", p, f"https://archive.org/download/{ITEM}/{urllib.parse.quote(f)}"], check=True)
        out[nama] = p
    return gzip.open(out["bukhari_st.txt.gz"], "rt", encoding="utf8").read(), json.load(gzip.open(out["bukhari_pi.json.gz"], "rt"))


def mirip(a, b):
    a, b = set(a.split()), set(b.split())
    return len(a & b) / max(1, min(len(a), len(b)))


def main():
    st, pi = unduh()
    B = [b for b in urai(os.path.join(SRC, "openiti-0275AH", "0256Bukhari.Sahih.Shamela0001681-ara1"), "bukhari") if b["no"] is not None]
    nb = [norm_ar(b["bab"] or "") for b in B]
    entri = []
    for leaf in LEAF_FIHRIS:
        t = norm_ar(st[pi[leaf][0]:pi[leaf][1]])
        for m in re.finditer(r"(?<![ء-ي])(?:باب|بات|ياب)\s+(?:حدثن[اي]|اخبرن[اي]|حدتنا|حدنا)\s+((?:(?!باب|بات)\S+\s+){1,5})(?:باب|بات)\s+((?:\S+\s+){1,6})", t):
            entri.append((leaf, m.group(1).strip(), " ".join(w for w in m.group(2).split() if w not in ("باب", "بات"))))
    hasil, mulai = [], 0
    for leaf, perawi, berikut in entri:
        j = next((i for i in range(mulai, len(B)) if nb[i] != "باب" and (i == 0 or nb[i] != nb[i - 1])
                  and mirip(berikut, nb[i].replace("باب ", "", 1)) >= 0.75), None)
        h = {"leaf": leaf, "perawi_ocr": perawi, "bab_berikut_ocr": berikut}
        if j is None:
            hasil.append({**h, "status": "bab-berikut-tak-terbaca"})
            continue
        mulai = j + 1
        run, k = [], j - 1
        while k >= 0 and nb[k] == nb[j - 1]:
            run.append(k)
            k -= 1
        pw = " ".join(w for w in perawi.split() if len(w) > 2)
        cocok = [i for i in run[::-1] if pw and mirip(pw, " ".join(norm_ar(B[i]["teks"]).split()[1:7])) >= 0.67]
        h.update(bab_berikut_no=B[j]["no"], bab_sebelumnya=B[j - 1]["bab"])
        if nb[j - 1] == "باب":
            h["status"] = "sudah-tanpa-judul"
        elif len(cocok) == 1:
            h.update(status="terlewat", rentang=[B[cocok[0]]["no"], B[j - 1]["no"]])
        else:
            h["status"] = f"ragu-{len(cocok)}-kandidat"
        hasil.append(h)
    json.dump(hasil, open(os.path.join(BUILD, "cek_fihris_bukhari.json"), "w"), ensure_ascii=False, indent=1)
    print(dict(collections.Counter(h["status"] for h in hasil)))
    for h in hasil:
        if h["status"] == "terlewat":
            print("terlewat:", h["rentang"], "sebelum bab no.", h["bab_berikut_no"], "|", h["perawi_ocr"])


if __name__ == "__main__":
    main()
