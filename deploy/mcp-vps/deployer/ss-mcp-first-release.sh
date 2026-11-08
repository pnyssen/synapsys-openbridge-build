#!/usr/bin/env bash
# SynapSys MCP first release onto the pull-based deployer — CHG-2027-093.
#
# One-time, Steward-run bridge from the VPS's current hand-built containers
# (built from 4d6d332, which is not a commit on main) to a provenance-verified
# baseline that `ss-mcp-deploy adopt` will accept. Run as root on the VPS.
#
#   ss-mcp-first-release.sh [TARGET_SHA]            preflight only (read-only; default)
#   ss-mcp-first-release.sh --apply [TARGET_SHA]    release TARGET_SHA and adopt it
#   ss-mcp-first-release.sh --rollback              restore the pre-release images and checkout
#
# TARGET_SHA defaults to origin/main. It must be on origin/main with the
# required CI checks green on that exact commit.
#
# --apply never enables the timer. Auto-deploy stays OFF until the Steward
# runs `ss-mcp-deploy enable <CHG-ref>` after the release conditions in
# README.md (OAuth login, ChatGPT tool list, rollback rehearsal, D009).
#
# Never reads, sources or prints deploy/mcp-vps/.env (docker compose reads it).
set -uo pipefail

REPO="${SS_REPO:-/docker/mcp-src}"
COMPOSE="deploy/mcp-vps/docker-compose.yml"
STATE_DIR="${SS_STATE_DIR:-/var/lib/ss-mcp-deploy}"
LOG="${SS_LOG:-/var/log/ss-mcp-deploy.log}"
DOCKER="${SS_DOCKER:-docker}"
HEALTH_WAIT="${SS_HEALTH_WAIT:-15}"
GH_API="${SS_GH_API:-https://api.github.com}"
GH_REPO="${SS_GH_REPO:-pnyssen/synapsys-openbridge-build}"
PUBLIC_URL="${SS_PUBLIC_URL:-https://github.com/$GH_REPO.git}"
REQUIRED_CHECKS="${SS_REQUIRED_CHECKS:-test}"
DEPLOYER_BIN="${SS_DEPLOYER_BIN:-/usr/local/sbin/ss-mcp-deploy}"
UNIT_DIR="${SS_UNIT_DIR:-/etc/systemd/system}"
SYSTEMCTL="${SS_SYSTEMCTL:-systemctl}"
SERVICES="odoo-mcp n8n-mcp"
RB="$STATE_DIR/first_release_rollback"

# --apply checks out another commit under $REPO; bash reads scripts lazily,
# so a copy running from inside the checkout could be rewritten mid-run.
SELF=$(readlink -f "$0")
case "$SELF" in
  "$(readlink -f "$REPO")"/*)
    echo "HOLD: run a copy from outside $REPO, e.g.:"
    echo "  install -m 700 $SELF /root/ss-mcp-first-release.sh && /root/ss-mcp-first-release.sh"
    exit 1 ;;
esac

mkdir -p "$STATE_DIR"
ts(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
log(){ echo "$(ts) FIRST-RELEASE $*" | tee -a "$LOG"; }
hold(){ log "HOLD $*"; exit 1; }
g(){ git -C "$REPO" "$@"; }
dc(){ (cd "$REPO" && "$DOCKER" compose -f "$COMPOSE" "$@"); }
image_of(){ dc images -q "$1" 2>/dev/null | head -1; }
image_name(){ dc config --images "$1" 2>/dev/null | head -1; }
health(){
  dc exec -T "$1" python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=5).read().strip()==b'ok' else 1)" >/dev/null 2>&1
}
ci_green(){ # $1=sha — same rule as ss-mcp-deploy
  local url="$GH_API/repos/$GH_REPO/commits/$1/check-runs"
  case "$url" in https://*) url="$url?per_page=100" ;; esac
  curl -fsS --max-time 20 "$url" 2>/dev/null | REQUIRED="$REQUIRED_CHECKS" python3 -c '
import json, os, sys
runs = json.load(sys.stdin).get("check_runs", [])
for name in os.environ["REQUIRED"].split():
    mine = sorted((r for r in runs if r.get("name") == name),
                  key=lambda r: r.get("started_at") or "", reverse=True)
    if not mine or mine[0].get("status") != "completed" or mine[0].get("conclusion") != "success":
        sys.exit(1)
' 2>/dev/null
}

exec 9>"$STATE_DIR/lock"
flock -n 9 || { echo "another ss-mcp-deploy run holds the lock"; exit 1; }

MODE=preflight
case "${1:-}" in
  --apply) MODE=apply; shift ;;
  --rollback) MODE=rollback; shift ;;
  -h|--help) sed -n 2,20p "$0"; exit 0 ;;
esac

# ---------------------------------------------------------------- rollback --
if [ "$MODE" = rollback ]; then
  [ -f "$RB" ] || hold "no $RB; nothing recorded to roll back to"
  PREV=$(awk '$1=="sha"{print $2}' "$RB")
  [ -n "$PREV" ] || hold "rollback record has no sha"
  log "ROLLBACK to pre-release checkout ${PREV:0:7}"
  g -c advice.detachedHead=false checkout -q --detach "$PREV" || hold "cannot check out $PREV"
  for s in $SERVICES; do
    "$DOCKER" image inspect "ss-baseline/$s" >/dev/null 2>&1 || hold "missing image ss-baseline/$s"
    "$DOCKER" tag "ss-baseline/$s" "$(image_name "$s")" || hold "cannot retag $s"
  done
  dc up -d --no-build $SERVICES >>"$LOG" 2>&1 || hold "compose up failed during rollback; manual intervention required"
  sleep "$HEALTH_WAIT"
  for s in $SERVICES; do health "$s" || hold "rollback: $s unhealthy; manual intervention required"; done
  # The deployer must not believe the target is still the deployed baseline.
  rm -f "$STATE_DIR/deployed_sha" "$STATE_DIR/auto_deploy_enabled"
  log "ROLLBACK done: pre-release images running, deployer baseline cleared"
  exit 0
fi

# --------------------------------------------------------------- preflight --
echo "== Preflight (read-only) =="
[ "$(id -u)" = 0 ] || [ -n "${SS_ALLOW_NONROOT:-}" ] || hold "run as root"
for t in git curl python3 flock sha256sum; do command -v "$t" >/dev/null || hold "missing tool: $t"; done
"$DOCKER" compose version >/dev/null 2>&1 || hold "docker compose not available"
g rev-parse --git-dir >/dev/null 2>&1 || hold "$REPO is not a git checkout"
[ -f "$REPO/deploy/mcp-vps/.env" ] && echo "  .env: present (not read)" || hold "$REPO/deploy/mcp-vps/.env missing"

REMOTE=$(g remote get-url origin)
case "$REMOTE" in
  *@*) REMOTE_STATE="carries credentials (will be replaced by the public URL on --apply)" ;;
  "$PUBLIC_URL"|"${PUBLIC_URL%.git}") REMOTE_STATE="public, token-free" ;;
  *) REMOTE_STATE="other: will be replaced by the public URL on --apply" ;;
esac
echo "  origin remote: $REMOTE_STATE"

CUR=$(g rev-parse HEAD)
echo "  current checkout: ${CUR:0:12} ($(g rev-parse --abbrev-ref HEAD))"
EDITS=$(g status --porcelain --untracked-files=no -- mcp-servers deploy) || hold "cannot read checkout state"
[ -z "$EDITS" ] || { echo "$EDITS" | sed 's/^/    /'; hold "tracked local edits under mcp-servers/ or deploy/; commit or discard them first"; }
echo "  tracked local edits: none"

GIT_TERMINAL_PROMPT=0 git -C "$REPO" fetch -q "$PUBLIC_URL" "+refs/heads/main:refs/remotes/origin/main" \
  || hold "cannot fetch main from $PUBLIC_URL"
TARGET=$(g rev-parse --verify -q "${1:-origin/main}^{commit}") || hold "unknown target ${1:-origin/main}"
g merge-base --is-ancestor "$TARGET" origin/main || hold "target ${TARGET:0:12} is not on origin/main"
ci_green "$TARGET" || hold "required checks ($REQUIRED_CHECKS) not green on ${TARGET:0:12}"
echo "  target: ${TARGET:0:12} on origin/main, CI green"
echo "  delta: $(g rev-list --count "$CUR".."$TARGET" 2>/dev/null || echo '?') commits ahead of the current checkout"

for s in $SERVICES; do
  id=$(image_of "$s")
  [ -n "$id" ] || hold "$s: no running image found"
  if health "$s"; then h=healthy; else h=UNHEALTHY; fi
  echo "  $s: image ${id:0:19} $h"
done

if [ -x "$REPO/deploy/mcp-vps/preflight_check.sh" ] && [ -z "${SS_SKIP_HOST_PREFLIGHT:-}" ]; then
  echo "-- deploy/mcp-vps/preflight_check.sh --"
  (cd "$REPO/deploy/mcp-vps" && ./preflight_check.sh) || hold "host preflight failed"
fi

if [ "$MODE" = preflight ]; then
  echo "PREFLIGHT OK. Release with: $0 --apply ${TARGET}"
  exit 0
fi

# ------------------------------------------------------------------- apply --
log "APPLY ${CUR:0:7} -> ${TARGET:0:7}"
: > "$RB.next"
echo "sha $CUR" >> "$RB.next"
for s in $SERVICES; do
  id=$(image_of "$s")
  "$DOCKER" tag "$id" "ss-baseline/$s" || hold "cannot tag rollback image for $s"
  echo "image $s $id" >> "$RB.next"
done
mv "$RB.next" "$RB"
log "ROLLBACK_IDENTITY $(tr '\n' ' ' < "$RB")"

case "$REMOTE_STATE" in public*) ;; *) g remote set-url origin "$PUBLIC_URL" || hold "cannot set token-free remote"; log "origin set to public URL" ;; esac
g fetch -q origin main || hold "fetch from public origin failed"

fail_back(){ # $1=reason
  log "FAIL $1; restoring pre-release images"
  exec 9>&-   # the rollback run takes the lock itself
  "$SELF" --rollback && log "auto-rollback verified" || log "AUTO-ROLLBACK FAILED; manual intervention required"
  exit 1
}

g -c advice.detachedHead=false checkout -q --detach "$TARGET" || fail_back "checkout"
dc up -d --build $SERVICES >>"$LOG" 2>&1 || fail_back "build/up"
sleep "$HEALTH_WAIT"
for s in $SERVICES; do health "$s" || fail_back "health $s"; done
log "containers healthy on ${TARGET:0:7}"

install -m 755 "$REPO/deploy/mcp-vps/deployer/ss-mcp-deploy.sh" "$DEPLOYER_BIN" || fail_back "install deployer"
install -m 644 "$REPO/deploy/mcp-vps/deployer/ss-mcp-deploy.service" "$REPO/deploy/mcp-vps/deployer/ss-mcp-deploy.timer" "$UNIT_DIR/" \
  || fail_back "install units"
"$SYSTEMCTL" daemon-reload >/dev/null 2>&1 || true

# The deployer takes the same lock; release ours for these two calls.
exec 9>&-
"$DEPLOYER_BIN" adopt "$TARGET" || fail_back "adopt refused (provenance)"
"$DEPLOYER_BIN" status
log "RELEASED ${TARGET:0:7}: baseline adopted with provenance; auto-deploy remains DISABLED"
cat <<EOF

Released ${TARGET:0:12}. Auto-deploy is still OFF (timer not enabled).
Before 'ss-mcp-deploy enable <CHG-ref>' and 'systemctl enable --now ss-mcp-deploy.timer':
  1. ChatGPT / Claude connector: OAuth login completes against n8n-mcp and odoo-mcp.
  2. Connector tool list shows trigger_webhook with the optional auth_profile argument.
  3. If W15 profiles are configured in .env: one bounded W15 dispatch PASS, and an
     unlisted path refused (AUTH_PATH_NOT_ALLOWED).
  4. Rollback rehearsal if wanted: $SELF --rollback  (then --apply again).
  5. D009 independent assurance of this release.
EOF
