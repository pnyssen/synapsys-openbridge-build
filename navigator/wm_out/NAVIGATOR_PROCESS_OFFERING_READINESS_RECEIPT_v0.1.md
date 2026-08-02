# NAVIGATOR_PROCESS_OFFERING_READINESS_RECEIPT_v0.1

CONTROL MARKER: CLAUDE-CODE-NAVIGATOR-L1-L2-L3-COMPLETE-DEPLOYMENT-v0.1
Work Object: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Snapshot: 2026-08-03T09:00:00+10:00
Lane: claude_code · PPV: Potential · Replay-validity: PRESERVED

## Surface

COMPONENTS/NAVIGATOR_NEW_PROCESS_AND_OFFERING_START_v1.0.html (current) lets a
Steward choose New Process or New Offering and produce a governed candidate
packet with all 28 required fields (candidate_id .. replay_validity), including
a copyable blank template. The surface states explicitly that it creates a
design candidate, not an authorised operational record, and why V7 Activate is
HELD (Steward decision + CR required).

## Governed route

Candidates route Orient -> Canonicalise -> Structure -> Assure -> Navigate ->
Compose -> Activate(HOLD) -> Transform(candidate) -> Project. The route is
rendered on the surface and validated in the fixtures.

## Fixtures (synthetic, clearly non-operational)

- DATA/TEST_PROCESS_001_CANDIDATE.json — TEST-PROCESS-001
- DATA/TEST_OFFERING_001_CANDIDATE.json — TEST-OFFERING-001

Each fixture carries: full 28-field packet (synthetic=true plus a
non_operational_notice), a 9-step verb routing trace with V7 state=HOLD, the
Elements touched at each step, and Mesh coverage of all nine stages
(Signal..Feedback). Harness tests T31/T32 verify completeness, trace order,
V7 HOLD, full Mesh coverage and result=CANDIDATE_ROUTING_COMPLETE_ACTIVATION_HELD.
An adversarial injection (V7 HOLD removed) is caught by the harness
(evidence/ADVERSARIAL_INJECTION_RESULTS.json).

## Boundaries preserved

No Odoo or N8N write occurred or is implied. Pattern field is 'NONE (one cycle
is evidence, not a Pattern)'. PPV remains Potential. Benefit realisation is not
declared. Activation remains HELD pending separate Steward/CR authority.
