---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
last_updated_by: Claude Code, this session
last_updated_context: v0.2 corrects a structural error in v0.1 — Phil's actual framing was "3 capabilities to be aligned and implemented," not a sequential priority queue. v0.1 is retained below the fold as historical record, not deleted.
supersedes: TOBE_PRIORITY_STACK_CURRENT_v0.1.md (same session — corrects structure, not content)
---

# TOBE Capability Alignment — Current v0.2

Do not trust the `as_is_state` fields below past the moment you read
them. Each `source_of_truth` path MUST be re-fetched fresh before this
entry informs any action.

**Structural correction from v0.1**: these are three capabilities to be
**aligned with each other and implemented together**, not a queue where
capability 3 simply waits its turn. Capability 3 is specifically the
**integration test** for capabilities 1 and 2 — the thing that proves
(or fails to prove) that Navigator MVP reconciliation and the Mesh
enablement layer actually cohere, once both exist. Framing it as a
gate rather than an integration point was this document's own error in
v0.1, not a restatement of what Phil said.

### 1. Capability 1 — Navigator MVP reconciliation (CGPT)

- **tobe_goal**: this lane actively supports whichever lane is
  reconciling the Navigator MVP. Direct answer to Phil's question this
  session ("do you intend to support this?"): **yes** — intent is not
  in question. What's blocking is locating the actual work, not
  willingness.
- **as_is_state**: as of 2026-08-10, this session — Phil reported CGPT
  is completing Navigator MVP reconciliation as ecosystem first
  priority. A live read of `AI_LANE_ALIGNMENT_REGISTER_v0.1.md` the
  same session did **not** corroborate this — no problem item, lane
  role, or ledger entry names CGPT working on Navigator MVP
  reconciliation. The closest related item (P5, Navigator identity
  merge question) is already closed. Separately, this lane's own
  85-file Navigator/Mesh documentation-stream survey this session
  (`05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-navigator-stream-reconciliation-packet_v0.1.md`)
  is a documentation reconciliation, not necessarily the same effort as
  "Navigator MVP" — session sidebar evidence (`Navigator MVP L1-L3
  deployment`, `Systems Navigator MVP completion` in Claude Code
  Recents) suggests a possibly-distinct running-application thread.
- **source_of_truth**: `05_AI_RETURNS_HASHED/AI_LANE_ALIGNMENT_REGISTER_v0.1.md`
- **verification_instruction**: re-read the alignment register fresh;
  if it still doesn't show CGPT/Navigator-MVP activity, get the
  specific filename or session link from Phil before doing support
  work, rather than acting on the unconfirmed premise.
- **next_valid_action**: obtain the actual source pointer for CGPT's
  work. Once located, support means: independent verification (same
  method as this session's own D2 survey), cross-check against what
  this lane already found, candidate documentation — not duplicating
  or overriding CGPT's own work.
- **self_authority_claim**: none.

### 2. Capability 2 — SynapSys Mesh enablement layer

- **tobe_goal**: a Mesh enablement layer that is demonstrably aligned
  to the verified Hermes/OpenClaw lessons and the advisor-tool proxy
  test result — not just "a layer that was tested," but the layer
  *as shaped by* what that test actually shows.
- **as_is_state**: as of 2026-08-10 — strip architecture filed as
  candidate
  (`05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_navigator-multichannel-gateway-strip-architecture-candidate_v0.1.md`).
  Advisor-tool test designed (3 signals: 1 routine control, 2
  ambiguous) but **not yet run** — blocked on Anthropic Console credits
  ($0 balance, confirmed via screenshot this session). A zero-cost
  proxy test via this session's own Agent tool was offered but not yet
  executed either.
- **source_of_truth**: `05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_navigator-multichannel-gateway-strip-architecture-candidate_v0.1.md`
- **verification_instruction**: before treating this as tested, confirm
  either the Workbench run happened (check for actual `server_tool_use`
  / `advisor_tool_result` output) or the Agent-tool proxy ran — absence
  of a result means still FORM stage, not FLOW.
- **next_valid_action**: run one of the two test paths; feed the result
  back into the strip architecture as the thing capability 2 is
  actually aligned to, not a separate afterthought.
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
  (b) once capabilities 1 and 2 have real evidence, a concrete design
  pass on how Section 14 actually tests their integration (not yet
  written — flagged here as missing, not filled in with a guess).
- **self_authority_claim**: none.

## Why v0.1 was wrong, kept for the record

v0.1 filed these as a numbered "priority stack" with capability 3
described as "gated on 1 and 2" — technically not false, but it missed
Phil's actual point: capability 3 isn't just waiting, it's the
mechanism that tests whether 1 and 2 actually cohere. A queue and an
integration test are different structures, and this document should
reflect the one Phil actually specified rather than the simpler one
that was easier to file.
