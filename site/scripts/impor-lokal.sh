#!/usr/bin/env bash
# Impor hasil `python3 pipeline/export_d1.py` (build/d1/*.sql) ke database D1 LOKAL.
set -euo pipefail
cd "$(dirname "$0")/.."
export WRANGLER_SEND_METRICS=false
# Mulai dari database lokal kosong: menghapus & membuat ulang tabel besar di database lama
# membuat SQLite di emulator lokal kehabisan memori (SQLITE_NOMEM).
rm -rf .wrangler/state/v3/d1 .wrangler/state/v3/cache   # cache tepi lokal ikut dikosongkan: data baru = halaman baru
for f in ../build/d1/*.sql; do
  echo "impor $(basename "$f") ..."
  if ! out=$(npx wrangler d1 execute teman-hadits --local --yes --file "$f" 2>&1); then
    echo "$out" | grep -iE "error|✘" | head -5
    echo "GAGAL mengimpor $f" >&2
    exit 1
  fi
done
npx wrangler d1 execute teman-hadits --local --command "SELECT kunci, nilai FROM info"
