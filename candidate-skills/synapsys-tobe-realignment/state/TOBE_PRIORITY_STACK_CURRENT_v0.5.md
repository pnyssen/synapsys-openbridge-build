---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
last_updated_by: Claude Code, this session
last_updated_context: v0.5 updates capability 2 with the self-triage test result -- both halves of the advisor-tool hypothesis now have real executed evidence. Capabilities 1 and 3 unchanged from v0.4.
supersedes: TOBE_PRIORITY_STACK_CURRENT_v0.4.md (same session -- content update, not a structural correction)
---

# TOBE Capability Alignment — Current v0.5

Do not trust the `as_is_state` fields below past the moment you read
them. Each `source_of_truth` path MUST be re-fetched fresh before this
entry informs any action.

Three capabilities to be aligned with each other and implemented
together — capability 3 is the integration test for capabilities 1 and
2, not a queue item waiting its turn. (Unchanged from v0.2; see that
file for why v0.1's queue framing was wrong.)

### 1. Capability 1 — Navigator MVP reconciliation (CGPT) — RESOLVED, verified

- **tobe_goal**: this lane actively supports whichever lane is
  reconciling the Navigator MVP. Resolved: the work object, its state,
  and its controlling gate are independently confirmed, not relayed.
- **as_is_state**: as of 2026-08-10, this session — the work object is
  `WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`, controlled
  by `STATE_CONTROL/NAVIGATOR_STATE_CONTROL_v14.4.json`, state revision
  136. Independently verified: 4 of 4 cited file hashes match exactly
  (state control JSON, state control MD, the Odoo Target UI Blueprint
  v1.2, the D007 O1-O4 release candidate v1.2 — byte-for-byte and
  SHA-256 confirmed by direct read + independent hash computation). 3
  of 3 cited Odoo records confirmed live: `x_itc_program` id 101
  (PRG-BASIN-CONTINUITY-001), `project.project` id 100 (ProBico/Basin),
  `x_ss_benefit_register` id 107 (BEN-BASIN-CONTINUITY-001) — all
  cross-linked correctly, all created 2026-08-10 by Phil Nyssen. MVP
  accepted; controlling gate is `current_gate: "Current Obsidian
  design rebase complete; Odoo implementation held pending Steward
  review of the rebased design package"` — the old 10-item NOT_ISSUED
  decision list is confirmed **not** the active blocker. Reality state,
  verbatim from source:
  `MVP_ACCEPTED__OBSIDIAN_TARGET_DESIGN_REBASED_TO_PROBABLE_HELD__ODOO_NOT_YET_ALIGNED_TO_CURRENT_DESIGN`.
  The 27-verb correction has propagated into this work object's design
  package but not yet into Odoo's live `x_pool_verb` field.
- **source_of_truth**: `05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/STATE_CONTROL/NAVIGATOR_STATE_CONTROL_v14.4.json`
  (check for a higher state_revision before trusting this as current —
  revision 136 moved fast, multiple times per hour, across this
  session).
- **verification_instruction**: re-read the state control JSON fresh;
  confirm the state_revision number and current_gate field before
  treating anything above as still accurate — this work object updates
  frequently.
- **next_valid_action**: per the work object's own `next_action` field —
  Steward (Phil) reviews the Current Obsidian design baseline before
  D007 Odoo implementation resumes. Not this lane's action.
- **self_authority_claim**: none.

### 2. Capability 2 — SynapSys Mesh enablement layer — both halves now tested

- **tobe_goal**: unchanged — a Mesh enablement layer demonstrably
  aligned to the verified Hermes/OpenClaw lessons and the advisor-tool
  test result.
- **as_is_state**: as of 2026-08-10, this session — the advisor-tool
  hypothesis has now been tested from both directions with real,
  executed evidence, not plans. (1) Escalation-adds-value proxy test
  (6 agents, 3 signals, fast-pass vs. escalated-pass): escalation
  helped on all three signals tested, including catching an unverified
  "urgent" claim the fast pass took at face value. Filed at
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`.
  (2) Self-triage test (5 fresh agents, one signal each, decide
  ESCALATE/PROCEED for themselves): 3 of 5 escalated, 2 of 5 proceeded.
  Judgment was real, not noise — correctly separated a clean routine
  case from two genuinely high-stakes cases, naming precise reasons
  each time (one correctly cited this lane's own Steward/D007-only
  credential-action boundary without being told it). But it
  over-escalated on one signal designed as routine, purely because it
  referenced another AI lane's unverified claim — the opposite failure
  mode from under-escalating, costing some of the savings the
  mechanism exists to capture. Filed at
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-test-result_v0.1.md`.
  The real Workbench-based `advisor_20260301` test is still not run —
  still blocked on Anthropic Console credits. Both proxy results are
  real evidence toward the underlying hypothesis; neither is the
  branded mechanism itself.
- **source_of_truth**: `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`
  (escalation-value result);
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-test-result_v0.1.md`
  (self-triage result);
  `05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_navigator-multichannel-gateway-strip-architecture-candidate_v0.1.md`
  (strip architecture this feeds into).
- **verification_instruction**: re-read both result documents fresh;
  confirm they still reflect "escalation helps, self-triage works but
  over-escalates on low-stakes cross-lane claims" rather than assuming
  that framing holds indefinitely — the sample size (5-6 signals each)
  is small.
- **next_valid_action**: a decision, not another test by default — does
  the observed over-escalation rate get accepted as the cost of the
  caution it buys, or does the triage prompt get refined to distinguish
  low-stakes from high-stakes unverified claims? Both proxy tests
  together are a reasonable stopping point pending that decision,
  unless Phil wants a larger, more stakes-varied sample first.
- **self_authority_claim**: none.

### 3. Capability 3 — Collaborator Geometry Section 14: the integration point for 1 and 2

- **tobe_goal**: prove (or disprove) that Navigator MVP reconciliation
  (capability 1) and the Mesh enablement layer (capability 2) actually
  integrate — using the Collaborator Geometry Section 14 experiment as
  the test bed, per Phil's own framing this session. Honest gap: this
  document does not yet know the specific technical mechanism by which
  a collaborator-activation-pattern experiment integrates a Navigator
  reconciliation effort and a Mesh enablement layer — that connection
  is Phil's synthesis, not something this lane has independently
  derived. Recording it as intent, not re-explaining it as if solved.
- **as_is_state**: as of 2026-08-10 — document read this session,
  confirmed real and substantial
  (`Deliverables/baselines/ADAPTIVE_COLLABORATOR_GEOMETRY_v0.1.md`).
  Section 14 experiment exists, Potential PPV, not run. Explicitly
  gated in its own text on a Steward decision and a Gemini independent
  challenge, neither of which has happened. Contains real named
  individuals and relationship assessments — handle accordingly.
- **source_of_truth**: `Deliverables/baselines/ADAPTIVE_COLLABORATOR_GEOMETRY_v0.1.md`,
  Section 14 specifically.
- **verification_instruction**: re-read Section 14 fresh before acting —
  do not run this experiment from this summary alone; the actual
  experiment design, named participant, and gating conditions live in
  the source document, not here.
- **next_valid_action**: two things, not one — (a) the Steward decision
  and Gemini challenge Section 14's own text names as prerequisite, and
  (b) now that capabilities 1 and 2 both have real evidence, a concrete
  design pass on how Section 14 actually tests the integration — still
  not written, still flagged as missing rather than guessed at.
- **self_authority_claim**: none.

## Change log

- v0.1 → v0.2: corrected queue framing to aligned-capabilities framing.
- v0.2 → v0.3: capability 2 updated with a real executed proxy-test
  result (escalation adds value).
- v0.3 → v0.4: capability 1 resolved. 4/4 file hashes and 3/3 Odoo
  records independently verified, not trusted from the ChatGPT relay.
- v0.4 → v0.5: capability 2 updated with the self-triage test result
  (3/5 escalated, judgment real but over-cautious on low-stakes
  cross-lane claims). Both halves of the advisor-tool hypothesis now
  tested with real evidence.
