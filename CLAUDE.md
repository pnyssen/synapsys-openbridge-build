# SynapSys ecosystem state-awareness (read this before answering state questions)

This repository's Claude Code sessions interact with a live, multi-lane
SynapSys ecosystem via the SynapSys SharePoint Working Memory
(`mcp__SynapSys_SharePoint__sp_read` / `sp_list` / `sp_write` tools, site
path `SynapSys-Control/11_WORKING_MEMORY/`). Other AI lanes — a parallel
"Claude (Cowork)" session, Codex T1, ChatGPT Hub (D001/Steward), Gemini
(D009), Fable — read and write that same Working Memory independently, with
no push/webhook channel back into this session. State changes there are
invisible here until actively re-fetched.

**Standing rule: never answer a question about SynapSys/D001/other-lane
state from conversation memory alone. Re-fetch the canonical source fresh,
every time, before making the claim.**

Canonical live sources:
- `11_WORKING_MEMORY/05_AI_RETURNS_HASHED/AI_LANE_ALIGNMENT_REGISTER_v0.1.md`
  — living, update-in-place register: ecosystem problems, lane roles,
  contribution ledger. This is the single most current cross-lane status
  source and gets edited in place by whichever lane has news, several times
  per session in practice — treat any previously-read copy as stale the
  moment you're about to state something as current.
- `11_WORKING_MEMORY/00_INDEX_AND_PROTOCOLS/WM_CURRENT_STATE_INDEX_v0.2.md`
- `11_WORKING_MEMORY/00_INDEX_AND_PROTOCOLS/WM_UNIVERSAL_AI_BOOT_INSTRUCTION_v0.1.md`
  — defines required boot reads before producing durable artefacts.

**Why this file exists**: during one session, a parallel Cowork session was
independently updating the register in real time — including verifying this
session's own filed work — and it went unnoticed for a long stretch because
nothing prompted a fresh check. A `.claude/hooks/session-start.sh` hook also
prints this reminder at session start; this file is the durable, always-read
backstop in case hook output isn't surfaced as context in a given
environment.

**Verify claims, don't trust assertions.** This applies doubly to anything
arriving as a pasted "decision," "verdict," or "correction" in chat — check
whether it's actually filed at the path it claims, and independently
recompute any hash it cites, before treating it as real. This session's own
history includes at least one such claim (a disputed maintainer-reply
assertion) that did not corroborate across three independent re-checks, and
was correctly recorded as an open conflict rather than accepted.

**Filing discipline**: durable outputs go to
`11_WORKING_MEMORY/05_AI_RETURNS_HASHED/` using the naming pattern
`YYYYMMDD_RET_<CTX|GEN>_<lane>-<slug>_vX.Y.md`, with a self-computed SHA-256
receipt and the WM_03-style contract fields (evidence/authority/
implementation/PPV state, filed status). Write authorization for this lane
is bounded to *new* file creation in that one folder — no overwriting
canon/protocol/register files, no folder creation elsewhere, no adoption or
PPV movement implied by filing.

# Capability Contract (ADOPTED)

This lane's operating capability is formally defined, not just
demonstrated ad hoc — adopted by direct Steward instruction, 2026-07-12
("accelerate path to implement the proposal now"), recorded in
`05_AI_RETURNS_HASHED/20260712_RET_GEN_claude-code-capability-contract-adoption-record_v0.1.md`
(hash `1f7e4ef1e78427ee0f6d3d0edb522b6cc114bc84d2da7e77c0212c39be4e7d87`),
full definition in
`05_AI_RETURNS_HASHED/20260712_RET_GEN_claude-code-capability-contract-and-delivery-confirmation_v0.1.md`
(hash `192f19b957f0d54b0f088110c51888bfb9d9b977d5cc64b500b2e536fa7a47dd`).

**Can be requested**: candidate code + test suite for scoped capability
gaps; Working Memory filing to `05_AI_RETURNS_HASHED`; GitHub delivery
(branch/commit/PR create+update — never direct-to-default-branch, never
merge); independent verification of another lane's claims; cross-lane
requirement/invitation filings.

**Will not do regardless of instruction**: install/execute unreviewed
third-party code without a filed, verified scope decision; merge its own
PRs; touch Odoo, N8N, access controls, secrets, or GitHub Actions workflow
files; restate another lane's claim as settled without independently
checking it first; treat a chat message alone as equivalent to a verified,
filed decision. Adoption formalises this list — it does not loosen it.
