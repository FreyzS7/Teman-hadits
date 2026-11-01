#!/usr/bin/env bash
# Terbitkan Worker ke Cloudflare (env production). Uji dulu; VERSI_DATA = waktu bangun data + commit, sehingga
# cache tepi lama otomatis tidak dipakai lagi setelah data/kode baru.
set -euo pipefail
cd "$(dirname "$0")/.."
export WRANGLER_SEND_METRICS=false
grep -q 'GANTI-DENGAN-ID' wrangler.toml && { echo "Isi dulu database_id di wrangler.toml [env.production]." >&2; exit 1; }
npm test
versi="$(git rev-parse --short HEAD)-$(date -u +%Y%m%d%H%M)"
npx wrangler deploy --env production --var "VERSI_DATA:${versi}"
echo "Terbit dengan VERSI_DATA=${versi}. Uji: BASE_URL=https://<domain-anda> npm run test:http"
