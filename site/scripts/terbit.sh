#!/usr/bin/env bash
# Satu perintah untuk menerbitkan pembaruan (npm run terbit, dari folder site). Urutannya:
#   1. git pull (fast-forward saja)
#   2. jalankan ulang HANYA langkah pipeline yang berkasnya berubah sejak terbit terakhir
#   3. ekspor data D1 (±30 detik) lalu bandingkan sidiknya dengan impor terakhir:
#      sama  -> impor online DILEWATI (pembaruan kode saja: beberapa menit)
#      beda  -> impor bertahap (hanya baris yang berubah); impor penuh hanya bila belum ada cermin / skema berubah
#   4. tabel catatan kueri (IF NOT EXISTS, murah), lalu deploy (uji dulu)
# Status terbit terakhir disimpan di site/.terbit/ (tidak ikut git), termasuk cermin data online (cermin.sqlite).
# Data berubah + ada cermin -> IMPOR BERTAHAP: hanya baris yang berubah, satu cicilan (< 70 ribu tulisan) per hari
# (pipeline/impor_cicil.py; docs/12). Cermin dibuat otomatis pada terbit pertama yang datanya sama dengan online.
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

bahan() { case "$1" in katalog_palsu) echo "hadits_populer\.json" ;; bab_openiti) echo "glosarium_kitab\.json|koreksi_bab\.json" ;; *) echo "-" ;; esac; }
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
  # langkah + berkas data yang dibacanya (hadits_populer.json -> katalog_palsu, glosarium/koreksi -> bab_openiti)
  for s in riyadh bab_openiti katalog_palsu rijal perawi; do
    if echo "$berubah" | grep -qxE "pipeline/($s\.py|$(bahan "$s"))"; then langkah="$langkah $s"; fi
  done
  # perawi.py memakai hasil rijal.py
  case " $langkah " in *" rijal "*) case " $langkah " in *" perawi "*) ;; *) langkah="$langkah perawi" ;; esac ;; esac
fi
for s in $langkah; do echo "-- pipeline/$s.py"; pyu -I "pipeline/$s.py"; done
[ -n "$langkah" ] || echo "Tidak ada langkah pipeline yang berubah."

echo "== 3/4 Data D1"
pyu pipeline/export_d1.py >/dev/null
sidik="$(cat "$ROOT"/build/d1/*.sql | "$PY" -c "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")"
CERMIN="$STATUS/cermin.sqlite"          # isi data yang sedang online (dasar impor bertahap)
TARGET="$STATUS/cermin-target.sqlite"   # data yang sedang dicicil ke online
impor_penuh() {
  echo "PERHATIAN: impor penuh menulis ±564 ribu baris. Paket GRATIS hanya 100 ribu tulisan/hari: bila Workers Paid sudah tidak aktif,"
  echo "           jawab selain YA lalu tanyakan Claude (lihat docs/12, bagian Impor bertahap)."
  jalan bash scripts/impor-online.sh
  [ "${COBA:-}" = 1 ] || { echo "$sidik" > "$STATUS/sidik-data"; cp "$ROOT/build/d1-cermin.sqlite" "$CERMIN"; rm -f "$TARGET" "$STATUS"/cicil-*; }
}
if [ -f "$TARGET" ] || { [ "$sidik" != "$(cat "$STATUS/sidik-data" 2>/dev/null || true)" ] && [ -f "$CERMIN" ]; }; then
  # Impor bertahap: hanya baris yang berubah, maksimal satu cicilan (< 70 ribu tulisan) per hari UTC.
  if [ ! -f "$TARGET" ]; then
    [ "${COBA:-}" = 1 ] || { cp "$ROOT/build/d1-cermin.sqlite" "$TARGET"; echo "$sidik" > "$STATUS/cicil-sidik"; echo 0 > "$STATUS/cicil-selesai"; }
  elif [ "$sidik" != "$(cat "$STATUS/cicil-sidik")" ]; then
    echo "Data berubah lagi, tetapi cicilan sebelumnya belum selesai: cicilan lama diselesaikan dulu, perubahan baru menyusul."
  fi
  tujuan="$TARGET"; [ -f "$TARGET" ] || tujuan="$ROOT/build/d1-cermin.sqlite"   # mode COBA tidak menyalin target
  set +e; pyu pipeline/impor_cicil.py rencana "$CERMIN" "$tujuan" "$ROOT/build/d1-cicil"; rc=$?; set -e
  if [ "$rc" = 2 ]; then
    echo "Skema database berubah: impor bertahap tidak bisa; perlu impor penuh."
    rm -f "$TARGET" "$STATUS"/cicil-*
    impor_penuh
  elif [ "$rc" != 0 ]; then
    echo "Rencana impor bertahap gagal (lihat pesan di atas)." >&2; exit 1
  else
    berkas=( "$ROOT"/build/d1-cicil/*.sql ); [ -e "${berkas[0]}" ] || berkas=()
    selesai="$(cat "$STATUS/cicil-selesai" 2>/dev/null || echo 0)"
    if [ "$selesai" -lt "${#berkas[@]}" ]; then
      if [ "$(cat "$STATUS/cicil-tanggal" 2>/dev/null || true)" = "$(date -u +%F)" ]; then
        echo "Cicilan hari ini sudah dikirim ($selesai dari ${#berkas[@]}). Jalankan lagi npm run terbit besok (sesudah pukul 07.00 WIB)."
      else
        f="${berkas[$selesai]}"
        echo "Mengirim cicilan $((selesai + 1)) dari ${#berkas[@]} ($(basename "$f"))..."
        jalan npx wrangler d1 execute teman-hadits --env production --remote --yes --file "$f"
        [ "${COBA:-}" = 1 ] || { selesai=$((selesai + 1)); echo "$selesai" > "$STATUS/cicil-selesai"; date -u +%F > "$STATUS/cicil-tanggal"; }
      fi
    fi
    if [ "$selesai" -ge "${#berkas[@]}" ] && [ "${COBA:-}" != 1 ]; then
      mv "$TARGET" "$CERMIN"; cp "$STATUS/cicil-sidik" "$STATUS/sidik-data"; rm -f "$STATUS"/cicil-*
      echo "Impor bertahap selesai: data online sama dengan data terbaru."
      [ "$sidik" = "$(cat "$STATUS/sidik-data")" ] || echo "Masih ada perubahan data yang lebih baru: jalankan npm run terbit lagi besok."
    fi
  fi
elif [ "$sidik" = "$(cat "$STATUS/sidik-data" 2>/dev/null || true)" ]; then
  echo "Data sama dengan impor terakhir: impor online dilewati."
  if [ ! -f "$CERMIN" ] && [ "${COBA:-}" != 1 ]; then
    cp "$ROOT/build/d1-cermin.sqlite" "$CERMIN"
    echo "Cermin data online disimpan di site/.terbit/ (dasar impor bertahap untuk perubahan data berikutnya)."
  fi
else
  echo "Data berubah, tetapi belum ada cermin data online (site/.terbit/cermin.sqlite)."
  if [ "${COBA:-}" != 1 ] && bash scripts/cermin-awal.sh; then
    echo "Cermin data online berhasil disusun ulang. Jalankan npm run terbit sekali lagi untuk mulai impor bertahap."
  else
    echo "Cermin data online tidak bisa disusun ulang: impor bertahap belum bisa."
    impor_penuh
  fi
fi
jalan npx wrangler d1 execute teman-hadits --env production --remote --yes --file scripts/catatan.sql

echo "== 4/4 Deploy"
jalan bash scripts/deploy.sh
[ "${COBA:-}" = 1 ] || git -C "$ROOT" rev-parse HEAD > "$STATUS/commit"
echo "Selesai. Kabari Claude untuk menguji situs online."
