#!/usr/bin/env bash
# Pinned, gated dev install of a unified-diff patch onto /opt/odoo20/addons/synapsys, restart only (no module upgrade).
# Usage: bash install_patch.sh PATCH PATCH_SHA256 PRE_TREE_HASH POST_TREE_HASH BACKUP_DIR
# Refuses (exit 1, nothing changed) on: patch hash, prestate tree hash, existing backup dir, failed backup, failed dry run.
# Reverses the patch itself (exit 1) if apply fails, a Python file does not parse, or the poststate tree hash differs.
# Never deletes with rm. Env overrides exist for offline tests only.
set -u
PATCH="${1:?patch}"; PSHA="${2:?patch sha256}"; PRE="${3:?pre tree hash}"; POST="${4:?post tree hash}"; BK="${5:?backup dir}"
ADDONS="${ADDONS:-/opt/odoo20/addons}"; HASHER="${HASHER:?path to rc04g_baseline_hash script}"
CTR="${CTR:-odoo20-odoo-1}"; WAIT="${WAIT:-45}"; DOCKER="${DOCKER:-docker}"; REPORTS="${REPORTS:-/root}"
fail() { echo "STOP: $*"; exit 1; }
tree() { OUT="$REPORTS/install_tree_$(date -u +%H%M%S)_$$_$RANDOM.txt" bash "$HASHER" "$ADDONS/synapsys" | sed -n '/## tree hash/{n;p}'; }
reverse() { (cd "$ADDONS" && patch -R -E -p1 -s < "$PATCH") && echo "REVERSED_PATCH"; }
[ -f "$PATCH" ] || fail PATCH_MISSING
[ "$(sha256sum "$PATCH" | cut -d' ' -f1)" = "$PSHA" ] || fail PATCH_HASH_MISMATCH
echo "patch hash ok"
T="$(tree)"; [ "$T" = "$PRE" ] || fail "PRESTATE_MISMATCH (found $T)"
echo "PRESTATE_OK"
[ -e "$BK" ] && fail "BACKUP_DIR_EXISTS ($BK)"
mkdir -p "$(dirname "$BK")" && cp -a "$ADDONS/synapsys" "$BK" || fail BACKUP_FAILED
echo "BACKUP_OK $BK"
(cd "$ADDONS" && patch -p1 --dry-run -s < "$PATCH") || fail DRYRUN_FAILED
(cd "$ADDONS" && patch -p1 -s < "$PATCH") || { reverse; fail APPLY_FAILED; }
echo "APPLIED"
PYS="$(grep '^+++ ' "$PATCH" | sed -E 's/^\+\+\+ [^/]+\/([^[:space:]]+).*/\1/' | grep '\.py$')"
for f in $PYS; do
  [ -f "$ADDONS/$f" ] || continue
  python3 -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$ADDONS/$f" || { reverse; fail "PARSE_FAILED $f"; }
done
echo "PARSES_OK"
T="$(tree)"; [ "$T" = "$POST" ] || { reverse; fail "POSTSTATE_MISMATCH (found $T)"; }
echo "POSTSTATE_OK"
"$DOCKER" restart "$CTR" || fail RESTART_FAILED
sleep "$WAIT"
echo "--- log errors (none expected):"; "$DOCKER" logs --since 2m "$CTR" 2>&1 | grep -iE 'traceback|critical|importerror|syntaxerror' | head -5
echo "--- probes:"
"$DOCKER" exec "$CTR" python3 -c "
import urllib.request
print('login', urllib.request.urlopen('http://localhost:8069/web/login').status)
for u in ('/synapsys/scaffold/context','/synapsys/scaffold/view'):
    r=urllib.request.Request('http://localhost:8069'+u,data=b'{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{}}',headers={'Content-Type':'application/json'})
    try:
        x=urllib.request.urlopen(r); print(u, x.status, x.read()[:90])
    except Exception as e: print(u, e)"
echo "INSTALL_DONE. Rollback: cd $ADDONS && patch -R -E -p1 < $PATCH && $DOCKER restart $CTR"
