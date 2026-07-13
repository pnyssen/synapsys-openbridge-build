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

# GitHub Change Control Rule — Claude Code Read/Write Discipline

This repo's Claude GitHub App installation grants full read/write scope
(code, actions, checks, issues, PRs, hooks, workflows). That access exists;
this section is the discipline for using it. Full rationale, verified
access-state evidence, and gap register in
`11_WORKING_MEMORY/07_SYSTEM_DEVELOPMENT_LIBRARY/GITHUB_CHANGE_CONTROL_RULE_v0.1.md`
(SHA-256 `7fad82d8726e90dece665e9d83b34762ca313ac79ef5f2f888ea736b7d7faaab`,
independently re-verified byte-for-byte against that hash before this
section was written — not taken on the filing lane's word for it).
Registered in SynapSys CR control as CHG-2026-410.

**Read access**: unrestricted, no CR needed — code, issues, PRs,
discussions, Actions runs/logs, commit history, workflow files, any time,
for any SynapSys-related purpose.

**No CR needed** (git's own staging is the safety mechanism): pushing to a
non-default branch, opening a PR, commenting on issues/PRs/discussions,
triggering an existing Actions workflow via its normal trigger (not editing
the workflow file).

**CR required before the action** (same discipline as this ecosystem's N8N
change-control rule, scaled to git's mechanics): merging a PR into a
default branch, direct push to a default branch, editing a
`.github/workflows/*` file, any commit changing deployment-relevant
config/secrets-references/CI-CD behaviour on a branch about to be merged.
CR needs `x_test_evidence` and `x_rollback_plan` (name the actual git
mechanism — revert SHA, branch to reset to) populated before the action, or
retrospective emergency registration immediately after, same exception
structure as every other CR-gated action this ecosystem uses.

**Never, no CR overrides these**: modifying repo/org access controls
(collaborator/team permissions, App installation scope, branch protection,
org membership), deleting a repository, force-push or history rewrite on a
shared/default branch, modifying or exfiltrating secrets, granting any app/
user/token broader access than it currently has. If a task seems to need
one of these, don't implement it — surface the conflict instead.

**Open gaps, not yet resolved** (check before assuming coverage): branch
protection status on this repo's default branch is unverified; whether
every repo under the `pnyssen` account is actually in SynapSys scope for
this rule (vs. personal/experimental) is unconfirmed; no GitHub Actions
workflow inventory has been done yet, so the "editing a workflow file"
trigger can't be checked against a concrete list.

# Capability Contract (ADOPTED, AMENDED)

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
PRs; touch access controls, secrets, or GitHub Actions workflow files;
restate another lane's claim as settled without independently checking it
first; treat a chat message alone as equivalent to a verified, filed
decision; self-configure an MCP connector or self-issue a credential —
connector installation and credential issuance are Steward/D007 actions on
this lane's own environment, not something this lane executes for itself
even under direct instruction. Adoption formalises this list — it does not
loosen it.

**Status note, per Phil's explicit instruction on merge approval**: this
"will not do" list is written directly into CLAUDE.md so it remains visible
to every future session automatically, not only in a Working Memory
filing — and stays open for update if experience shows it needs revision.
Merge of this section is gated on CR assignment — see
`05_AI_RETURNS_HASHED/20260712_RET_GEN_claude-code-pr6-cr-assignment-request_v0.1.md`
(hash `39ac33c99fe4ed0122cc40300454356067af45e83dc650e010e29e0e6000cb9c`).

## Amendment 2 — Odoo/N8N Full CRUD Parity with Claude (Cowork)

Steward ruling, 2026-07-13, recorded in
`05_AI_RETURNS_HASHED/CLAUDE_CODE_CAPABILITY_CONTRACT_AMENDMENT_2_ODOO_N8N_FULL_CRUD_v0.1.md`
(supersedes the narrower read-only
`CLAUDE_CODE_CAPABILITY_CONTRACT_AMENDMENT_1_ODOO_N8N_READONLY_v0.1.md`,
hash `847be3abfecb7bb7e2b663d9a2f19adeebc953b9c14b9864a54f623fcf0b5028`,
filed for lineage, not the operative grant): the "will not touch Odoo,
N8N" portion of the clause above is lifted. Once an MCP connector and a
distinct credential for this lane exist (a separate Steward/D007 action —
see below), this lane may use the same Odoo tool set Claude (Cowork) uses
(`search_odoo`/`read_odoo`/`count_odoo`/`create_odoo`/`write_odoo`/
`unlink_odoo`/`execute_odoo`/`create_fields_batch`/`create_acls_batch`)
and the same N8N tool set (`ping_n8n`/`list_workflows`/`get_workflow`/
`update_workflow`/`activate_workflow`/`deactivate_workflow`/
`list_executions`/`get_execution`/`list_credentials`/`trigger_webhook`).

**Binding conditions of this grant, not optional**: the N8N Workflow
Change Control Rule (no `update_workflow`/activation/deactivation without
a CR reference filed before deployment, or same-session emergency
registration) applies to this lane exactly as it applies to Cowork;
every Odoo write must be independently re-read and confirmed post-write
before being reported as done; every custom record write must populate
`x_company_id`/`x_context_id` correctly. These bind by action, not by
which lane holds the credential.

**Still outstanding, not resolved by this text change**: the actual MCP
connector configuration and a distinct API credential for this lane. This
document makes the *authorization* durable and in-repo; it does not
itself grant working access — that requires Steward/D001 to run
`claude mcp add` with a real, distinct Odoo/N8N credential against this
lane's own environment, which this lane cannot do for itself per the
"will not self-configure an MCP connector or self-issue a credential"
clause above. Until that technical step happens, this lane still has no
working Odoo/N8N tool in its session toolset, regardless of what this
file says.
