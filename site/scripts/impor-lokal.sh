#!/usr/bin/env bash
# Impor hasil `python3 pipeline/export_d1.py` (build/d1/*.sql) ke database D1 LOKAL.
set -euo pipefail
cd "$(dirname "$0")/.."
export WRANGLER_SEND_METRICS=false
for f in ../build/d1/*.sql; do
  echo "impor $(basename "$f") ..."
  npx wrangler d1 execute teman-hadits --local --yes --file "$f" > /dev/null
done
npx wrangler d1 execute teman-hadits --local --command "SELECT kunci, nilai FROM info"
