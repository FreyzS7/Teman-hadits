#!/usr/bin/env bash
# Impor build/d1/*.sql ke database D1 ONLINE (Cloudflare). Lihat docs/12-online.md.
#
# PENTING: impor penuh menulis ±1,7 juta baris (cek: npm run estimasi). Paket gratis D1 hanya 100.000 baris
# ditulis per hari; bila habis, D1 berhenti melayani SEMUA kueri sampai 00:00 UTC. Jalankan impor penuh hanya
# saat akun memakai paket Workers Paid (50 juta tulis/bulan termasuk), lalu boleh kembali ke paket gratis.
set -euo pipefail
cd "$(dirname "$0")/.."
export WRANGLER_SEND_METRICS=false
grep -q 'GANTI-DENGAN-ID' wrangler.toml && { echo "Isi dulu database_id di wrangler.toml [env.production] (lihat docs/12-online.md)." >&2; exit 1; }
node scripts/estimasi-d1.mjs 2>/dev/null | tail -3 || true
read -r -p "Akun memakai paket Workers Paid dan siap menimpa database online? Ketik YA untuk lanjut: " jawab
[ "$jawab" = "YA" ] || { echo "Dibatalkan."; exit 1; }
for f in ../build/d1/*.sql; do
  echo "impor $(basename "$f") ..."
  if ! npx wrangler d1 execute teman-hadits --env production --remote --yes --file "$f"; then
    echo "GAGAL di $f. Database online sekarang setengah terisi: perbaiki penyebabnya lalu ulangi skrip ini dari awal." >&2
    exit 1
  fi
done
npx wrangler d1 execute teman-hadits --env production --remote --command "SELECT kunci, nilai FROM info"
echo "Selesai. Lanjutkan dengan: npm run deploy"
