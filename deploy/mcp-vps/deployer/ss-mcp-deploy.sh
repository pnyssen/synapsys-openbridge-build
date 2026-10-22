#!/usr/bin/env bash
# SynapSys MCP pull-based deployer — CHG-2027-093 (Odoo x_ss_change_request 1375).
#
# Loop 3 of the separated delivery loop: the VPS PULLS merged commits from
# `main` of the public repo pnyssen/synapsys-openbridge-build. Nothing pushes
# into the server; no AI holds a key to it. A change only reaches production
# after the Steward has approved and merged its PR on GitHub.
#
# Modes (run as root):
#   status              show deployed SHA, origin/main SHA, gate and provenance state
#   adopt [SHA]         record SHA (default: current HEAD) as already deployed; no rebuild.
#                       Refused unless every running container's source matches SHA.
#   enable CHG-REF      allow `run` to deploy (release-gated; requires a verified baseline)
#   disable             stop `run` from deploying (containers keep running)
#   run                 deploy origin/main if it differs from the deployed SHA (used by the timer)
#   rollback            restore the previously deployed SHA and images
#
# Safety (every failed gate is a HOLD: nothing is changed):
#   - auto-deploy is OFF until `enable <CHG-ref>` is run by the Steward
#   - refuses to act until `adopt` has recorded a provenance-verified baseline
#   - refuses if the checkout has local edits
#   - refuses divergent history (deployed SHA not an ancestor of origin/main)
#   - refuses a commit whose required CI checks are not green on that exact SHA
#   - refuses if the running containers no longer match the deployed SHA (drift)
#   - rebuilds only services whose inputs changed; keeps :ss-prev images for rollback
#   - health + source-provenance check after deploy; automatic rollback on failure
#   - never reads, sources or prints the .env file
set -uo pipefail

REPO="${SS_REPO:-/docker/mcp-src}"
BRANCH="${SS_BRANCH:-main}"
COMPOSE="deploy/mcp-vps/docker-compose.yml"
DOCKERFILE="deploy/mcp-vps/Dockerfile"
STATE_DIR="${SS_STATE_DIR:-/var/lib/ss-mcp-deploy}"
LOG="${SS_LOG:-/var/log/ss-mcp-deploy.log}"
DOCKER="${SS_DOCKER:-docker}"
HEALTH_WAIT="${SS_HEALTH_WAIT:-10}"
APP_DIR="${SS_APP_DIR:-/app}"
GH_API="${SS_GH_API:-https://api.github.com}"
GH_REPO="${SS_GH_REPO:-pnyssen/synapsys-openbridge-build}"
REQUIRED_CHECKS="${SS_REQUIRED_CHECKS:-test}"   # mcp-tests.yml job name
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
  files=$(g diff --name-only "$1" "$2" -- mcp-servers "$DOCKERFILE" "$COMPOSE")
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

# Source provenance: the files the Dockerfile at $1 copies from mcp-servers/
# into the image, minus the other service's entry script (which that service
# never runs, and which services_for() does not rebuild it for).
app_files(){ # $1=sha $2=service
  local other
  case "$2" in odoo-mcp) other=n8n_mcp.py ;; n8n-mcp) other=odoo_mcp.py ;; *) other="" ;; esac
  g show "$1:$DOCKERFILE" 2>/dev/null \
    | awk '$1=="COPY"{for(i=2;i<NF;i++) if($i ~ /^mcp-servers\//) print $i}' \
    | sed 's#^mcp-servers/##' | grep -vxF "${other:-/}" | sort -u
}

# 0 iff every app file in the running container of $2 is byte-identical to
# the same file at commit $1. Prints the first mismatch reason otherwise.
provenance_ok(){ # $1=sha $2=service
  local files f want got
  files=$(app_files "$1" "$2")
  [ -n "$files" ] || { echo "no app files resolvable at ${1:0:7}"; return 1; }
  for f in $files; do
    want=$(g show "$1:mcp-servers/$f" 2>/dev/null | sha256sum | cut -d' ' -f1)
    got=$(dc exec -T "$2" sha256sum "$APP_DIR/$f" 2>/dev/null | cut -d' ' -f1)
    [ -n "$got" ] && [ "$got" = "$want" ] || { echo "$2:$f differs from ${1:0:7}"; return 1; }
  done
  return 0
}

all_provenance_ok(){ # $1=sha
  local s why
  for s in $SERVICES_ALL; do
    why=$(provenance_ok "$1" "$s") || { echo "$why"; return 1; }
  done
  return 0
}

# 0 iff every required check run on this exact commit completed successfully.
ci_green(){ # $1=sha
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

do_rollback(){ # $1=sha to restore  $2=services   (returns 1 if the restore is not verified)
  log "ROLLBACK to ${1:0:7} services: $2"
  g -c advice.detachedHead=false checkout -q --detach "$1" || { log "ROLLBACK FAILED checkout ${1:0:7}; manual intervention required"; return 1; }
  for s in $2; do
    if "$DOCKER" image inspect "ss-prev/$s" >/dev/null 2>&1; then
      local img; img=$(dc config --images "$s" 2>/dev/null | head -1)
      [ -n "$img" ] && "$DOCKER" tag "ss-prev/$s" "$img"
    fi
  done
  if [ -n "$2" ]; then   # an empty list must never reach `compose up` (= every service)
    dc up -d --no-build $2 >>"$LOG" 2>&1 || { log "ROLLBACK FAILED compose up; manual intervention required"; return 1; }
    sleep "$HEALTH_WAIT"
  fi
  local s why
  for s in $2; do
    health "$s" || { log "ROLLBACK FAILED health $s; manual intervention required"; return 1; }
  done
  # Every service, not only the restored ones: services that were not
  # rebuilt must already match $1, or the restore is not what it claims.
  why=$(all_provenance_ok "$1") || { log "ROLLBACK FAILED provenance: $why; manual intervention required"; return 1; }
  echo "$1" > "$STATE_DIR/deployed_sha"
  log "ROLLBACK done ${1:0:7} (verified)"
}

case "${1:-status}" in
status)
  g fetch -q origin "$BRANCH" 2>/dev/null
  echo "deployed:    $(deployed || echo NONE)"
  echo "origin/main: $(g rev-parse origin/$BRANCH 2>/dev/null)"
  echo "checkout:    $(g rev-parse HEAD)"
  echo "local edits: $(g status --porcelain --untracked-files=no -- mcp-servers deploy | wc -l)"
  echo "auto-deploy: $(cat "$STATE_DIR/auto_deploy_enabled" 2>/dev/null || echo DISABLED)"
  if D=$(deployed) && [ -n "$D" ]; then
    why=$(all_provenance_ok "$D") && echo "provenance:  OK (running source = ${D:0:7})" || echo "provenance:  MISMATCH ($why)"
  fi
  systemctl is-active ss-mcp-deploy.timer 2>/dev/null | sed 's/^/timer:       /' ;;
adopt)
  SHA=$(g rev-parse --verify -q "${2:-HEAD}^{commit}") || { log "HOLD adopt: unknown commit ${2:-HEAD}"; exit 1; }
  why=$(all_provenance_ok "$SHA") || { log "HOLD adopt ${SHA:0:7}: running containers do not match it ($why). Build and verify a known SHA first; baseline not recorded"; exit 1; }
  echo "$SHA" > "$STATE_DIR/deployed_sha"; log "ADOPT baseline ${SHA:0:7} (provenance verified; no rebuild)" ;;
enable)
  REF="${2:-}"
  [[ "$REF" =~ ^CHG-[0-9]{4}-[0-9]{3,}$ ]] || { echo "usage: ss-mcp-deploy enable CHG-YYYY-NNN"; exit 2; }
  D=$(deployed) && [ -n "$D" ] || { log "HOLD enable: no baseline; run adopt first"; exit 1; }
  why=$(all_provenance_ok "$D") || { log "HOLD enable: baseline ${D:0:7} not verified ($why)"; exit 1; }
  echo "$REF $(ts)" > "$STATE_DIR/auto_deploy_enabled"; log "ENABLE auto-deploy under $REF (baseline ${D:0:7})" ;;
disable)
  rm -f "$STATE_DIR/auto_deploy_enabled"; log "DISABLE auto-deploy" ;;
run)
  [ -f "$STATE_DIR/auto_deploy_enabled" ] || { log "HOLD auto-deploy disabled; run: ss-mcp-deploy enable <CHG-ref>"; exit 0; }
  OLD=$(deployed) || true
  [ -n "$OLD" ] || { log "HOLD no baseline; run: ss-mcp-deploy adopt"; exit 0; }
  # Tracked files only: the untracked deploy/mcp-vps/.env compose reads must
  # not block deploys. A failing `git status` is itself a HOLD.
  EDITS=$(g status --porcelain --untracked-files=no -- mcp-servers deploy) || { log "HOLD cannot read checkout state in $REPO"; exit 1; }
  [ -z "$EDITS" ] || { log "HOLD local edits in $REPO; deploy refused"; exit 1; }
  g fetch -q origin "$BRANCH" || { log "FAIL fetch"; exit 1; }
  NEW=$(g rev-parse "origin/$BRANCH")
  [ "$NEW" = "$OLD" ] && exit 0
  # Don't retry a commit that already failed and rolled back; wait for a new merge.
  [ "$NEW" = "$(cat "$STATE_DIR/failed_sha" 2>/dev/null)" ] && exit 0
  g merge-base --is-ancestor "$OLD" "$NEW" 2>/dev/null || { log "HOLD divergent deployment history: ${OLD:0:7} -> ${NEW:0:7}; reconcile first"; exit 1; }
  ci_green "$NEW" || { log "HOLD ${NEW:0:7}: required checks ($REQUIRED_CHECKS) not green on this commit"; exit 0; }
  why=$(all_provenance_ok "$OLD") || { log "HOLD drift: running containers no longer match deployed ${OLD:0:7} ($why)"; exit 1; }
  SVCS=$(services_for "$OLD" "$NEW")
  log "DEPLOY ${OLD:0:7} -> ${NEW:0:7} services: ${SVCS:-none} commits: $(g log --oneline "$OLD..$NEW" 2>/dev/null | wc -l)"
  : > "$STATE_DIR/rollback_identity.next"
  echo "sha $OLD" >> "$STATE_DIR/rollback_identity.next"
  for s in $SVCS; do
    id=$(image_of "$s")
    [ -n "$id" ] || { log "HOLD no running image for $s; rollback identity unavailable"; exit 1; }
    "$DOCKER" tag "$id" "ss-prev/$s" || { log "HOLD cannot tag rollback image for $s"; exit 1; }
    echo "image $s $id" >> "$STATE_DIR/rollback_identity.next"
  done
  log "ROLLBACK_IDENTITY $(tr '\n' ' ' < "$STATE_DIR/rollback_identity.next")"
  g -c advice.detachedHead=false checkout -q --detach "$NEW" || { log "FAIL checkout"; exit 1; }
  if [ -n "$SVCS" ]; then
    if ! dc up -d --build $SVCS >>"$LOG" 2>&1; then log "FAIL build"; echo "$NEW" > "$STATE_DIR/failed_sha"; do_rollback "$OLD" "$SVCS"; exit 1; fi
    sleep "$HEALTH_WAIT"
    for s in $SVCS; do health "$s" || { log "FAIL health $s"; echo "$NEW" > "$STATE_DIR/failed_sha"; do_rollback "$OLD" "$SVCS"; exit 1; }; done
  fi
  why=$(all_provenance_ok "$NEW") || { log "FAIL provenance after deploy ($why)"; echo "$NEW" > "$STATE_DIR/failed_sha"; do_rollback "$OLD" "$SVCS"; exit 1; }
  mv "$STATE_DIR/rollback_identity.next" "$STATE_DIR/rollback_identity"
  echo "$OLD" > "$STATE_DIR/previous_sha"; echo "$NEW" > "$STATE_DIR/deployed_sha"
  log "OK deployed ${NEW:0:7} (provenance verified)" ;;
rollback)
  PREV=$(cat "$STATE_DIR/previous_sha" 2>/dev/null) || { log "FAIL no previous_sha"; exit 1; }
  IDENT="$STATE_DIR/rollback_identity"
  grep -qxF "sha $PREV" "$IDENT" 2>/dev/null || { log "FAIL rollback identity missing or not for ${PREV:0:7}; nothing changed"; exit 1; }
  # Restore exactly the services the last deploy rebuilt (their ss-prev
  # images were tagged by that deploy); any other ss-prev tag may be stale.
  SVCS=$(awk '$1=="image"{print $2}' "$IDENT" | tr '\n' ' ')
  # Mark the rolled-back commit failed so the timer does not redeploy it;
  # the next merge to main is deployed as usual.
  CUR=$(deployed) && [ -n "$CUR" ] && echo "$CUR" > "$STATE_DIR/failed_sha"
  do_rollback "$PREV" "$SVCS" || exit 1 ;;
*) echo "usage: ss-mcp-deploy status|adopt [SHA]|enable CHG-REF|disable|run|rollback"; exit 2 ;;
esac
