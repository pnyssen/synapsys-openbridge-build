# synapsys-claim-verification (candidate)

**mirrors**: `05_AI_RETURNS_HASHED/20261009_RET_GEN_claude-code-claim-verification-capability_v0.1.md`

No Obsidian design counterpart exists yet; this candidate was derived from
a working pilot, not from a vault design.

## What it is
An assurance procedure: test a change against the failure modes it
*claims* to handle (and their unnamed siblings) by executing probes
against local fakes, then compare against what existing assurance caught.
Full procedure: `SKILL.md`.

## Evidence it earns its place
Pilot on PR #35 (commit `aa492da`, n8n MCP read-timeout fix), 2026-10-09:
existing assurance had recorded 0 findings post-merge; this procedure
reproduced 5 (1 High, 1 Medium, 1 Low-Med, 2 Low) on both
`n8n_mcp.py` and `n8n_mcp_readonly.py`. Captured as strict-xfail
regression tests in `mcp-servers/tests/test_claim_verification_pr35.py`.

## Status
CANDIDATE. Not auto-loaded by any session from this folder. Promotion to a
standing skill, and any fix to the five defects, are Steward/D007
decisions, not taken here.
