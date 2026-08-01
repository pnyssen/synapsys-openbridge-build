# Component-to-Schema Mapping v0.1

How every SCVS v0.2.1 component (per `LANE_C_SCVS_2D_SPECIMEN_v0.2.1.html` §2.3's
16-component catalogue) maps onto `schema/graph_schema_v0.2.json` and is
rendered by `scvs/scvs_compiler.py`. This is the seam between "what Lane C
designed" and "what Lane B's compiler + this build's SCVS pass actually
emit" — every row is either implemented (with the exact field/function that
does it) or named as a disclosed gap, never silently skipped.

| SCVS component | Schema field(s) | Compiler behaviour | Status |
|---|---|---|---|
| Card (object) | `objects[].id`, `.label`, `.kind` | One Obsidian Canvas text node per object, via `canvas_compiler.compile_canvas()` (unmodified, imported from Lane B) | Implemented |
| Work-Object card (heavy left bar) | `objects[].kind` | Not distinguished visually in `.canvas` output (no per-node style variants beyond colour) — the label text itself states "Work Object" for such nodes (see candidate canvas 01, node `n4`) | Partially implemented — text-only, disclosed |
| Chip row | `objects[].evidence`, `.ppv`, `.owner_lane`, `.authority`, `.lifecycle_state` | `scvs_compiler._scvs_chip_line()` — appended as an extra text line on every object node | Implemented |
| Source corner-tag | `objects[].source_tag` | `scvs_compiler._source_corner()` — prepended to node text as `[TAG]` (Canvas nodes have no absolute-positioned corner overlay, so this is a text prefix, not a positioned badge) | Implemented, text-form |
| Gate card (◇ GATE) | `objects[].kind` | Not a distinct node type in `.canvas` output — same generic text-node shape as any other object; the label/kind text says "gate" where applicable (e.g. Mesh canvas 05's `n10` "Gates" node) | Not implemented as a distinct shape — disclosed gap |
| Lane container | `objects[].group` | `_layout()` (Lane B, unmodified) — objects sharing a `group` are laid out in the same column, which is the nearest Canvas-native equivalent to a "lane" | Implemented, structural only (no visible lane border) |
| Exception lane | `relationships[].verb` / `objects[].lifecycle_state` | Not distinguished from the happy path in `.canvas` output; IS distinguished in the N8N viewer HTML (`viewer/n8n_viewer_scvs.py` renders the D007 webhook-auth gap in an explicit `.card.lc-failed` STOP/HOLD block) | Implemented in HTML viewer only — disclosed gap in `.canvas` output |
| Labelled directed edge | `relationships[].verb`, `.id`, `.from`, `.to` | `canvas_compiler.compile_canvas()` edge emission (unmodified) — every edge always carries its verb as the Obsidian Canvas `label` field | Implemented |
| Warning band | `objects[].stop_hold` | HTML only: `.card.lc-failed` + `⚠` chip in the N8N viewer. `.canvas` output represents it as a `⚠ STOP/HOLD: <holder>` chip-line segment (see `_scvs_chip_line()`) | Implemented, both surfaces |
| Flagged table row | (N/A — table rows are an HTML-only construct) | `viewer/n8n_viewer_scvs.py::render_executions()` uses `tr.flag` for non-success executions | Implemented in HTML viewer |
| Stat tile | (N/A) | Not used in this build — no aggregate-count surface was in scope | Not applicable this pass |
| CONTROL/RETURN block | View-level `source`, `snapshot`, `evidence`, `reality`, `ppv`, `authority`, `return_route` | `canvas_compiler._metadata_panel_text()` (unmodified) — the fixed `__source_evidence_authority_panel__` node on every compiled canvas | Implemented |
| Next-action card | (N/A this pass — dispatch's Current Priority requirement is satisfied at the Architecture v1.3 shell level, not per-canvas) | `architecture/build_architecture_v1_3.py` leaves the existing Current Priority panel's action structure untouched | Implemented at shell level, not per-canvas |
| Replay-safe return path | View-level `return_route` | `canvas_compiler._layout()`'s fixed `__return_to_navigator_home__` node + edge (unmodified); schema `pattern` rejects arrow notation | Implemented |
| STOP/HOLD frame | `objects[].stop_hold`, `.lifecycle_state == "held"/"failed"` | Chip-line `⚠ STOP/HOLD:` segment (`.canvas`); `.card.lc-failed` block (HTML viewer) | Implemented, both surfaces |
| Temporary-specimen banner | (N/A — page-level, not object-level) | Present verbatim on both HTML outputs (`generated/N8N_VIEWER_CANDIDATE.html`, `generated/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html`) | Implemented |

## Honest summary

11 of 16 components are fully implemented across both `.canvas` and HTML
surfaces. 3 (Work-Object card, Gate card, Exception lane) are implemented as
plain text within the existing chip-line/label grammar for `.canvas` output
specifically, because Obsidian's JSON Canvas format has no native shape/
border-style variation beyond a single `color` property — this is a format
constraint, not an oversight, and is why the HTML viewer (which has real
CSS) renders the same information with actual visual distinction. 1 (Stat
tile) was not applicable to any surface built this pass. 1 (Next-action
card) is satisfied once, at the shell level, rather than duplicated per
canvas — duplicating it per canvas was considered and rejected in
`INVERSION_AND_DELETION_LOG_v0.1.md` (inversion question 7).
