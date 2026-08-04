# NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_RETURN_v1.0

CONTROL MARKER: `CLAUDE-CODE-NAVIGATOR-R1-V1.5-BOUNDED-CORRECTION-CANDIDATE-BUILD`
Thread: `CLAUDE-CODE-NAVIGATOR-R1-V1.5-BOUNDED-CORRECTION-CANDIDATE-BUILD`
Lane ID: `CLAUDE-CODE-CANDIDATE-PATCH`
Wave ID: `WAVE-NAV-R1-V1.5-CORRECTION-20260804-01`
Work Object: `WO-NAV-R1-V1.5-VISUAL-ROLE-CORRECTION-001`
Parent Work Object: `WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`
Return profile: `MULTI_LANE_MM3CCC_RETURN_PROFILE`
Date: 2026-08-04 (AEST)

## Status

`CANDIDATE_PATCH_TESTED__READY_FOR_HUB_REVIEW__NO_CURRENT_MUTATION`

(Maximum permitted conclusion under this Work Object. The candidate is not
declared accepted, current, deployed, final-locked or Round-2-ready.)

## MM3CCC

- **Minto (governing question):** Can the seven evidenced current-v1.5
  presentation/lineage defects be corrected in an isolated, non-mutating
  candidate that passes exact desktop/mobile/route regression, so ChatGPT
  Hub has real evidence to arbitrate promotion?
- **MECE:** One bounded correction Work Object, one candidate patch, one
  return. No overlap with Round-2, D007, ACL/portal, or other Navigator
  surfaces.
- **Criticality:** P1 — sole blocker on Round-1 Steward visual-role
  acceptance per the controlling HOLD return.
- **Continuity:** Controlling HOLD return (consumed) -> Hub bounded
  correction Work Object (consumed) -> this candidate build and test ->
  filed for Hub review -> Hub arbitrates promotion or further correction.
- **Commerciality:** Removes navigation friction and role ambiguity that
  block Steward cold-start use of the accepted Navigator, without
  redesign, external-portal work, or premature authority movement.

## Governing evidence — freshness note (read before relying on the WO's cited hashes)

The controlling Work Object and Hold Return were re-read fresh this cycle
and verified byte-exact against the identities the dispatch quoted:

| File | Expected bytes/SHA-256 | Verified |
|---|---|---|
| `HUB_NAVIGATOR_R1_CURRENT_V1_5_BOUNDED_CORRECTION_WORK_OBJECT_v1.0.md` | 14,482 / `9d1cded979f521bfbf320cecadbc909f41188ae6ea7482f5ab581050726c920f` | MATCH |
| `NAVIGATOR_R1_VISUAL_ROLE_STEWARD_COLD_START_ACCEPTANCE_RETURN_v1.0.md` | 17,381 / `08778c7752f7f9deb9b120e88d3134155a10b6c9627bbf8f6065c50583cfac2f` | MATCH |

The Hold Return additionally cites the **source bodies it reviewed**:
`SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html` (49,468 bytes, SHA-256
`1855057f...`) and `00_HOME.md` (5,140 bytes, SHA-256 `170d1c0c...`). A
fresh fetch this cycle found both files at the **same byte count** but a
**different SHA-256** (v1.5: `185505e2...`; `00_HOME.md`: `170d1c85...`).
Per this repository's standing state-awareness discipline, live state is
never trusted from a prior read — the current v1.5 and current
`00_HOME.md` have been edited again (same length) by another lane since
the Hold Return's review, most visibly through the addition of nine
`ELEMENT_*_v1.3.html` pages and re-pointing of v1.5's element links from
v1.2 to v1.3 (itself the exact lineage gap C7 corrects). This candidate is
built from the **live-current body as it exists now**, per the Work
Object's explicit instruction to "read the exact current v1.5 body and its
current linked files" — not from the frozen snapshot the return quoted.
This is a freshness/lineage finding, not a STOP trigger: it does not
question the Hold Return's underlying findings (all seven defects
independently reproduce against the live-current body, see Baseline
regression below), and none of the WO's listed escalation conditions apply.

## Identity and scope

### Source files read (live-current, fresh fetch this cycle)

| Path | Bytes | SHA-256 |
|---|---:|---|
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html` | 49,468 | `185505e22a4df2a7e36008e36236aafa7ac0d66234e88000790a1a0e3ad935c6` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/DATA/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json` | 81,211 | `a5927546a7c525a27d6cdf356e71e466d6fe1e63f4e5ea3314552bd17fca1aa1` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ELEMENT_MESH_CONTROL_GATES_v1.3.html` | 22,009 | `b1cf397f7d6568e75c4ba4f99879f33b7a11dfe0cab869c77dbba6e388bba8e8` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ELEMENT_BENEFITS_ASSETS_v1.3.html` | 23,132 | `e162eed20613532a4df05c55cf9a5f6370d19a017719756fb1d0c6b56f7a0a4c` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html` | 22,420 | `28bfcb8f22f5d399a7f2d2d0b96a8bef65af435b1c7bee2a2f322574c8f95680` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ELEMENT_CONTEXT_MEMBRANE_v1.3.html` | 22,384 | `67dd1636b12df2af731eca6a9cafa83cd845ff5217a44ccb34d88cb7fb86f0d8` |
| `Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html` | 22,387 | `c01f170e8985bb536df8d871b4dcd2d7961033833b7626fdcf466af6ab1e6ed0` |

(Full 17-file source mirror manifest, including the four unaffected v1.3
element pages and iframe-embedded surfaces read for local test-tree
completeness only, is `EVIDENCE/../SOURCE_MIRROR_MANIFEST_SHA256.csv` in
the working directory; not shipped in the ZIP since it is not a modified
file. Available on request.)

### Candidate files produced (isolated workspace only)

| Path (relative to ZIP root) | Bytes | SHA-256 |
|---|---:|---|
| `SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html` | 51,753 | `dd29d373fb7dd310781b7e0729cb1eb43f0641de8ea3b549b936b4c404adaf69` |
| `COMPONENTS/ELEMENT_MESH_CONTROL_GATES_v1.3.html` | 22,313 | `5f5bae42e4544bc03fef3d68cace8ab5325e0ae801bb129935f747e1bf573a98` |
| `COMPONENTS/ELEMENT_BENEFITS_ASSETS_v1.3.html` | 23,436 | `378b42317403221215813ad0e1585fc0296931ef5e2e2b18426b26620d5ce75b` |
| `COMPONENTS/ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html` | 22,724 | `c1c126ef8a532b2182e0d91d5aac613c6e4abab7aeed756ae75a2a6908193839` |
| `COMPONENTS/ELEMENT_CONTEXT_MEMBRANE_v1.3.html` | 22,688 | `d37e5eff47f62f1ec736212de2234de7d63803eb458645a982ab2054128837cf` |
| `COMPONENTS/ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html` | 22,691 | `066b44996bff8c879ed0985ec0641849f9d8048a59c5ebff5fc5cc4062501d76` |
| `DATA/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json` | 81,211 | `f2a486c20b4a1552b4696c37b0fe7101daba35b1e63d7482de3c4b77445cf8d2` |

Full manifest of all 21 files in the ZIP (candidate files + evidence +
manifest itself): `MANIFEST_SHA256.csv`, included at the ZIP root.

### Diff proving no unrelated file changed

Unified diffs for every modified file are included at
`EVIDENCE/diffs/*.diff` (source_mirror -> candidate). The registry diff is
additionally rendered as a field-level diff
(`EVIDENCE/diffs/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY_FIELD_DIFF.txt`) since
the source is single-line minified JSON: it lists exactly the 9
`elements[*].routes.html` fields changed, and a programmatic full-object
equality check (reverting only those 9 fields) confirmed **no other field
in the registry changed**. No file outside the 7 listed above appears in
either diff set.

### Current Working Memory files not modified — confirmation

This build used `sp_read` exclusively against all Obsidian/current paths
throughout (zero `sp_write`/`sp_create_folder` calls against
`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/` or `Obsidian/00_HOME.md`
this cycle). A fresh `sp_list` of
`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/COMPONENTS/` taken
immediately before writing this return shows every relevant file's
`lastModified` timestamp still dated 2026-08-02/03 — none dated today
(2026-08-04) — confirming no write occurred to any current path during
this candidate-build session. No Odoo, N8N, runtime, schema, menu, ACL,
view, field, record, Canon, Pattern, Method, Service, Asset, Benefit or
PPV mutation of any kind occurred.

## Changed-file list (7 total)

1. `SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html` — C1, C2a, C2b, C3, C4, C5a, C5b
2. `COMPONENTS/ELEMENT_MESH_CONTROL_GATES_v1.3.html` — C6
3. `COMPONENTS/ELEMENT_BENEFITS_ASSETS_v1.3.html` — C6
4. `COMPONENTS/ELEMENT_CURRENT_WORK_OBJECT_QUEUE_v1.3.html` — C6
5. `COMPONENTS/ELEMENT_CONTEXT_MEMBRANE_v1.3.html` — C6
6. `COMPONENTS/ELEMENT_AGENT_RUNTIME_ROUTING_v1.3.html` — C6
7. `DATA/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json` — C7

## Corrections applied (exact mechanism, not narrative)

- **C1 — cold-start position.** Root cause: on a hash-less load the init
  script still wrote `#operate` into the URL via `history.replaceState`,
  and native/async browser scroll-restoration then scrolled to the
  `id="operate"` panel before or independent of any explicit
  `scrollIntoView` call (the code's only `scrollIntoView` is gated on an
  explicit `anchor` argument, which is `null` on cold start — the scroll
  was happening through the URL-fragment side channel, not the app's own
  scroll call). Fix: on a genuine cold start (no incoming hash), the
  default panel state is now applied via direct class toggles with **no**
  `history.replaceState` call and **no** URL fragment; `scrollY` is then
  forced to 0 synchronously, on the next animation frame, and on a
  zero-delay timeout, to defeat native or async restoration regardless of
  its exact trigger. An incoming deep-link hash (e.g. `#status/mesh`)
  still routes and anchor-scrolls exactly as before — deep-linking is
  unaffected.
- **C2a — mobile hero column cascade.** Root cause: `@media(max-width:1400px)`
  (3-column hero) is declared in source **after**
  `@media(max-width:820px)` (1-column hero); at mobile widths both match,
  and the later, wider-range rule wins the cascade, reintroducing 3
  columns. Fix: scoped the 1400px rule to `min-width:821px`, so it only
  applies in the tablet/small-desktop band it was written for.
- **C2b — priority title truncation (found during candidate testing, same
  defect class as C2, not previously isolated from the column-count bug).**
  Root cause: `.priority-copy b{white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}` is unconditional (outside any `@media` block),
  so even after C2a restores one column, long titles still truncate with
  an ellipsis. Fix: added a mobile-scoped override
  (`white-space:normal;overflow:visible;text-overflow:clip`) inside the
  existing 820px mobile block so titles wrap instead of truncating.
- **C3 — persistent operating identity header.** Added a static block
  inside `<header class="top">`, populated with the same values already
  shown elsewhere on this exact page (Work Object id, PPV, authority
  summary) — no new claim, no live ACL simulation. Content: Role
  (Steward / D001 — internal), Context/membrane (CTX-SS), Plane
  (Form/Flow/Evolve), Work Object, PPV (Potential), Authority (HELD —
  projection/link scope only), source/freshness pointer, STOP/HOLD.
- **C4 — non-Steward fail-closed disclosure.** Added directly under the
  existing primary-actions notice: governance/Project-owner/Benefit-owner
  routes stated as internal-governed and Context/authority-bounded;
  collaborator/partner and client-sponsor access stated as **not
  available** through this surface, fail-closed, separately held; no
  control implies live authentication, ACL enforcement or a permission
  grant.
- **C5a/C5b — one current next action.** The page exposed two different,
  conflicting next-action texts with no field to say which was current.
  Added one clearly labelled "Current next action" field in the hero,
  visible pre-scroll, using the text already shown (verbatim) in the
  existing authoritative status-panel metric — no new claim. Relabelled
  the Steward-reminders cell that previously also said "Next action" to
  "Supporting action (steward reminder, held)" so it no longer reads as a
  second, competing current action.
- **C6 — direct return continuity.** The 5 flagged v1.3 element pages had
  **zero** navigation markup of any kind (verified: 0 occurrences of the
  Navigator filename, no `.routes` CSS class) — a genuine absence, not a
  differently-shaped route. Added a minimal `<nav class="routes"><a
  href="../SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.5.html">Return to
  Navigator</a></nav>` (with matching CSS, styled identically to the 4
  pages that already had it) immediately inside `<main>`. The other 4
  v1.3 pages were independently verified (fresh grep against the live
  source, not assumed from the prior return) to already carry this link
  and were left untouched.
- **C7 — route registry lineage.** The live registry named `_v1.2.html`
  for all 9 Element `routes.html` entries while the live v1.5 body links
  `_v1.3.html` pages for all 9 (verified both facts directly against
  fresh source, not assumed). Updated only the candidate copy's 9
  `routes.html` values to `_v1.3.html`; every `canvas_source` field (which
  correctly still names real, historical `_v1.2.canvas` files — a
  different artefact type with its own independent version) was left
  untouched, confirmed by the field-level diff and full-object-equality
  check above.

## Desktop test matrix (1440 × 1000, candidate)

| Test | Result |
|---|---|
| White page / readable dark text | PASS |
| Initial Home control surface visible | PASS |
| Initial auto-scroll absent | PASS — `scrollY=0` |
| Persistent operating identity header visible | PASS |
| One current next action visible | PASS |
| Three primary actions operate | 3/3 |
| Top Five Priorities readable | 5/5 |
| MVP Elements readable | PASS |
| No horizontal overflow | PASS |
| No browser script/component errors | PASS |

## Mobile test matrix (390 × 844, candidate)

| Test | Result |
|---|---|
| Initial Home control surface visible | PASS |
| Initial auto-scroll absent | PASS — `scrollY=0` |
| Persistent header readable, doesn't cover primary actions | PASS |
| Top Five priority titles readable, no ellipsis/clipping | PASS — 5/5, 0 clipped (measured `scrollWidth<=clientWidth` per title) |
| Affected cards render in one readable column | PASS — `grid-template-columns` resolves to 1 track |
| One current next action visible | PASS |
| No horizontal overflow | PASS — `0px` |
| No browser script/component errors | PASS |

## Route and lineage test matrix (candidate)

| Test | Result |
|---|---|
| Three primary actions | 3/3 |
| Nine Element pages | 9/9 |
| Nine Canvas routes | 9/9 |
| Direct Navigator return from Element pages | 9/9 |
| Canvas return continuity | 9/9 (unaffected by this candidate; verified still resolving) |
| Route registry v1.3 Element references | 9/9 |
| No current route targets v1.0 or v0.2 | PASS — 0 found |

## Role and membrane test matrix (candidate)

| Test | Result |
|---|---|
| Current role visibly Steward / D001 internal | PASS |
| Context/membrane and operating plane visible | PASS |
| Work Object, PPV, authority, STOP/HOLD visible | PASS (all 4 present in header) |
| Internal governance/Project-owner/Benefit-owner routes stated bounded | PASS |
| Collaborator/client sponsor access stated unavailable, fail-closed | PASS |
| No control implies live authentication/ACL/permission grant | PASS |
| Source, evidence, freshness, reality, authority, replay-validity distinct | PASS |

## Baseline regression (unmodified live-current body, same harness — proves the defects exist pre-candidate)

Run against the **unmodified** live-current source (no candidate files
applied), same assertions, same viewports:

| Check | Baseline result |
|---|---|
| Cold-start scrollY (desktop) | **FAIL** — `scrollY=1546` |
| Cold-start scrollY (mobile) | **FAIL** — `scrollY=4691` |
| Mobile hero columns | **FAIL** — 3 tracks (`94.5px 134.4px 105px`) |
| Priority titles clipped | **FAIL** — 5/5 clipped |
| Identity header present | **FAIL** — absent |
| Role-boundary disclosure present | **FAIL** — absent |
| Single current-next-action field | **FAIL** — absent |
| Direct Navigator return, 9 element pages | **FAIL** — 4/9 (exactly the 5 flagged pages missing it) |

The measured desktop/mobile `scrollY` values (1546 / 4691) match the
controlling Hold Return's own measurements exactly, independently
confirming both that the defects are real and that this harness reproduces
the Hold Return's evidence from the live-current body rather than from the
Hold Return's text.

## Full assertion count

99 total assertions this cycle: 58 candidate-specific + 12 role/membrane +
29 baseline (of which 17 baseline assertions correctly FAIL, reproducing
all seven defects; 12 baseline assertions correctly PASS — e.g. Canvas
routes and 3 primary actions were never broken). **Candidate: 58/58 pass,
0 fail.** Structured evidence: `EVIDENCE/browser_test_report.json`.
Screenshots: `EVIDENCE/screenshots/{baseline,candidate}_{desktop,mobile}_initial.png`.

## Evidence state

SUFFICIENT. Every claim above is backed by a fresh, this-cycle
`sp_read`/`sp_list` call, a locally-executed Chromium test (Playwright,
`/opt/pw-browsers/chromium`), or a programmatic diff/equality check — none
is a narrative-only PASS claim.

## Authority state

HELD, as scoped by the Work Object. This return authorises nothing beyond
filing the two required candidate outputs for Hub review.

## Reality state

The candidate is a tested, non-deployed design artefact. The exact current
v1.5 surface remains the sole current Navigator interface, unedited,
unreplaced, unpromoted by this return.

## Open gaps

- The Hold Return's cited source hashes for v1.5.html and `00_HOME.md` no
  longer match the live body (see freshness note above) — informational,
  not a defect in this candidate; Hub should be aware the live surface has
  continued moving since the Hold Return's snapshot.
- `NAVIGATOR_DIM_ANTIFRAGILE_CHALLENGE_v1.0.html` is now linked from v1.5
  (`#home` anchor) and was not part of the Hold Return's seven cited
  defects or this Work Object's seven corrections; out of scope here,
  noted for Hub awareness only.
- Canvas-view and Canvas-source routes were spot-verified to still resolve
  (9/9) but were not independently re-audited byte-for-byte in this cycle
  since they are unmodified and were not part of the cited defects.

## Exactly one recommended next action

ChatGPT Hub reviews this candidate (ZIP + return) against the seven
required corrections and the full test evidence, and arbitrates promotion,
further bounded correction, or rejection — Round-1 final lock, Round 2 and
all mutation authority remain Hub's to release, not this lane's.

## STOP/HOLD flags

None triggered. No escalation condition from the Work Object's list
applied during this build (no live ACL/portal/authentication requirement
surfaced; no current-file overwrite was needed; no competing Home/dashboard
was required; every source body was identified exactly; the v1.2->v1.3
lineage mismatch resolved without historical rewrite — v1.2 pages remain
on disk as historical lineage, untouched; scope did not expand beyond the
seven stated defects; no D007/final-lock/Round-2/PPV/canon/external
authority is implicated by this candidate).

## Replay-validity

`PRESERVED__LIVE_CURRENT_BODY_RE_READ_FRESH__SEVEN_DEFECTS_INDEPENDENTLY_REPRODUCED_IN_BASELINE__CANDIDATE_CORRECTS_ALL_SEVEN_ZERO_REGRESSION__NO_CURRENT_MUTATION__HUB_REVIEW_PENDING`

Every check in this return is reproducible from the filed ZIP alone: serve
its contents over the exact same relative paths as
`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/` (or diff each file against
the live-current body using the included unified diffs) and re-run the
same desktop/mobile/route assertions.

## ADDENDUM — binary ZIP filing limitation (added after initial return filing)

The Working Memory SharePoint write tool available to this lane
(`sp_write`) accepts text content only, has no chunked/append mode, and a
single call cannot carry an ~1.1MB base64 payload (the encoded size of
this 840,226-byte ZIP) — this is the same hard ceiling independently
documented earlier in this Work Object's parent thread on files an order
of magnitude smaller. No binary-upload tool for this SharePoint site is
connected to this lane.

Given that constraint, the deliverable was filed as faithfully as tools
allow:

- All 15 text-based files that make up the ZIP's contents (7 candidate
  files, 5 unified diffs, the field-level registry diff, the structured
  browser test report, and `MANIFEST_SHA256.csv`) are filed individually
  to this same destination folder, at the exact relative paths they hold
  inside the ZIP, each independently byte/hash-verified.
- The 4 PNG screenshots (binary, `EVIDENCE/screenshots/`) and the ZIP
  itself could not be placed in Working Memory through any available tool.
  Both were handed directly to the requesting user/Steward as file
  attachments in this session, and their SHA-256 identities are recorded
  above and in `MANIFEST_SHA256.csv` so Hub can verify byte-identity of
  whatever copy it receives by hand.
- The ZIP's own SHA-256 (for identity verification of any copy that
  reaches Hub by another channel): `a4c6a2a0288d23addf8946b5e3a670ad31e4fbf386b8da1ca1ad3bccd470aa49`,
  840,226 bytes.
- The ZIP is fully and deterministically reconstructable from the filed
  text files alone (same relative paths, same bytes) plus the two binary
  screenshots, using any standard zip tool — no information is lost by
  this filing method, only the single-archive packaging.

Verdict, evidence, authority, reality and STOP/HOLD statements above are
unaffected by this addendum: the candidate was built, tested and evidenced
in full; only the final binary-packaging step could not be transmitted
through this lane's SharePoint write tool.

## ADDENDUM 2 — one raw diff file not filed to Working Memory (all others 16/16 filed)

`EVIDENCE/diffs/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json.diff` (162,628
bytes — two single-line unified-diff hunks, since the registry is
minified single-line JSON) could not be transmitted through `sp_write` in
this session: its content exceeds the per-turn output-generation limit
even when reconstructed and dumped directly, independent of any chunking
strategy tried. It was independently reconstructed locally and verified
byte-identical to the copy inside the ZIP (`cmp` clean; SHA-256
`576cec75b2c9c024eada179df753e7ebe89b142b4d4786c4c72a2446de6fedf4`,
162,628 bytes, matches `MANIFEST_SHA256.csv` exactly) — its correctness is
established, only its transmission through this text-input tool failed.

This file carries no information not already available: it is fully
superseded by `EVIDENCE/diffs/NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY_FIELD_DIFF.txt`
(filed, human-readable, lists the exact 9 changed fields), and it is
present byte-exact inside the ZIP already delivered directly to the
Steward. All other 16 of 17 ZIP-content text files are filed and
returned-hash-verified in Working Memory at
`ZIP_CONTENTS_TEXT_FILES/` under this same destination folder.
