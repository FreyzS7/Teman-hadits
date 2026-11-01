#!/usr/bin/env python3
"""UJI INDEPENDEN identifikasi perawi (pipeline/perawi.py) terhadap data Ifta' Sunnah (sunna.alifta.gov.sa):
rantai enam kitab yang setiap posisinya sudah ditetapkan ke satu perawi oleh kurator Ifta', ditautkan ke nomor Taqrib
oleh proyek marwangalaly14/Isnad. Data itu TIDAK diterbitkan ulang dan tidak dipakai untuk membangun situs: hanya
diunduh ke build/ifta/ untuk mengukur kesepakatan.

Cara banding: hanya hadits yang teksnya cocok (2-gram >= 0.5); posisi dipasangkan bila nama di sanad COCOK dengan
entri Taqrib pilihan Ifta' (model nama kita) dan paling dekat urutannya. Ketidaksepakatan = dua orang yang sama-sama
cocok namanya tetapi beda pilihan; sebagian adalah kesalahan data pembanding (lihat docs/11-perawi.md).

Jalankan (sesudah perawi.py):  python3 -I pipeline/uji_perawi_ifta.py
"""
import io, os, urllib.request, zipfile
import json, glob, sqlite3, collections, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm_ar
from nama import urai, cocok
from perawi import Rijal
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "build", "ifta", "data") + "/"
URL = "https://github.com/marwangalaly14/Isnad/releases/latest/download/isnad-data.zip"
if not os.path.exists(D + "people.json"):
    print("unduh", URL, file=sys.stderr)
    zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL, timeout=300).read())).extractall(os.path.join(ROOT, "build", "ifta"))
people = {p['id']: p for p in json.load(open(D + 'people.json'))}
KB = {'bukhari': 'bukhari', 'muslim': 'muslim', 'abudawud': 'abudawud', 'tirmidhi': 'tirmidzi', 'nasai': 'nasai', 'ibnmajah': 'ibnumajah'}
def g2(t):
    w = norm_ar(t).split(); return {w[i] + ' ' + w[i + 1] for i in range(len(w) - 1)}
rj = Rijal()
tq = rj.taqrib
def cocok_tq(m, no):
    t = tq.get(no)
    return bool(t) and cocok(urai(m), t["nama"], t["kata"])
ref = {}
for f in glob.glob(D + 'hadith/*.json'):
    for h in json.load(open(f)):
        if len(h['chains']) == 1:
            ref[f"{KB[h['book']]}:{h['num']}"] = ([people.get(x, {}).get('taqrib') for x in h['chains'][0][::-1][1:]], h['text'])
src = sqlite3.connect(os.path.join(ROOT, 'build', 'teman-hadits.sqlite'))
db = sqlite3.connect(os.path.join(ROOT, 'build', 'perawi.sqlite'))
per = collections.defaultdict(list)
for rid, pos, nama, t, label in db.execute("SELECT riwayat_id, pos, nama_ar, taqrib, label FROM sebutan ORDER BY riwayat_id, pos"):
    per[rid].append((nama, t, label))
st = collections.Counter(); salah = collections.defaultdict(list)
for rid, ours in per.items():
    r = ref.get(rid)
    if r is None: continue
    a = g2(src.execute("SELECT arab FROM riwayat WHERE id=?", (rid,)).fetchone()[0]); b = g2(r[1])
    if not a or len(a & b) / len(a) < 0.5: continue
    st['hadits'] += 1
    dipakai = set()
    for i, (nama, t, label) in enumerate(ours):
        js = [j for j, rt in enumerate(r[0]) if j not in dipakai and rt and cocok_tq(nama, rt)]
        j = min(js, key=lambda j: abs(j - i)) if js else None
        if j is None:
            st[f'{label}_tak_berpasangan'] += 1; continue
        dipakai.add(j); rt = r[0][j]
        if label in ('pasti', 'kuat'):
            if t is None: st[f'{label}_kita_tanpa_taqrib'] += 1
            elif t == rt: st[f'{label}_sama'] += 1
            else: st[f'{label}_beda'] += 1; salah[label].append((rid, nama, t, rt))
        else:
            st[f'{label or "tanpa_kandidat"}_ref_ada'] += 1
for k in sorted(st): print(f'{k:28s} {st[k]}')
for lab in ('pasti', 'kuat'):
    s, b = st[f'{lab}_sama'], st[f'{lab}_beda']
    print(lab, 'kesepakatan', f'{s/(s+b):.4f}' if s + b else '-', 'dari', s + b)
json.dump({'statistik': st, 'beda': salah}, open(os.path.join(ROOT, 'build', 'uji_perawi_ifta.json'), 'w'), ensure_ascii=False)
