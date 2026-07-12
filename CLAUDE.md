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

# AI Lane Roles

What `claude_code` (this lane, in this repo) actually has, demonstrated not
assumed:
- Local git/GitHub push access via the installed Claude GitHub App —
  verified by successfully pushing branches and opening PRs this session,
  not merely granted-in-theory.
- Local test execution (pytest) — demonstrated across three candidate
  skills (8/8, 9/9, 15/15 passing, real output, not summarised).
- Working Memory filing to `05_AI_RETURNS_HASHED` — demonstrated, multiple
  receipts filed and independently re-verified this session.

What this lane does **not** have: Odoo or N8N MCP access (explicit
task-scope exclusion — see the standing requirement filed to address this
gap at `05_AI_RETURNS_HASHED/20260712_RET_GEN_claude-code-t1-odoo-verification-gap-requirement_v0.1.md`),
browser control, or any push/notification channel to another AI lane
(Cowork, Codex T1, ChatGPT Hub, Gemini, Fable). Coordination with those
lanes is relay-through-Phil or shared-Working-Memory-read only — the same
constraint every lane in this ecosystem operates under, not a limitation
specific to this one.

Distinct value: this is the lane that can actually write and execute code
with a real test runner and push it somewhere reviewable. Cowork has
Odoo/N8N/browser access this lane doesn't. Neither substitutes for the
other — route work to whichever lane's demonstrated capability actually
matches the task, not by assumption.

# Proactive Behaviors

1. **Check before duplicating.** Before starting candidate-build or
   CR-adjacent work, check Working Memory and any live change-request
   register for existing coverage first, so this lane doesn't re-do work
   another lane already has in flight.
2. **File before referencing.** Every candidate artefact gets a filed
   evidence receipt *before* it's referenced anywhere else (a PR, a chat
   message, another document) — and that reference must cite the receipt's
   exact filename and SHA-256 inline, not just describe what it contains.
   A description without the citation is exactly what caused a real false
   "no evidence exists" flag on this repo's own candidate-skill PRs.
3. **Recompute before restating.** Never restate another lane's hash or
   byte-count claim as settled without independently recomputing it first.
   This is already this lane's practice (see the AgentBudget-receipt
   correction and the CHG-2026-411 non-existence finding, both this
   session) — this section exists to make it a written rule rather than an
   incidental habit that could lapse under time pressure.

# Change Request Cross-Reference

| CR | Governs | Status |
|---|---|---|
| CHG-2026-410 | GitHub Change Control Rule (the section above this one in this file) | PR #4, pending merge — Phil's call |
| CHG-2026-412 | This section and the two above it (AI Lane Roles, Proactive Behaviors) | Implemented via PR, this commit |
| — | The three candidate skills' authorising ruling | Hash `e96cae5d20816c80f3e9090c5aa990fd467b98f73c2bb6a72fd9b77f34299b66` (Work Object D001-EXT-TOOLING-CODE-01 covers `synapsys-security-audit`/`synapsys-browser-verify`; a separate direct Steward ruling of the same hash covers `synapsys-agentic-safety`) |

Note on CHG-2026-411: cited elsewhere as the standing rule requiring
CHG-2026-412 to exist, but the document it names
(`T1_CR_TRACEABILITY_RULE_v0.1.md`) does not appear in
`05_AI_RETURNS_HASHED` as of this section being written — checked via full
folder listing, not a single lookup. Recorded as an open discrepancy, not
resolved by assumption in either direction. The four changes CHG-2026-412
actually requested were implemented on their own merits regardless of
whether CHG-2026-411 itself is real.
