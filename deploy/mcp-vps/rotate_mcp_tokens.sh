#!/usr/bin/env bash
# Rotate MCP_AUTH_TOKEN_ODOO and/or MCP_AUTH_TOKEN_N8N on this VPS.
#
# Closes the item logged in SECRETS_INDEX.md: both tokens were partially
# exposed in chat on 2026-07-14 and have been "pending rotation decision"
# since. Run this ON THE VPS, in this directory, by whoever holds shell
# access — it is not executed by any AI lane.
#
# What it does:
#   1. Generates a fresh 32-byte hex token for each target (openssl rand).
#   2. Backs up the current .env (timestamped, chmod 600) before touching it.
#   3. Replaces the old token value(s) in .env in place.
#   4. Restarts only the affected container(s) — not the whole stack.
#   5. Verifies the new token against the container's own /health endpoint
#      and confirms the OLD token no longer authenticates.
#   6. Prints the last 8 chars of each new token only (never the full
#      value) so the operator can update the password manager entry and
#      the SECRETS_INDEX.md rotation-note column per this repo's own
#      logging discipline. The full value is only ever in .env on disk.
#
# Usage:
#   ./rotate_mcp_tokens.sh odoo      # rotate MCP_AUTH_TOKEN_ODOO only
#   ./rotate_mcp_tokens.sh n8n       # rotate MCP_AUTH_TOKEN_N8N only
#   ./rotate_mcp_tokens.sh both      # rotate both (default if no arg given)

set -euo pipefail

TARGET="${1:-both}"
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Run this from deploy/mcp-vps/ on the VPS." >&2
  exit 1
fi

case "$TARGET" in
  odoo) VARS=(MCP_AUTH_TOKEN_ODOO) ;;
  n8n)  VARS=(MCP_AUTH_TOKEN_N8N) ;;
  both) VARS=(MCP_AUTH_TOKEN_ODOO MCP_AUTH_TOKEN_N8N) ;;
  *) echo "ERROR: unknown target '$TARGET' — use odoo, n8n, or both" >&2; exit 1 ;;
esac

declare -A SERVICE_FOR_VAR=(
  [MCP_AUTH_TOKEN_ODOO]="odoo-mcp"
  [MCP_AUTH_TOKEN_N8N]="n8n-mcp"
)
declare -A HOSTVAR_FOR_VAR=(
  [MCP_AUTH_TOKEN_ODOO]="odoo-mcp"
  [MCP_AUTH_TOKEN_N8N]="n8n-mcp"
)

BACKUP="${ENV_FILE}.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp "$ENV_FILE" "$BACKUP"
chmod 600 "$BACKUP"
echo "Backed up current .env -> $BACKUP (chmod 600)"

DOMAIN_NAME="$(grep -E '^DOMAIN_NAME=' "$ENV_FILE" | cut -d= -f2-)"
if [[ -z "$DOMAIN_NAME" ]]; then
  echo "ERROR: DOMAIN_NAME not set in $ENV_FILE" >&2
  exit 1
fi

for VAR in "${VARS[@]}"; do
  OLD_VALUE="$(grep -E "^${VAR}=" "$ENV_FILE" | cut -d= -f2-)"
  NEW_VALUE="$(openssl rand -hex 32)"

  if grep -qE "^${VAR}=" "$ENV_FILE"; then
    sed -i "s|^${VAR}=.*|${VAR}=${NEW_VALUE}|" "$ENV_FILE"
  else
    echo "${VAR}=${NEW_VALUE}" >> "$ENV_FILE"
  fi

  SERVICE="${SERVICE_FOR_VAR[$VAR]}"
  HOST="${HOSTVAR_FOR_VAR[$VAR]}.${DOMAIN_NAME}"

  echo "Restarting ${SERVICE}..."
  docker compose -f "$COMPOSE_FILE" up -d --no-deps "$SERVICE"

  echo "Waiting for ${SERVICE} to come back up..."
  for i in $(seq 1 15); do
    if curl -fsS "https://${HOST}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  echo "Verifying new token authenticates against ${SERVICE}..."
  # /health itself is unauthenticated by design (see odoo_mcp.py / n8n_mcp.py);
  # the real check is an authenticated MCP call. Adjust the endpoint below if
  # your client library differs — this uses a bare tools/list JSON-RPC call.
  NEW_OK=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://${HOST}/mcp" \
    -H "Authorization: Bearer ${NEW_VALUE}" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}') || NEW_OK="000"

  if [[ -n "$OLD_VALUE" ]]; then
    OLD_STILL_WORKS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://${HOST}/mcp" \
      -H "Authorization: Bearer ${OLD_VALUE}" \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}') || OLD_STILL_WORKS="000"
  else
    OLD_STILL_WORKS="n/a"
  fi

  echo "  new token -> HTTP ${NEW_OK} (expect 200)"
  echo "  old token -> HTTP ${OLD_STILL_WORKS} (expect 401/403, confirms rotation took effect)"
  echo "  new ${VAR} ends in: ...${NEW_VALUE: -8}  (record this in SECRETS_INDEX.md's rotation note and the password manager entry — never the full value)"
  echo
done

echo "Done. Next steps (not automated by this script):"
echo "  1. Update the password-manager entry for each rotated token (see SECRETS_INDEX.md naming convention)."
echo "  2. Update SECRETS_INDEX.md's 'Rotation note' column with today's date and 'rotated, last-8 ...<chars>'."
echo "  3. If verification above failed for any service, restore from $BACKUP and investigate before retrying."
echo "  4. Delete $BACKUP once rotation is confirmed good and recorded (it holds the OLD tokens in plaintext)."
