#!/usr/bin/env bash
# SynapSys MCP pull-based deployer — CHG-2027-093 (Odoo x_ss_change_request 1375).
#
# Loop 3 of the separated delivery loop: the VPS PULLS merged commits from
# `main` of the public repo pnyssen/synapsys-openbridge-build. Nothing pushes
# into the server; no AI holds a key to it. A change only reaches production
# after the Steward has approved and merged its PR on GitHub.
#
# Modes (run as root):
#   status            show deployed SHA, origin/main SHA, timer state
#   adopt [SHA]       record SHA (default: current HEAD) as already deployed; no rebuild
#   run               deploy origin/main if it differs from the deployed SHA (used by the timer)
#   rollback          restore the previously deployed SHA and images
#
# Safety:
#   - refuses to act until `adopt` has recorded a baseline (no surprise first deploy)
#   - refuses if the checkout has local edits
#   - rebuilds only services whose inputs changed; keeps :ss-prev images for rollback
#   - health-checks rebuilt services; automatic rollback on failure
#   - never reads, sources or prints the .env file
set -uo pipefail

REPO="${SS_REPO:-/docker/mcp-src}"
BRANCH="${SS_BRANCH:-main}"
COMPOSE="deploy/mcp-vps/docker-compose.yml"
STATE_DIR="${SS_STATE_DIR:-/var/lib/ss-mcp-deploy}"
LOG="${SS_LOG:-/var/log/ss-mcp-deploy.log}"
DOCKER="${SS_DOCKER:-docker}"
HEALTH_WAIT="${SS_HEALTH_WAIT:-10}"
SERVICES_ALL="odoo-mcp n8n-mcp"

mkdir -p "$STATE_DIR"
ts(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
log(){ echo "$(ts) $*" | tee -a "$LOG"; }
g(){ git -C "$REPO" "$@"; }
dc(){ (cd "$REPO" && "$DOCKER" compose -f "$COMPOSE" "$@"); }

exec 9>"$STATE_DIR/lock"
flock -n 9 || { log "SKIP another run holds the lock"; exit 0; }

deployed(){ cat "$STATE_DIR/deployed_sha" 2>/dev/null; }

# Map changed paths to the services that must be rebuilt.
services_for(){ # $1=old $2=new
  local files svc=""
  files=$(g diff --name-only "$1" "$2" -- mcp-servers deploy/mcp-vps/Dockerfile "$COMPOSE")
  [ -z "$files" ] && { echo ""; return; }
  while read -r f; do
    case "$f" in
      mcp-servers/n8n_mcp.py) svc="$svc n8n-mcp" ;;
      mcp-servers/odoo_mcp.py) svc="$svc odoo-mcp" ;;
      mcp-servers/tests/*|mcp-servers/*.md|mcp-servers/*_readonly.py) ;;
      *) svc="$SERVICES_ALL" ;;   # shared module, requirements, Dockerfile, compose
    esac
  done <<< "$files"
  echo $svc | tr ' ' '\n' | sort -u | tr '\n' ' '
}

image_of(){ dc images -q "$1" 2>/dev/null | head -1; }

health(){ # $1=service
  dc exec -T "$1" python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=5).read().strip()==b'ok' else 1)" >/dev/null 2>&1
}

do_rollback(){ # $1=sha to restore  $2=services
  log "ROLLBACK to ${1:0:7} services: $2"
  g -c advice.detachedHead=false checkout -q --detach "$1"
  for s in $2; do
    if "$DOCKER" image inspect "ss-prev/$s" >/dev/null 2>&1; then
      local img; img=$(dc config --images "$s" 2>/dev/null | head -1)
      [ -n "$img" ] && "$DOCKER" tag "ss-prev/$s" "$img"
    fi
  done
  dc up -d --no-build $2 >>"$LOG" 2>&1
  echo "$1" > "$STATE_DIR/deployed_sha"
  log "ROLLBACK done"
}

case "${1:-status}" in
status)
  g fetch -q origin "$BRANCH" 2>/dev/null
  echo "deployed:    $(deployed || echo NONE)"
  echo "origin/main: $(g rev-parse origin/$BRANCH 2>/dev/null)"
  echo "checkout:    $(g rev-parse HEAD)"
  echo "local edits: $(g status --porcelain -- mcp-servers deploy | wc -l)"
  systemctl is-active ss-mcp-deploy.timer 2>/dev/null | sed 's/^/timer:       /' ;;
adopt)
  SHA=$(g rev-parse "${2:-HEAD}") || exit 1
  echo "$SHA" > "$STATE_DIR/deployed_sha"; log "ADOPT baseline ${SHA:0:7} (no rebuild)" ;;
run)
  OLD=$(deployed) || true
  [ -n "$OLD" ] || { log "HOLD no baseline; run: ss-mcp-deploy adopt"; exit 0; }
  [ -z "$(g status --porcelain -- mcp-servers deploy)" ] || { log "HOLD local edits in $REPO; deploy refused"; exit 1; }
  g fetch -q origin "$BRANCH" || { log "FAIL fetch"; exit 1; }
  NEW=$(g rev-parse "origin/$BRANCH")
  [ "$NEW" = "$OLD" ] && exit 0
  # Don't retry a commit that already failed and rolled back; wait for a new merge.
  [ "$NEW" = "$(cat "$STATE_DIR/failed_sha" 2>/dev/null)" ] && exit 0
  g merge-base --is-ancestor "$OLD" "$NEW" 2>/dev/null || { log "HOLD divergent deployment history: ${OLD:0:7} -> ${NEW:0:7}; reconcile first"; exit 1; }
  SVCS=$(services_for "$OLD" "$NEW")
  log "DEPLOY ${OLD:0:7} -> ${NEW:0:7} services: ${SVCS:-none} commits: $(g log --oneline "$OLD..$NEW" 2>/dev/null | wc -l)"
  for s in $SVCS; do id=$(image_of "$s"); [ -n "$id" ] && "$DOCKER" tag "$id" "ss-prev/$s"; done
  g -c advice.detachedHead=false checkout -q --detach "$NEW" || { log "FAIL checkout"; exit 1; }
  if [ -n "$SVCS" ]; then
    if ! dc up -d --build $SVCS >>"$LOG" 2>&1; then log "FAIL build"; echo "$NEW" > "$STATE_DIR/failed_sha"; do_rollback "$OLD" "$SVCS"; exit 1; fi
    sleep "$HEALTH_WAIT"
    for s in $SVCS; do health "$s" || { log "FAIL health $s"; echo "$NEW" > "$STATE_DIR/failed_sha"; do_rollback "$OLD" "$SVCS"; exit 1; }; done
  fi
  echo "$OLD" > "$STATE_DIR/previous_sha"; echo "$NEW" > "$STATE_DIR/deployed_sha"
  log "OK deployed ${NEW:0:7}" ;;
rollback)
  PREV=$(cat "$STATE_DIR/previous_sha" 2>/dev/null) || { log "FAIL no previous_sha"; exit 1; }
  do_rollback "$PREV" "$SERVICES_ALL" ;;
*) echo "usage: ss-mcp-deploy status|adopt [SHA]|run|rollback"; exit 2 ;;
esac
