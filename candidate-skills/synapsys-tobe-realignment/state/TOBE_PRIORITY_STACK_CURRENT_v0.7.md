---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
last_updated_by: Claude Code, this session
last_updated_context: v0.7 records Gemini/D009's HOLD verdict on the proposed Section 14 configuration (relayed by the Steward, not independently re-verifiable by this lane), the corrected Kapeleris identity (independently checked against live Odoo), and the concrete defects that remain before the experiment can proceed. Capabilities 1 and 2 unchanged from v0.6.
supersedes: TOBE_PRIORITY_STACK_CURRENT_v0.6.md (same session -- content update, not a structural correction)
---

# TOBE Capability Alignment — Current v0.7

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
  136. Independently verified: 4 of 4 cited file hashes match exactly. 3
  of 3 cited Odoo records confirmed live: `x_itc_program` id 101
  (PRG-BASIN-CONTINUITY-001), `project.project` id 100 (ProBico/Basin),
  `x_ss_benefit_register` id 107 (BEN-BASIN-CONTINUITY-001). MVP
  accepted; controlling gate is `current_gate: "Current Obsidian
  design rebase complete; Odoo implementation held pending Steward
  review of the rebased design package"`.
- **source_of_truth**: `05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/STATE_CONTROL/NAVIGATOR_STATE_CONTROL_v14.4.json`
  (check for a higher state_revision before trusting this as current).
- **verification_instruction**: re-read the state control JSON fresh;
  confirm the state_revision number and current_gate field before
  treating anything above as still accurate.
- **next_valid_action**: per the work object's own `next_action` field —
  Steward (Phil) reviews the Current Obsidian design baseline before
  D007 Odoo implementation resumes. Not this lane's action.
- **self_authority_claim**: none.

### 2. Capability 2 — SynapSys Mesh enablement layer — RESOLVED, Steward-ruled

- **tobe_goal**: unchanged — a Mesh enablement layer demonstrably
  aligned to the verified Hermes/OpenClaw lessons and the advisor-tool
  test result.
- **as_is_state**: as of 2026-08-10 — both halves of the advisor-tool
  hypothesis tested with real evidence (escalation-adds-value proxy;
  self-triage proxy, 3/5 escalated). Steward ruling "Accept self triage"
  closes the one open tradeoff — accepted as-is, no prompt tuning
  instructed.
- **source_of_truth**: `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`;
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-test-result_v0.1.md`;
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-self-triage-accepted-and-section14-readiness_v0.1.md`.
- **verification_instruction**: re-read the Steward-ruling document
  fresh; confirm it still reflects "accepted as-is."
- **next_valid_action**: none outstanding on this capability.
- **self_authority_claim**: none — the ruling is Phil's, quoted and
  filed, not self-asserted.

### 3. Capability 3 — Collaborator Geometry Section 14 — HOLD returned, not yet ready

- **tobe_goal**: prove (or disprove) that Navigator MVP reconciliation
  (capability 1) and the Mesh enablement layer (capability 2) actually
  integrate — using the Collaborator Geometry Section 14 experiment as
  the test bed, per Phil's own framing this session.
- **as_is_state**: as of 2026-08-11, this session — significant motion,
  still not ready to run. (a) Primary collaborator identity corrected
  and independently verified: **Dr John Kapeleris** (not "Capillaris" —
  a repeated dictation error, now permanently corrected), confirmed live
  in Odoo (`res.partner` id 10, "Steward / Senior Capability Partner —
  Commercialisation & Industrialisation", `john@synapsys.com.au`). Ben
  Robinson (Director, Probico Pty Ltd, `res.partner` id 19) remains the
  second proposed collaborator, tied to the live `project.project` id
  100 (GemLife/Basin precinct pathway). Cohort confirmed by the Steward
  as-is: Mark Wist, Steve Hartley, Bill Stack, Jeremy Fox, Lucas
  Meadowcroft — enterprise capability development. (b) The Gemini
  independent-challenge prerequisite has now been dispatched (filed
  prompt, 2026-08-11) and answered: **HOLD**, relayed by the Steward.
  This lane could not independently re-verify Gemini's authorship of
  the return (no live claude_code↔Gemini channel exists) but the return
  is structurally consistent with the dispatch — it answers the four
  numbered questions asked, in order, in the requested format. Four
  named defects: (1) cohort-expansion drift — Kapeleris and Ben sit
  outside the analysed Sections 2–8 cohort; acceptable as a fresh case
  only with a baseline analysis first; (2) hypothesis degradation — the
  "I already know what they'll say, they're validating not creating"
  framing invalidates what SVAP2 (bilateral verification-basis
  articulation) is built to test, per Gemini turning it into "a
  confirmation exercise dressed as a test"; (3) commercial trust-damage
  risk — testing an experimental activation pattern on Probico, a live
  commercial counterparty with an active project thread, risks
  confusing project scope with experimental consulting; (4) unmet
  preconditions — identity gap now closed (see (a)); Gemini's own Mode
  3 governance additionally triggered `STOP CONDITION: MISSING
  SUBSTRATE PAYLOAD` because the dispatch referenced documents by path
  rather than pasting their literal text. Gemini's own (unadopted)
  recommendation: route to ChatGPT for Steward-facing arbitration,
  supply literal payloads, confirm identities, align hypothesis
  boundaries before execution. **Still open at end of this turn**: the
  run-sequencing question (solo dry-run vs. Kapeleris-then-Ben,
  Gemini-blocking vs. parallel) and what specifically Kapeleris/Ben are
  being asked to validate — both asked of the Steward, not yet
  answered.
- **source_of_truth**: `Deliverables/baselines/ADAPTIVE_COLLABORATOR_GEOMETRY_v0.1.md`,
  Section 14;
  `05_AI_RETURNS_HASHED/20260811_DISPATCH_CLAUDE_gemini-independent-challenge-collaborator-geometry-section14_v0.1.md`
  (the prompt as sent);
  `05_AI_RETURNS_HASHED/20260811_RET_GEN_claude-code-gemini-section14-hold-and-kapeleris-correction_v0.1.md`
  (the HOLD return and identity correction, this turn).
- **verification_instruction**: re-read the HOLD-return document fresh;
  confirm whether the Steward has since supplied literal payloads for
  re-challenge, run a baseline analysis on the new collaborators, or
  otherwise resolved the three still-open defects, before treating this
  entry's "not yet ready" conclusion as current.
- **next_valid_action**: Steward decides how to respond to the HOLD —
  options named in the return document are (a) supply literal payloads
  and re-challenge Gemini, (b) run baseline geometric analysis on
  Kapeleris/Ben first, (c) resolve the validate-vs-discover framing
  question directly, (d) reconsider Probico as the first test surface
  given the named commercial-trust risk. This lane holds, does not
  choose among these.
- **self_authority_claim**: none.

## Change log

- v0.1 → v0.2: corrected queue framing to aligned-capabilities framing.
- v0.2 → v0.3: capability 2 updated with a real executed proxy-test
  result (escalation adds value).
- v0.3 → v0.4: capability 1 resolved. 4/4 file hashes and 3/3 Odoo
  records independently verified, not trusted from the ChatGPT relay.
- v0.4 → v0.5: capability 2 updated with the self-triage test result.
- v0.5 → v0.6: capability 2 resolved — Steward ruling "Accept self
  triage." Capability 3 freshly re-verified as NOT ready to commence.
- v0.6 → v0.7: capability 3 updated — primary collaborator identity
  corrected and independently verified (Kapeleris, not Capillaris);
  Gemini independent challenge dispatched and answered with a HOLD
  (relayed, not independently re-verifiable by this lane); four named
  defects recorded, one closed (identity), three still open. Capability
  3 remains not yet ready to commence.
