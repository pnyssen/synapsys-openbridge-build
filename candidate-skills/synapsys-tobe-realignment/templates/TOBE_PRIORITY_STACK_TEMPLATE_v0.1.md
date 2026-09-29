---
status: LIVING — UPDATE IN PLACE AS STATE CHANGES
authority_state: HELD — this document tracks and orients; it grants no authority and moves no PPV
replay_validity: PRESERVED
---

# TOBE Priority Stack — Template v0.1

Each priority entry below is REQUIRED to carry all six fields. An entry
missing any field is incomplete — not filed, not usable as an anchor.

## Entry format

```
### [rank]. [thread_id] — [short title]

- **tobe_goal**: one sentence, the target state this thread is working
  toward. Not a task list — a state description.
- **as_is_state**: dated snapshot of current reality, as last verified.
  Must carry an explicit date. An undated as_is_state is not a
  snapshot, it's a guess.
- **source_of_truth**: exact Working Memory path(s) (or other
  canonical location) that must be re-checked fresh before this
  entry's as_is_state is treated as current. Not a description of the
  source — the literal path.
- **verification_instruction**: explicit statement that source_of_truth
  must be re-fetched before acting, and what to do if it has moved
  (e.g. "if this no longer matches, update this entry in place before
  proceeding").
- **next_valid_action**: the one next step this thread is actually
  waiting on. Not a wish list.
- **self_authority_claim**: MUST be "none" or explicitly "HELD /
  candidate only." Any entry that asserts VERIFIED, ADOPTED, or
  AUTHORISED about itself (as opposed to quoting that status from a
  cited source) fails validation by design — this is the one failure
  mode this template exists to prevent.
```

## Why every field is required, not optional

- **tobe_goal** without **as_is_state** is aspiration with nothing to
  measure progress against.
- **as_is_state** without a dated **source_of_truth** is a snapshot
  nobody can trust past the moment it was written — exactly the
  failure this repo's own CLAUDE.md names explicitly (a parallel
  session updating shared state unnoticed).
- **verification_instruction** exists because a session under time
  pressure will otherwise treat a stale snapshot as current — this
  field is the forcing function, not decoration.
- **self_authority_claim** exists because a TOBE document is exactly
  the kind of artefact that quietly accumulates authority it was never
  given, one confident restatement at a time.
