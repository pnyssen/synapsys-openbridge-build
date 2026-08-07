#!/usr/bin/env bash
# Create the missing Entra ID (Azure AD) app registration pair for n8n-mcp.
#
# Closes the gap logged in SECRETS_INDEX.md: odoo-mcp already has its
# "-api" / "-connector" app pair, n8n-mcp does not ("Not yet created"),
# so n8n-mcp currently runs bearer-token-only while odoo-mcp additionally
# supports Entra OAuth sign-in for connector UIs (see mcp-servers/_azure_auth.py
# for how the two apps are consumed at runtime).
#
# This mirrors the SAME two-app split odoo-mcp already uses:
#   - "<prefix>-api"       — resource app; exposes the mcp.access scope
#   - "<prefix>-connector" — confidential client app; requests that scope
# _azure_auth.py's comment block explains why the split exists (Entra issues
# tokens whose `aud` is the resource app's bare client ID, not its
# api://... URI — the code already accounts for this).
#
# Prerequisites:
#   - Azure CLI installed and logged in (`az login`) as a user with
#     Application Administrator (or equivalent) rights in the SynapSys tenant.
#   - Nobody in this AI ecosystem currently holds a verified grant to do
#     this (see NAVIGATOR_D007-adjacent filings on VPS/Entra access) — this
#     is a human action, run from wherever `az` is authenticated, not from
#     any AI session.
#
# This script only PRINTS the values to fill into deploy/mcp-vps/.env — it
# does not write .env itself, so a secret is never silently placed in a
# file this script's own stdout/history could leak twice.

set -euo pipefail

DOMAIN_NAME="${DOMAIN_NAME:?Set DOMAIN_NAME env var first, e.g. export DOMAIN_NAME=srv1536619.hstgr.cloud}"
PREFIX="n8n-mcp"
SCOPE_NAME="mcp.access"
REDIRECT_URI="https://${PREFIX}.${DOMAIN_NAME}/auth/callback"

echo "== 1. Create the resource ('-api') app =="
API_APP_ID=$(az ad app create \
  --display-name "${PREFIX}-api" \
  --sign-in-audience AzureADMyOrg \
  --query appId -o tsv)
echo "  ${PREFIX}-api appId: ${API_APP_ID}"

API_OBJECT_ID=$(az ad app show --id "$API_APP_ID" --query id -o tsv)

# Set the Application ID URI (api://<appId>) — this is MCP_API_AUDIENCE.
az ad app update --id "$API_APP_ID" --identifier-uris "api://${API_APP_ID}"

# Expose the mcp.access scope that AzureProvider requests (see _azure_auth.py:
# `required_scopes=[scope]` where scope defaults to "mcp.access").
SCOPE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/${API_OBJECT_ID}" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"oauth2PermissionScopes\": [
        {
          \"id\": \"${SCOPE_ID}\",
          \"value\": \"${SCOPE_NAME}\",
          \"type\": \"User\",
          \"adminConsentDisplayName\": \"Access n8n-mcp\",
          \"adminConsentDescription\": \"Allows the app to call the n8n-mcp server on behalf of the signed-in user.\",
          \"userConsentDisplayName\": \"Access n8n-mcp\",
          \"userConsentDescription\": \"Allow this app to call the n8n-mcp server.\",
          \"isEnabled\": true
        }
      ]
    }
  }"
echo "  exposed scope: api://${API_APP_ID}/${SCOPE_NAME}"

echo
echo "== 2. Create the client ('-connector') app =="
CONNECTOR_APP_ID=$(az ad app create \
  --display-name "${PREFIX}-connector" \
  --sign-in-audience AzureADMyOrg \
  --web-redirect-uris "$REDIRECT_URI" \
  --query appId -o tsv)
echo "  ${PREFIX}-connector appId: ${CONNECTOR_APP_ID}"

CONNECTOR_OBJECT_ID=$(az ad app show --id "$CONNECTOR_APP_ID" --query id -o tsv)

echo "  minting client secret (shown once — copy it into the password manager NOW)..."
CONNECTOR_SECRET=$(az ad app credential reset \
  --id "$CONNECTOR_APP_ID" \
  --display-name "n8n-mcp-connector-secret-$(date -u +%Y%m%d)" \
  --years 1 \
  --query password -o tsv)

# Grant the connector app the api app's exposed scope.
az ad app permission add \
  --id "$CONNECTOR_APP_ID" \
  --api "$API_APP_ID" \
  --api-permissions "${SCOPE_ID}=Scope"

echo
echo "== 3. Also create a Service Principal for each app (required before admin consent) =="
az ad sp create --id "$API_APP_ID" >/dev/null 2>&1 || echo "  (service principal for -api already exists)"
az ad sp create --id "$CONNECTOR_APP_ID" >/dev/null 2>&1 || echo "  (service principal for -connector already exists)"

echo
echo "== 4. Grant admin consent (requires tenant admin) =="
az ad app permission admin-consent --id "$CONNECTOR_APP_ID" \
  || echo "  admin-consent failed/needs a tenant admin — run manually: az ad app permission admin-consent --id ${CONNECTOR_APP_ID}"

cat <<EOF

===============================================================
DONE. Fill these into deploy/mcp-vps/.env (never commit the file):

  ENTRA_TENANT_ID=$(az account show --query tenantId -o tsv)
  N8N_OAUTH_CLIENT_ID=${CONNECTOR_APP_ID}
  N8N_OAUTH_CLIENT_SECRET=${CONNECTOR_SECRET}
  N8N_MCP_API_AUDIENCE=api://${API_APP_ID}

Then also record (metadata only, no secret value) two new rows in
SECRETS_INDEX.md, same pattern as the existing odoo-mcp-api /
odoo-mcp-connector rows, and add matching password-manager entries:
  "SynapSys - Entra - n8n-mcp-api (App ID + secret)"
  "SynapSys - Entra - n8n-mcp-connector (App ID + secret)"

Restart n8n-mcp to pick up the new env vars:
  docker compose -f docker-compose.yml up -d --no-deps n8n-mcp

Verify: hit https://n8n-mcp.${DOMAIN_NAME}/.well-known/oauth-protected-resource
and confirm it now advertises Entra OAuth alongside the existing bearer path.
===============================================================
EOF
