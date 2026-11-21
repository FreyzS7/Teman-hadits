#!/usr/bin/env bash
# Susun ulang CERMIN data yang sedang online (site/.terbit/cermin.sqlite) bila belum ada, supaya impor bertahap bisa
# dipakai tanpa impor penuh. Caranya: checkout commit terbit terakhir (site/.terbit/commit) di folder sementara,
# jalankan ulang langkah pipeline yang berubah sejak commit itu (versi lamanya), lalu ekspor. Hasilnya HANYA dipakai
# bila sidik build/d1/*.sql-nya sama persis dengan sidik impor terakhir (site/.terbit/sidik-data).
set -euo pipefail
cd "$(dirname "$0")/.."
SITE="$(pwd)"; ROOT="$(cd .. && pwd)"; STATUS="$SITE/.terbit"
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Python 3.10+ tidak ditemukan." >&2; exit 1; }
[ -s "$STATUS/commit" ] && [ -s "$STATUS/sidik-data" ] || { echo "Belum ada catatan terbit (site/.terbit/commit, sidik-data)." >&2; exit 1; }
c="$(cat "$STATUS/commit")"; target="$(cat "$STATUS/sidik-data")"
git -C "$ROOT" cat-file -e "$c" 2>/dev/null || { echo "Commit terbit terakhir $c tidak ada di repositori lokal." >&2; exit 1; }
if git -C "$ROOT" diff --name-only "$c" HEAD -- pipeline/ | grep -qE '^pipeline/(common|fetch_sources|build_db|takhrij|hadeethenc)\.py$'; then
  echo "Berkas inti pipeline berubah sejak terbit terakhir: cermin tidak bisa disusun ulang." >&2; exit 1
fi
TMP="$(mktemp -d)"; W="$TMP/wt"
selesai() { git -C "$ROOT" worktree remove --force "$W" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap selesai EXIT
echo "Menyusun ulang data online dari commit $(git -C "$ROOT" rev-parse --short "$c")..."
git -C "$ROOT" worktree add --detach --quiet "$W" "$c"
mkdir -p "$W/build"
for f in "$ROOT"/build/*.sqlite "$ROOT"/build/*.json; do
  case "$(basename "$f")" in d1-cermin.sqlite) ;; *) cp "$f" "$W/build/" ;; esac
done
for d in cetak ifta; do [ -e "$ROOT/build/$d" ] && ln -s "$ROOT/build/$d" "$W/build/$d"; done
[ -e "$W/sources" ] || ln -s "$ROOT/sources" "$W/sources"
berubah="$(git -C "$ROOT" diff --name-only "$c" HEAD -- pipeline/)"
langkah=""
for s in riyadh bab_openiti katalog_palsu rijal perawi; do
  case "$s" in katalog_palsu) b="hadits_populer\.json" ;; bab_openiti) b="glosarium_kitab\.json|koreksi_bab\.json" ;; *) b="-" ;; esac
  if echo "$berubah" | grep -qxE "pipeline/($s\.py|$b)"; then langkah="$langkah $s"; fi
done
case " $langkah " in *" rijal "*) case " $langkah " in *" perawi "*) ;; *) langkah="$langkah perawi" ;; esac ;; esac
for s in $langkah; do echo "-- pipeline/$s.py (versi $(git -C "$ROOT" rev-parse --short "$c"))"; (cd "$W" && "$PY" -X utf8 -I "pipeline/$s.py" >/dev/null); done
# ekspor versi lama belum menulis cermin: pakai export_d1.py terbaru (hasilnya tetap diverifikasi lewat sidik)
grep -q '^CERMIN' "$W/pipeline/export_d1.py" || cp "$ROOT/pipeline/export_d1.py" "$W/pipeline/export_d1.py"
(cd "$W" && "$PY" -X utf8 pipeline/export_d1.py >/dev/null 2>&1)
sidik="$(cat "$W"/build/d1/*.sql | "$PY" -c "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")"
if [ "${CETAK_SIDIK:-}" = 1 ]; then echo "$sidik"; fi
if [ "$sidik" != "$target" ]; then
  echo "Sidik hasil susun ulang ($sidik) tidak sama dengan sidik impor terakhir ($target): cermin TIDAK disimpan." >&2
  exit 1
fi
cp "$W/build/d1-cermin.sqlite" "$STATUS/cermin.sqlite"
echo "Cermin data online disimpan: site/.terbit/cermin.sqlite"
