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

## Convergence

The reconciliation ran to a fixed point over three passes: each pass's
fresh SharePoint readback scan fed newly discovered stale phrasings back
into the shared replacement table and marker list (final marker count 23 +
semantic scan), until a readback found zero not-yet-executed framings.

## Files corrected and redeployed (final; returned-hash == local-hash, byte-exact)

- SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html — 45,742 B —
  e23893fd4fce26ce1fbaf63be0a6506a384aaaff629e0046a0682b174b6d59b1
- COMPONENTS/NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html — 34,286 B —
  c74b0d60aeac1643ca3c6bf1651fc160196f8b9b905f62ed5fb89528cb12167b
- DATA/NAVIGATOR_DELIVERY_STATE.json — 16,608 B —
  afc8952b62b1c158df1a765248a57002f5181fcd9ba06a1ba2f22a9ecc5b83ed
- DATA/NAVIGATOR_DELIVERY_STATE.js — 15,611 B —
  f35bece8797c18188046940317e68a191d5ffb207386b451669793fd52692680
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
