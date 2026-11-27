# RETURN: Claude Code, RC05b Steward screenshot observations and RC05c polish patch (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: OBSERVATIONS RECORDED; RC05c CANDIDATE, SOURCE-READY, NOT INSTALLED. Not D007, not D009, not Steward-accepted.

## Observed by the Steward on dev V20 (Chrome, logged in as Steward; screenshots read by Claude Code; widths of most screenshots unknown)
- Lenses level 1 (action-358) renders after the RC05b install; the card "Context scaffold (read-only)" is shown below the four lens cards. The Depth bar still switches state. The web client did not blank: the new home.js bundle loaded.
- Scaffold view (card clicked): Enable shows the Context headline only; Enhance shows the 7 H.CTX roles (context, purpose, rights_holder required; intersects+, portfolio+, shape, strategy+ optional) and the peers Capability (PROPOSAL) and Service (RULED), both "NO OPERATING SOURCE: HOLD"; Enrich adds Evidence "none", Open questions, Definition source and a Provenance block (kind, definition source, open questions). The "<- Lenses" link is present; level 2 pages (lens pattern, Movement lenses) were reached afterwards. The view states "Presentation only: this view changes no data, kind, PPV, approval or right".
- Steward's note: Lenses levels 1 and 2 are identical at Enable, Enhance and Enrich (existing behaviour; the depth bar acts only on element views).

## Defects recorded
D13 Lenses card gap: large vertical gap between the lens footnote and the scaffold card (wrapper inherited the lens page's bottom padding). Fixed in RC05c.
D14 Open-questions lists in the scaffold view: text right-aligned with bullets far left. Fixed in RC05c.
D15 (layout width, UNRESOLVED): earlier Enhance and Enrich screenshots showed the view in the right half of the window with a blank left area while the Enable screenshot filled the width; the later screenshot at normal width showed the expected left margin. Cause not established (zoom, window or layout). The 390 px and 1024 px layouts are NOT TESTED (the Steward could not set the width): recorded as not tested, not as a pass.
D16 (existing, design question): the depth bar does nothing on Lenses levels 1 and 2, and the level label ("Level 2 of 3 ... Enhance") does not follow the depth bar (same label clash as D9 from the RC04 returns). Needs a Steward ruling on what depth means on list screens.

## RC05c delta (RC05c_scaffold_polish_vs_RC05b_installed.patch.txt, 2,069 B, sha256 83de7a4551dd79c0dcdc59caae9ac60fe464317b234ef0f5e021cf3c67155195)
Two files: scaffold_view.py (left-aligns lists in the value column) and controllers/lenses.py (link card wrapper without the extra page padding). Pinned: prestate tree hash 46df7bc09f15003840431f46dcf3495eb4512556a052c0be0eee4a718e39bd8a (54 files, the RC05b state); expected poststate tree hash f963b951fc1706c25983e1e2bd6fbd39c60b60073dd48edca9dc3d9c9ebb291e (54 files, computed offline). Dry run clean.

## New: pinned install script (install_patch.sh.txt, 2,889 B, sha256 c2ee1f8e8249979bed55ba47cdc40d51adfe92ca567cd74974d45a879605204c)
One command replaces the manual blocks. It refuses on a wrong patch hash, wrong prestate tree hash, an existing backup directory or a failed dry run (nothing changed); it reverses the patch itself if apply, a Python parse check or the poststate hash fails; it restarts only after the poststate gate passes; it never uses rm. Tested offline against dummy trees with a fake docker: 8 tests; 4 mutation controls (no reverse on poststate mismatch, no prestate gate, no patch-hash gate, restart before the poststate gate) each fail a test.

## Tests (offline): 16 + 11 + 22 + 8 = 57 pass. NOT established: anything in a real browser beyond the screenshots above, 390/1024 px, bundle behaviour for RC05c, the install script on the real box.

## ONE NEXT
Steward authorises RC05c (chat word), then runs the two commands Claude Code supplies (fetch the pinned commit; run install_patch.sh). Then one screenshot of Lenses level 1 and one of the scaffold view at Enrich.
