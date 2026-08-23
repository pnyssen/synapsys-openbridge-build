# SharePoint MCP — Recovery + Patch Spec (D1/D2/D3)

**Status:** BLOCKED_ON_SOURCE_RECOVERY. This file exists so the fix is ready to apply the
moment the running server's source lands in this repo — it is not itself the fix.

## Why this file exists instead of a patch

The SharePoint MCP server backing `mcp__.../sp_list`, `sp_read`, `sp_resolve_item`, etc. is not
built from, tracked by, or reproducible from this repository. Verified directly against this
repo at `HEAD 40ada95` (2026-08-23):

| Check | Result |
|---|---|
| `grep -rl "def sp_list"` across the repo | no matches |
| `mcp-servers/` contents | `odoo_mcp.py`, `odoo_mcp_readonly.py`, `n8n_mcp.py`, `n8n_mcp_readonly.py`, `_azure_auth.py`, `_bearer_auth.py` — no sharepoint module |
| `deploy/mcp-vps/docker-compose.yml` services | `odoo-mcp`, `n8n-mcp` only — no sharepoint service |
| `deploy/mcp-vps/Dockerfile` `COPY` line | copies only the odoo/n8n scripts — sharepoint is not built by this image |

The server is live in production on the Hostinger VPS as an independently-deployed container with
no tracked build. It cannot be patched until its source exists somewhere version-controlled.

**Recovery (one command, needs VPS shell access):**

```
docker ps                                    # identify the sharepoint mcp container
docker cp <container>:/app/. ./spmcp-recovered/
```

Once `spmcp-recovered/` exists, commit it into `mcp-servers/` (matching the existing
`odoo_mcp.py`/`n8n_mcp.py` reference-copy convention already documented in
`mcp-servers/README.md`), add a `sharepoint-mcp` service to
`deploy/mcp-vps/docker-compose.yml` alongside the existing two, and extend the Dockerfile's
`COPY` line — then the D1/D2/D3 patch below applies directly against the real source instead of
being reconstructed from behavioral observation.

## Provenance

Root cause and defect enumeration (D1/D2/D3 below) originally diagnosed and specified by
`claude_cowork`, filed at
`ARCHITECTURE_DATA_RECONCILIATION/20260823--claude-cowork--fix-record-and-patch-spec--sp-list-truncation-and-shadow-tree--v1-0.md`
(SynapSys Working Memory, under
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/`), SHA-256
`80a3731cc99289cbd46c5eacaecfadb5cb90c27b3676fc8a093a6e9152194293` — independently read and
byte-verified by `claude_code` before transcription here. Reproduced in full below so the spec
lives with the code it targets, not only in Working Memory (which is itself reachable by the same
doubled-root defect D2 describes).

## D1 — Silent truncation (highest priority)

`sp_list` currently returns a bounded page with no indication that more items exist. A caller
cannot distinguish "this folder has 11 files" from "here are the first 11 of 200." Every negative
conclusion drawn from a long listing is unsound — this was independently reproduced twice more in
a different tool the same day (`search_odoo` with `limit: 40` returning exactly 40 rows from a
53-row register with no truncation signal).

**Required behaviour:** return a structured envelope, never a bare array.

```json
{ "items": [...], "count": 200, "returned": 200, "truncated": false, "next": null }
```

When the underlying Graph API paginates, set `truncated: true` and return `next` as the
continuation token. Accept an optional `after` parameter to resume. A caller receiving
`truncated: true` without following `next` must treat the result as UNKNOWN, not as absent.

## D2 — Doubled-root paths resolve silently

`sp_diagnostics` reports `SP_ROOT = SynapSys-Control/11_WORKING_MEMORY`. A caller who includes
`11_WORKING_MEMORY` as a leading path segment produces
`.../11_WORKING_MEMORY/11_WORKING_MEMORY/...` — a real, distinct folder that `sp_list`/
`sp_resolve_item` currently resolve without complaint, silently returning content from the wrong
tree. This is independently confirmed live in production: a real folder exists at
`11_WORKING_MEMORY/05_AI_RETURNS_HASHED/...` inside the true WM root, separate from the canonical
`05_AI_RETURNS_HASHED/...` tree.

**Required behaviour:** `_safe_full()` (or equivalent path-resolution helper) must detect that the
caller's path begins with the final segment of `SP_ROOT` and **hard-fail** with a named error —
`SpAmbiguousRootError` — stating both the interpreted path and the likely intended path (the same
path with the leading `SP_ROOT`-tail segment stripped). Never resolve it silently.

## D3 — Inconsistent error contract between `sp_read` and `sp_list`

`sp_read`/`sp_read_bytes`/`sp_resolve_item` return an honest error on an unresolvable path;
`sp_list` does not fail the same way (a missing folder returns an HTTP 404 from the underlying
Graph call rather than a structured, tool-level error consistent with the read-side tools). Align
both on one error class so callers can trust a negative without needing to know which tool they
called.

## Acceptance criteria

- A listing of a folder with 200+ items returns `truncated: true` with a working `next`.
- A call whose path includes the `SP_ROOT` tail segment (`11_WORKING_MEMORY`) raises
  `SpAmbiguousRootError` naming both the interpreted and likely-intended path.
- An unresolvable path raises the same error class in both `sp_list` and `sp_read`/
  `sp_resolve_item`.

## Deploy path

Source lands in this repo under `mcp-servers/` (matching the odoo/n8n reference-copy
convention). Build and deploy through this repo's `deploy/mcp-vps/` pipeline, mirroring the
existing `odoo-mcp`/`n8n-mcp` service definitions in `docker-compose.yml`.
