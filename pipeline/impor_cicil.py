#!/usr/bin/env python3
"""Impor bertahap ke D1 online: tulis hanya baris yang BERUBAH sejak impor terakhir, dibagi per hari.

Paket gratis D1 hanya mengizinkan 100.000 baris ditulis per hari (baris tabel + entri indeks + baris bayangan FTS);
impor penuh menulis ±564 ribu. Pembaruan data biasanya hanya mengubah sebagian kecil baris (mis. perapian terjemah
mengubah ±2.800 riwayat), jadi cukup ditulis selisihnya.

Bahan: dua CERMIN (build/d1-cermin.sqlite, dibuat export_d1.py): yang terakhir diimpor (site/.terbit/cermin.sqlite) dan
yang baru. Cermin memuat persis baris yang dikirim ke D1, termasuk isi tabel FTS yang di D1 tidak bisa dibaca kembali
(tabel FTS tanpa konten hanya bisa dihapus dengan menyebut nilai lamanya).

  python3 pipeline/impor_cicil.py rencana LAMA.sqlite BARU.sqlite FOLDER [--batas 70000]
     -> FOLDER/001.sql, 002.sql, ... (tiap berkas <= batas perkiraan tulis) dan FOLDER/rencana.json
     kode keluar 0 = rencana dibuat (bisa 0 berkas bila sama), 2 = skema berubah (perlu impor penuh)

Satuan kerja tidak pernah dipecah ke dua hari: hapus + sisip satu baris (atau satu tabel tanpa kunci) selalu di
berkas yang sama, jadi tidak ada baris yang hilang semalaman. Perkiraan tulis: (1 + jumlah indeks) per baris yang
dihapus atau disisipkan; FTS 10 per baris (diukur 8,5 dengan SQLite lokal: 100 baris hapus+sisip = 850 tulisan).
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_d1 import MAKS_BARIS, MAKS_PERNYATAAN, sql_val  # noqa: E402

BATAS = 70_000          # sisakan ruang di bawah 100.000/hari untuk catatan kueri & cadangan perkiraan
TULIS_FTS = 10


def info_tabel(skema_sql):
    """{tabel: (kolom_kunci atau None, biaya_per_baris, fts?)} dari skema D1 yang sebenarnya."""
    m = sqlite3.connect(":memory:")
    m.executescript(skema_sql)
    hasil = {}
    for nama, sql in m.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        if sql and sql.upper().startswith("CREATE VIRTUAL TABLE"):
            hasil[nama] = (["rowid"], TULIS_FTS, True)
            continue
        if any(nama.startswith(v + "_") for v, (_, _, fts) in hasil.items() if fts):
            continue                                            # tabel bayangan FTS
        kunci = [r[1] for r in sorted(m.execute(f'PRAGMA table_info("{nama}")'), key=lambda r: r[5]) if r[5] > 0]
        n_idx = len(m.execute(f'PRAGMA index_list("{nama}")').fetchall())
        hasil[nama] = (kunci or None, 1 + n_idx, False)
    return {k: v for k, v in hasil.items() if not any(k.startswith(f + "_") and hasil[f][2] for f in hasil if f != k)}


def kolom(db, skema, tabel):
    return [r[1] for r in db.execute(f'PRAGMA {skema}.table_info("{tabel}")')]


class Berkas:
    def __init__(self, folder, batas):
        self.folder, self.batas, self.daftar, self.buf, self.tulis, self.ringkas = folder, batas, [], [], 0, {}

    def satuan(self, biaya, pernyataan, tabel, n):
        if biaya > self.batas:
            raise SystemExit(f"satu satuan kerja ({tabel}) butuh ±{biaya} tulisan, lebih dari batas harian {self.batas}")
        if self.tulis + biaya > self.batas:
            self.tutup()
        self.buf.extend(pernyataan)
        self.tulis += biaya
        self.ringkas[tabel] = self.ringkas.get(tabel, 0) + n

    def tutup(self):
        if not self.buf:
            return
        nama = f"{len(self.daftar) + 1:03d}.sql"
        with open(os.path.join(self.folder, nama), "w", encoding="utf8") as f:
            f.write("".join(self.buf))
        self.daftar.append({"berkas": nama, "tulis": self.tulis, "baris": self.ringkas})
        self.buf, self.tulis, self.ringkas = [], 0, {}


def sisip(tabel, kol, baris, fts_hapus=False):
    """Pernyataan INSERT majemuk dalam batas panjang D1. fts_hapus: perintah 'delete' FTS5 dengan nilai lama."""
    kepala = (f"INSERT INTO {tabel} ({tabel}, {', '.join(kol)}) VALUES " if fts_hapus
              else f"INSERT INTO {tabel} ({', '.join(kol)}) VALUES ")
    keluar, buf, pjg = [], [], len(kepala)
    for b in baris:
        v = "(" + ("'delete'," if fts_hapus else "") + ",".join(sql_val(x) for x in b) + ")"
        if buf and (pjg + len(v.encode("utf8")) + 2 > MAKS_PERNYATAAN or len(buf) >= MAKS_BARIS):
            keluar.append(kepala + ",".join(buf) + ";\n")
            buf, pjg = [], len(kepala)
        buf.append(v)
        pjg += len(v.encode("utf8")) + 1
    if buf:
        keluar.append(kepala + ",".join(buf) + ";\n")
    return keluar


def hapus(tabel, kunci, nilai_kunci):
    if len(kunci) == 1:
        return [f"DELETE FROM {tabel} WHERE {kunci[0]} IN ({','.join(sql_val(k[0]) for k in nilai_kunci[i:i + 400])});\n"
                for i in range(0, len(nilai_kunci), 400)]
    return [f"DELETE FROM {tabel} WHERE " + " AND ".join(f"{c} = {sql_val(v)}" for c, v in zip(kunci, k)) + ";\n"
            for k in nilai_kunci]


def rencana(lama, baru, folder, batas=BATAS):
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        if f.endswith(".sql") or f == "rencana.json":
            os.remove(os.path.join(folder, f))
    db = sqlite3.connect(baru)
    db.execute("ATTACH DATABASE ? AS lama", (lama,))
    sk_baru = db.execute("SELECT sql FROM main._skema").fetchone()[0]
    sk_lama = db.execute("SELECT sql FROM lama._skema").fetchone()
    if not sk_lama or sk_lama[0] != sk_baru:
        print("Skema berubah sejak impor terakhir: impor bertahap tidak bisa dipakai, perlu impor penuh.", file=sys.stderr)
        return 2
    tabel = info_tabel(sk_baru)
    ada_lama = {r[0] for r in db.execute("SELECT name FROM lama.sqlite_master WHERE type='table'")}
    out = Berkas(folder, batas)
    for t, (kunci, biaya, fts) in tabel.items():
        kb = kolom(db, "main", t)
        if not kb and t not in ada_lama:
            continue
        if kb != kolom(db, "lama", t):
            print(f"Kolom tabel {t} berubah: perlu impor penuh.", file=sys.stderr)
            return 2
        daftar = ", ".join(f'"{c}"' for c in kb)
        if kunci is None:
            beda = db.execute(f'SELECT EXISTS (SELECT {daftar} FROM main."{t}" EXCEPT SELECT {daftar} FROM lama."{t}") '
                              f'OR EXISTS (SELECT {daftar} FROM lama."{t}" EXCEPT SELECT {daftar} FROM main."{t}")').fetchone()[0]
            if beda:   # tabel tanpa kunci: ganti seluruh isinya dalam satu satuan kerja
                n_lama = db.execute(f'SELECT count(*) FROM lama."{t}"').fetchone()[0]
                rows = db.execute(f'SELECT {daftar} FROM main."{t}"').fetchall()
                out.satuan((n_lama + len(rows)) * biaya, [f"DELETE FROM {t};\n"] + sisip(t, kb, rows), t, len(rows))
            continue
        kk = ", ".join(f'"{c}"' for c in kunci)
        ubah = [tuple(r) for r in db.execute(
            f'SELECT {kk} FROM (SELECT {daftar} FROM main."{t}" EXCEPT SELECT {daftar} FROM lama."{t}") '
            f'UNION SELECT {kk} FROM (SELECT {kk} FROM lama."{t}" EXCEPT SELECT {kk} FROM main."{t}")')]
        if not ubah:
            continue
        pos = [kb.index(c) for c in kunci]

        def ambil(skema):
            return {tuple(r[i] for i in pos): r for r in db.execute(
                f'SELECT {daftar} FROM {skema}."{t}" WHERE ({kk}) IN (SELECT {kk} FROM temp.tmp_kunci)')}
        # kunci sementara untuk JOIN (kunci majemuk didukung)
        db.execute("DROP TABLE IF EXISTS temp.tmp_kunci")
        db.execute(f"CREATE TEMP TABLE tmp_kunci ({kk})")
        db.executemany(f"INSERT INTO temp.tmp_kunci VALUES ({','.join('?' * len(kunci))})", ubah)
        lama_r, baru_r = ambil("lama"), ambil("main")
        # satuan kerja: sekelompok kunci (hapus lama + sisip baru dalam satu berkas)
        g = max(1, min(200, batas // (2 * biaya)))   # kunci per satuan: hapus+sisip satu kelompok muat dalam batas
        for i in range(0, len(ubah), g):
            ks = ubah[i:i + g]
            ada_l = [lama_r[k] for k in ks if k in lama_r]
            ada_b = [baru_r[k] for k in ks if k in baru_r]
            if fts:
                pernyataan = (sisip(t, kb, ada_l, fts_hapus=True) if ada_l else []) + (sisip(t, kb, ada_b) if ada_b else [])
            else:
                pernyataan = (hapus(t, kunci, [k for k in ks if k in lama_r]) if ada_l else []) + (sisip(t, kb, ada_b) if ada_b else [])
            out.satuan((len(ada_l) + len(ada_b)) * biaya, pernyataan, t, len(ks))
    out.tutup()
    ringkasan = {"berkas": out.daftar, "total_tulis": sum(b["tulis"] for b in out.daftar), "batas": batas}
    with open(os.path.join(folder, "rencana.json"), "w", encoding="utf8") as f:
        json.dump(ringkasan, f, ensure_ascii=False, indent=1)
    titik = lambda n: f"{n:,}".replace(",", ".")
    print(f"{len(out.daftar)} cicilan, perkiraan {titik(ringkasan['total_tulis'])} tulisan")
    for b in out.daftar:
        print(f"  {b['berkas']}: ±{titik(b['tulis'])} tulisan; " + ", ".join(f"{t} {n}" for t, n in b["baris"].items()))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "rencana":
        batas = int(a[a.index("--batas") + 1]) if "--batas" in a else BATAS
        sys.exit(rencana(a[1], a[2], a[3], batas))
    print(__doc__)
    sys.exit(1)
