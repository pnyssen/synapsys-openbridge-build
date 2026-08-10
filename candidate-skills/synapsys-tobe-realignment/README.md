# synapsys-tobe-realignment

Candidate tooling for a persistent TOBE (target-state) realignment
anchor — the "first iteration of the future SynapSys.md file for our
verb-based model," per direct Phil instruction this session. Built
within the same boundary as every other artefact this lane has filed:
no PPV movement, no authority assertion, no Odoo/N8N/canon mutation.

## What problem this solves

Every SynapSys session (any lane) starts from whatever context that
session happens to load. Without a durable anchor, "what should I be
working on, and against what target state" gets re-derived from scratch
or drifts. This candidate is that anchor — but deliberately thin: it
does not carry state itself. It carries a *pointer and a discipline*
that forces a fresh Working Memory check every time, mirroring this
repo's own CLAUDE.md rule ("never answer a question about SynapSys
state from conversation memory alone — re-fetch the canonical source
fresh, every time").

## What's here

- `templates/TOBE_PRIORITY_STACK_TEMPLATE_v0.1.md` — the required
  schema for any TOBE priority entry: a target-state goal, a dated
  AS-IS snapshot, a named source-of-truth Working Memory path, and an
  explicit instruction to re-verify that path before treating the
  snapshot as current. An entry missing any of these fields is
  incomplete by definition, not just by convention.
- `state/TOBE_PRIORITY_STACK_CURRENT_v0.2.md` — **current** — the real
  three capabilities Phil instructed this session, corrected from
  v0.1's structural error (v0.1 filed them as a sequential queue; v0.2
  reflects what was actually said — three capabilities to be aligned
  and implemented, where capability 3 is the *integration test* for
  1 and 2, not merely gated behind them): (1) support CGPT's claimed
  Navigator MVP reconciliation — **flagged unverified**, since a live
  check of `AI_LANE_ALIGNMENT_REGISTER_v0.1.md` this session did not
  corroborate it; (2) the SynapSys Mesh enablement layer, aligned to
  the verified Hermes/OpenClaw lessons and the advisor-tool proxy test;
  (3) the Collaborator Geometry Section 14 experiment, as the proof
  point for whether 1 and 2 actually cohere. `v0.1` is retained
  unchanged as historical record, per this ecosystem's own
  supersede-don't-delete convention.
- `validator.py` — offline, zero-network, zero-subprocess validator
  for TOBE priority stack documents: required-field presence per
  entry, and an explicit reject rule for any entry that asserts its
  own elevated authority state (`VERIFIED`, `ADOPTED`, `AUTHORISED`
  applied to itself rather than quoted from another source) — the one
  failure mode this whole design exists to prevent.
- `tests/test_validator.py` — tests against both a passing document and
  deliberately broken variants (missing source-of-truth, missing
  re-verification instruction, a self-asserted authority claim).

## What this is not

Not a live orchestration system. Not a substitute for reading
`AI_LANE_ALIGNMENT_REGISTER_v0.1.md`, `WM_CURRENT_STATE_INDEX_v0.2.md`,
or the specific source-of-truth path named in each entry — it is a
forcing function to do exactly that, not a cache of the answer.
`validator.py` reads a single file's text and returns a report; it has
no side effects, mutates nothing, and does not itself decide whether
a priority stack is "correct" — only whether it is structurally honest
about what it does and doesn't currently know.

## How a session is meant to use this

1. Read `state/TOBE_PRIORITY_STACK_CURRENT_v0.2.md` (the current file —
   check for a higher version number first; this document is living).
2. For whichever entry is relevant, re-fetch its named source-of-truth
   path fresh — do not trust the AS-IS snapshot's date as still current.
3. Work from what the fresh check actually shows, not from the
   snapshot.
4. If the state has materially changed, update
   `state/TOBE_PRIORITY_STACK_CURRENT_v0.1.md` in place (same
   living-document discipline as `AI_LANE_ALIGNMENT_REGISTER_v0.1.md`)
   and re-run `validator.py` before treating the update as filed.

## Status

CANDIDATE — filed per direct Phil instruction this session. Not
installed as a standing skill. Not itself a Working Memory filing;
see the corresponding evidence receipt in
`05_AI_RETURNS_HASHED/` for the hashed, filed record of this candidate's
existence (per this lane's own "file before referencing" rule).
