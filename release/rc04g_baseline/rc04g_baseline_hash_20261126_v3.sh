#!/usr/bin/env bash
# RC04g installed-source baseline hash, v3. READ-ONLY on the addon directory and its git metadata.
# v1 defect: report written INTO the addon dir (relative OUT after cd) and hashed with the tree.
# v2 fixes: OUT made absolute BEFORE cd and refused if inside ADDON (incl. '..' paths); LC_ALL=C sort;
#   symlinks/special files listed as findings.
# v3 fixes (found on review of v2):
#   - git status can refresh and REWRITE .git/index: now run with --no-optional-locks and GIT_OPTIONAL_LOCKS=0.
#   - a .git directory inside the addon was hashed into the tree (noisy, changes with git activity): excluded,
#     and its presence is reported.
#   - hashing errors (e.g. permission denied) went to the terminal only and the tree hash silently covered
#     fewer files: stderr now goes into the report, files listed vs files hashed are compared, and a
#     mismatch prints HASH_INCOMPLETE.
#   - xargs ran sha256sum on stdin when the list was empty: now xargs -r.
#   - a git probe failure (e.g. 'dubious ownership') was reported as 'not a git work tree': the probe text is shown.
#   - the file list is hashed once and the tree hash is computed from that same pass.
# Usage: bash rc04g_baseline_hash_20261126_v3.sh.txt [ADDON_DIR] [EXPECTED_SHA256_FILE] [EXPECTED_PREFIX_FILE]
#   EXPECTED_SHA256_FILE : lines "<full sha256>  <path relative to ADDON_DIR>"
#   EXPECTED_PREFIX_FILE : lines "<hex prefix> <path relative to ADDON_DIR>" ('#' comments allowed)
#   OUT=/abs/path/file.txt (optional; default $PWD/rc04g_baseline_<utc>.txt; must be outside ADDON_DIR, must not exist)
set -u
export LC_ALL=C
export GIT_OPTIONAL_LOCKS=0
ADDON_IN="${1:-/opt/odoo20/addons/synapsys}"
EXPECTED="${2:-}"
PREFIXES="${3:-}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
[ -d "$ADDON_IN" ] || { echo "ADDON NOT FOUND: $ADDON_IN" >&2; exit 2; }
ADDON="$(cd "$ADDON_IN" && pwd -P)" || exit 2
OUT="${OUT:-$PWD/rc04g_baseline_${TS}.txt}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
OUTDIR="$(cd "$(dirname "$OUT")" 2>/dev/null && pwd -P)" || { echo "OUT directory does not exist: $OUT" >&2; exit 2; }
OUT="$OUTDIR/$(basename "$OUT")"
case "$OUT/" in "$ADDON"/*) echo "REFUSED: OUT is inside the addon dir ($OUT)" >&2; exit 3 ;; esac
[ -e "$OUT" ] && { echo "REFUSED: OUT already exists ($OUT)" >&2; exit 3; }
if [ -n "$EXPECTED" ]; then case "$EXPECTED" in /*) ;; *) EXPECTED="$PWD/$EXPECTED" ;; esac; fi
if [ -n "$PREFIXES" ]; then case "$PREFIXES" in /*) ;; *) PREFIXES="$PWD/$PREFIXES" ;; esac; fi
cd "$ADDON" || exit 2
LIST() { find . -type f ! -path './.git/*' ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 | sort -z; }
{
  echo "# RC04g installed-source baseline v3 (read-only)"
  echo "utc: $TS"; echo "host: $(hostname)"; echo "addon_dir: $ADDON"; echo "script: rc04g_baseline_hash_20261126_v3"
  echo "run_as: $(id -un)"
  echo; echo "## manifest version"
  grep -nE "['\"]version['\"]" __manifest__.py || echo "NO version line found"
  echo; echo "## git state (read-only, no optional locks)"
  GP="$(git -C "$ADDON" rev-parse --is-inside-work-tree 2>&1)"
  echo "git probe: $GP"
  if [ "$GP" = "true" ]; then
    echo "head: $(git -C "$ADDON" rev-parse HEAD 2>&1)"; echo "branch: $(git -C "$ADDON" rev-parse --abbrev-ref HEAD 2>&1)"
    echo "toplevel: $(git -C "$ADDON" rev-parse --show-toplevel 2>&1)"
    echo "dirty files:"; git --no-optional-locks -C "$ADDON" status --porcelain 2>&1 | head -50
    echo "(a repo here does NOT prove it equals installed source; the file hashes below are the evidence)"
  fi
  [ -e .git ] && echo ".git present in addon dir (excluded from the hashes below)"
  echo; echo "## symlinks and special files (not hashed; any line here is a finding)"
  find . ! -path './.git/*' ! -type f ! -type d -print | sort
  echo "(end)"
  echo; echo "## key files (bytes, sha256)"
  for f in lens_contract.py controllers/lenses.py arch_map.py home.xml __manifest__.py; do
    p="$(find . -path ./node_modules -prune -o -path ./.git -prune -o -type f -name "$(basename "$f")" -print 2>/dev/null | sort | head -5)"
    if [ -z "$p" ]; then echo "MISSING: $f"; else
      echo "$p" | while IFS= read -r q; do echo "$(stat -c %s "$q") $(sha256sum "$q" | cut -d' ' -f1)  $q"; done
    fi
  done
  HASHES="$(LIST | xargs -0 -r sha256sum 2>&1)"
  NLIST="$(LIST | tr -cd '\0' | wc -c)"
  NHASH="$(printf '%s\n' "$HASHES" | grep -cE '^[0-9a-f]{64}  \./')"
  NBAD="$(printf '%s\n' "$HASHES" | grep -vE '^[0-9a-f]{64}  \./' | grep -c .)"
  echo; echo "## all source files (sha256  path), excluding .git and caches"
  printf '%s\n' "$HASHES"
  echo; echo "## tree hash (sha256 of the list above)"
  printf '%s\n' "$HASHES" | sha256sum | cut -d' ' -f1
  echo; echo "## completeness"
  echo "files_listed: $NLIST"; echo "files_hashed: $NHASH"; echo "hash_error_lines: $NBAD"
  if [ "$NLIST" = "$NHASH" ] && [ "$NBAD" = "0" ]; then echo "HASH_COMPLETE"; else echo "HASH_INCOMPLETE (tree hash does NOT cover every file)"; fi
  echo "tests: $(find . -path '*/tests/*' -name 'test_*.py' | wc -l)"
  if [ -n "$EXPECTED" ] && [ -f "$EXPECTED" ]; then
    echo; echo "## comparison to $EXPECTED"
    sha256sum -c "$EXPECTED" 2>&1 | grep -v ': OK$' || echo "ALL LISTED FILES MATCH"
  fi
  if [ -n "$PREFIXES" ] && [ -f "$PREFIXES" ]; then
    echo; echo "## prefix comparison to $PREFIXES"
    while read -r pre path; do
      [ -z "$pre" ] && continue
      case "$pre" in \#*) continue ;; esac
      if [ -f "$path" ]; then
        h="$(sha256sum "$path" | cut -d' ' -f1)"
        case "$h" in "$pre"*) echo "MATCH    $path" ;; *) echo "MISMATCH $path expected-prefix=$pre actual=$h" ;; esac
      else echo "MISSING  $path"; fi
    done < "$PREFIXES"
  fi
} > "$OUT" 2>&1
cat "$OUT"
echo; echo "Wrote: $OUT   (file this to Working Memory; do not edit it)"
echo "REPORT_SHA256=$(sha256sum "$OUT" | cut -d' ' -f1)"
