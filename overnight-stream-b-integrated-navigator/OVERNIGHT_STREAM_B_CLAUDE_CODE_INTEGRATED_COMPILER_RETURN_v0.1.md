# Overnight Stream B — Claude Code Integrated Compiler Return v0.1

Wave: `W-NAV-INT-MVP-20260802-01` / Overnight wave `W-NAV-INT-MVP-20260802-OVERNIGHT-01`
Work Object: `WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`
Dispatch executed: `OVERNIGHT_STREAM_B_CLAUDE_CODE_INTEGRATED_COMPILER_DISPATCH_v0.1.md`,
7,013 bytes, SHA-256 `6bb0415d2faa2b512b5d72d85025b03e186f580ad9205917ba736bf6447c60ac`
— independently recomputed and byte-count-cross-checked against `sp_list`
before execution (first reconstruction attempt produced a false 1-byte
mismatch from an added trailing newline; corrected via `printf '%s'`
before trusting the match, per this repo's CLAUDE.md standing rule to
recompute rather than trust a cited hash).
Build snapshot: `2026-08-01T17:02:57Z` (UTC, real capture via `date -u`, not
fabricated). Return filed: `2026-08-01T17:03:24Z` (UTC).

**Verdict: `CANDIDATE_COMPLETE / READY_FOR_REVIEW`.** All eight retrieve →
build → test → invert → delete → repair → rebuild → file steps executed
this session, in that order, to completion. 26/26 tests pass. No production
promotion, Obsidian front-door replacement, Odoo/N8N mutation, workflow
activation, credential, ACL, PPV, canon, Service, Pattern, Method, or asset
change was made — confirmed by tool-call log (only `sp_read`/`sp_list` and
the read-only N8N/Odoo MCP tools were called; no `sp_write` prior to this
filing; no write/mutate Odoo/N8N tool called at all).

## Sources consumed (read, never written)

- Consumed deterministic Canvas compiler: `lane-b-n8n-viewer-canvas-compiler/compiler/canvas_compiler.py`,
  commit `86ffa850a92f23e5f35436b66e4d0063e1662ccd` — imported unmodified,
  never edited. Its own row in Lane B's consumed manifest
  (`LANE_B_CANDIDATE_BUILD_v0.2/CANDIDATE_MANIFEST_SHA256.csv`) is untouched
  by this build.
- Consumed SCVS v0.2.1 visual standard: `LANE_C_CLAUDE_COWORK_UNIFIED_VISUAL_SYSTEM_RETURN_v0.2.1.md`
  (17,835 bytes) plus both specimen files (`LANE_C_SCVS_2D_SPECIMEN_v0.2.1.html`,
  `LANE_C_SCVS_2D_SPECIMEN_SET_B_v0.1.html`) — read live this session,
  16-component catalogue and 13-channel encoding table used as the direct
  source for `scvs/scvs_compiler.py`'s chip-line grammar.
- Architecture v1.2: `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html`
  — read live this session, captured verbatim into
  `architecture/architecture_v1_2_raw_capture.html`, confirmed byte-unchanged
  at the live path after the build (re-`sp_list` matched original size).
- Accepted Canvas suite: all 15 files at `Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/*.canvas`
  — read live this session, node/edge counts verified against the parsed
  capture (01: 9n/6e … 15: 9n/13e, full table in build script), confirmed
  byte-unchanged at the live path after the build (re-`sp_list` matched all
  15 original sizes: 3064, 3386, 3038, 4368, 3279, 4457, 2674, 3498, 3467,
  3304, 3713, 3548, 5201, 3869, 5058 bytes).
- Current read-only N8N/Odoo evidence: reused from Lane B's own live capture
  (`fixtures_live/n8n_topology_overview.json`, `fixtures_live/odoo_menu_govern.json`,
  `fixtures_live/d007_workflow_topology.json`) — not re-fetched, per the
  dispatch's "reuse the consumed compiler" instruction; no new N8N/Odoo call
  was needed since Lane B's capture is still the current basis per
  `NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.8.md`'s Lane B row
  (`CURRENT_TECHNICAL_INTEGRATION_BASIS`).
- Fresh cross-check performed immediately before this filing: re-read
  `NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md` and the newer
  `v0.8.md` (5,887 bytes, later `lastModified` than v0.7) via `sp_read`
  rather than relying on this session's earlier memory of lane state — v0.8
  confirms this stream's row was `RETURN_EXPECTED / NOT_LOCATED /
  WAITING_FOR_EXACT_RETURN` at its own snapshot, and `sp_list` on the target
  output folder returned 404 (folder does not exist yet), consistent with no
  prior filing having happened. This return and its filing are what close
  that gap.

## Candidate architecture produced

`generated/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html`
(20,620 bytes, SHA-256 `a291793a2a04c8811042d505bc2de85b76ae8c1bcf5f074c4cf4d0a213bb2e03`).
Built by `architecture/build_architecture_v1_3.py` via fixed, fail-closed
string substitutions (`_replace_once`, raises if a target substring does
not appear exactly once) over the raw v1.2 capture. Changes: title/header
now states "CANDIDATE, not current"; the one `class="state implemented"`
self-reference removed; a top banner added stating this is not the current
control surface with a live link back to v1.2; one new tab
("Integrated Candidate (Overnight)") added before `</nav>`, no new page;
footer updated; the one inherited vault-relative broken link
(`../../../10_WORKSPACES/NAVIGATOR_MVP_v0.2/CURRENT_DELIVERY.md`) replaced
with the stable SharePoint URL to the same document (self-caught via a
sanity-check `href` grep, not user-reported — see Inversion log #8 and
Errors section below); the vestigial, confirmed-unused `packets`/
`copyPacto()` clipboard script removed (confirmed unused via a `data-copy`
grep on the live v1.2 body finding zero matches). Current Architecture v1.2
was read, never written — confirmed by tool-call log and by re-`sp_list`
matching its original byte size after the build.

## Candidate Canvas suite and view profiles generated

15 candidate versions of the accepted Canvas suite, all `_CANDIDATE.canvas`,
in `generated/candidate_canvases/`, plus all 11 view profiles in
`generated/candidate_profiles/` — 26 files total, every one compiled
through the single `scvs.scvs_compiler.compile_canvas_scvs()` function,
which itself calls Lane B's unmodified `compile_canvas()` and adds exactly
one additional pass (an SCVS chip line appended to every object node's
text; source corner tags on the three live-sourced profiles). Zero
per-view branching — same function, 26 different graph inputs. Full
filename/byte/hash list is in `CANDIDATE_MANIFEST_SHA256.csv` (reproduced
in full below in "Exact files and hashes").

Evidence labelling (never invented, never unlabelled):

| Source | Count | Evidence label |
|---|---|---|
| Accepted canvas suite, adapted | 15 | `ADAPTED_FROM_ACCEPTED_CANVAS` |
| N8N topology / N8N workflow detail / Odoo Govern menu | 3 | `LIVE_VERIFIED` |
| Enterprise / PSA / 3x3x3 / nine verbs / Mesh / Signal-to-Asset / Service-Pattern-Method-Canonical / Work-Object-queue | 8 | `LABELLED_FIXTURE` |

## Corrected N8N viewer

`generated/N8N_VIEWER_CANDIDATE.html` (32,700 bytes, SHA-256
`f55f82bfcfc13571650c928ab6cba5276e2fdc03e7cf4afbabcd4e2e7caaa99d`), built
by `viewer/n8n_viewer_scvs.py`. Reuses Lane B's live-sourced snapshot
(`fixtures/n8n_viewer_snapshot.json`) unchanged. Renders SCVS chip/border
grammar via real CSS (`.card.lc-*` lifecycle classes); D007's webhook-auth
gap rendered as an explicit `.card.lc-failed` STOP/HOLD block, not
suppressed or softened; return route points at this candidate's own filed
location, no arrow notation, white background / dark text, no
`prefers-color-scheme` media query anywhere in the file.

## Shared graph schema

`schema/graph_schema_v0.2.json` (4,895 bytes, SHA-256
`9f0cd846db9eadcba60feeb2b6c6c09ed429439634aa226974af206ed9b25528`) —
additive-only extension of Lane B's v0.1 contract: adds optional
`evidence`, `ppv`, `owner_lane`, `source_tag`, `stop_hold` on objects and
optional `line_style` on relationships; `evidence` enum gains
`ADAPTED_FROM_ACCEPTED_CANVAS`; `lifecycle_state` enum gains `conceptual`,
`canonical`. `return_route` keeps Lane B's Correction-v0.1 arrow-notation
rejection pattern unchanged. `SchemaTests.test_optional_v02_fields_do_not_break_v01_shaped_graphs`
proves every v0.1-shaped graph still compiles through the same compiler
unmodified.

## Bounded Stream A adapter

`scvs/stream_a_adapter.py` (6,342 bytes, SHA-256
`07666a403930c9d999ee210591b25ce56183acaf8318c76551a1b17077bfeb0f`) —
`adapt_stream_a_payload()` is the one seam a real Stream A payload will
pass through into `graph_schema_v0.2`'s shape. Stream A has **not**
returned as of this filing (re-verified fresh this session against both
`NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md`, state `TOOL_BLOCKED`,
and the newer `v0.8.md`, state `TOOL_BLOCKED / HELD_PENDING_D001_D007_TRANSPORT_RELEASE`).
Calling the function with no payload raises `StreamANotReturnedError`
(tested, `StreamAAdapterTests.test_adapter_refuses_when_no_payload`) — not
a stub that silently returns empty data. No Stream A data is fabricated
anywhere in this build. When Stream A returns, only this function's body
needs to change; nothing downstream does, since every consumer already
speaks `graph_schema_v0.2` regardless of data origin.

## Tests run

`python3 -B -m unittest tests.test_integrated -v`, from
`overnight-stream-b-integrated-navigator/`, run after all three build
scripts and — last, only after every other file was final — the manifest
regeneration.

**Result: 26/26 PASSED, exit code 0, no skips, no expected failures.**

Full transcript and the requirement-to-test coverage table are in
`TEST_REPORT.md` (5,222 bytes, SHA-256
`4f7e626d788a7462a764ca6ab6c47abb6414800b4d59610d805c87ef33e415b2`).
Categories covered per the dispatch's step 5: schema validation, link/
route validity (fail-closed on arrow notation, every canvas edge resolves
to a real node, no Mac-absolute paths, one disclosed vault-relative
exception named not silently passed), accessibility (`lang`, skip link,
ARIA tablist/tabpanel roles), white background (no `prefers-color-scheme`
anywhere), determinism (same graph compiles byte-identical twice; all 15
adapted-canvas graphs independently proven deterministic; on-disk output
re-derived from inputs right now and matched byte-for-byte), no competing
Home (no file named like `00_HOME`, exactly one architecture shell file,
the shell never claims to be a new Home), Stream A adapter (refuses
without a payload, maps a synthetic well-formed payload without
fabrication), manifest integrity (every manifest row's SHA-256 and byte
count recomputed from the file on disk).

## Inversion and deletion log

`INVERSION_AND_DELETION_LOG_v0.1.md` (8,431 bytes, SHA-256
`b177f46aed0eae73910bc4bfa49b138d5239fe3557ed13d2930decd7cc27897f`) — 10
inversion questions, each resulting in either a concrete deletion/fix (with
its regression test named) or a documented reason no change was needed.

**Deletions made**: a candidate standalone Overnight dashboard HTML (never
built, to avoid a second Home); a duplicated per-view SCVS rendering code
path (never built, single wrapper used instead); the vestigial
copy-to-clipboard `packets` script (present-but-unused in the v1.2
reference capture, removed from the v1.3 candidate); a tempting "example
Stream A payload" fixture that would have blurred the no-fabrication
boundary (never built).

**Not deleted, disclosed instead**: the three `COMPONENTS/*.html` iframe
`src` paths on the Architecture v1.3 shell — vault-relative by original
v1.2 design, will not resolve if this HTML is opened directly from its
Working Memory filing location; kept (removing them would violate
"preserve the strong existing architecture"), named as a disclosed
exception in `README.md` and allow-listed by name (not silently passed) in
`tests/test_integrated.py`.

## Component-to-schema mapping

`COMPONENT_TO_SCHEMA_MAPPING_v0.1.md` (5,219 bytes, SHA-256
`4538e9f594e839d33100fc3bf64e0b3c3294acc9e8994ea0854bdcb1d43a69ac`) — all
16 SCVS v0.2.1 components mapped to schema fields and compiler behaviour:
11 fully implemented across both `.canvas` and HTML surfaces; 3
(Work-Object card, Gate card, Exception lane) implemented as text-only
within the `.canvas` chip-line grammar because Obsidian's JSON Canvas
format has no native shape/border-style property beyond a single `color`
— a disclosed format constraint, not an oversight, with the HTML viewer
rendering the same facts with real CSS border-style/shape where the format
allows it; 1 (Stat tile) not applicable to any surface built this pass; 1
(Next-action card) satisfied once at the shell level rather than
duplicated per canvas, a choice made explicitly in inversion question 7.

## Exact files and hashes (manifest)

Full manifest: `CANDIDATE_MANIFEST_SHA256.csv`, 70 rows (69 files + header),
regenerated last, after every other file was final including
`COMPONENT_TO_SCHEMA_MAPPING_v0.1.md`. Selected top-level entries (full CSV
filed alongside this return):

| File | Bytes | SHA-256 |
|---|---|---|
| `README.md` | 9,474 | `895c0145d6e658eeda63fea3df8deedc232e40c2c3e07787ef321a8f49a2894f` |
| `TEST_REPORT.md` | 5,222 | `4f7e626d788a7462a764ca6ab6c47abb6414800b4d59610d805c87ef33e415b2` |
| `INVERSION_AND_DELETION_LOG_v0.1.md` | 8,431 | `b177f46aed0eae73910bc4bfa49b138d5239fe3557ed13d2930decd7cc27897f` |
| `COMPONENT_TO_SCHEMA_MAPPING_v0.1.md` | 5,219 | `4538e9f594e839d33100fc3bf64e0b3c3294acc9e8994ea0854bdcb1d43a69ac` |
| `schema/graph_schema_v0.2.json` | 4,895 | `9f0cd846db9eadcba60feeb2b6c6c09ed429439634aa226974af206ed9b25528` |
| `scvs/scvs_compiler.py` | 4,305 | `c25bbe4ce4959706721396fbbb3714ba31294e040b40ad6ea5894aa9d287bd5b` |
| `scvs/stream_a_adapter.py` | 6,342 | `07666a403930c9d999ee210591b25ce56183acaf8318c76551a1b17077bfeb0f` |
| `viewer/n8n_viewer_scvs.py` | 10,820 | `c3530322a3153f9947164bf653b34001a889f3265644299bf8aaf9871c4b3b39` |
| `architecture/build_architecture_v1_3.py` | 11,200 | `5672ce15484f891b39e45fe71deeb9548a0a6d33b427dd5de4dcf7518822d488` |
| `build_overnight_candidate.py` | 6,594 | `511b9255a32074103d2f11115398af3fb793a3d17136f8ee0c2fa20fdfd09eb8` |
| `tests/test_integrated.py` | 12,263 | `772cf02051c6c0c3591255e963e5b1af29c15c53f7ba81a8975e59438e09024a` |
| `generated/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html` | 20,620 | `a291793a2a04c8811042d505bc2de85b76ae8c1bcf5f074c4cf4d0a213bb2e03` |
| `generated/N8N_VIEWER_CANDIDATE.html` | 32,700 | `f55f82bfcfc13571650c928ab6cba5276e2fdc03e7cf4afbabcd4e2e7caaa99d` |

All 15 `generated/candidate_canvases/*_CANDIDATE.canvas` and all 11
`generated/candidate_profiles/*.canvas` hashes are in the full CSV filed
alongside this return — every entry independently recomputed from disk by
`ManifestIntegrityTests` at 26/26-green time, not hand-typed.

## Branch and commit

Branch: `claude/n8n-viewer-canvas-compiler-u60beo`
Commits (both pushed to `pnyssen/synapsys-openbridge-build`):

- `a8407569ef66672cbc73596d0b28658cfa402839` — "Add Overnight Stream B:
  SCVS-integrated candidate Navigator generation system" (69 files, full
  first build).
- `80d7d0b7404b7bb9116cd5f2ea0d0fc83909fe2e` — "Add
  COMPONENT_TO_SCHEMA_MAPPING_v0.1.md for the overnight integrated build"
  (2 files: the mapping doc plus regenerated manifest). **Current HEAD —
  cite this SHA as the build basis.**

## Stream A substitution boundary

Nothing in this build stands in for Stream A. All 26 candidate canvases
carry one of exactly three evidence labels
(`ADAPTED_FROM_ACCEPTED_CANVAS`, `LIVE_VERIFIED`, `LABELLED_FIXTURE`) —
never a fourth, invented "as if Stream A" label. `stream_a_adapter.py`
exists only as an empty, refusing seam (raises `StreamANotReturnedError`
unconditionally with no payload) — it was never populated with a
plausible-looking example Stream A payload, a temptation explicitly
identified and rejected in inversion question 10.

## Unresolved gaps (disclosed)

- Obsidian Canvas JSON format cannot express border-style/shape variation
  beyond a single `color` — 3 of 16 SCVS components are text-only in
  `.canvas` output (see component-to-schema mapping). Real format
  constraint, not covered by any workaround this session.
- The three `COMPONENTS/*.html` iframe sources on the Architecture v1.3
  candidate are vault-relative and will not resolve from this Working
  Memory filing location — disclosed and allow-listed, not silently
  passing.
- No live-browser/rendered-DOM test of either HTML output — structural
  (lang/ARIA/CSS-pattern) testing only, same limitation Lane B's own test
  suite already disclosed.
- Stream A has still not returned as of this filing (v0.8 manifest:
  `TOOL_BLOCKED / HELD_PENDING_D001_D007_TRANSPORT_RELEASE`) — the eight
  fixture-based profiles remain fixtures, not yet reconciled to a real
  Stream A contract; this was already a known, inherited condition from
  Lane B, not newly introduced here.
- This candidate has not been reconciled against Stream D's overnight
  output (`OVERNIGHT_STREAM_D_OUTPUT_v0.1/`, filed and `CANDIDATE_WORK_COMPLETE`
  per v0.8) — that folder concerns transport/queue/assurance packets, a
  different technical layer than this stream's Canvas/viewer/architecture
  output, and no dependency between the two was identified in the
  dispatch; noted here rather than assumed compatible without checking.

## Productive improvement

The single largest lever for the next stage is not more Canvas output but
closing the Stream A transport gap: once a verified WM-to-Codex transport
pilot is released (v0.8's own "exactly one controller action"), this
build's `stream_a_adapter.py` seam and the eight fixture-based profiles
become the very next reconciliation, with zero other code needing to
change, because every consumer already speaks the same
`graph_schema_v0.2` contract regardless of where data originates. That
seam existing and being tested now, ahead of Stream A's return, is what
makes that reconciliation a small next step rather than a redesign.

## Exactly one controller recommendation

`STEWARD/D001: REVIEW THIS CANDIDATE (v1.3 shell + 26 canvases + viewer)
AGAINST THE CURRENT v1.2/ACCEPTED-CANVAS BASIS, IN PARALLEL WITH — NOT
BLOCKED BY — THE ALREADY-PENDING D007 WM-TO-CODEX TRANSPORT PILOT
DECISION.` These are independent decisions: the transport pilot governs
whether Stream A can return at all; this candidate's review governs
whether the visual/compiler integration layer is fit to receive Stream A's
data once it does. Holding this review until the transport decision lands
would serialise two things that do not depend on each other.

## Replay-validity

`PRESERVED`. Every claim in this return is either a recomputed hash, a
tool-call-log-confirmed fact (no write calls beyond this filing; original
v1.2 and all 15 accepted canvases re-`sp_list`-confirmed byte-unchanged),
or a disclosed, named limitation — no assertion here depends on trusting
an earlier lane's or an earlier turn's unrechecked claim. Both governing
dispatch manifests (`v0.7`, `v0.8`) were re-read fresh via `sp_read`
immediately before this filing, not recalled from this session's earlier
context.
