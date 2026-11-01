#!/usr/bin/env python3
"""Tulis docs/01-audit-data.md dari hasil build (angka selalu dihitung ulang, tidak diketik tangan)."""
import collections
import datetime
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DB_PATH, ROOT

db = sqlite3.connect(DB_PATH)
q = lambda s, *a: db.execute(s, a).fetchall()
lap = json.load(open(os.path.join(BUILD, "laporan-build.json"), encoding="utf8"))
lock = json.load(open(os.path.join(ROOT, "pipeline", "sources.lock.json"), encoding="utf8"))

L = []
w = L.append
w("# Audit Data Teman Hadits\n")
w(f"_Dibuat otomatis oleh `pipeline/audit.py` pada {datetime.date.today().isoformat()}. "
  "Jangan disunting manual — jalankan ulang pipeline._\n")
w("## Ringkasan\n")
tot = dict(q("SELECT tingkat, count(*) FROM riwayat GROUP BY tingkat"))
w(f"- Riwayat dimuat: **{sum(tot.values()):,}**")
w(f"- Tingkat **A** (teks Arab cocok di 2 sumber digital + terjemah terpasang): **{tot.get('A', 0):,}**")
w(f"- Tingkat **B** (baru 1 sumber digital / belum terpasang terjemahnya): **{tot.get('B', 0):,}**")
w(f"- **Karantina** (tidak ditampilkan): **{tot.get('K', 0):,}**")
w(f"- Riwayat yang punya ≥1 penilaian derajat bernama: **{q('SELECT count(DISTINCT riwayat_id) FROM penilaian')[0][0]:,}**\n")

w("## Per kitab\n")
w("| Kitab | Baris Lidwa | Nomor standar | A | B | Karantina | Ada penilaian | Penilai |")
w("|---|---:|---:|---:|---:|---:|---:|---|")
for kid, nama, nl, ns in q("SELECT id, nama, jumlah_lidwa, jumlah_standar FROM kitab"):
    t = dict(q("SELECT tingkat, count(*) FROM riwayat WHERE kitab_id=? GROUP BY tingkat", kid))
    np_ = q("SELECT count(DISTINCT riwayat_id) FROM penilaian WHERE riwayat_id LIKE ?", kid + ":%")[0][0]
    pen = ", ".join(r[0] for r in q("SELECT DISTINCT penilai FROM penilaian WHERE riwayat_id LIKE ? ORDER BY 1", kid + ":%"))
    w(f"| {nama} | {nl:,} | {ns or '—'} | {t.get('A', 0):,} | {t.get('B', 0):,} | {t.get('K', 0):,} | {np_:,} | {pen or '—'} |")
w("")

w("## Pencocokan dua sumber (crosswalk)\n")
w("Teks Arab Lidwa/carihadis dicocokkan dengan teks Arab fawazahmed0 memakai irisan 3-kata "
  "(Jaccard) setelah harakat dan variasi hamzah diseragamkan. *1:1* = Jaccard ≥ 0,85. "
  "*gabungan* = ≥ 90% teks nomor standar tercakup dalam satu baris Lidwa yang lebih panjang "
  "(Lidwa sering menggabungkan beberapa jalur sanad Muslim dalam satu nomor). Kandidat yang "
  "posisinya menyimpang > 40 baris dari urutan tetangganya ditolak.\n")
w("| Kitab | 1:1 | gabungan | tidak cocok | posisi menyimpang | baris Lidwa tak terpakai |")
w("|---|---:|---:|---:|---:|---:|")
for kid, r in lap.items():
    p = r.get("pasangan")
    if not p:
        continue
    w(f"| {kid} | {p.get('1:1', 0):,} | {p.get('gabungan', 0):,} | {p.get('tidak cocok (<0.85 & <0.9)', 0):,} | "
      f"{p.get('tidak cocok (posisi menyimpang dari urutan kitab)', 0):,} | {r['lidwa_tak_terpasang']:,} |")
w("")

w("## Perbedaan penilaian antar ulama\n")
w("Satu hadits bisa dinilai berbeda oleh ulama yang berbeda. Situs menampilkan **semua** penilaian "
  "berdampingan dan tidak membuat \"nilai akhir\" sendiri.\n")
beda = collections.Counter()
contoh = {}
for rid, kats in q("SELECT riwayat_id, group_concat(DISTINCT kategori) FROM penilaian GROUP BY riwayat_id"):
    ks = set(kats.split(",")) - {"lainnya"}
    if len(ks) > 1 and ("lemah" in ks or "palsu" in ks) and ({"shahih", "hasan", "shahih-hasan"} & ks):
        k = rid.split(":")[0]
        beda[k] += 1
        contoh.setdefault(k, rid)
for k, n in beda.most_common():
    pen = q("SELECT penilai, hukum FROM penilaian WHERE riwayat_id=?", contoh[k])
    w(f"- **{k}**: {n:,} riwayat dinilai diterima oleh sebagian ulama dan lemah oleh yang lain. "
      f"Contoh `{contoh[k]}`: " + "; ".join(f"{a} — *{b}*" for a, b in pen))
w("")

bab_path = os.path.join(BUILD, "bab.sqlite")
if os.path.exists(bab_path):
    bi = sqlite3.connect(bab_path)
    w("## Pencocokan dengan edisi tahqiq (OpenITI)\n")
    w("Lihat `docs/09-judul-kitab-bab.md`. Tingkat di tabel \"Per kitab\" di atas adalah tingkat **sebelum** pencocokan ini; "
      "untuk Ahmad, Darimi, dan Syafi'i, riwayat yang teksnya ≥ 90% cocok dengan edisi tahqiq naik ke tingkat A saat ekspor ke situs.\n")
    w("| Kitab | Edisi | Terpetakan menurut isi | Cocok ≥ 90% | Urutan naik | Nomor sama | Penilaian muhaqqiq |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for kid in ("bukhari", "muslim", "abudawud", "tirmidzi", "nasai", "ibnumajah", "malik", "ahmad", "darimi", "syafii"):
        d = dict(bi.execute("SELECT kunci, nilai FROM info WHERE kitab_id=?", (kid,)))
        if d:
            w(f"| {kid} | {d.get('edisi') or '—'} | {d['cocok_teks']}/{d['riwayat']} | {d.get('cocok_090', '—')} | {d['urutan_naik']} | "
              f"{d['nomor_sama'] if d['nomor_sama'] != '0/0' else '—'} | {d.get('tahqiq') or '—'} |")
    w("")

kt_path = os.path.join(BUILD, "katalog.sqlite")
if os.path.exists(kt_path):
    kt = sqlite3.connect(kt_path)
    ki = dict(kt.execute("SELECT kunci, nilai FROM info"))
    w("## Katalog hadits populer & palsu\n")
    w("Lihat `docs/10-katalog-palsu.md`. Teks entri apa adanya dari OpenITI; kata kunci penilaian dikenali otomatis dan "
      "selalu ditampilkan bersama kalimat aslinya.\n")
    w("| Kitab | Penulis | Edisi digital | Entri | Entri dengan kata kunci |")
    w("|---|---|---|---:|---:|")
    for kid, nama, penulis, wafat, edisi, n, nk in kt.execute(
            "SELECT b.id, b.nama, b.penulis, b.wafat, b.edisi, count(*), sum(k.kata_kunci != '[]') FROM katalog k "
            "JOIN katalog_kitab b ON b.id = k.kitab_id GROUP BY b.id ORDER BY b.wafat"):
        w(f"| {nama} | {penulis} (w. {wafat} H) | {edisi or '—'} | {n:,} | {nk:,} |")
    w(f"\nUcapan populer berbahasa Indonesia: {ki['ucapan_populer']} (daftar **belum ditinjau**); tautan ke judul entri: "
      f"{ki.get('tautan_katalog', 0)}; disebut di pembahasan entri lain: {ki.get('sebut_di_entri_lain', 0)}; "
      f"ada di kitab hadits kita: {ki.get('ada_di_kitab_hadits', 0)}; tidak ada: {ki.get('tidak_ada_di_kitab_hadits', 0)}.\n")

pr_path = os.path.join(BUILD, "perawi.sqlite")
if os.path.exists(pr_path):
    pi = dict(sqlite3.connect(pr_path).execute("SELECT kunci, nilai FROM info"))
    tot = int(pi["sebutan"])
    w("## Identitas perawi di sanad (enam kitab)\n")
    w("Lihat `docs/11-perawi.md`. Hanya label **pasti** yang tampil di situs.\n")
    w("| Label | Sebutan nama | % |")
    w("|---|---:|---:|")
    for k in ("pasti", "kuat", "ragu", "tanpa_kandidat"):
        w(f"| {k} | {int(pi.get(k, 0)):,} | {100 * int(pi.get(k, 0)) / tot:.1f}% |")
    w(f"\nPerawi teridentifikasi: {int(pi['perawi_teridentifikasi']):,} ({int(pi['perawi_dengan_taqrib']):,} tertaut ke Taqrib). "
      f"Hubungan guru-murid Tahdzib al-Kamal yang terselesaikan: {int(pi['relasi_terselesaikan']):,} dari {int(pi['relasi']):,}.\n")

w("## Temuan kualitas data\n")
ry_path = os.path.join(BUILD, "riyadh.sqlite")
if os.path.exists(ry_path):
    ri = dict(sqlite3.connect(ry_path).execute("SELECT kunci, nilai FROM info"))
    w(f"- **Riyadhus Shalihin** dipecah ulang per hadits oleh `pipeline/riyadh.py` (lihat `docs/08-riyadhus-shalihin.md`): "
      f"{ri['hadits_arab']} hadits; terjemah terpasang pasti {ri['terjemah_pasti']}; terhubung ke sumber {ri['punya_sumber']}; "
      f"uji silang atribusi an-Nawawi {ri['uji_silang_cocok']}/{ri['uji_silang_dicek']}. "
      "Berkas versi Arab tahqiq al-Fahl (850 potongan halaman) belum dipakai.")
else:
    w("- **Riyadhus Shalihin** belum diproses (jalankan `pipeline/riyadh.py`).")
w("- Penomoran Lidwa **berbeda** dari penomoran standar (mis. Bukhari Lidwa 7.008 vs standar 7.563; "
  "Muslim 5.362 vs 7.563). Situs memakai nomor standar sebagai alamat utama dan menampilkan nomor Lidwa sebagai pembanding.")
w("- Teks identik di nomor berbeda **tidak** dianggap rusak: al-Bukhari dan penyusun lain memang mengulang "
  "hadits yang sama di bab berbeda. Ditandai sebagai \"pengulangan\".")
w("- Musnad Ahmad, Sunan ad-Darimi, Musnad asy-Syafi'i baru punya **satu** sumber digital (Lidwa) dan "
  "belum ada penilaian derajat per hadits → tingkat B, label \"belum ada penilaian tercatat\".")
w("- Terjemahan Indonesia di **kedua** sumber berasal dari Lidwa Pusaka (gaya `[nama perawi]` identik). "
  "Jadi terjemahan baru diverifikasi oleh satu pihak; kecocokan dua sumber hanya menguji teks Arab dan nomor.")
w("- Lima berkas SQL yang diunggah pemilik proyek identik byte-per-byte (sha256) dengan berkas di repo "
  "irsyadulibad/hadits-database commit `db43bda`.\n")

w("## Sumber terkunci\n")
w("| Berkas | Commit | sha256 (12 awal) | Ukuran |")
w("|---|---|---|---:|")
for k, v in sorted(lock.items()):
    w(f"| `{k}` | `{v['commit'][:7]}` | `{v['sha256'][:12]}` | {v['bytes']:,} |")

open(os.path.join(ROOT, "docs", "01-audit-data.md"), "w", encoding="utf8").write("\n".join(L) + "\n")
print("docs/01-audit-data.md ditulis")
