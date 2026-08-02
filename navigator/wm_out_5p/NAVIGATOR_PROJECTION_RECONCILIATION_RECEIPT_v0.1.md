# NAVIGATOR_PROJECTION_RECONCILIATION_RECEIPT_v0.1

CONTROL MARKER: CLAUDE-CODE-FIVE-PRIORITY-NESTED-COMPLETION-v0.1
Work Object: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Lane: claude_code · PPV: Potential · Replay-validity: PRESERVED
Date: 2026-08-03 (AEST)
Trigger: independent review verdict P1_LIVE_VERIFIED /
HOLD_FINAL_FIVE_PRIORITY_ACCEPTANCE — projection incoherence after the
executed D007 correction. Scope: projection-only. No Odoo, N8N or Stream A
action of any kind occurred in this reconciliation.

## Root cause (RC12, appended to the fix log)

The same D007-state facts existed in multiple copies: a hardcoded
applyCurrentUiPatch() JavaScript override inside the Navigator (which
overwrote the loaded runtime state with pre-execution priorities, critical
path, Stream C state and next action), plus parallel copies in
NAVIGATOR_DELIVERY_STATE.json (work_object.authority, embedded
parallel_streams Stream C, held_items), NAVIGATOR_PRIORITY_MODEL.json
(one_next_action), NAVIGATOR_PARALLEL_STREAMS.json (one_next_action,
Stream E next_action), the Navigator's static status metric, and
NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html (static rows + embedded JSON
literal). Prior updates patched fields individually — the drift class this
Work Object exists to eliminate.

## Durable correction (not per-field patches)

1. applyCurrentUiPatch() replaced with an identity passthrough — the
   generated DATA/NAVIGATOR_DELIVERY_STATE.js|.json are now the single
   runtime state source; the screen can no longer regress on load.
2. One shared replacement table (model.POST_D007_REPLACEMENTS +
   reconcile_post_d007) applied to every surface carrying pre-execution
   language; every copy of priorities, authority, held items, stream C/E
   state and one-next-action now states the executed, receipted correction.
3. Build-failing coherence guards added to all three generators: any
   surviving stale marker (READY_FOR_D007_RELEASE, "prepared but not
   released", "Obtain explicit", etc.) aborts generation.
4. Permanent regression test 36 scans every deployed html/json/js/md
   surface for the stale-marker list on every harness run.

## Files corrected and redeployed (returned-hash == local-hash, byte-exact)

- SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html — 45,585 B —
  d0b9bec175857333bd921dd2e958b24c3b5394422db02c2eb1b36661a864de44
- COMPONENTS/NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html — 34,056 B —
  f57df2e01135d7e095814e43a1cee29013eff9919a51fd9b876a9630e5367baf
- DATA/NAVIGATOR_DELIVERY_STATE.json — 16,615 B —
  d5924b40106a8bfa65a08f71a231ebea14915d8909ecc0878e11efb17e225c1e
- DATA/NAVIGATOR_DELIVERY_STATE.js — 15,618 B —
  0ec2065f430c4a8691859d2179edb4e307a0b61d77732aabc5a5297f73de5b48
- DATA/NAVIGATOR_PRIORITY_MODEL.json — 2,821 B —
  907530bca1be915b837f0247e277aac5fbd87ae7e4b13c814e64a2502a918382
- DATA/NAVIGATOR_PARALLEL_STREAMS.json — 8,623 B —
  ca60860f7df0e2ed8451efd7b0798130686a8d138ebd243def8bd3d6e8d44422
(NAVIGATOR_BENEFIT_REALISATION.json was already coherent — unchanged.)

## Verification

36 static tests (incl. new test 36) + 134 browser interaction checks PASS;
live rendered DOM re-checked in Chromium: contains EXECUTED_RECEIPTED, no
READY_FOR_D007_RELEASE, no "Obtain explicit", critical path shows the
executed state, zero JS errors. Fresh SharePoint readback of all six
deployed files with stale-marker scan recorded in
NAVIGATOR_D009_READONLY_REPLAY_RECEIPT_v0.1.md.

Authority: interface/projection scope only. Held items unchanged.
