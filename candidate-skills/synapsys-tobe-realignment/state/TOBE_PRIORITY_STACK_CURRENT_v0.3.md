---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
last_updated_by: Claude Code, this session
last_updated_context: v0.3 updates capability 2 only, with a real executed test result (the zero-cost Agent-tool proxy for the advisor-tool hypothesis). Capabilities 1 and 3 are unchanged from v0.2.
supersedes: TOBE_PRIORITY_STACK_CURRENT_v0.2.md (same session — content update, not a structural correction this time)
---

# TOBE Capability Alignment — Current v0.3

Do not trust the `as_is_state` fields below past the moment you read
them. Each `source_of_truth` path MUST be re-fetched fresh before this
entry informs any action.

Three capabilities to be aligned with each other and implemented
together — capability 3 is the integration test for capabilities 1 and
2, not a queue item waiting its turn. (Unchanged from v0.2; see that
file for why v0.1's queue framing was wrong.)

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

- **tobe_goal**: unchanged — a Mesh enablement layer demonstrably
  aligned to the verified Hermes/OpenClaw lessons and the advisor-tool
  test result.
- **as_is_state**: as of 2026-08-10, this session — the zero-cost
  Agent-tool proxy test **ran** (6 agents: 3 signals × fast-pass/Haiku
  vs. escalated-pass/Fable). Real, executed result, not a plan:
  escalation added material value on **all three** signals, not just
  the two designed as "ambiguous" — including catching an unverified
  "Steward-flagged urgent" claim that had no corresponding entry in
  the live alignment register (fast pass took it at face value and
  misrouted on it). The biggest driver of the quality difference was
  that the escalated pass actually fetched live Working Memory state
  before ruling; the fast pass answered from framing alone.
  **Explicit limitation**: this proxy tested whether escalation adds
  value — it did **not** test whether a cheap model can correctly
  self-triage (skip escalation on genuinely trivial signals), which is
  the actual cost-control question the real `advisor_20260301`
  mechanism depends on. That remains untested. Full comparison filed
  at
  `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`.
  The real Workbench-based advisor-tool test is still not run — still
  blocked on Anthropic Console credits.
- **source_of_truth**: `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-advisor-tool-proxy-test-result_v0.1.md`
  (proxy result); `05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_navigator-multichannel-gateway-strip-architecture-candidate_v0.1.md`
  (strip architecture this feeds into).
- **verification_instruction**: re-read the proxy result document fresh;
  confirm it still reflects "escalation adds value, self-triage
  untested" rather than assuming that framing holds indefinitely.
- **next_valid_action**: design and run a self-triage test — does a
  cheap executor correctly decide *not* to escalate on a genuinely
  routine signal, without being told the answer in advance the way this
  proxy's system prompts effectively did (both passes were pointed at
  the same signal by a human, not deciding for themselves whether to
  escalate). That's the real gap now, not "does escalation help."
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
  (b) now that capability 2 has real (partial) evidence, a concrete
  design pass on how Section 14 actually tests the integration — still
  not written, still flagged as missing rather than guessed at.
- **self_authority_claim**: none.

## Change log

- v0.1 → v0.2: corrected queue framing to aligned-capabilities framing.
- v0.2 → v0.3: capability 2 updated with a real executed proxy-test
  result. Capabilities 1 and 3 untouched — no new evidence arrived for
  either this turn.
