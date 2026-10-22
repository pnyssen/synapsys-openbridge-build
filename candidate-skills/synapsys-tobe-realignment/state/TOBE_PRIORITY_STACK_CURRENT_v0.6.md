---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
last_updated_by: Claude Code, this session
last_updated_context: v0.6 records the Steward's "accept self triage" ruling (closes capability 2) and a fresh readiness check on capability 3 (Section 14 not yet ready -- two named prerequisites unmet). Capability 1 unchanged from v0.4/v0.5.
supersedes: TOBE_PRIORITY_STACK_CURRENT_v0.5.md (same session -- content update, not a structural correction)
---

# TOBE Capability Alignment — Current v0.6

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

### 2. Capability 2 — SynapSys Mesh enablement layer — RESOLVED, Steward-ruled

- **tobe_goal**: unchanged — a Mesh enablement layer demonstrably
  aligned to the verified Hermes/OpenClaw lessons and the advisor-tool
  test result.
- **as_is_state**: as of 2026-08-10, this session — both halves of the
  advisor-tool hypothesis are tested with real, executed evidence: (1)
  escalation-adds-value proxy (6 agents, 3 signals, fast-pass vs.
  escalated-pass) — escalation helped on all three signals. (2)
  self-triage proxy (5 fresh agents, one signal each, decide for
  themselves) — 3 of 5 escalated; judgment real, correctly separating
  routine from high-stakes cases, but over-cautious on one signal
  designed as routine purely because it referenced another AI lane's
  unverified claim. **Resolved this turn**: direct Steward instruction
  "Accept self triage" rules on the one open tradeoff (accept the
  over-escalation rate as the cost of the caution it buys, vs. tune the
  triage prompt) — accepted as-is, no prompt tuning instructed. Filed
  at
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-accepted-and-section14-readiness_v0.1.md`.
  The real Workbench-based `advisor_20260301` test is still not run —
  still blocked on Anthropic Console credits; both proxy results plus
  this ruling are the real evidence toward the underlying hypothesis,
  not the branded mechanism itself.
- **source_of_truth**: `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`
  (escalation-value result);
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-test-result_v0.1.md`
  (self-triage result);
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-accepted-and-section14-readiness_v0.1.md`
  (Steward ruling accepting the tradeoff).
- **verification_instruction**: re-read the Steward-ruling document
  fresh; confirm it still reflects "accepted as-is" rather than
  assuming a ruling recorded once stays uncontested indefinitely.
- **next_valid_action**: none outstanding on this capability. If a
  future session wants a larger, stakes-varied sample to test whether
  the over-escalation rate holds at scale, that is optional follow-up,
  not a blocking gap.
- **self_authority_claim**: none — the ruling is Phil's, quoted and
  filed, not self-asserted.

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
- **as_is_state**: as of 2026-08-10, this session — re-read Section 14
  in full this turn (not from summary or memory). Document confirmed
  real and substantial
  (`Deliverables/baselines/ADAPTIVE_COLLABORATOR_GEOMETRY_v0.1.md`).
  **Freshly re-verified: NOT ready to commence.** Section 14's own text
  names two explicit prerequisites before the experiment is even
  designed: a Gemini independent challenge of the exploration, and a
  Steward/ChatGPT sequencing decision on which collaborator and which
  configuration to test. Cross-checked against the live
  `AI_LANE_ALIGNMENT_REGISTER_v0.1.md` this turn — neither prerequisite
  appears as done anywhere this lane can verify. The document's own
  Artefact Status footer states the next experiment is "HELD pending
  Steward + ChatGPT design + Gemini challenge." Section 14 does define
  its own success measures (5 named test questions: activation-geometry
  hypothesis validity, no trust damage, optionality preserved,
  T3/T4 trust-threshold testing via bilateral articulation, cohort-
  pattern generalisation) and four candidate activation-pattern options
  (SVAP1-4: single-basis micro-engagement, bilateral verification-basis
  test, method-binding micro-test, counterparty-currency refresh) — but
  explicitly leaves the specific pass/fail bar to be co-defined
  bilaterally with the collaborator during the experiment (CR6), not
  fixed in advance. Full extraction filed at the receipt below. This is
  a separate gate from capability 2's Steward ruling above — "accept
  self triage" did not name a collaborator or authorise Gemini's
  challenge, and treating it as if it had would be exactly the kind of
  unverified inference this lane's standing rule exists to prevent.
- **source_of_truth**: `Deliverables/baselines/ADAPTIVE_COLLABORATOR_GEOMETRY_v0.1.md`,
  Section 14 specifically;
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-accepted-and-section14-readiness_v0.1.md`
  (this turn's readiness assessment and success-measure/options
  extraction);
  `05_AI_RETURNS_HASHED/AI_LANE_ALIGNMENT_REGISTER_v0.1.md` (checked for
  any recorded Gemini challenge or Steward sequencing decision — none
  found as of this turn).
- **verification_instruction**: re-read Section 14 and the alignment
  register fresh before acting — do not run this experiment from this
  summary alone; the actual experiment design, named participant, and
  gating conditions live in the source document, not here. Confirm
  whether either prerequisite has since been met before treating this
  entry's "not ready" conclusion as still current.
- **next_valid_action**: two things, not one — (a) the Steward decision
  (name the collaborator and configuration) and Gemini challenge
  Section 14's own text names as prerequisite — neither yet done; (b)
  once both exist, the concrete design pass on how Section 14 actually
  tests the integration with capabilities 1 and 2 — still not written,
  still flagged as missing rather than guessed at.
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
- v0.5 → v0.6: capability 2 resolved — Steward ruling "Accept self
  triage" closes the one open tradeoff. Capability 3 freshly
  re-verified as NOT ready to commence — two named prerequisites
  (Gemini challenge, Steward/ChatGPT collaborator+configuration
  sequencing decision) remain unmet, confirmed absent from the live
  alignment register this turn. Section 14's own success measures and
  activation-pattern options extracted from source and recorded.
