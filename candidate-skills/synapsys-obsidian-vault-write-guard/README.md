# synapsys-obsidian-vault-write-guard

Candidate tooling for making writes to the shared SynapSys Obsidian vault
(`SynapSys-Control/11_WORKING_MEMORY/Obsidian`) safe under concurrent
access — built in response to Phil's request for what a "reliable"
Obsidian-access requirement actually needs, this session.

## What's here

- `vault_write_guard.py` — offline, zero-network, zero-subprocess
  precondition checker for vault writes. Two protections: a default-deny
  path allowlist (this lane's write authorization is `05_AI_RETURNS_HASHED`
  only per CLAUDE.md; the vault is not yet in scope, so the allowlist
  starts empty until a Steward ruling names specific subfolders), and
  optimistic concurrency (re-read the target path, compare its hash
  against what the caller last saw, refuse to overwrite on a mismatch).
  Also catches malformed `.canvas` JSON before it reaches the vault,
  since a broken canvas file simply fails to open in Obsidian.
- `tests/test_vault_write_guard.py` — 19 tests, zero network/subprocess
  (isolation enforced by an AST-import-scan test, same pattern as
  `candidate-skills/synapsys-service-catalogue-pilot`), covering: allowlist
  allow/deny including a prefix-string-collision case, new-file vs.
  update-conflict vs. clean-update paths, canvas format validation, and
  that `write_fn` is never invoked when any precondition fails.

## What this is not

Not connected to the SharePoint MCP tools — it takes `read_fn`/`write_fn`
as injected callables so the actual `sp_read`/`sp_write` calls stay in the
caller's hands. Not a standing skill, not self-installed, not authorized
to write to the vault on its own: the allowlist a caller supplies must
come from an actual, current, verifiable Steward scope decision — this
module enforces whatever scope it's given, it doesn't grant one.

## Related gap found the same session

`mcp__SynapSys_SharePoint__sp_search` returns HTTP 500 for every query
tried (single-word, no special characters) — not query-specific, so the
fault is in the Graph API call construction or the drive's search-indexing
configuration, not the search term. This is server-side (the SharePoint
MCP server's source isn't in this repo, unlike `mcp-servers/{n8n,odoo}_*`),
so it's reported, not fixed, here — see the filed CR/gap request for the
exact reproduction.

## Status

CANDIDATE_CODE, not yet authorized for live use. Building this was within
this lane's standing capability contract ("candidate code + test suite for
scoped capability gaps") — using it against the real vault requires a
Steward scope decision naming the allowed path prefixes, which does not
exist yet as of this filing.
