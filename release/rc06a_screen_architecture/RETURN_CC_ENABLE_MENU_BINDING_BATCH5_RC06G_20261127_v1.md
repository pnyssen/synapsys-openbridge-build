# RETURN: RC06g batch 5, bind the 43 menu screens to their live menus (Enable panel on the native view), source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_MENU_BINDING_BATCH5_RC06G_20261127_v1.md, sha256 61b6f0126375e167d027dea35bf1c569d8831cd33531872fe954124b859ba7bf (Steward word "Instruct code", 27 Nov 18:13 local).
Evidence state: offline tests run and passing (223); live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.
Steward instruction carried: the Context date edit (D7) stays NOT approved; Context's declaration and goldens are untouched.

## Consumed base state and hashes (verified before any change)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD 02c1727d5829ff1dbc9fcc8f74cb75e0cd37de3f (RC06f), equal to origin, no later commit.
- Base addon tree (64 files): baad1cc64c151d0ce099a48cbfd1473355713df87733665d4143259a1fcfae16 with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the value given.
- N1 spec: NAV_N1_RC06_BATCH5_LIVE_MENU_DECLARATION_BINDING_20261127_v1.json, 111,806 bytes, sha256 9e316030d709896390c99cf845848d17c2d87e678a08344d0c6da54b43d695ee, read with sp_read_bytes, hash matched. Kept as a test fixture; the generator refuses any other hash.

## Mechanism chosen, and rejected
Chosen: a read-only route plus one OWL main-component panel. The native menu, action and view are not touched. When the action on screen is a window action, the panel asks `/synapsys/menu/enable` with the action id only. The server decides everything (role, binding, read right, anchors) and returns the Enable panel HTML or a reason code. A refusal, error or non-window action leaves no panel and no trace.
Rejected, with reasons:
- Replacing or re-pointing the native action or menu: contract forbids; breaks 22 actions carrying domains or contexts.
- Inheriting each of the 43 native views to insert the panel: 43 edits in `views/*.xml`, security-relevant, large blast radius, and not reversible by one file.
- Binding by label or xmlid-only on the client: the client would hold ids and could be spoofed; N1 requires the immutable screen id and menu_id plus action_xmlid anchors.
- Routing record screens or SCR.MESH.NOUN as menu defaults: N1 forbids it; refused by the validator and by the route.

## What was built
- `data/screen_bindings_batch5.json` (49,919 bytes): 51 rows from N1 (43 bound, 8 NONE). Reproduced byte-for-byte by `tools/gen_batch5_bindings.py` from the N1 fixture.
- `screen_binding.py`: loads and validates the table (unique menu, action and screen; undeclared screen refused; record screens, SCR.CONTEXT.RECORD, SCR.ASSET.RECORD, SCR.MESH.NOUN never routed; an unbound row may not carry a screen).
- `scaffold_wire.menu_enable(env, action_id, menu_id, screen_id, depth)`; `screen_render.render_enable_panel`; `controllers/menu_binding.py` (one `auth='user'` jsonrpc route); `static/src/enable_panel.js` and `.xml`; `__manifest__.py` gains the two web assets; `controllers/__init__.py` gains one import.
- Entitlement is fail-closed and ordered so a refusal leaks nothing: recognised role, then binding by action id, then the caller's own `check_access('read')` on the native model, then anchors (`env.ref` of the xmlid equals the action id; `ir.ui.menu` for the menu id is visible to the caller and points at that action), then the screen. Refusal is a reason code only: NO_RECOGNISED_ROLE, MENU_NOT_BOUND, NO_READ_RIGHT, ANCHOR_MISMATCH, MENU_NOT_VISIBLE, SCREEN_NOT_BOUND_TO_MENU, UNKNOWN_SCREEN, DEPTH_NOT_SUPPORTED, BINDING_INVALID.
- No sudo, no write, no raw SQL, no new menu, model, action, ACL, group, rule or hook. Source status shown follows the screen's own word (N1 `source_status` is CANDIDATE_NOT_ADOPTED on every row); RULED is never a default.

## File table (expected versus actual)
| File | Expected | Actual | sha256 |
|---|---|---|---|
| data/screen_bindings_batch5.json | new | new | e26d574412280f0796629b8dde742f90bf8036ea570cda0851d8bbece8287de0 |
| screen_binding.py | new | new | 3f0a7049e82031f1b3c23ea04ce09013366358fdb75e3fd32db1bb68029f689b |
| controllers/menu_binding.py | new | new | 2c01a7450a44144eda7bc9b76290467061e02adcf11b0eea99d0ecc9ced24fc8 |
| static/src/enable_panel.js | new | new | 93c14aa9c01505075fb81e9fabbddf2dc353654248f1c76f284a0707d8e7be1f |
| static/src/enable_panel.xml | new | new | 71fbb05cd525c25bd68b2a48e218d894e79186f6e407eff82e013df2e0b68902 |
| __manifest__.py, controllers/__init__.py, scaffold_wire.py, screen_render.py | modified | modified | see patch |
| views/*.xml, security/*, models/*, migrations/*, hooks.py, all other data files, all goldens | unchanged | unchanged (file-hash proven against the RC06f manifest, tests/golden/rc06f_tree_manifest.json) | |
Tree: 64 to 69 files.

## Tree hash and patch
- New tree (69 files): 2ab96fd52ace9dee2b7cf0f388f805a7232a4addabfed22ca355291983a4017b.
- Patch against the RC06f tree: RC06g_menu_binding_batch5_vs_rc06f.patch, 69,193 bytes, sha256 6e4e152611ab93de3746f5de9d19d9e0c2d6cbf55a2b286b7282351ad9755a17. Applied to a clean copy of the base tree it gives 2ab96fd5…; reversed it gives baad1cc6… again.

## Offline tests run versus live tests not run
Run: 223 tests, all pass (192 earlier plus 31 new in tests/test_batch5.py; log TEST_LOG_rc06g_batch5_offline.txt, sha256 159ec1fdb640357f996fabec44f80428bf4ce389a6888b92ab711973b38d69e7). They cover: the 43 bindings reproduce from N1; every screen exists and is unique; menu and action anchors equal N1; 8 NONE rows unbound and never routed; native action fields equal N1 for all 51 (and, for the 39 synapsys.* actions, the addon XML's model, view_mode and domain); only the 5 expected new and 4 modified files differ from RC06f; all 43 routes return their own screen at Enable only; refusal paths return reason only, no content, zero writes, and read nothing before the entitlement check; status follows the source word; the JS component under node (asks by action id only, nothing on refusal, error or client action); checks 1-17 still pass over all 46 declarations. Mutation checks caught: wrong screen bound, native domain altered, NONE row bound, read gate removed, status hardcoded RULED, client sending a screen id, back link added, new menuitem added, sudo introduced.
Not run, and offline tests cannot show: the caller's effective read right on a real database; how the panel is placed and looks in a browser at 390 and 1024 px; whether Odoo 20's web client mounts the main component and fires ACTION_MANAGER:UI-UPDATED as assumed; Collaborator and Client behaviour; the 10 window actions from synapsys_mesh and synapsys_v19_reference (not in this tree, files untouched; N1 fields taken as given).

## The 8 gaps (SOURCE_OR_SPECIAL_SURFACE_GAPS), left unbound as N1 directs
17 Architecture register (steward-only reference, no declaration); 18 Lexicon (steward-only reference, no declaration); 34 Map (custom client, not covered); 35 Registry (N.MESH is not a registry release); 36 Elements (not an entry list); 37 Clusters (not a cluster list); 38 Verbs (nine action menus do not cover the master 27-verb list); 42 Lenses (custom client, RC05 lens not equivalent to a generic menu declaration). Each keeps its existing native action. Placement defaults kept: Learning under Navigator, Inbox as Signals intake, Architecture register and Lexicon Steward-only under Form (leaf group 35, root 34).

## Rights
Every read runs as the caller (their own env). No sudo, no write, no new group, ACL or rule. A caller who cannot read the native model gets a reason code and no content. The menu group on the native menu still controls visibility; the panel adds none and removes none.

## Findings and choices to review (mine, not rulings)
1. Contract says no registry or catalogue read, but 27 bound screens are noun screens that draw on the registry-backed projection. I kept the installed noun path (caller's own rights) and skip the catalogue read unless the screen has peers (only SCR.CONTEXT.NOUN). Menu screens read neither. Please confirm or tighten.
2. Anchors are N1's dev database ids (menu_id, action_id). On any other database they fail closed (ANCHOR_MISMATCH), so the panel shows nothing there. The xmlid is checked against the id, so a renumbered database is refused rather than mis-bound. A later contract may want xmlid-only anchors for menus.
3. Panel placement (a main component at the foot of the page, not inside the native view) is unverified in a browser. It may sit below long lists. This is the main thing the dev install must check.
4. Enable depth only. Enhance and Enrich are refused (DEPTH_NOT_SUPPORTED) on this route.
5. Two manifest assets and one controller import are the only non-data edits outside the wire and renderer; the data list is unchanged.
6. N1 view_type, ACL text and source_status are carried as given; every status is CANDIDATE_NOT_ADOPTED. I did not re-derive them from the live database.
7. Context (menu 188) is served by SCR.CONTEXT.NOUN, never SCR.CONTEXT.RECORD. D7 still not applied.

## Dissent
A panel appended outside the native view is the smallest safe change but may not be the layout the Steward wants; the alternative (per-view inheritance) is larger and was rejected on risk, not on merit. Not decided here.

## Delivered versus Realised
Delivered: source, tests, patch, this return, committed and pushed to the branch. Realised: nothing. Not installed, not seen in a browser, no user has used it. Realisation needs the Steward-gated dev install and live checks listed above.

## Release path (not authorised here)
Dev install of the patch by the Steward/D007, then live checks as the Steward and a Collaborator at 390 and 1024 px. Registry release is a separate D007 step.

## ONE NEXT
Install this patch on dev (Steward/D007 step) and check the panel's placement and the refusal behaviour on three menus: one noun (Service), one menu screen (Measures) and one unbound (Lexicon), as Steward and as a Collaborator.
