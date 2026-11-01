#!/usr/bin/env bash
# Jalankan seluruh pipeline dari nol: unduh sumber -> build -> takhrij -> uji -> audit -> ekspor D1.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 pipeline/fetch_sources.py
python3 pipeline/build_db.py
python3 pipeline/takhrij.py
python3 -m unittest pipeline/test_golden.py -v
python3 pipeline/audit.py
python3 pipeline/export_d1.py
python3 pipeline/fixtures_js.py
python3 design/build_prototype.py
