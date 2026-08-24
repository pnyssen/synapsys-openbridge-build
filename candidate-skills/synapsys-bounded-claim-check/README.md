# synapsys-bounded-claim-check — CANDIDATE

**Status**: CANDIDATE. Not installed, not promoted. Proposed for D001 review.
**Proposed by**: `claude_code`, 2026-08-24, jointly with the Cowork lane after
four instances of the same failure in one session.
**Relationship to existing skills**: narrows a gap left by
`read-first-never-assume`, which fires on integration, connector, SDK, protocol
and "why is this failing" debugging work. Every failure below happened outside
those triggers. This does not replace that skill and does not overlap its scope.

## The failure this catches

> **Asserting a property of a whole from a bounded sample or filtered view,
> without stating the bound.**

Not a reasoning error. In all four cases below the reasoning was valid *on the
evidence the lane had*. The failure was not checking the evidence's boundary
before speaking as though it had none.

## Why a narrower trigger than "verify claims"

An earlier draft proposed triggering on "claims about artefacts". That is too
broad to fire usefully — it covers nearly every statement either lane makes, and
a trigger that fires on everything gets ignored. The bounded-view formulation is
narrow enough to fire and specific enough to be checkable, because **the test is
not whether the claim was true — it is whether the bound was stated.** That is
a property of the sentence, verifiable without re-doing the work.

## Evidence base — four failures, one session, both lanes

| # | Lane | Bounded view taken | Claim made | Reality |
|---|---|---|---|---|
| 1 | Cowork | `order id desc, limit 3` | "`x_reference` is false on every recent record" | Populated on 649 of 661. Records 834–835 carried the inverse pattern, invisible in a 3-record window |
| 2 | Cowork | Never opened the file | "CLAUDE.md §3's schema block is wrong in three places" | Block is correct in zero places; the field names came from two other models |
| 3 | `claude_code` | `select(.isFolder==true)` on a 459-entry listing | "No such block exists; zero matches for all four strings" | The canonical 107 KB `CLAUDE.md` was in that listing; the filter discarded it |
| 4 | `claude_code` | Searched `/home/user` + `/root/.claude` only | Same as #3 | Canonical file lives in SharePoint Working Memory, never searched |

Cases 3 and 4 are the same claim from two different unstated bounds, which is
why one lane can make the error twice in one breath.

A fifth instance is structural rather than human: the SharePoint MCP's **D1**
defect returned a silently truncated listing with no `truncated`/`next`/count
field. That is this exact failure implemented in tooling — a bounded view
presented as complete. It is fixed in the server now, but it establishes that
the failure mode is not specific to a lane's carelessness.

## Proposed trigger

Fires when a statement generalises over a set — "every", "all", "none", "no
such", "doesn't exist", "zero matches", "on every recent record", "the whole
folder" — **and** the evidence behind it came from any of:

- a query with `limit`, `offset`, `order` + head/tail, or any paging
- a filter, projection, `select`, `grep`, or field subset applied before reading
- a search over a scope narrower than the claim (one folder, one repo, one
  mount, one connector)
- a listing from a source that can truncate
- a document characterised without being opened

## Required output

State the bound in the same sentence as the claim, or don't make the claim:

- ❌ "`x_reference` is false on every recent record"
- ✅ "`x_reference` is false on the 3 most recent records by id; I have not
  checked the population"
- ❌ "No such block exists"
- ✅ "No such block in the repo-local `CLAUDE.md`; I have not searched Working
  Memory"

Where the claim genuinely needs to hold for the whole set, widen the evidence
before speaking: `count_odoo` over the full domain rather than a sampled
`search_odoo`; an exhaustively paginated listing; a search across every mount
the claim covers.

## Escalation rule

**"Not found" is never "does not exist" until the search scope is stated and
covers the claim.** This ecosystem already has the vocabulary for it —
`SEARCH_MISS_NOT_ABSENCE`, used correctly in the AI Lane Alignment Register's
P9 — but it was applied there and missed in all four cases above. The rule is
that the classification is mandatory, not available.

## Scope limits

- Does **not** apply to claims already scoped in their own words ("in this
  repo", "of the records I sampled") — those have stated their bound.
- Does **not** require exhaustive verification of every statement. It requires
  the bound be stated, which is cheap; widening the evidence is only required
  when the claim's scope exceeds it.
- Not a governance gate. Adds no authority, blocks no action, moves no PPV.

## No executable component proposed

Deliberately. This is a discipline rule about how a claim is worded relative to
its evidence, not an algorithm. A linter for it would fire on prose and produce
false positives at a rate that would get it disabled. If D001 wants tooling
support, the higher-value target is the one already demonstrated: make bounded
tools *say* they are bounded, as the D1 fix now does — an unbounded-looking
return from a boundable source is the machine version of this same error.

## Promotion criteria

Promote only if, on review, D001 finds the trigger fires on the four cases above
and does **not** fire on a sample of correctly-bounded statements from the same
session. If it fires on everything, it has the earlier draft's defect and should
be rejected rather than installed and ignored.
