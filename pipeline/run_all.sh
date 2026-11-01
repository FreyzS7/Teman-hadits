#!/usr/bin/env bash
# Jalankan seluruh pipeline dari nol: unduh sumber -> build -> takhrij -> uji -> audit -> ekspor D1.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 pipeline/fetch_sources.py
python3 pipeline/build_db.py
python3 pipeline/takhrij.py
# HadeethEnc: unduhan bisa dilanjutkan; ulangi sampai lengkap (sopan, <= 3 permintaan/detik)
until python3 -I pipeline/hadeethenc.py unduh --maks-detik 500 | tee /dev/stderr | grep -q "unduhan lengkap"; do :; done
python3 -I pipeline/hadeethenc.py bangun
python3 -I pipeline/riyadh.py
python3 -I pipeline/bab_openiti.py
python3 -I pipeline/katalog_palsu.py
python3 -m unittest pipeline/test_golden.py pipeline/test_hadeethenc.py pipeline/test_riyadh.py pipeline/test_bab.py pipeline/test_katalog.py -v
python3 pipeline/audit.py
python3 pipeline/export_d1.py
python3 pipeline/fixtures_js.py
python3 design/build_prototype.py
