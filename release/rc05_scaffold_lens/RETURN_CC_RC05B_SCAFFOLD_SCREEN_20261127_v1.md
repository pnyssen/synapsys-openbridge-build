# RETURN: Claude Code, RC05b scaffold screen (Architecture > Lenses > Context scaffold), source-ready delta
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | 27 Nov 2026 | Status: CANDIDATE, SOURCE-READY, NOT INSTALLED. Not D007, not D009, not Steward-accepted. Basis for building it: Steward's chat choice "A" (the screen) on 26 Nov 2026; install still needs the Steward's word.

## Base (proved)
Live synapsys tree after the RC05 data-route install: 53 files, tree hash c06edf7172a52e3540b61d136b9f5145571dd7643816377369374962cb8bafcb (verified POSTSTATE_OK on the box; RECEIPT_CC_RC05_DEV_INSTALL_20261126_v1.md sha256 74011412...). Byte-exact copies of live controllers/lenses.py (47db8392...), static/src/home.js (ff0bd4d3..., 3,143 B) and lens_contract.py (c101592a...) were transferred as base64 from the box and matched their printed hashes. lens_render.py (70b4c9e9..., 11,550 B) and lens_mode.js (822ec7c3...) were printed but not needed or transcribed; the change does not edit them.

## Delta (RC05b_scaffold_screen_vs_RC05_installed.patch.txt, 9,541 B, sha256 d7f0956fe7165b9085864d5c2a8f25729c0895a1b3592fbd29120d538da3a893)
Dry run, apply and reverse verified on a reconstruction of the post-RC05 tree. Changes: controllers/scaffold.py (adds route /synapsys/scaffold/view, jsonrpc, auth user, caller's own rights), controllers/lenses.py (adds, at level 1 and only for a Steward, one link card "Context scaffold (read-only)"), static/src/home.js (the Lenses component handles the link, loads the view at the current global depth, reloads it when the depth bar changes, and the existing back link returns to the normal Lenses), new scaffold_view.py (pure renderer: all values escaped, no scripts, handlers or external URLs; missing sources shown in words as "NO OPERATING SOURCE: HOLD"; mobile rules and 44 px back target). No manifest, template, ACL, data or schema change; no module upgrade. The JS is an asset: restart for the Python, hard reload (Cmd+Shift+R) in the browser for the new bundle.
Expected poststate: 54 files, tree hash 46df7bc09f15003840431f46dcf3495eb4512556a052c0be0eee4a718e39bd8a.

## Tests (offline, no Odoo): 47/47 pass
16 core + 11 wiring + 20 UI (10 renderer, 6 JavaScript behaviour run under node with stubbed Odoo/OWL, 4 controller behaviour with stubbed Odoo). 13 mutation controls across the three suites each fail at least one test: new this round, renderer without escaping (V4), renderer without the HOLD text (V2), JS without the depth reload (J2), JS click not opening the scaffold (J1, J2), lenses link without the Steward gate (L2). JavaScript syntax checked with node --check.

## NOT established
Nothing ran inside a real Odoo or a real browser: the OWL component behaviour, the rendered page, bundle regeneration after a restart, the Steward-only link in the live Lenses screen, the 390 px and 1024 px layouts (CSS rules are present and unit-checked, not seen on a device), back/forward/refresh behaviour (the scaffold view, like the other lens levels, is not addressable by URL and a reload returns to level 1), keyboard and screen-reader use. Collaborator and portal users are out of scope under Option A. D6 (open /synapsys/lenses/data) is unchanged. A JavaScript error in an asset can stop the backend web client until rollback.

## Acceptance checks for the Steward, after install (Chrome, logged in as Steward)
1. Architecture > Lenses shows the card "Context scaffold (read-only)"; click opens it. 2. Depth buttons Enable / Enhance / Enrich change the view (roles and peers at Enhance; provenance at Enrich). 3. Both peers read "NO OPERATING SOURCE: HOLD". 4. "Lenses" back link returns to the lens list. 5. DevTools device toolbar at 390 px and 1024 px: no horizontal scroll, text readable, back link and cards easy to hit. 6. No error text, no blank screen, Odoo menus still work. Report each as pass or fail with a screenshot.

## ONE NEXT
Steward says "apply RC05b" (dev fast path) and runs the pinned install commands Claude Code supplies (backup of the current tree, patch, hash gate, restart, readback, rollback ready); then the six checks above.
