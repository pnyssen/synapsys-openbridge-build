# Live Findings v0.1 — Navigator Static-Validation Regression Suite

Scope: read-only checks run against real, freshly-fetched evidence for
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`, this session.
No file was written to the live Obsidian workspace or SharePoint
Working Memory as part of producing these findings — every check ran
against a local copy already verified byte-identical to the live
source (see "Snapshot fidelity" below).

## Snapshot fidelity

`findings/live_snapshot_v1_2.html` is a local copy of
`Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html`,
fetched via `sp_read` this session. Verified byte-identical to the
value receipted in `NAVIGATOR_AI_ROUTE_AND_SUBMIT_GATE_CLARITY_RECEIPT_v0.1.md`
(the most recent live-edit receipt found for this file): 27,099 bytes,
SHA-256 `8c360285b95f3eef7e7d78ca2e4a0ce1815d2467e60812f7f42a866bde696184`
— recomputed locally from the saved copy, matches exactly.

## Results

Run: `python3 -B run_live_findings.py`, this session.

| Check | Result |
|---|---|
| `link_checker` (broken relative links, missing Home return, arrow notation, competing primary-interface claims) | **No findings.** Every relative link on the live page resolves against paths independently confirmed via `sp_list` this session; a Home-return link (`../../../00_HOME.md`) is present; no arrow notation; no phrase repeated as a competing "current interface" claim. |
| `presentation_standard` (white background, no dark-mode query, dead `data-open` controls) | **No findings.** Explicit `#fff` background declared; no `prefers-color-scheme` media query; every `data-open` target has a matching `id` on the page. |
| `state_vocabulary` — candidate/implemented/canonical/current collapse | **No findings**, after a correction — see "Tool defect found and fixed" below. |
| `state_vocabulary` — displayed-state vs `window.navigatorStatus` test hook | **No findings.** All 29 independently-derived visible-DOM values (integrity domain counts, Mesh cell/gate/edge counts, Service/Canonical/Benefit/Asset/Pattern/Method counts, PPV) match the embedded test hook exactly, after a parser fix — see below. |
| `manifest_parity` — `FILE_MANIFEST_SHA256_v0.3.csv` vs live `sp_list` byte counts | **1 finding.** `CURRENT_DELIVERY.md`: manifest records 4,235 bytes; live `sp_list` (this session) shows 3,029 bytes. See "Controlling defect" below. |

## Controlling defect: stale manifest row for `CURRENT_DELIVERY.md`

`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/FILE_MANIFEST_SHA256_v0.3.csv`
(last modified `2026-08-01T22:40:27Z`, confirmed via `sp_list` this
session) records `CURRENT_DELIVERY.md,4235,ea01bab35cfcaddd82130b7067224d771ba13235ac90cc0977167a9a8fc5b0a3`.

The live `CURRENT_DELIVERY.md` (confirmed via `sp_list` this session)
is `3,029` bytes, last modified `2026-08-02T00:59:33Z` — **after** the
manifest was last generated. The file has been edited since the
manifest that is supposed to describe it was filed; the manifest's
byte count (and therefore its SHA-256, which was not independently
recomputed here — see "What was not fabricated" below) no longer
describes the file it claims to.

This is exactly the "manifest completeness / byte and SHA-256 parity"
failure mode this cycle's checklist names, found on the real, current
workspace — not a candidate build.

### What was not fabricated

This report does **not** supply a replacement SHA-256 for the current
`CURRENT_DELIVERY.md`. `sp_read`'s returned text has, elsewhere this
session, been shown to not always be byte-identical to the source
(trailing-newline and line-ending differences seen when round-tripping
through `sp_write`) — self-computing a hash from a fetched copy and
presenting it as authoritative would risk exactly the kind of
unverified claim this Work Object's own discipline exists to prevent.
The correct fix is for whoever holds write access to
`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/` to regenerate
`FILE_MANIFEST_SHA256_v0.3.csv` (or file a v0.4) from the files as they
now stand. This finding identifies exactly which row and by how much,
so that regeneration does not have to be preceded by another
discovery pass.

### Isolated candidate correction (not applied)

See `CANDIDATE_MANIFEST_ROW_CORRECTION_v0.1.md` in this same folder —
a one-row note, not a full replacement CSV, naming the stale row and
the two independently-sourced numbers that disagree. Not written to
`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/` — this lane's write
authority does not extend there, and even if it did, this task's own
instruction ("Do not implement these patches unless a separate
authority statement exists") applies.

## Tool defects found and fixed during this cycle

Running the checks against real content (rather than only synthetic
fixtures) surfaced two real limitations in the checks themselves,
both fixed before this report was written, with regression tests added
against the exact real phrasings that triggered them:

1. **`state_vocabulary.find_state_collapse` false-positived nine times**
   on real content. The first version flagged any occurrence of
   'candidate' within 160 characters of 'implemented'/'canonical'/etc.,
   which fires on entirely correct governance prose like "Canonical
   candidates and Pattern candidates materially exceed promoted/admitted
   objects" — two different things legitimately both called
   "candidate" and "canonical" in one sentence, not a claim that a
   candidate object IS canonical. Fixed by requiring an explicit
   linking verb ("is", "are", "now", "remains", "marked as", "becomes")
   between the two words within one HTML chunk, and by excluding
   `<script>` block content (JS object field names are not prose
   claims). Regression tests use the exact real phrasings that
   originally false-positived.

2. **`state_vocabulary.extract_window_hook` could not parse the real
   `window.navigatorStatus` object** at all (silently returned "hook
   not found"), because the real hook's first field,
   `currentPanel:()=>document.querySelector('.panel.active')?.id`, is
   a function value the offline extractor's quote-conversion regex
   could not turn into valid JSON. Fixed with a depth-aware top-level
   entry splitter that drops function-valued (`() =>` / `function(`)
   entries before attempting to parse the remainder as JSON, keeping
   every data-valued field (including nested objects like
   `integrity:{...}`) intact. This is what made the 29-field
   displayed-state-vs-test-hook comparison possible at all.

Neither defect was in this Work Object's own artifacts — both were in
this cycle's own new tooling, caught by testing it against real content
instead of only hand-written fixtures, and are recorded here rather
than quietly fixed and left undisclosed.
