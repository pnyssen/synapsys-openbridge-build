# Navigator Static-Validation Regression Suite

Built for the "CLAUDE CODE CONTINUATION — NAVIGATOR MVP TRAVELLING
WORKSTREAM" instruction, Work Object
`WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001`, Priority 1
("Navigator static-validation regression suite"). One cycle of the
goal loop: read the governing manifest, find the highest-value
completable defect, delete unnecessary scope, apply the smallest
isolated correction, test, byte-check, file.

**No live endpoint call, credential, N8N/Odoo mutation, or write to
any live Obsidian/SharePoint path was made anywhere in this package.**

## Layout

```
checks/manifest_parity.py         manifest completeness + byte/SHA-256 parity — reusable, not tied to one manifest
checks/link_checker.py            broken relative links, missing Home return, arrow notation, competing-interface claims
checks/presentation_standard.py   white-background/no-dark-mode standard, dead data-open controls
checks/state_vocabulary.py        candidate/implemented/canonical/current state-collapse + displayed-state-vs-test-hook comparator
tests/test_checks.py              32 deterministic tests, no network calls
run_live_findings.py              runs the checks against real, freshly-fetched Work Object evidence
findings/live_snapshot_v1_2.html  local copy of the live Architecture v1.2, verified byte-identical to the receipted live file
findings/LIVE_FINDINGS_v0.1.md    the actual findings from running the suite against real content this session
findings/CANDIDATE_MANIFEST_ROW_CORRECTION_v0.1.md   isolated candidate correction note (not applied to the live file)
TEST_REPORT.md                    full test transcript and checklist coverage table
CANDIDATE_MANIFEST_SHA256.csv     final file/byte/hash manifest for this package, regenerated last
```

Run it yourself:

```
python3 -m unittest tests.test_checks -v   # 32 tests
python3 run_live_findings.py               # re-run the real-content scan (uses the saved live snapshot, no network call)
```

## Why priority 1, not priorities 2-6

Fresh reads of the governing manifest and recent correction receipts
this session showed another lane (matching the pattern this Work
Object's own CLAUDE.md warns about) actively, live-editing the
Architecture v1.2 interface and the Wave Runner component today —
copy/alert-defect fix, AI-route/submit-gate clarity, entry/hierarchy
correction, MECE priority correction, all filed within the last few
hours. Priority 3 ("Architecture v1.2 defect isolation") is
substantially already being worked, live, by whoever holds write
access to that surface — this lane has none there regardless (write
authority is bounded to new-file creation under `05_AI_RETURNS_HASHED/`
only), so duplicating that investigation would both waste effort and
risk stepping on live, in-progress work. Priority 1 is genuinely
additive: a reusable, offline, testable tool that complements rather
than competes with that manual/visual correction work, and directly
serves priorities 2 and 4 as well (link/Home-return checks are exactly
what a HAION orientation check needs; the manifest-parity and
state-vocabulary checks are general-purpose, not tied to one file).

## What running it against real content actually found

One real, confirmed defect: `Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/FILE_MANIFEST_SHA256_v0.3.csv`
has a stale row for `CURRENT_DELIVERY.md` — the manifest records 4,235
bytes, but the live file (edited after the manifest was last
generated) is now 3,029 bytes. Full detail, evidence, and an isolated
candidate correction note (not applied) are in `findings/`.

Everything else checked — links, Home-return path, arrow notation,
competing-interface claims, white-background/dark-mode standard, dead
`data-open` controls, and (after fixing two bugs in this cycle's own
new tooling) state-collapse language and the displayed-state-vs-test-hook
comparison across 29 fields — came back clean on the real, current
Architecture v1.2.

## What this cycle deliberately did not attempt

- Fixing the stale manifest row directly. This lane's write authority
  does not extend to `Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/`, and
  even if it did, this task's own instruction bars implementing
  Architecture-adjacent patches without separate authority. A candidate
  correction *note* was produced instead — see `findings/`.
- A general Canvas JSON structural validator (schema conformity, unique
  node/edge IDs, resolvable targets). Real, valuable, but a large
  enough piece of work that folding it into this same cycle would have
  meant a rushed, under-tested version — better as its own next cycle.
- Any HAION/Obsidian-surface work beyond what the link checker already
  covers (one front door, one primary interface, direct return routes)
  — a full HAION review (nine-verb navigation, one/two-action access,
  projection-vs-operational-truth distinction) is priority 2's own
  scope and deserves a dedicated pass, not a rider on this one.
- Any N8N viewer work (priority 5) — no new N8N evidence changed since
  the last cycle's read-only work, so there was nothing higher-value
  there than the manifest-parity finding.

## Boundary

No live endpoint called. No credential read, held, or invented. No
write to any Obsidian/SharePoint path outside this lane's own
`05_AI_RETURNS_HASHED/` scope. No N8N/Odoo mutation. No PPV or canon
movement. No replacement of Architecture v1.2. No competing Home,
dashboard, or architecture created.
