#!/usr/bin/env bash
# RC04g installed-source baseline hash, v2 (READ-ONLY on the addon directory).
# Changes from v1 (defect: the report was written INTO the addon dir via a relative path,
# then hashed with the tree): OUT is made absolute BEFORE cd and refused if inside ADDON;
# LC_ALL=C pins sort order so the tree hash is reproducible; symlinks and non-regular files
# are listed explicitly instead of silently skipped.
# Usage: bash rc04g_baseline_hash_20261126_v2.sh [ADDON_DIR] [EXPECTED_HASH_FILE]
#   OUT=/abs/path/file.txt (optional; default: $PWD/rc04g_baseline_<utc>.txt, must be outside ADDON_DIR)
set -u
export LC_ALL=C
ADDON_IN="${1:-/opt/odoo20/addons/synapsys}"
EXPECTED="${2:-}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
[ -d "$ADDON_IN" ] || { echo "ADDON NOT FOUND: $ADDON_IN" >&2; exit 2; }
ADDON="$(cd "$ADDON_IN" && pwd -P)" || exit 2
OUT="${OUT:-$PWD/rc04g_baseline_${TS}.txt}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
OUTDIR="$(cd "$(dirname "$OUT")" 2>/dev/null && pwd -P)" || { echo "OUT directory does not exist: $OUT" >&2; exit 2; }
OUT="$OUTDIR/$(basename "$OUT")"
case "$OUT/" in "$ADDON"/*) echo "REFUSED: OUT is inside the addon dir ($OUT)" >&2; exit 3 ;; esac
[ -e "$OUT" ] && { echo "REFUSED: OUT already exists ($OUT)" >&2; exit 3; }
[ -n "$EXPECTED" ] && case "$EXPECTED" in /*) ;; *) EXPECTED="$PWD/$EXPECTED" ;; esac
cd "$ADDON" || exit 2
LIST() { find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 | sort -z; }
{
  echo "# RC04g installed-source baseline v2 (read-only)"
  echo "utc: $TS"; echo "host: $(hostname)"; echo "addon_dir: $ADDON"; echo "script: rc04g_baseline_hash_20261126_v2"
  echo; echo "## manifest version"
  grep -nE "['\"]version['\"]" __manifest__.py || echo "NO version line found"
  echo; echo "## git state (if a repo; read-only)"
  if git -C "$ADDON" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "head: $(git -C "$ADDON" rev-parse HEAD)"; echo "branch: $(git -C "$ADDON" rev-parse --abbrev-ref HEAD)"
    echo "dirty files:"; git -C "$ADDON" status --porcelain | head -50
    echo "(a repo here does NOT prove it equals installed source; files below are the evidence)"
  else echo "not a git work tree"; fi
  echo; echo "## symlinks and special files (not hashed; any line here is a finding)"
  find . ! -type f ! -type d -print | sort
  echo "(end)"
  echo; echo "## key files (bytes, sha256)"
  for f in lens_contract.py controllers/lenses.py arch_map.py home.xml __manifest__.py; do
    p="$(find . -path ./node_modules -prune -o -type f -name "$(basename "$f")" -print 2>/dev/null | sort | head -5)"
    if [ -z "$p" ]; then echo "MISSING: $f"; else
      echo "$p" | while IFS= read -r q; do echo "$(stat -c %s "$q") $(sha256sum "$q" | cut -d' ' -f1)  $q"; done
    fi
  done
  echo; echo "## all source files (sha256  path), excluding caches"
  LIST | xargs -0 sha256sum
  echo; echo "## tree hash (sha256 of the sorted list above)"
  LIST | xargs -0 sha256sum | sha256sum | cut -d' ' -f1
  echo; echo "## file counts"
  echo "files: $(find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' | wc -l)"
  echo "tests: $(find . -path '*/tests/*' -name 'test_*.py' | wc -l)"
  if [ -n "$EXPECTED" ] && [ -f "$EXPECTED" ]; then
    echo; echo "## comparison to $EXPECTED"
    sha256sum -c "$EXPECTED" 2>&1 | grep -v ': OK$' || echo "ALL LISTED FILES MATCH"
  fi
} > "$OUT"
cat "$OUT"
echo; echo "Wrote: $OUT   (file this to Working Memory; do not edit it)"
echo "REPORT_SHA256=$(sha256sum "$OUT" | cut -d' ' -f1)"
