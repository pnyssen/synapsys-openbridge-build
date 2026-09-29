# SharePoint MCP — Patch Spec (D1/D2/D4 fixed, merged and DEPLOYED)

**Status:** D1, D2 and D4 are fixed in source, merged to `main` on
`pnyssen/synapsys-openbridge` (PR #13/#12 2026-08-23; PR #15/#16 2026-08-24),
and **live in production** — Azure Container App `synapsys-spmcp-dev`
revision `0000046`, deployed 2026-08-24, all three post-deploy verification
checks passing (see Deployment integrity). D3 was never a real defect. This
file is a status record, not a recovery plan.

## Deploy location

The server is built and deployed via Azure, not the Hostinger VPS. Image:
Azure Container Registry `synapsysspmcp11242.azurecr.io/synapsys-sharepoint-mcp`.
Runtime: Azure Container App `synapsys-spmcp-dev`. Source of truth:
`pnyssen/synapsys-openbridge` → `mcp/sharepoint/sharepoint_mcp.py`.

An earlier revision of this file claimed the server ran as an untracked
container on Hostinger VPS 1536619, and that source recovery from a running
container was the prerequisite for any fix. That was wrong — inferred from
the server's absence in *this* repo rather than established positively; the
source was in a separate, sibling repo the whole time. `docker ps` on that
VPS returns only `hermes-agent`, `mcp-vps-odoo-mcp-1`, `mcp-vps-n8n-mcp-1`,
`n8n-n8n-1` and `n8n-traefik-1` — no SharePoint container is or was present
there. Source recovery was never actually required; the gap has always been
**deployment**, not authorship — see Deployment Integrity below.

## Provenance

Root cause and defect enumeration (D1/D2/D3 below) originally diagnosed and
specified by `claude_cowork`, filed at
`ARCHITECTURE_DATA_RECONCILIATION/20260823--claude-cowork--fix-record-and-patch-spec--sp-list-truncation-and-shadow-tree--v1-0.md`
(SynapSys Working Memory), SHA-256
`80a3731cc99289cbd46c5eacaecfadb5cb90c27b3676fc8a093a6e9152194293`.
D4 diagnosed independently the same day, root-caused to the exact parameter-
naming defect it describes; see
`05_AI_RETURNS_HASHED/20260823--claude-code--correction--sp-list-divergence-resolved-caller-error--v1-0.md`.

## D1 — Silent truncation — FIXED, merged, DEPLOYED

`sp_list` returned a bounded page with no indication that more items exist.
A caller could not distinguish "this folder has 11 files" from "here are
the first 11 of 200." Confirmed live in production, re-confirmed with
correct parameters 2026-08-23: `sp_list(folder="05_AI_RETURNS_HASHED")`
returns ~200 entries and stops at
`20260717_RET_CLAUDE_all-four-ruled-improvements-execution-receipt_v0.1.md`
— files known to exist in that folder dated after that point, including
receipts filed by two different lanes on 2026-08-23, are absent from the
response, with no `truncated`/`next`/count field to signal it.

**Fixed in source**: `sp_list` now follows Graph's `@odata.nextLink`
internally and always returns the complete listing, bounded by a
page-count safety cap (`SpListTruncatedError` on exceeding it, never a
silent partial return). See `pnyssen/synapsys-openbridge` PR #13.

## D2 — Doubled-root paths resolve silently — FIXED, merged, DEPLOYED

A caller path beginning with just `SP_ROOT`'s final segment
(`11_WORKING_MEMORY/...`) silently produced a second, real, doubled-root
folder tree instead of an error. Confirmed live 2026-08-23:
`sp_resolve_item(path="11_WORKING_MEMORY/05_AI_RETURNS_HASHED")` resolved to
`.../11_WORKING_MEMORY/11_WORKING_MEMORY/05_AI_RETURNS_HASHED` (item id
`01INC5JSXMIZOKZV7VWNCKGCPKV5NBRAB4`) instead of raising.

**Severity: latent, not realised — no content was ever misfiled.** An earlier
revision of this file claimed the shadow tree was "not empty", that it held a
duplicate of the genuine 73.2 MB
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`, and that "content
has already been written to the wrong location". **That claim is retracted.**
Exhaustive enumeration on 2026-08-24 found the entire shadow tree to be three
nested empty folders, 0 bytes, no files at any level. The error was inferring
duplicated *content* from a matching folder *name*, when `size: 0` was
visible in the same response. Retraction filed at
`05_AI_RETURNS_HASHED/20260824--claude-code--correction--d2-shadow-tree-is-empty-no-realised-harm--v1-0.md`,
SHA-256 `e9fa5761c9348b7123a0c875ee425dfbc1c15ea23dbb6c77700ae4875301283a`.
A narrower same-week check had already established that the one file cited as
shadow-write evidence was not duplicated:
`05_AI_RETURNS_HASHED/20260823--claude-code--correction--shadow-tree-cited-evidence-file-not-duplicated--v1-0.md`.

**Fixed in source**: any path whose leading segment duplicates the
`SP_ROOT` tail now raises `SpAmbiguousRootError` naming both the
misinterpreted and likely-intended path, rather than resolving silently.
See PR #13.

**Remediation: CLOSED.** The shadow tree was empty scaffolding, so
disposition was deletion of empty folders, not content reconciliation — no
data was ever at risk. The Steward deleted it via the SharePoint web UI on
2026-08-24. Deletion had to go through the UI because the deployed D2 guard
blocks *every* MCP tool on that path including `sp_delete`: the fix has no
escape hatch for remediating its own historical artefact. Recorded as a known
design wrinkle. Removal verified cross-connector (the shadow item id no
longer resolves via the Microsoft 365 connector) and the genuine
`05_AI_RETURNS_HASHED` confirmed intact by id, size and canonical single-root
webUrl. Closure receipt:
`05_AI_RETURNS_HASHED/20260824--claude-code--closure--d2-shadow-tree-removed-and-verified--v1-0.md`,
SHA-256 `49555d8181896ba087732e8f8df8f9c7888180dd86942fe24efc9f98cd784d1d`.
Authorship of the shadow tree confirmed as the container's own managed
identity ("SharePoint App"), i.e. the MCP server via this defect — not a
human misfile and not the separate OpenAI-native SharePoint write path.

## D3 — Inconsistent error contract between `sp_read` and `sp_list` — FIXED, merged, DEPLOYED

`sp_read`/`sp_read_bytes`/`sp_resolve_item` returned a clean, named
`SpItemNotFoundError` on an unresolvable path; `sp_list` did not — a
missing folder surfaced as a raw HTTP error instead of a structured,
tool-level error consistent with the read-side tools.

**Fixed in source**: `sp_list` and `sp_read` now both raise
`SpItemNotFoundError` on 404, matching the rest of the module. See PR #13.

*(A separate, unrelated claim — that `sp_list` ignores its `folder`
argument entirely and always returns the Working Memory root — surfaced in
cross-lane chat the same day and was investigated as a possible fourth
defect. It was retracted: root-caused to a caller passing the wrong
parameter name, not a server defect — see D4. It was never filed into this
document as D3 and there is nothing here to withdraw on that account; noted
here only so the two "D3"s in this day's record don't get conflated.)*

## D4 — Parameter naming inconsistency and silent keyword drop — FIXED, merged, DEPLOYED

**Observed (pre-fix).** `sp_list` took `folder`. `sp_read`, `sp_write` and
`sp_resolve_item` take `path`. A call passing `path` to `sp_list` is not
rejected: the unknown keyword is discarded, `folder` falls back to its
default `""`, and the server returns the Working Memory root — a
syntactically valid, confident, entirely wrong answer to the question
actually asked.

**Why it matters.** This failure mode is invisible. The caller receives a
well-formed listing of a real folder (the WM root) and has no signal it is
not the folder requested. On 2026-08-23 this produced a false defect report
— "`sp_list` ignores its path argument" — that was escalated as a systemic
evidence-integrity failure across two AI lanes before being traced back to
the caller's own malformed call. It is the direct cause of the false D3
claim referenced above.

**Required behaviour:**
1. Rename `sp_list`'s parameter to `path`, matching every sibling tool.
   Accept `folder` as a deprecated alias for one release if backward
   compatibility is needed, and log its use.
2. Reject unrecognised keyword arguments with an explicit error naming the
   unexpected key and the accepted keys. Never silently discard.
3. Do not let an empty/absent path silently mean "root" on a call that
   supplied *some* location argument. Absent → root is fine; unparsed →
   error.

**Fixed in source and deployed**: `sp_list` now takes `path`, with `folder`
retained as a deprecated alias so existing callers keep working. See PR #16.

**Acceptance:** `sp_list(path="10_SCRATCH_TRANSIT")` returns that folder's
3 entries. `sp_list(folder="10_SCRATCH_TRANSIT")` either works with a
deprecation notice or errors. `sp_list(nonsense="x")` errors and names the
offending key. No call form returns the root without the caller having
asked for the root. Condition 1 verified live 2026-08-24 (see Deployment
integrity); conditions 2 and 3 not separately re-tested post-deploy.

## Deployment integrity

**Resolved.** Merged to `main` does not by itself change live behaviour, and
for most of 2026-08-23 it did not: the running Container App served the
pre-fix image (instance id `3bdb0d17bbee43f5be1070579668d050`), still
exhibiting D1, D2 and D4 — confirmed independently by two separate AI lanes.
The ACR rebuild and Container App redeploy of `synapsys-spmcp-dev` were
carried out on 2026-08-24, producing revision `0000046` and instance id
`64edae8a32734517b9a6209e29c75d17`. This repo's history documents a standing
image/source drift predating this fix (see `mcp/sharepoint/README.md`'s
"Known git/deployment drift" section in `pnyssen/synapsys-openbridge`); this
deploy closes that gap for D1/D2/D4.

**Verification required after any redeploy** — all three must pass against
the live server before any of D1/D2/D3 is marked closed in production:
1. `sp_list(path="10_SCRATCH_TRANSIT")` → exactly 3 entries, 321 bytes total.
2. `sp_resolve_item(path="11_WORKING_MEMORY/05_AI_RETURNS_HASHED")` → an
   error, not a resolved shadow item.
3. A listing of a folder with more entries than the internal page cap
   carries an explicit truncation signal (or is exhaustively paginated with
   no cap hit).

**Post-deploy verification result: 3/3 PASS**, re-confirmed independently
against the live server on 2026-08-24 (instance id
`64edae8a32734517b9a6209e29c75d17`):
1. `sp_list(path="10_SCRATCH_TRANSIT")` → exactly 3 entries
   (`Scheduled_RETIRED_20260713` 0 B, `_sharepoint_mcp_verify_test_20260714.txt`
   170 B, `_verify_write_test_2026-07-14.txt` 151 B) = 321 bytes total. The
   call also confirms D4: `path` is now the accepted parameter.
2. `sp_resolve_item(path="11_WORKING_MEMORY/05_AI_RETURNS_HASHED")` → raises,
   naming both the misinterpreted and the likely-intended path, rather than
   resolving a shadow item.
3. Exhaustive pagination confirmed: the WM root returns 459 entries and
   `05_AI_RETURNS_HASHED` returns 3,584 entries in a single complete
   listing, well past the ~200-entry point at which the pre-fix server
   silently stopped.

## Acceptance criteria (source-level, all confirmed met by PR #13 for D1–D3)

- A listing of a folder with 200+ items returns the complete listing (no
  silent truncation) or a named `SpListTruncatedError`, never a partial
  result presented as complete.
- A call whose path includes the `SP_ROOT` tail segment (`11_WORKING_MEMORY`)
  raises `SpAmbiguousRootError` naming both the interpreted and
  likely-intended path.
- An unresolvable path raises the same error class (`SpItemNotFoundError`)
  in both `sp_list` and `sp_read`/`sp_resolve_item`.
- D4's three acceptance conditions above, met by PR #16 and deployed.

## Deploy path

Source lives in `pnyssen/synapsys-openbridge` under `mcp/sharepoint/`.
Build via that repo's `mcp/sharepoint/Dockerfile`, push to
`synapsysspmcp11242.azurecr.io/synapsys-sharepoint-mcp`, deploy to Azure
Container App `synapsys-spmcp-dev` — not this repo's `deploy/mcp-vps/`
pipeline, which only builds the Odoo/N8N servers.
