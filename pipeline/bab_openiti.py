#!/usr/bin/env python3
"""Judul kitab & bab berbahasa Arab dari teks OpenITI, dipetakan ke riwayat kita MENURUT ISI.

Masukan : sources/openiti-*/... (lihat sources.json), build/teman-hadits.sqlite
Keluaran: build/bab.sqlite
  riwayat_bab(riwayat_id, kitab_ar, bab_ar, skor, cara, no_openiti)
  kitab_nama(kitab_id, bab_no, nama_ar, setuju, total)   -- nama Arab untuk "kitab" (section) fawazahmed0
  info(kitab_id, kunci, nilai)

Cara:
  1. Urai berkas OpenITI: setiap baris "### " diklasifikasi menjadi kitab / bab / penanda hadits / halaman.
     Teks di antara penanda menjadi "blok", membawa judul kitab & bab terakhir.
  2. Setiap riwayat kita dicocokkan ke blok yang paling memuat teksnya (2-gram berbobot IDF, seperti
     takhrij). Cocok bila >= 70% bobot 2-gram riwayat ada di blok. Nomor penomoran tidak dipakai untuk
     mencocokkan, hanya untuk MENGUJI hasilnya.
  3. Riwayat yang tidak cocok mendapat judul dari tetangganya hanya bila riwayat sebelum & sesudahnya
     berada di bab yang sama (cara = "urutan").
  4. Nama Arab tiap "kitab" fawazahmed0 = judul kitab OpenITI yang paling banyak dimiliki riwayat di dalamnya.

Uji (dilaporkan, juga di test_bab.py):
  - urutan: blok yang cocok untuk riwayat berurutan harus naik;
  - nomor: bila blok OpenITI bernomor, nomornya sama dengan nomor standar riwayat;
  - kesepakatan kitab: berapa % riwayat dalam satu kitab fawazahmed0 sepakat pada satu judul kitab OpenITI.

Jalankan:  python3 pipeline/bab_openiti.py
"""
import collections
import json
import math
import os
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, SRC, norm_ar
from hadeethenc import grams

OUT = os.path.join(BUILD, "bab.sqlite")
BERKAS = {
    "bukhari": "openiti-0275AH/0256Bukhari.Sahih.Shamela0001681-ara1",
    "muslim": "openiti-0275AH/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown",
    "abudawud": "openiti-0275AH/0275AbuDawudSijistani.Sunan.Shamela0001726-ara1",
    "ibnumajah": "openiti-0275AH/0273IbnMaja.Sunan.Shamela0001198-ara1",
    "tirmidzi": "openiti-0300AH/0279Tirmidhi.Sunan.Shamela0007895-ara2",
    "nasai": "openiti-0325AH/0303Nasai.SunanSughra.Shamela0000829-ara1",
    "malik": "openiti-0200AH/0179MalikIbnAnas.Muwatta.Shamela0001699-ara1.completed",
    # Kitab yang di sumber kita hanya punya satu sumber digital (Lidwa): OpenITI = sumber kedua + nomor edisi tahqiq.
    "ahmad": "openiti-0250AH/0241IbnHanbal.Musnad.Shamela0025794-ara1.mARkdown",      # ar-Risalah (al-Arna'uth dkk.)
    "darimi": "openiti-0275AH/0255CabdAllahDarimi.Sunan.Shamela0021795-ara3",        # Dar al-Mughni (Husain Salim Asad)
    "syafii": "openiti-0225AH/0204Shafici.Musnad.Shamela0009615-ara1",              # Ghiras (Mahir Yasin al-Fahl)
}
EDISI = {"ahmad": "ar-Risalah (tahqiq Syu'aib al-Arna'uth dkk.)", "darimi": "Dar al-Mughni (tahqiq Husain Salim Asad)",
         "syafii": "Ghiras (tahqiq Mahir Yasin al-Fahl)"}
LIDWA_SAJA = {"ahmad", "darimi", "syafii"}
# Musnad Ahmad: judul tingkat 1–2 ("مسند الصحابة بعد العشرة") = kelompok besar; tingkat 3+ ("مسند عمر بن الخطاب") = bab.
TINGKAT_KITAB = {"ahmad": 2}
AMBANG = 0.7
_GLOSARIUM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "glosarium_kitab.json"), encoding="utf8"))
_GLOS = {norm_ar(k): v for k, v in _GLOSARIUM["nama"].items()}


def nama_indonesia(kitab_ar):
    """'كتاب البيوع' -> 'Kitab Jual Beli'; 'أبواب الطهارة عن رسول الله…' -> 'Bab-bab Thaharah (Bersuci)'.
    None bila tidak ada di glosarium (glosarium disusun Teman Hadits, belum ditinjau)."""
    if not kitab_ar:
        return None
    n = norm_ar(kitab_ar)
    awal = "Kitab " if re.sub(r"^و?من\s+", "", n).startswith("كتاب") else "Bab-bab " if n.startswith("ابواب") else ""
    n = re.sub(r"^و?من\s+", "", n)
    inti = re.sub(r"^(كتاب|ابواب)\s+", "", n)
    inti = re.sub(r"\s*عن رسول الله.*$", "", inti).strip()
    v = _GLOS.get(inti)
    return (awal + v) if v else None
_ANGKA_TIMUR = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NOMOR_SAJA = re.compile(r"^\s*\(?\s*([0-9٠-٩]+)\s*\)?\s*[-–]?\s*$")
_AWALAN_NOMOR = re.compile(r"^\s*(?:\(?\s*[0-9٠-٩]+\s*\)?\s*[-–]?\s*)+")
_SAMPAH = re.compile(r"ms\d+|PageV\d+P\d+|\[ص:\s*\d+\]")


def bersihkan_judul(t):
    t = _SAMPAH.sub(" ", t)
    t = re.sub(r"\(\s*\d+\s*\)", " ", t)            # penanda catatan kaki "(1)" di judul
    t = re.sub(r"[\"“”]+", "", t)
    t = re.sub(r"</?[a-zA-Z][^>]*>", " ", t)          # sisa markup HTML di teks digital ("</span>")
    t = re.sub(r"\s*«\s*$", "", t)                   # tanda kutip pembuka yang tertinggal di akhir judul
    return re.sub(r"\s+", " ", t).strip(" :.-–،")


# Judul tingkat kitab. "أبواب" hanya tingkat kitab di Jami' at-Tirmidzi; di Abu Dawud ia sub-bagian
# di dalam kitab (mis. "أبواب قيام الليل" di dalam كتاب الصلاة), jadi tidak boleh menimpa nama kitab.
AWALAN_KITAB = {"tirmidzi": ("كتاب", "ابواب")}


_AWAL_SANAD = re.compile(r"^(?:و)?(?:حدثنا|حدثني|اخبرنا|اخبرني|انبانا|سمعت|قال|وقال|ح|عن|حدثنيه|حدثناه|ثنا|نا)\b")


def urai(path, kid=None):
    """Kembalikan daftar blok: {kitab, bab, no, teks, tahqiq}."""
    awalan = AWALAN_KITAB.get(kid, ("كتاب",))
    tingkat_kitab = TINGKAT_KITAB.get(kid)
    blok, kitab, bab, no, teks = [], None, None, None, []
    if kid == "darimi":
        kitab = "المقدمة"     # Sunan ad-Darimi dibuka dengan Muqaddimah panjang sebelum كتاب الطهارة (tanpa judul di berkas)
    tahqiq, mode_tahqiq = [], False
    # "### | باب" lalu judulnya di baris "# ..." berikutnya (gaya teks digital Bukhari). Bab tanpa judul sungguhan
    # langsung diikuti sanad ("حدثنا ..."), jadi baris pertama yang BUKAN awal sanad adalah judul bab itu.
    tunggu_judul = False

    def tutup():
        if teks:
            blok.append({"kitab": kitab, "bab": bab, "no": no, "teks": " ".join(teks), "tahqiq": " ".join(tahqiq) or None})

    for baris in open(path, encoding="utf8"):
        baris = baris.rstrip("\n")
        if baris.startswith("#META#") or baris.startswith("######"):
            continue
        if baris.startswith("### "):
            m = re.match(r"^### (\|+|\$)\s*(.*)$", baris)
            if not m:
                continue
            isi = m.group(2)
            if re.search(r"\[ص\s*:", isi) and len(norm_ar(re.sub(r"\[ص\s*:[^\]]*\]", " ", _SAMPAH.sub(" ", isi)))) < 5:
                continue                                  # penanda halaman cetak: bukan batas hadits/bab
            if "تعليق المحقق" in isi or re.search(r"\[\s*تعليق", isi):   # Darimi (Asad): penilaian muhaqqiq; Bukhari dll.: "[تعليق مصطفى البغا]" = komentar editor, BUKAN judul bab
                mode_tahqiq = True
                continue
            mode_tahqiq = False
            polos = norm_ar(_AWALAN_NOMOR.sub("", isi))
            mn = _NOMOR_SAJA.match(isi)
            if mn:                                         # "### | 12 - " = awal hadits bernomor
                tunggu_judul = False
                tutup()
                teks, tahqiq, no = [], [], int(mn.group(1).translate(_ANGKA_TIMUR))
                continue
            if tingkat_kitab and m.group(1) != "$":       # judul bertingkat (Musnad Ahmad)
                tutup()
                teks, tahqiq, no = [], [], None
                if len(m.group(1)) <= tingkat_kitab:
                    kitab, bab = bersihkan_judul(isi), None
                else:
                    bab = bersihkan_judul(isi)
                continue
            # "ومن كتاب الزكاة" / "من كتاب المناسك" (gaya ad-Darimi) juga judul kitab
            inti_polos = re.sub(r"^و?من\s+", "", polos)
            if inti_polos.startswith(awalan) or polos == "بد الوحي" or polos.startswith("مقدمه الامام"):   # hamzah sudah dibuang norm_ar
                tutup()
                teks, tahqiq, no = [], [], None
                kitab, bab = bersihkan_judul(_AWALAN_NOMOR.sub("", isi)), None
                continue
            if m.group(1) == "$" and len(polos.split()) > 12:   # Muslim: "### $ وحدثنا ..." = awal hadits
                tutup()
                teks, tahqiq, no = [isi], [], None
                continue
            if len(polos.split()) <= 60 and polos:         # judul bab (dengan/tanpa kata "باب")
                tutup()
                teks, tahqiq, no = [], [], None
                bab = bersihkan_judul(_AWALAN_NOMOR.sub("", isi))
                tunggu_judul = kid == "bukhari" and norm_ar(bab) == "باب"
                continue
            teks.append(isi)
        elif baris.startswith("# ") or baris.startswith("~~"):
            isi = baris.lstrip("#~ ")
            if "PageV" in isi and len(_SAMPAH.sub("", isi).strip()) < 3:
                continue
            if mode_tahqiq:
                tahqiq.append(_SAMPAH.sub(" ", isi).strip())
                continue
            if (kid == "bukhari" and baris.startswith("# ") and kitab and "تفسير" in kitab
                    and re.match(r"^سوره\s", norm_ar(_SAMPAH.sub(" ", isi))) and len(norm_ar(isi).split()) <= 14):
                # Kitab at-Tafsir: judul surah ditulis sebagai baris biasa ("# سورة إذا جاء نصر الله") dan bab tanpa
                # judul sesudahnya tidak ada di teks digital. Tanpa ini, hadits surah baru mewarisi bab surah sebelumnya.
                tutup()
                teks, tahqiq, no = [], [], None
                bab = bersihkan_judul(_SAMPAH.sub(" ", isi))
                tunggu_judul = False
                continue
            if tunggu_judul and baris.startswith("# "):
                tunggu_judul = False
                kalimat = norm_ar(_SAMPAH.sub(" ", isi))
                if kalimat and not _AWAL_SANAD.match(kalimat) and len(kalimat.split()) <= 60:
                    bab = bersihkan_judul("باب " + _SAMPAH.sub(" ", isi))
                    continue
            mt = re.match(r"^#\s+(\d+)\s+-\s+(.*)$", baris) if kid == "ahmad" else None
            if mt:                                         # Musnad Ahmad: "# 12 - حدثنا ..." = awal hadits bernomor
                tutup()
                teks, tahqiq, no = [mt.group(2)], [], int(mt.group(1))
                continue
            teks.append(isi)
    tutup()
    return blok


def petakan(kid, blok, riwayat):
    """riwayat: list (id, arab, no_standar, bab_no) urut. Kembalikan dict id -> (i_blok, skor)."""
    gb = [grams(norm_ar(_SAMPAH.sub(" ", b["teks"]))) for b in blok]
    gr = {rid: grams(norm_ar(ar)) for rid, ar, _, _ in riwayat}
    df = collections.Counter()
    for g in gr.values():
        df.update(g)
    N = max(1, len(gr))
    post = collections.defaultdict(list)
    for i, g in enumerate(gb):
        for x in g:
            if df.get(x, 0) <= 40:
                post[x].append(i)
    kandidat = {}
    for rid, _, _, _ in riwayat:
        g = gr[rid]
        if len(g) < 4:
            continue
        bobot = {x: math.log(N / (1 + df[x])) + 0.1 for x in g}
        total = sum(bobot.values())
        cand = collections.Counter()
        for x in sorted(g, key=lambda x: df[x])[:20]:
            for i in post.get(x, ()):
                cand[i] += 1
        skor = [(sum(bobot[x] for x in g & gb[i]) / total, i) for i, _ in cand.most_common(30)]
        skor = [(s, i) for s, i in skor if s >= AMBANG]
        if skor:
            top = max(s for s, _ in skor)
            # semua blok yang hampir sama baiknya: teks yang diulang penyusun (umum di al-Bukhari)
            kandidat[rid] = [(i, s) for s, i in skor if s >= top - 0.03]
    # Pilih kandidat yang paling dekat dengan posisi tetangga yang tidak ambigu (urutan kitab).
    urut = [rid for rid, *_ in riwayat if rid in kandidat]
    pasti = [(k, kandidat[rid][0][0]) for k, rid in enumerate(urut) if len(kandidat[rid]) == 1]
    import bisect
    kunci = [k for k, _ in pasti]
    hasil = {}
    for k, rid in enumerate(urut):
        c = kandidat[rid]
        if len(c) == 1:
            hasil[rid] = (c[0][0], round(c[0][1], 3))
            continue
        j = bisect.bisect_left(kunci, k)
        tetangga = [pasti[x][1] for x in range(max(0, j - 3), min(len(pasti), j + 3))]
        harapan = sorted(tetangga)[len(tetangga) // 2] if tetangga else c[0][0]
        i, s = min(c, key=lambda x: (abs(x[0] - harapan), -x[1]))
        hasil[rid] = (i, round(s, 3))
    return hasil


_KOREKSI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "koreksi_bab.json"), encoding="utf8"))["koreksi"]


def koreksi_cetak(rid):
    """Koreksi judul bab yang sudah diverifikasi terhadap kitab cetak (pipeline/koreksi_bab.json)."""
    kid, _, no = rid.partition(":")
    if not no.isdigit():
        return None
    return next((k for k in _KOREKSI if k["kitab_id"] == kid and k["dari"] <= int(no) <= k["sampai"]), None)


def main():
    t0 = time.time()
    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
    CREATE TABLE riwayat_bab (riwayat_id TEXT PRIMARY KEY, kitab_ar TEXT, bab_ar TEXT, skor REAL, cara TEXT, no_openiti INT,
      kitab_nama_id TEXT, tahqiq TEXT, urut_openiti INT);
    CREATE TABLE kitab_nama (kitab_id TEXT, bab_no INT, nama_ar TEXT, setuju INT, total INT, nama_id TEXT, PRIMARY KEY (kitab_id, bab_no));
    CREATE TABLE info (kitab_id TEXT, kunci TEXT, nilai TEXT);
    """)
    for kid, rel in BERKAS.items():
        blok = urai(os.path.join(SRC, rel), kid)
        riwayat = src.execute(
            "SELECT id, arab, no_standar, bab_no FROM riwayat WHERE kitab_id=? AND tingkat IN ('A','B') "
            "ORDER BY COALESCE(CAST(no_standar AS REAL), no_lidwa)", (kid,)).fetchall()
        peta = petakan(kid, blok, riwayat)
        # isi celah dari tetangga bila keduanya di bab yang sama
        urut = [rid for rid, *_ in riwayat]
        cara = {rid: "teks" for rid in peta}
        akhir = dict(peta)
        for k, rid in enumerate(urut):
            if rid in akhir or kid == "syafii":   # Syafi'i: susunan edisi al-Fahl berbeda dari Lidwa, tetangga tak bermakna
                continue
            a = next((akhir[urut[j]] for j in range(k - 1, -1, -1) if urut[j] in akhir), None)
            b = next((akhir[urut[j]] for j in range(k + 1, len(urut)) if urut[j] in akhir), None)
            if a and b and blok[a[0]]["bab"] == blok[b[0]]["bab"] and blok[a[0]]["kitab"] == blok[b[0]]["kitab"]:
                akhir[rid], cara[rid] = (a[0], 0.0), "urutan"
        for rid, (i, s) in akhir.items():
            b = blok[i]
            # Penilaian muhaqqiq hanya dipasang bila teks riwayat jelas ada di blok edisi itu (>= 0.9)
            tq = b.get("tahqiq") if (cara[rid] == "teks" and s >= 0.9) else None
            bab_ar, cr = b["bab"], cara[rid]
            k = koreksi_cetak(rid)
            if k:
                bab_ar, cr = k["bab_ar"], "koreksi-cetak"
            db.execute("INSERT INTO riwayat_bab VALUES (?,?,?,?,?,?,?,?,?)",
                       (rid, b["kitab"], bab_ar, s, cr, b["no"], nama_indonesia(b["kitab"]), tq, i))

        # uji: urutan & nomor
        idx = [peta[rid][0] for rid in urut if rid in peta]
        naik = sum(1 for x, y in zip(idx, idx[1:]) if y >= x)
        nomor_dicek = nomor_sama = 0
        no_std = {rid: nos for rid, _, nos, _ in riwayat}
        for rid, (i, _) in peta.items():
            if blok[i]["no"] is not None and no_std[rid] and re.fullmatch(r"\d+", str(no_std[rid])):
                nomor_dicek += 1
                nomor_sama += blok[i]["no"] == int(no_std[rid])
        # nama Arab per "kitab" fawazahmed0 (bab_no di data kita) = judul kitab OpenITI terbanyak
        per_bagian = collections.defaultdict(collections.Counter)
        for rid, _, _, bno in riwayat:
            if rid in akhir and blok[akhir[rid][0]]["kitab"]:
                per_bagian[bno][blok[akhir[rid][0]]["kitab"]] += 1
        setuju = total = 0
        for bno, c in (per_bagian.items() if kid not in LIDWA_SAJA else []):
            nama, n = c.most_common(1)[0]
            jml = sum(c.values())
            setuju += n
            total += jml
            # Nama hanya bila mayoritas jelas (>= 60%). Bagian "0" Muslim di fawazahmed0 misalnya adalah
            # tampungan riwayat tanpa nomor kitab yang tersebar di seluruh kitab — tidak punya satu nama.
            jelas = n / jml >= 0.6
            db.execute("INSERT INTO kitab_nama VALUES (?,?,?,?,?,?)",
                       (kid, bno, nama if jelas else None, n, jml, nama_indonesia(nama) if jelas else None))
        info = {"blok": len(blok), "riwayat": len(riwayat), "cocok_teks": len(peta),
                "dari_urutan": sum(1 for c in cara.values() if c == "urutan"),
                "urutan_naik": f"{naik}/{max(1, len(idx) - 1)}", "nomor_sama": f"{nomor_sama}/{nomor_dicek}",
                "cocok_090": sum(1 for _, sk in peta.values() if sk >= 0.9), "edisi": EDISI.get(kid, ""),
                "tahqiq": sum(1 for rid, (i, sk) in akhir.items() if cara[rid] == "teks" and sk >= 0.9 and blok[i].get("tahqiq")),
                "kesepakatan_kitab": f"{setuju}/{total}"}
        db.executemany("INSERT INTO info VALUES (?,?,?)", [(kid, k, str(v)) for k, v in info.items()])
        db.commit()
        print(f"{kid:10s} blok {len(blok):5d} | cocok {len(peta):5d}/{len(riwayat)} (+{info['dari_urutan']} urutan) | "
              f"urutan naik {info['urutan_naik']} | nomor sama {info['nomor_sama']} | kitab sepakat {info['kesepakatan_kitab']} "
              f"({time.time() - t0:.0f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
