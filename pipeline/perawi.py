#!/usr/bin/env python3
"""Identifikasi perawi di sanad: menautkan setiap nama di rantai ke satu entri Tahdzib al-Kamal / Taqrib.

Cara (seperti yang dilakukan muhaddits saat "تمييز المهمل"): sebuah nama ("سفيان") bisa merujuk ke banyak orang;
yang menentukan adalah SIAPA murid dan gurunya di rantai itu. Tahdzib al-Kamal mencatat untuk setiap perawi daftar
guru (روى عن) dan murid (روى عنه), dan untuk setiap hubungan, di kitab mana hubungan itu ada (خ م د ت س ق ع 4).

1. Kandidat: entri yang namanya cocok (nama.cocok) DAN kode kitabnya memuat kitab hadits ini.
2. Bukti tiap pasangan murid->guru: 2 = tercatat di daftar guru/murid DENGAN kode kitab ini; 1 = tercatat tanpa kode;
   0 = tidak tercatat. Penalti bila tabaqah guru lebih muda dari muridnya.
3. Max-marginal sepanjang rantai (Viterbi maju-mundur). Sebuah nama DITERIMA hanya bila satu kandidat unggul
   mutlak atas semua kandidat lain dan minimal satu hubungannya bernilai 2.
   'pasti' = semua hubungan dengan tetangga yang dikenali bernilai 2; 'kuat' = minimal satu.

Keluaran: build/perawi.sqlite.   Jalankan:  python3 -I pipeline/perawi.py
"""
import collections
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, norm_ar
from nama import Nama, cocok, urai
from rijal import KODE_KITAB, OUT as RIJAL
from sanad import rantai_riwayat

OUT = os.path.join(BUILD, "perawi.sqlite")
KITAB6 = ["bukhari", "muslim", "abudawud", "tirmidzi", "nasai", "ibnumajah"]
_VONIS = re.compile(r"(?<![ء-ي])(ثقه|صدوق|مقبول|ضعيف|متروك|مجهول|مستور|لين|كذاب|متهم|صحابي|صحابيه|له صحبه|لها صحبه|"
                    r"ام المومنين|شهد|ثبت|حافظ|امام|فقيه|من الاولي|من الثانيه|من الثالثه|من الرابعه|من الخامسه|"
                    r"من السادسه|من السابعه|من الثامنه|من التاسعه|من العاشره|من الحاديه|من صغار|من كبار|يقال|مشهور)(?![ء-ي])")
PENULIS = {"bukhari": "محمد بن اسماعيل بن ابراهيم بن المغيره", "muslim": "مسلم بن الحجاج بن مسلم",
           "abudawud": "سليمان بن الاشعث بن شداد", "tirmidzi": "محمد بن عيسي بن سوره",
           "nasai": "احمد بن شعيب بن علي", "ibnumajah": "محمد بن يزيد"}


def bagian_nama(teks, maks=40):
    """Bagian awal biografi sampai kata penilaian/tabaqah pertama (nama, nasab, kunyah, nisbah)."""
    n = norm_ar(teks)
    m = _VONIS.search(n)
    return " ".join(n[:m.start() if m else len(n)].split()[:maks])


# potongan kepala biografi yang membicarakan ORANG LAIN ("وأمه ... أخت أم سلمة", "شريك ابن جريج", "صاحب فلان")
_ORANG_LAIN = re.compile(r"(?<![ء-ي])(?:و?امه|و?ابوه|اخو|اخت|اخي|خال|خاله|عم|عمه|ابن اخت|ابن اخي|ابن عم|صاحب|شريك|جد|جده|"
                         r"والد|والده|زوج|زوجه|مولي|مولاه|مولاهم|حليف|ختن|صهر|ربيب|قريب|راويه|كاتب|غلام|وصي|ابنه|بنت اخي)(?![ء-ي])")


def nama_kepala_tk(kepala):
    """Bagian NAMA dari kepala biografi Tahdzib al-Kamal: potongan sebelum titik, tanpa 'ويقال ...' dan tanpa
    potongan (dipisah '،') yang membicarakan kerabat/guru/tuan orang itu."""
    t = re.sub(r"\(\d+\)", " ", kepala).split(".")[0]
    t = re.split(r"\s(?:ويقال|وقيل|ويقال له|كذا قال|قال)\b", t)[0]
    out = []
    for i, bag in enumerate(t.split("،")):
        if i and _ORANG_LAIN.search(norm_ar(bag)):
            break
        out.append(bag)
    return " ، ".join(out)


_RE_MAULA = re.compile(r"(?<![ء-ي])(?:مولي|مولاه|مولاهم)\s+((?:\S+\s*){1,5})")


def maula_dari(teks):
    """Kata-kata tuan/kabilah dari 'مولى ...' di biografi (pembeda "عكرمة مولى ابن عباس")."""
    from nama import kata_maula
    out = []
    for m in _RE_MAULA.finditer(norm_ar(teks)):
        out += kata_maula(m.group(1).split())
    return out


_RE_NASAB_JADD = re.compile(r"(?:ينسب|ينسبه\s+\S+|نسب|نسبه\s+\S+)\s+(?:الي\s+|ل)جده")


def luaskan(rumuz):
    """'ع' = keenam kitab, '4' = empat Sunan: luaskan sebelum dibandingkan (TK 'بخ ع' ~ Taqrib 'بخ م 4')."""
    out = set(rumuz)
    if "ع" in out:
        out |= {"خ", "م", "د", "ت", "س", "ق"}
    if "4" in out:
        out |= {"د", "ت", "س", "ق"}
    return out - {"ع", "4"}


def _lis(pasangan):
    """Pasangan (tk_id, taqrib_no) terurut tk_id -> subhimpunan terpanjang yang taqrib_no-nya naik (O(n log n))."""
    import bisect
    ekor, idx_ekor, induk = [], [], [None] * len(pasangan)
    for i, (_, no) in enumerate(pasangan):
        j = bisect.bisect_left(ekor, no)
        if j == len(ekor):
            ekor.append(no); idx_ekor.append(i)
        else:
            ekor[j] = no; idx_ekor[j] = i
        induk[i] = idx_ekor[j - 1] if j else None
    out, k = [], idx_ekor[-1] if idx_ekor else None
    while k is not None:
        out.append(pasangan[k]); k = induk[k]
    return out[::-1]


class Rijal:
    def __init__(self):
        r = sqlite3.connect(RIJAL)
        self.tk = {}
        for i, rumuz, kepala in r.execute("SELECT id, rumuz, kepala FROM tk"):
            nama_tk = nama_kepala_tk(kepala)
            kata = set(norm_ar(nama_tk).split()) | ({"ام_المومنين"} if "ام المومنين" in norm_ar(kepala[:200]) else set())
            self.tk[i] = {"rumuz": set(rumuz.split()), "varian": [urai(nama_tk)], "kata": kata,
                          "kepala": kepala, "maula": maula_dari(kepala[:300])}
        self.taqrib = {}
        for no, t, rz, tb in r.execute("SELECT no, teks, rumuz, tabaqah FROM taqrib"):
            bn = bagian_nama(t)
            m = _ORANG_LAIN.search(bn)
            bn = bn[:m.start()] if m and m.start() > 0 else bn
            bn = re.split(r"(?<![ء-ي])(?:عن|روي عن|يروي عن|شيخ ل)(?![ء-ي])", bn)[0]   # "أبو زرعة عن أبي إدريس"
            kata = set(bn.split()) | ({"ام_المومنين"} if "ام المومنين" in norm_ar(t[:150]) else set())
            self.taqrib[no] = {"teks": t, "rumuz": set(rz.split()), "tabaqah": tb, "nama": urai(bn), "kata": kata,
                               "maula": maula_dari(t)}
        self.petakan_taqrib()
        self.relasi = collections.defaultdict(list)
        for tk_id, arah, nama, kode in r.execute("SELECT tk_id, arah, nama, kode FROM tk_relasi"):
            self.relasi[tk_id].append((arah, nama, set(kode.split())))
        self.buat_indeks()
        self.cari_penulis()
        self.buat_graf()

    def cari_penulis(self):
        self.penulis = {}
        for k, nm in PENULIS.items():
            kand = [i for i in self.idx.get(("r", urai(nm).rantai[0]), set()) if self.cocok_entri(urai(nm), self.tk[i])]
            if k == "ibnumajah":
                kand = [i for i in kand if "ماجه" in self.tk[i]["kata_semua"] or "القزويني" in self.tk[i]["kata_semua"]]
            self.penulis[k] = kand[0] if len(kand) == 1 else None

    @staticmethod
    def _skor(nm, rz1, tn, rz2):
        pref = 0
        while pref < min(len(nm.rantai), len(tn.rantai)) and nm.rantai[pref] == tn.rantai[pref]:
            pref += 1
        a, b = luaskan(rz1), luaskan(rz2)
        rz = (len(a & b) / len(a | b)) if (a or b) else 0.5
        return pref, rz, len(set(nm.kunyah) & set(tn.kunyah))

    # --- Tahdzib al-Kamal <-> Taqrib: kedua kitab berurutan abjad yang sama ---------------------------------------
    def petakan_taqrib(self):
        idx = collections.defaultdict(list)
        for no, t in self.taqrib.items():
            if t["nama"].rantai:
                idx[tuple(t["nama"].rantai[:2])].append(no)
            for k in t["nama"].kunyah:
                idx[("k", k)].append(no)
        # 1) jangkar: nama (ism+ayah, atau kunyah) dan kode kitab cocok
        jangkar, kuat = [], {}
        for i, e in sorted(self.tk.items()):
            nm = e["varian"][0]
            kand = set(idx.get(tuple(nm.rantai[:2]), [])) if nm.rantai else set()
            if not kand and not nm.rantai:
                for k in nm.kunyah:
                    kand |= set(idx.get(("k", k), []))
            best = []
            for no in kand:
                t = self.taqrib[no]
                pref, rz, kun = self._skor(nm, e["rumuz"], t["nama"], t["rumuz"])
                if e["rumuz"] and t["rumuz"] and rz < 0.5:
                    continue
                if not nm.rantai and len((e["kata"] & t["kata"]) - set(" ".join(nm.kunyah).split())) == 0:
                    continue                    # "أبو جعفر الرازي" bukan "أبو جعفر المؤذن": nisbah harus ikut sama
                sama = len((e["kata"] & t["kata"]) - {"بن", "ابن", "ابو", "ابي", "بنت"})
                best.append((pref + 2 * rz + 0.5 * kun + 0.3 * sama, no, pref, rz))
            best.sort(reverse=True)
            if best and (len(best) == 1 or best[0][0] - best[1][0] >= 0.5):
                jangkar.append((i, best[0][1]))
                if best[0][2] >= 2 and best[0][3] >= 0.99 and (len(best) == 1 or best[0][0] - best[1][0] >= 1):
                    kuat[i] = best[0][1]       # jangkar kuat: >= 2 nama sama, kode kitab identik, unggul jelas
        # 2) buang jangkar yang melanggar urutan (subbarisan naik terpanjang). Urutan abjad kedua kitab sedikit
        #    berbeda (mis. "آدم" sesudah "إدريس" di TK, sesudah "أحمد" di Taqrib): jangkar kuat tetap dipakai.
        jangkar = _lis(jangkar)
        peta = dict(jangkar)
        for i, no in kuat.items():
            peta.setdefault(i, no)
        hit = collections.Counter(peta.values())
        peta = {i: no for i, no in peta.items() if hit[no] == 1}
        # 3) isi celah di antara dua jangkar: entri TK & Taqrib yang belum berpasangan, urut, kode kitab sama
        dipakai = set(peta.values())
        tk_urut = sorted(self.tk)
        posisi = {i: k for k, i in enumerate(tk_urut)}
        for (i1, n1), (i2, n2) in zip(jangkar, jangkar[1:]):
            celah_tk = [i for i in tk_urut[posisi[i1] + 1:posisi[i2]]]
            celah_tq = [no for no in range(n1 + 1, n2) if no in self.taqrib and no not in dipakai]
            if not celah_tk or not celah_tq or len(celah_tk) > 8 or len(celah_tq) > 12:
                continue
            j = 0
            for i in celah_tk:
                e = self.tk[i]
                for k in range(j, len(celah_tq)):
                    t = self.taqrib[celah_tq[k]]
                    pref, rz, kun = self._skor(e["varian"][0], e["rumuz"], t["nama"], t["rumuz"])
                    sama_ism = e["varian"][0].rantai[:1] == t["nama"].rantai[:1] and bool(t["nama"].rantai)
                    if (sama_ism or kun) and (rz >= 0.99 if (e["rumuz"] and t["rumuz"]) else False):
                        peta[i] = celah_tq[k]; dipakai.add(celah_tq[k]); j = k + 1
                        break
        self.tk_ke_taqrib = peta
        for i, e in self.tk.items():
            no = peta.get(i)
            t = self.taqrib.get(no) if no else None
            e["taqrib"] = no
            e["tabaqah"] = t["tabaqah"] if t else None
            e["rumuz_semua"] = e["rumuz"] | (t["rumuz"] if t else set())
            e["kata_semua"] = e["kata"] | (t["kata"] if t else set())
            if t:
                e["varian"].append(t["nama"])          # nama versi Taqrib: menambal kesalahan teks digital TK
                # Ibnu Hajar mencatat "وقد ينسب إلى جده" (mis. يحيى بن عبد الله بن بكير = "يحيى بن بكير"): varian tanpa ayah
                if _RE_NASAB_JADD.search(norm_ar(t["teks"])) and len(t["nama"].rantai) >= 3:
                    v = Nama(rantai=[t["nama"].rantai[0]] + t["nama"].rantai[2:], kunyah=list(t["nama"].kunyah),
                             atribut=list(t["nama"].atribut), alias_leluhur=list(t["nama"].alias_leluhur))
                    e["varian"].append(v)
                e["maula"] = e["maula"] + [x for x in t["maula"] if x not in e["maula"]]
            for v in e["varian"]:
                v.maula = e["maula"]

    # --- indeks kandidat ----------------------------------------------------------------------------------------
    def buat_indeks(self):
        self.idx = collections.defaultdict(set)
        for i, e in self.tk.items():
            for nm in e["varian"]:
                if nm.rantai:
                    self.idx[("r", nm.rantai[0])].add(i)
                for k in nm.kunyah:
                    self.idx[("k", k)].add(i)
                for x in nm.rantai[1:] + nm.alias_leluhur:
                    self.idx[("l", x)].add(i)
            for a in e["kata_semua"]:
                if a.startswith("ال"):
                    self.idx[("a", a)].add(i)

    def cocok_entri(self, nm, e):
        return any(cocok(nm, v, e["kata_semua"]) for v in e["varian"])

    def kandidat(self, nm, kode=None):
        if nm.kosong():
            return []
        if nm.rantai:
            pool = self.idx.get(("r", nm.rantai[0]), set())
        elif nm.leluhur:
            pool = self.idx.get(("l", nm.leluhur[0]), set())
        elif nm.kunyah:
            pool = self.idx.get(("k", nm.kunyah[0]), set())
        else:
            pool = self.idx.get(("a", nm.atribut[0]), set())
        out = []
        for i in pool:
            e = self.tk[i]
            if kode and not (e["rumuz_semua"] & kode):
                continue
            if self.cocok_entri(nm, e):
                out.append(i)
        return out

    # --- graf guru-murid dari daftar Tahdzib al-Kamal -----------------------------------------------------------
    def buat_graf(self):
        self.guru = collections.defaultdict(dict)    # murid -> {guru: kode}
        terselesaikan = 0
        total = 0
        # Dalam daftar murid, penulis keenam kitab ditulis singkat ("البخاري", "مسلم", ...): hubungan itu ADA di kitabnya
        alias = {"البخاري": ("bukhari", "خ"), "مسلم": ("muslim", "م"), "ابو داود": ("abudawud", "د"),
                 "الترمذي": ("tirmidzi", "ت"), "النسايي": ("nasai", "س"), "ابن ماجه": ("ibnumajah", "ق")}
        for i, rel in self.relasi.items():
            for arah, nama, kode in rel:
                total += 1
                pn = alias.get(norm_ar(nama)) if arah == "murid" else None
                if pn and self.penulis.get(pn[0]):
                    j = self.penulis[pn[0]]
                    self.guru[j][i] = self.guru[j].get(i, set()) | {pn[1]}
                    terselesaikan += 1
                    continue
                k = self.kandidat(urai(nama))
                if len(k) > 1 and kode:
                    # kode hubungan menyaring: "عمرو بن دينار (ع)" hanya bisa orang yang ada di keenam kitab
                    k = [j for j in k if menutup(self.tk[j]["rumuz_semua"], kode)] or k
                if not k or len(k) > 2:
                    continue
                terselesaikan += 1
                for j in k:
                    a, b = (i, j) if arah == "guru" else (j, i)   # (murid, guru)
                    lama = self.guru[a].get(b)
                    kode2 = set(kode) | ({"?"} if len(k) > 1 else set())
                    self.guru[a][b] = (lama | kode2) if lama is not None else kode2
        self.stat_graf = {"relasi": total, "relasi_terselesaikan": terselesaikan,
                          "pasangan": sum(len(v) for v in self.guru.values()), "tk_ke_taqrib": len(self.tk_ke_taqrib)}

    def bukti(self, murid, guru, kitab):
        kode = self.guru.get(murid, {}).get(guru)
        if kode is None:
            return 0
        if "?" not in kode and kode & KODE_KITAB[kitab]:
            return 2
        return 1


def menutup(rumuz, kode):
    """Apakah perawi dengan kode-kode kitab 'rumuz' bisa punya hubungan yang tercatat dengan 'kode'?"""
    for c in kode:
        if c in rumuz or "ع" in rumuz:
            continue
        if c in ("د", "ت", "س", "ق") and "4" in rumuz:
            continue
        if c == "4" and {"د", "ت", "س", "ق"} <= rumuz:
            continue
        if c in ("خت", "بخ", "عخ", "ر", "ي", "مد", "صد", "خد", "قد", "ف", "ل", "كد", "تم", "عس", "كن", "فق", "سي", "ز"):
            continue            # kitab-kitab kecil: Taqrib hanya menulis kode kitab utama bila ada
        return False
    return True


AYAH = {"ابيه", "ابي", "ابوه"}


def prior(nm, e):
    """Kebiasaan penyebutan: 'ابن X' lebih sering berarti X adalah AYAH. Hanya pemecah seri (< 1)."""
    if nm.leluhur:
        return 0.25 if any(v.rantai[1:2] == nm.leluhur[:1] for v in e["varian"]) else -0.25
    return 0.0


def dekode(rj, kitab, segs, penulis):
    """Kembalikan [(tk_id|None, label, margin)] per segmen (segmen Nabi dilewati)."""
    kode = KODE_KITAB[kitab]
    nama = [urai(s["nama_ar"]) for s in segs]
    C = []
    for i, (s, nm) in enumerate(zip(segs, nama)):
        if s["nabi"]:
            C.append([])
            continue
        if norm_ar(s["nama_ar"]) in AYAH and i > 0 and C[i - 1] and len(C[i - 1]) <= 30:
            # "عن أبيه" / "حدثني أبي": ayah dari perawi sebelumnya, namanya dari nasab perawi itu
            k = set()
            for p in C[i - 1]:
                for v in rj.tk[p]["varian"]:
                    if len(v.rantai) >= 2:
                        k |= set(rj.kandidat(Nama(rantai=v.rantai[1:3]), kode))
            C.append(sorted(k) if len(k) <= 120 else [])
            continue
        k = rj.kandidat(nm, kode)
        C.append(k if len(k) <= 120 else [])
    n = len(C)
    if not n:
        return []
    # skor tepi: (murid di posisi i-1, guru di posisi i). Posisi -1 = penulis kitab.
    def w(murid, guru):
        b = rj.bukti(murid, guru, kitab)
        tm, tg = rj.tk[murid]["tabaqah"] if murid in rj.tk else None, rj.tk[guru]["tabaqah"]
        if tm and tg and tg > tm + 1:
            b -= 2
        return b

    NEG = float("-inf")
    P = [{c: prior(nama[i], rj.tk[c]) for c in C[i]} for i in range(n)]
    f = []  # f[i][c] = skor terbaik prefiks berakhir di c
    for i in range(n):
        cur = {}
        for c in C[i]:
            if i == 0:
                cur[c] = (w(penulis, c) if penulis else 0) + P[i][c]
            else:
                prev = f[i - 1]
                cur[c] = (max((v + w(p, c) for p, v in prev.items()), default=0) if prev else 0) + P[i][c]
        f.append(cur)
    b = [dict() for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for c in C[i]:
            if i == n - 1 or not C[i + 1]:
                b[i][c] = 0
            else:
                b[i][c] = max(w(c, d) + b[i + 1][d] for d in C[i + 1])
    out = []
    for i in range(n):
        if not C[i]:
            out.append((None, None, 0))
            continue
        mm = sorted(((f[i][c] + b[i][c], c) for c in C[i]), reverse=True)
        best, c = mm[0]
        kedua = mm[1][0] if len(mm) > 1 else NEG
        margin = best - kedua
        # hubungan dengan tetangga pada jalur terbaik
        # Sisi kiri = murid (posisi i-1, atau penulis kitab). Sisi kanan = guru (posisi i+1), kecuali bila posisi i+1
        # adalah Nabi ﷺ / akhir rantai (sahabat): sisi itu tidak perlu tambatan.
        if i == 0:
            kiri = rj.bukti(penulis, c, kitab) if penulis else -1
        elif C[i - 1]:
            p = max(C[i - 1], key=lambda p: f[i - 1][p] + w(p, c))
            kiri = rj.bukti(p, c, kitab)
        else:
            kiri = -1                                  # tetangga tak dikenali: sisi ini tidak tertambat
        ujung = i + 1 >= n or segs[i + 1]["nabi"]
        if ujung:
            kanan = None
        elif C[i + 1]:
            d = max(C[i + 1], key=lambda d: w(c, d) + b[i + 1][d])
            kanan = rj.bukti(c, d, kitab)
        else:
            kanan = -1
        tepi = [x for x in (kiri, kanan) if x is not None]
        if margin <= 0 or 2 not in tepi:
            out.append((None, "ragu", margin))
        else:
            # 'pasti': unggul >= 1 dari bukti sanad (bukan hanya kebiasaan penyebutan) DAN kedua sisi tertambat
            # oleh hubungan guru-murid yang tercatat di kitab ini
            out.append((c, "pasti" if margin >= 1 and all(x == 2 for x in tepi) else "kuat", margin))
    return out


def perawi_id(tk_id, taqrib):
    """Alamat halaman perawi: nomor Taqrib (nomor standar edisi 'Awwamah) bila ada, selain itu nomor urut TK."""
    return f"t{taqrib}" if taqrib else f"k{tk_id}"


def nama_tampil(teks_taqrib):
    """Nama untuk judul: bagian nama entri Taqrib (tanpa keterangan ejaan 'بفتح ...', tanpa penilaian)."""
    kata = teks_taqrib.split()
    n = norm_ar(teks_taqrib).split()
    m = _VONIS.search(" ".join(n))
    batas = len(" ".join(n)[:m.start()].split()) if m else len(kata)
    out = []
    for w, x in zip(kata[:batas], n[:batas]):
        if x in ("بفتح", "بضم", "بكسر", "بمعجمه", "بمهمله", "بالتصغير", "مصغرا", "بموحده", "بنون", "بالمد", "بتشديد", "وقيل",
                 "ويقال", "يقال", "خادم", "صاحب", "اصله", "يكني", "نزيل", "الصحابي", "عم", "خدمه"):
            break
        out.append(w)
    out = out[:12]
    while out and norm_ar(out[-1]) in ("بن", "ابن", "بنت", "ثم"):
        out.pop()
    return " ".join(out) or teks_taqrib[:60]


def main():
    rj = Rijal()
    print(json.dumps({"tk": len(rj.tk), **rj.stat_graf}), file=sys.stderr)
    penulis = rj.penulis
    print("penulis:", {k: (v, rj.tk[v]["kepala"][:40] if v else None) for k, v in penulis.items()}, file=sys.stderr)

    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE sebutan (riwayat_id TEXT, pos INT, nama_ar TEXT, tk_id INT, taqrib INT, label TEXT, margin REAL,
                          PRIMARY KEY (riwayat_id, pos));
    CREATE TABLE info (kunci TEXT PRIMARY KEY, nilai TEXT);
    """)
    stat = collections.Counter()
    for kitab in KITAB6:
        for rid, arab in src.execute("SELECT id, arab FROM riwayat WHERE kitab_id=? AND tingkat IN ('A','B')", (kitab,)):
            segs = rantai_riwayat(arab)
            if not segs:
                stat["tanpa_rantai"] += 1
                continue
            hasil = dekode(rj, kitab, segs, penulis[kitab])
            rows = []
            for pos, (s, (c, label, margin)) in enumerate(zip(segs, hasil)):
                if s["nabi"]:
                    continue
                stat["sebutan"] += 1
                stat[label or "tanpa_kandidat"] += 1
                rows.append((rid, pos, s["nama_ar"], c, rj.tk[c]["taqrib"] if c else None, label, margin))
            db.executemany("INSERT INTO sebutan VALUES (?,?,?,?,?,?,?)", rows)
    # --- biodata perawi yang teridentifikasi 'pasti' minimal sekali ---------------------------------------------
    r = sqlite3.connect(RIJAL)
    tq = {row[0]: row for row in r.execute("SELECT no, teks, rumuz, tabaqah, wafat, wafat_teks, wafat_ragu, penilaian, tingkat FROM taqrib")}
    tkc = {row[0]: row for row in r.execute("SELECT id, no_cetak, rumuz, kepala FROM tk")}
    db.execute("""CREATE TABLE perawi (id TEXT PRIMARY KEY, taqrib INT, tk_id INT, tk_no_cetak INT, nama TEXT, teks_taqrib TEXT,
                  penilaian TEXT, tingkat INT, tabaqah INT, wafat INT, wafat_ragu INT, wafat_teks TEXT, rumuz TEXT, n_riwayat INT)""")
    pakai = db.execute("SELECT tk_id, count(DISTINCT riwayat_id) FROM sebutan WHERE label='pasti' GROUP BY 1").fetchall()
    rows = []
    for tk_id, n in pakai:
        no = rj.tk[tk_id]["taqrib"]
        t = tq.get(no)
        nama = nama_tampil(t[1]) if t else nama_kepala_tk(tkc[tk_id][3]).strip(" ،")
        rows.append((perawi_id(tk_id, no), no, tk_id, tkc[tk_id][1], nama, t[1] if t else None, t[7] if t else None,
                     t[8] if t else None, t[3] if t else None, t[4] if t else None, t[6] if t else None, t[5] if t else None,
                     t[2] if t else tkc[tk_id][2], n))
    db.executemany("INSERT INTO perawi VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    stat["perawi_teridentifikasi"] = len(rows)
    stat["perawi_dengan_taqrib"] = sum(1 for x in rows if x[1])
    db.executemany("INSERT INTO info VALUES (?,?)", [(k, str(v)) for k, v in {**stat, **rj.stat_graf}.items()])
    db.commit()
    print(json.dumps(stat), file=sys.stderr)


if __name__ == "__main__":
    main()
