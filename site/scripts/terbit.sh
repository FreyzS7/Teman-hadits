#!/usr/bin/env bash
# Satu perintah untuk menerbitkan pembaruan (npm run terbit, dari folder site). Urutannya:
#   1. git pull (fast-forward saja)
#   2. jalankan ulang HANYA langkah pipeline yang berkasnya berubah sejak terbit terakhir
#   3. ekspor data D1 (±30 detik) lalu bandingkan sidiknya dengan impor terakhir:
#      sama  -> impor online DILEWATI (pembaruan kode saja: beberapa menit)
#      beda  -> impor online (bagian yang lama; minta konfirmasi YA)
#   4. tabel catatan kueri (IF NOT EXISTS, murah), lalu deploy (uji dulu)
# Status terbit terakhir disimpan di site/.terbit/ (tidak ikut git).
# COBA=1 npm run terbit : jalankan pipeline & ekspor, tetapi pull/impor/deploy hanya dicetak (untuk menguji skrip).
set -euo pipefail
cd "$(dirname "$0")/.."
SITE="$(pwd)"; ROOT="$(cd .. && pwd)"; STATUS="$SITE/.terbit"
mkdir -p "$STATUS"
export WRANGLER_SEND_METRICS=false

PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Python 3.10+ tidak ditemukan." >&2; exit 1; }
pyu() { (cd "$ROOT" && "$PY" -X utf8 "$@"); }
jalan() { if [ "${COBA:-}" = 1 ]; then echo "   [COBA] $*"; else "$@"; fi; }

cabang="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
echo "== 1/4 Tarik perubahan ($cabang)"
jalan git -C "$ROOT" pull --ff-only origin "$cabang"

terakhir="$(cat "$STATUS/commit" 2>/dev/null || true)"
if [ -n "$terakhir" ] && git -C "$ROOT" cat-file -e "$terakhir" 2>/dev/null; then
  berubah="$(git -C "$ROOT" diff --name-only "$terakhir" HEAD -- pipeline/)"
else
  berubah="__semua__"   # terbit pertama dengan skrip ini: anggap semua langkah perlu dicek
fi

echo "== 2/4 Pipeline"
if [ "$berubah" = "__semua__" ]; then
  echo "Belum ada catatan terbit sebelumnya: jalankan langkah yang paling sering berubah (riyadh, bab_openiti)."
  langkah="riyadh bab_openiti"
else
  inti="$(echo "$berubah" | grep -E '^pipeline/(common|fetch_sources|build_db|takhrij|hadeethenc)\.py$' || true)"
  if [ -n "$inti" ]; then
    echo "Berkas inti pipeline berubah:"; echo "$inti"
    echo "Jalankan dulu dari folder utama: bash pipeline/run_all.sh  (lalu ulangi npm run terbit)" >&2
    exit 1
  fi
  langkah=""
  for s in riyadh bab_openiti katalog_palsu rijal perawi; do
    if echo "$berubah" | grep -qx "pipeline/$s.py"; then langkah="$langkah $s"; fi
  done
  # perawi.py memakai hasil rijal.py
  case " $langkah " in *" rijal "*) case " $langkah " in *" perawi "*) ;; *) langkah="$langkah perawi" ;; esac ;; esac
fi
for s in $langkah; do echo "-- pipeline/$s.py"; pyu -I "pipeline/$s.py"; done
[ -n "$langkah" ] || echo "Tidak ada langkah pipeline yang berubah."

echo "== 3/4 Data D1"
pyu pipeline/export_d1.py >/dev/null
sidik="$(cat "$ROOT"/build/d1/*.sql | "$PY" -c "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")"
if [ "$sidik" = "$(cat "$STATUS/sidik-data" 2>/dev/null || true)" ]; then
  echo "Data sama dengan impor terakhir: impor online dilewati."
else
  echo "Data berubah sejak impor terakhir: impor online diperlukan (bagian yang lama)."
  echo "PERHATIAN: impor penuh menulis ±564 ribu baris. Paket GRATIS hanya 100 ribu tulisan/hari: bila Workers Paid sudah tidak aktif,"
  echo "           jawab selain YA lalu tanyakan Claude (lihat docs/12, bagian Rekomendasi jalur terbit)."
  jalan bash scripts/impor-online.sh
  [ "${COBA:-}" = 1 ] || echo "$sidik" > "$STATUS/sidik-data"
fi
jalan npx wrangler d1 execute teman-hadits --env production --remote --yes --file scripts/catatan.sql

echo "== 4/4 Deploy"
jalan bash scripts/deploy.sh
[ "${COBA:-}" = 1 ] || git -C "$ROOT" rev-parse HEAD > "$STATUS/commit"
echo "Selesai. Kabari Claude untuk menguji situs online."
