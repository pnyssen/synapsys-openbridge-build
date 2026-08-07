#!/usr/bin/env bash
# Preflight for `docker compose -f docker-compose.yml up -d --build`.
#
# This deploy deliberately joins the N8N project's `n8n_default` network as
# external and relies on that project's already-running Traefik container
# for TLS/routing (see the comment at the top of docker-compose.yml) rather
# than owning either of those things itself. That keeps this repo from
# touching a production compose file it doesn't own, but it means a silent
# rename of that network or a stopped Traefik container fails this deploy
# in a way `docker compose up` alone won't explain clearly. Run this first.

set -euo pipefail

NETWORK="n8n_default"
DOMAIN_NAME="${DOMAIN_NAME:-}"
if [[ -z "$DOMAIN_NAME" && -f .env ]]; then
  DOMAIN_NAME="$(grep -E '^DOMAIN_NAME=' .env | cut -d= -f2- || true)"
fi

FAIL=0

echo "-- Checking external network '${NETWORK}' exists --"
if docker network inspect "$NETWORK" >/dev/null 2>&1; then
  echo "  OK: ${NETWORK} exists"
else
  echo "  FAIL: network '${NETWORK}' not found. Is the N8N compose project"
  echo "        (docker/n8n/docker-compose.yml) actually running on this host?"
  echo "        List available networks: docker network ls"
  FAIL=1
fi

echo "-- Checking a Traefik container is running and attached to ${NETWORK} --"
TRAEFIK_CIDS=$(docker ps --filter "label=traefik.enable=true" -q 2>/dev/null || true)
TRAEFIK_BY_IMAGE=$(docker ps --filter "ancestor=traefik" -q 2>/dev/null || true)
if [[ -n "$TRAEFIK_BY_IMAGE" ]]; then
  echo "  OK: found a running container from a 'traefik' image"
else
  echo "  WARNING: no running container matched image name 'traefik' — if your"
  echo "           Traefik uses a different/pinned image tag this check under-detects;"
  echo "           confirm manually with: docker ps | grep -i traefik"
fi

echo "-- Checking for port collisions on 8000 (this deploy's internal MCP port) --"
if command -v ss >/dev/null 2>&1; then
  ss -tlnp 2>/dev/null | grep -q ':8000 ' && \
    echo "  NOTE: something is already listening on :8000 host-side — confirm it's not a conflict (this deploy's port 8000 is container-internal only, not published to the host, but double check docker-compose.yml hasn't changed that)." || \
    echo "  OK: no host-level listener on :8000"
else
  echo "  skip: 'ss' not available to check"
fi

if [[ -n "$DOMAIN_NAME" ]]; then
  echo "-- Checking DNS resolves for expected hostnames under ${DOMAIN_NAME} --"
  for HOST in "odoo-mcp.${DOMAIN_NAME}" "n8n-mcp.${DOMAIN_NAME}"; do
    if getent hosts "$HOST" >/dev/null 2>&1 || host "$HOST" >/dev/null 2>&1; then
      echo "  OK: ${HOST} resolves"
    else
      echo "  WARNING: ${HOST} does not resolve — Traefik's TLS cert issuance will fail until DNS is fixed"
    fi
  done
else
  echo "-- Skipping DNS check: DOMAIN_NAME not set and no .env found --"
fi

echo "-- Checking .env exists and is not world-readable --"
if [[ -f .env ]]; then
  PERM=$(stat -c '%a' .env 2>/dev/null || stat -f '%Lp' .env 2>/dev/null || echo "??")
  echo "  .env present, permissions: ${PERM}"
  if [[ "$PERM" != "600" && "$PERM" != "400" ]]; then
    echo "  WARNING: .env should be chmod 600 (holds live ODOO_API_KEY, N8N_API_TOKEN, MCP bearer tokens)"
  fi
else
  echo "  FAIL: .env not found — copy .env.example and fill in real values first"
  FAIL=1
fi

echo
if [[ "$FAIL" -eq 1 ]]; then
  echo "PREFLIGHT FAILED — fix the FAIL items above before running docker compose up."
  exit 1
fi
echo "PREFLIGHT OK — safe to run: docker compose -f docker-compose.yml up -d --build"
