# NAVIGATOR_CANVAS_AND_LINK_TEST_RECEIPT_v0.1

CONTROL MARKER: CLAUDE-CODE-FIVE-PRIORITY-NESTED-COMPLETION-v0.1
Work Object: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Snapshot: 2026-08-03T09:00:00+10:00
Lane: claude_code · PPV: Potential · Replay-validity: PRESERVED

## What was tested

- 9 browser-safe Canvas views (CANVAS_VIEW_*_v1.0.html), each a self-contained
  inline-SVG projection generated from the authoritative v1.2 .canvas JSON in
  10_WORKSPACES/NAVIGATOR_MVP_v0.2/. No scripts, no network access required.
- Every relative link and internal anchor across all deployed HTML surfaces
  (static harness T18/T19/T20), with off-dist targets validated against a live
  sp_list-derived vault index.
- Browser interaction suite driven in Chromium: desktop (1440x900) and narrow
  (390x780) viewports, JavaScript-disabled pass, file:// pass, stale-anchor and
  direct-element-entry entry paths.

## Results

- Static link/anchor/return tests: PASS (35/35 harness tests green).
- Browser suite: 134 checks PASS, 0 FAIL. Each of the 9 Canvas views
  produced a visible graphical SVG (>= 3 rendered text nodes; full node/edge
  projection with labels). Screenshots captured under evidence/screenshots/
  (navigator desktop+narrow, 9 canvas views, nine verbs, start surface).
- Canvas source routes: each view links the .canvas source (relative) and an
  optional obsidian:// secondary; neither is the primary route (T23/T24).
- The raw .canvas JSON is nowhere a primary "View Canvas" target.

## Evidence files

- navigator/evidence/BROWSER_TEST_EVIDENCE.json (structured DOM evidence)
- navigator/evidence/screenshots/*.png
- Test harness: navigator/tests/test_navigator.py; runner output in
  NAVIGATOR_L1_L2_L3_COMPLETE_TEST_MATRIX_v0.1.csv (same folder as this receipt)

Authority: Obsidian interface + Working Memory filing only; all operational
mutation HELD. This receipt declares no Benefit realisation and no Asset
qualification.

Five-priority cycle re-run: the full browser suite was re-executed after the D007 propagation updates — 134/134 checks PASS, including all nine visible canvas renders, return routes, no-JS, file://, narrow viewport, stale-anchor and direct-entry paths.
