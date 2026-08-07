# Secrets Index — MCP Hosting (odoo-mcp / n8n-mcp)

Non-secret catalogue. **No credential value ever goes in this file** — it
only records *that a credential exists*, *what consumes it*, and *where to
find the actual value in the password manager*. Safe to commit.

Naming convention for the password-manager entry (LastPass or equivalent):
`SynapSys - <service> - <artifact>` — one entry per credential-bearing
artifact, filed under a `SynapSys` folder (use `SynapSys/Entra`,
`SynapSys/VPS`, `SynapSys/Odoo`, `SynapSys/N8N` subfolders), tagged
`synapsys` + the service name so folder browsing and tag search both work.

| LastPass entry name | What it is | Consumed by (file / env var) | Rotation note |
|---|---|---|---|
| `SynapSys - Odoo - API key (shared)` | Odoo API key, service account `phil@synapsys.com.au` | `deploy/mcp-vps/.env` → `ODOO_API_KEY`; also used by `.mcp.json` readonly servers | Shared with other lanes — do not rotate without checking downstream users |
| `SynapSys - N8N - API token` | N8N REST API token | `deploy/mcp-vps/.env` → `N8N_API_TOKEN` | |
| `SynapSys - VPS - MCP_AUTH_TOKEN_ODOO` | Bearer token guarding `odoo-mcp` HTTP endpoint | `deploy/mcp-vps/.env` → `MCP_AUTH_TOKEN_ODOO`; generated on-VPS via `openssl rand -hex 32` | Exposed in chat 2026-07-14 (partial) — **rotate via `./rotate_mcp_tokens.sh odoo`**, then update this row with rotation date + last-8-chars |
| `SynapSys - VPS - MCP_AUTH_TOKEN_N8N` | Bearer token guarding `n8n-mcp` HTTP endpoint | `deploy/mcp-vps/.env` → `MCP_AUTH_TOKEN_N8N`; generated on-VPS | Exposed in chat 2026-07-14 (partial) — **rotate via `./rotate_mcp_tokens.sh n8n`**, then update this row with rotation date + last-8-chars |
| `SynapSys - Entra - odoo-mcp-api (App ID + secret)` | API app registration — exposes the OAuth scope | `odoo_mcp.py` OAuth facade → `MCP_API_AUDIENCE` (App ID URI, non-secret) | Note: this app has no client secret of its own unless one was added by mistake — see connector app below |
| `SynapSys - Entra - odoo-mcp-connector (App ID + secret)` | Confidential client app — requests the API app's scope | `odoo_mcp.py` OAuth facade → `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET` | |
| `SynapSys - Entra - n8n-mcp-api (App ID + secret)` | API app registration | `n8n_mcp.py` OAuth facade → `MCP_API_AUDIENCE` | **Not yet created — run `./setup_n8n_mcp_entra.sh` to create this and the connector app below in one pass**, then fill in real appId/secret here |
| `SynapSys - Entra - n8n-mcp-connector (App ID + secret)` | Confidential client app | `n8n_mcp.py` OAuth facade → `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET` | **Not yet created — see `./setup_n8n_mcp_entra.sh`** |
| `SynapSys - Entra - Tenant ID` | Shared tenant ID, used by both facades | Both `.env` files → `ENTRA_TENANT_ID` | Not secret, but keep alongside for one-stop lookup |

## How to use this file

1. When a new credential is minted, add one row here (metadata only) and one
   entry in the password manager using the naming convention above.
2. Notes/description fields in the password-manager entry should name the
   exact env var and file it fills in — copy straight from this table.
3. When rotating, update the "Rotation note" column with the date and reason
   so the history survives even if the password-manager entry's own history
   is trimmed.
4. This table is the map; the password manager is the vault. Search this
   file first to find *which* entry you need, then look it up by exact name.

## Runbooks (run on the VPS, by whoever holds shell access — not by any AI lane)

- **Rotate a bearer token**: `./rotate_mcp_tokens.sh [odoo|n8n|both]` — generates
  a fresh token, backs up `.env` first, restarts only the affected container,
  verifies the new token works and the old one no longer does.
- **Create the missing n8n-mcp Entra app pair**: `DOMAIN_NAME=<domain>
  ./setup_n8n_mcp_entra.sh` — mirrors the existing odoo-mcp `-api`/`-connector`
  split, prints the four env values to add to `.env`. Requires `az login` as
  an Application Administrator first; this is a human action.
- **Back up VPS-side state**: `./backup_vps.sh` — archives the two OAuth
  state volumes and (if `.env` has N8N credentials) an N8N workflow export.
  Deliberately excludes `.env` itself; secrets stay in the password manager.
  Suggested as a daily cron — see the script header for the exact line.
- **Before `docker compose up` on a fresh or changed host**: `./preflight_check.sh`
  — confirms the external `n8n_default` network and Traefik are actually
  there before this deploy tries to join them, since this compose file
  deliberately depends on infrastructure it doesn't own (see the comment at
  the top of `docker-compose.yml`).
