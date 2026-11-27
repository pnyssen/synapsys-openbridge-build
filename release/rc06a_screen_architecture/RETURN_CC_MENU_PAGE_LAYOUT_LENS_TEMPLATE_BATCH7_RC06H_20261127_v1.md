# RETURN: RC06h batch 7, bound menu pages in the lens template (Depth tabs, definition on top, Records heading, wrapping table, answer prefix), source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_MENU_PAGE_LAYOUT_LENS_TEMPLATE_BATCH7_RC06H_20261127_v1.md, sha256 eca46e084a46bd0d4b6cc2f4cd5407357ac603b54d1b0ccbf88a49dc2adb796d (read with sp_read_bytes, hash matched).
Evidence state: offline tests run and passing (245); live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.
Steward instruction carried: Context frozen, D7 not applied.

## Consumed base state and hash (verified before any change)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 88eb331c6ee0d86afa885d7b973957941cbde83d (RC06g), equal to origin.
- Addon tree, 69 files: 2ab96fd52ace9dee2b7cf0f388f805a7232a4addabfed22ca355291983a4017b with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the value given.

## Mechanism chosen, and rejected
Chosen (smallest, nothing native replaced): keep the RC06g read-only route (`/synapsys/menu/enable`, now serving all three depths) and the one main-component, and turn what it shows into the lens-template page head.
- Tabs: the same shared Depth control the Context page uses (`synapsys_lens_mode` service, Enable default, persisted), as buttons Enable, Enhance, Enrich at the top of the panel. A change of tab re-asks the route with that depth.
- Content: the server renders the existing frame (header with chip, answer, trust line, movement line) plus the sections the declaration itself carries at that depth, through the existing projection and the same slot builders as the full screen. Enhance: made-of and peers. Enrich: trust table, open questions, technical. A screen with none says so in the existing words. No content is invented.
- Order: the panel ends with a "Records" heading. The page's CSS (travelling with its html, so it exists only while a page is shown) puts the panel before the native view using flex order on the web client's own children, and lets the native view take its own content height; the native empty-state helper is made static so an empty list shows directly under the heading.
Rejected, with costs:
- Inheriting the web client's ActionContainer template to insert the panel inside the action area: exact placement, but a wrong xpath in Odoo 20 breaks asset compilation for the whole backend, and I cannot see Odoo 20's source here. Kept as the fallback if the flex order does not hold on dev (needs a Steward decision, one-file change).
- OWL portal into the action manager: appends after the view, so still needs CSS order; adds a failure mode (missing target throws).
- Per-view js_class or replacing the action/view: forbidden by the contract (R3) and replaces the native view.
- DOM relocation by script: OWL loses track of moved nodes; rejected.

## What changed (file table, expected versus actual)
| File | Expected | Actual |
|---|---|---|
| screen_render.py | modified | modified: R5 CSS rule; R6 `strip_status_prefix` in the answer slot; new `render_menu_page` and `PAGE_STYLE` |
| scaffold_wire.py | modified | modified: `menu_enable` accepts enable, enhance, enrich (an unknown depth is refused); evidence is read at Enhance and Enrich as the full scaffold route does; html is the page |
| static/src/enable_panel.js, .xml | modified | modified: shared Depth tabs; asks by action id and depth only |
| everything else (views, security, models, migrations, hooks, controllers, all data files, goldens) | unchanged | unchanged, file-hash proven against the RC06g manifest (tests/golden/rc06g_tree_manifest.json) |
Tree stays at 69 files. No new menu, model, action, ACL, group, rule, route or file in the addon.
New hash: 5671fcafea9009845ee97b1fc511c335846a7bc38723ef302355457509ac5433.
Patch against the RC06g tree: RC06h_menu_page_lens_template_vs_rc06g.patch, 12,139 bytes, sha256 562da646160289f6fc1fc684016ec11b0a22f60cf1f23a4f18cdf7ffa29a87d8. Applied to a clean RC06g tree it gives 5671fcaf…; reversed it gives 2ab96fd5… again.

## Golden changes
No golden file on disk changed. The Context render differs from the RC06a and RC06e goldens in exactly one place, the trust table CSS rule (R5); the tests compare the render with that one rule put back and require byte equality with the unchanged goldens, so Context's text, route JSON and declaration are proved untouched (R7). The route JSON goldens are unchanged. Of the 46 declarations, one answer changes (R6, below).

## R6: what the list is, and where the contract's premise differs
- Declarations whose answer opens with its own status word and a colon: only SCR.PRODUCT.NOUN ("OPEN: placed at the same level as Method and Workflow…"). Its rendered answer now starts "placed at…", the chip carries OPEN.
- SCR.MESH_MEASURES.MENU does not have the pattern. Its row quote is "A measure stored by Mesh address". The "CANDIDATE:" the Steward saw is the status lead the RC06c rule adds before any non-RULED answer. On the menu page I no longer print that lead, because the chip sits directly above the answer; the page answer is exactly the quote. The full-screen render (Lenses and Context specimen) keeps the RC06c lead rule unchanged. If the Steward wants the lead removed from full screens too, that reverses a rule he accepted in RC06c: his call.

## Tests run versus not run
Run: 245 pass (223 earlier, adjusted as listed, plus 22 new; log TEST_LOG_rc06h_batch7_offline.txt, sha256 f3762cd224be5fcf8fc9e2689f2977927fe02c6b9df03fefbc44ea4368d945c2). New in tests/test_batch7.py: three tabs and Enable default; Enhance and Enrich through entitlement for all 43 pages and the declaration's own sections (and the plain "none declared" words); refusals unchanged at every depth; role depth cap; CSS rule checks for order, no tall blank band, Records heading; trust table wrap rule; answer-prefix rule and its list; Context frozen; file-level diff against RC06g.
Earlier tests changed, each because the contract replaces the behaviour they pinned: test_batch1/3/4/5 and test_batch2 (Context golden compare now undoes the one R5 rule first), test_batch2 (the answer assertion allows the dropped prefix), test_batch6 (pages compared with RC06e after undoing R5 and R6), test_batch5 (route key set gains depth, page markers, Records slot, an unknown depth is the refusal case, the client harness has the shared-mode service and sends the depth). Helper: tests/rc06h_compat.py.
Mutation checks, each caught: a tab dropped, entitlement skipped on Enhance, status prefix left, clipping rule restored, a native field altered, Records heading dropped, lead glued back on the page, order rule removed, tall blank band restored.
Not run, and offline tests cannot show: how the page looks and where it sits in Odoo 20 at 390 and 1024 px; whether the web client's containers take the flex order as assumed; the class name of Odoo 20's empty-list helper; role behaviour on a real database; Collaborator and Client behaviour.

## Findings and choices to review (mine, not rulings)
1. Placement is the risk. It rests on `.o_web_client` being a flex column and the main component or its container being a direct child (both cases covered by the rules). If dev still shows the page at the foot, the fallback is the ActionContainer template inheritance above, which needs Odoo 20's template text to be exact.
2. A long Enrich page scrolls inside the panel (max 60 vh) so it cannot push the list off screen. That is two scroll areas on a small screen; reducing it needs the template route.
3. The Depth tabs are the one shared mode: changing it on a menu page also changes it on Context and the Lenses, and it persists in the browser.
4. Enhance and Enrich on registry-backed nouns read the registry and catalogue with the caller's own rights, as the full scaffold route does. At Enable, as RC06g, the catalogue is read only for screens with peers.
5. Anchors are still the dev database ids from N1.
6. The Service Catalogue page still shows one registry sentence: content for Enhance and Enrich comes from the Navigator's N2, not from this batch.
7. Menu renames ("Architecture register" to "Register", "Benefit–Asset links" to "Links"): these menus are defined in synapsys_v19_reference and synapsys_mesh, not in this tree. A rename needs those modules' menu source (the menuitem name), or a Steward-run write to the menu record. Not edited here.

## Dissent
The cleaner structure is one page that scrolls as a whole with the list inside it, which only the template route gives; I took the safe route first because a template mismatch fails loudly and widely. Not decided here.

## Delivered versus Realised
Delivered: source, tests, patch and this return, committed and pushed. Realised: nothing. Not installed, not seen in a browser.

## Release path (not authorised here)
Dev install of the patch by the Steward/D007, then a look at Services and Measures at 390 and 1024 px as Steward and as Collaborator.

## ONE NEXT
Install this patch on dev and check, on Services (action 297) and Measures (action 189), that the page head with its three tabs sits above the list with the Records heading under it. If it still sits at the foot, say so and I build the ActionContainer fallback.
