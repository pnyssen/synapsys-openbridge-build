---
name: synapsys-claim-verification
description: Use before merging, closing, or filing as Verified any change or return that claims a fix, PASS, or closed gap (code, MCP server, n8n workflow, Odoo config), or when asked to review a diff/PR adversarially.
---

# Claim Verification (test claims, don't read them)

A change is judged against what it *claims*, by running it against the failure modes it says it handles. Reading code that looks right is not evidence. Origin: PR #35 (aa492da) claimed to fix production "timeout and Connection closed" failures; it caught only timeouts. A connection reset still escaped unhandled. Nobody had recorded it, and the existing tests only covered the timeout path.

## Scope
- In: any change, PR, AI return or receipt asserting "fixes", "handles", "never", "unchanged", "PASS", "Verified".
- Out (per Governance Scope Limiter): conversation, personal content, unnamed drafts. Dependency bumps and one-line changes get a proportionate check or none.
- Not the same as: `sk01-runtime-verifier` (live state vs an expected baseline), `perturbation-engine` and `synapsys-design-challenge` (designs before build). This skill tests built changes.

## Procedure
1. **Extract claims.** From the commit message, PR body, docstrings and return text, list each claim as a numbered, testable statement.
2. **Name the failure modes, including the siblings.** For each claim, list what it must survive. The usual miss is the sibling the fix didn't name. Check:
   - Error paths: timeout vs reset vs truncated body vs malformed or partial data vs wrong type.
   - Input bounds: negative, zero, huge, empty; unescaped values in paths and queries (injection, `../`).
   - Duplicated code paths: was the fix applied to every copy?
   - Data shape: mixed types, missing keys, ordering assumptions.
   - Documentation vs behaviour: does each promise in a docstring actually hold?
3. **Execute, don't read.** Reproduce each mode against a local fake or mock (e.g. a local HTTP server standing in for N8N). Never mutate live Odoo, N8N or SharePoint. Live access, if used at all, is read-only. Record the exact probe and the observed result.
4. **Baseline the existing check.** What did current assurance catch? Look at existing tests, PR reviews and later fix commits. Gap = found − caught. This is the number that justifies the check.
5. **Classify.** Give each finding a severity, plus CONFIRMED (reproduced) or PLAUSIBLE (reasoned, untested). Never present PLAUSIBLE as confirmed.
6. **Return.**
   - A findings table: claim, mode, probe, result, severity, status.
   - A test-coverage gap line.
   - The probe script saved for replay.
   - Control Return fields: Verdict, Evidence, Authority, Held, one next action, Replay-validity.
   - Each CONFIRMED finding proposed as a regression test (a Y-asset). Propose it; don't apply it. In a repo with pytest, use `xfail(strict=True)` so the test documents the defect without breaking CI and forces removal of the marker once fixed (pattern: `mcp-servers/tests/test_claim_verification_pr35.py`).

## Second model (high-stakes changes only)
When the change is high on Quality/Importance/Urgency, also run a second-model adversarial review (e.g. `/codex:adversarial-review` via the official `openai/codex-plugin-cc`). Score its findings against yours and record which model found what. Adopt a second model only where it finds things the first misses. A second model's pass is assurance, never approval.

## Authority
- This skill assures. It does not authorise (D009 assures; D001 authorises).
- Fixes are mutations: they route through D007 and the repo's change-control rule (branch + PR; merge needs Steward/D007 release).
- Never push a fix as part of verification.
- Never send code from credential-bearing or private repos to an external model without Steward approval.
