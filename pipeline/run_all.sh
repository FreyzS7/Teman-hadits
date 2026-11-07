#!/usr/bin/env bash
# Jalankan seluruh pipeline dari nol: unduh sumber -> build -> takhrij -> uji -> audit -> ekspor D1.
set -euo pipefail
cd "$(dirname "$0")/.."
# Cari Python 3 yang benar-benar jalan. Di Windows, "python3" sering hanya pintasan Microsoft Store yang mencetak
# "Python was not found"; Python dari python.org terpasang sebagai "python" / "py". "-X utf8": baca/tulis berkas
# dan cetak teks Arab sebagai UTF-8 di semua sistem (bawaan Windows cp1252 gagal); tetap berlaku bersama -I.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || { echo "Python 3.10+ tidak ditemukan. Pasang dari https://www.python.org/downloads/ (centang 'Add python.exe to PATH'), lalu buka terminal baru." >&2; exit 1; }
pyu() { "$PY" -X utf8 "$@"; }      # bukan "py": nama itu bisa = peluncur Python Windows
echo "Memakai $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"
pyu pipeline/fetch_sources.py
pyu pipeline/build_db.py
pyu pipeline/takhrij.py
# HadeethEnc: unduhan bisa dilanjutkan; ulangi sampai lengkap (sopan, <= 3 permintaan/detik)
# (pesan "unduhan lengkap" dicetak ke stderr; dulu hanya stdout yang diperiksa sehingga putaran ini tak pernah berhenti)
for coba in $(seq 1 40); do
  keluaran="$(pyu -I pipeline/hadeethenc.py unduh --maks-detik 500 2>&1)" || { echo "$keluaran" >&2; echo "Unduhan HadeethEnc gagal; periksa koneksi lalu jalankan lagi skrip ini." >&2; exit 1; }
  echo "$keluaran" | tail -n 3
  if grep -q "unduhan lengkap" <<<"$keluaran"; then break; fi
  [ "$coba" -lt 40 ] || { echo "HadeethEnc belum lengkap sesudah 40 putaran; jalankan lagi skrip ini." >&2; exit 1; }
done
pyu -I pipeline/hadeethenc.py bangun
pyu -I pipeline/riyadh.py
pyu -I pipeline/bab_openiti.py
pyu -I pipeline/katalog_palsu.py
pyu -I pipeline/rijal.py
pyu -I pipeline/perawi.py
# opsional (unduh data pembanding Ifta'): pyu -I pipeline/uji_perawi_ifta.py
# opsional (unduh OCR kitab cetak dari archive.org): pyu -I pipeline/verifikasi_cetak.py
pyu -m unittest pipeline/test_golden.py pipeline/test_hadeethenc.py pipeline/test_riyadh.py pipeline/test_bab.py pipeline/test_katalog.py pipeline/test_rijal.py pipeline/test_export.py -v
pyu pipeline/audit.py
pyu pipeline/export_d1.py
pyu pipeline/fixtures_js.py
pyu design/build_prototype.py
