"""Runnable probe prompts for the Capability/Cost Calibration Loop
(see probes.py for fixtures and grading, and the design candidate at
05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
20260815--claude-code--design-candidate--synapsys-agent-capability-calibration-loop--v0-1.md).

These are plain string constants, self-contained enough to send directly to
a candidate model configuration (Opus-high, Sonnet-medium, or any other
config under evaluation) without any live tool access. Source data is
embedded verbatim rather than fetched live, on purpose: a probe that reads
live Odoo/WM state would drift as that state changes, which defeats the
point of a fixed, repeatable golden probe. If the underlying real-world
data genuinely changes, a human re-establishes a new fixture + prompt pair
deliberately (see probes.py's fixture docstrings) -- this module does not
do that automatically.

Zero I/O, same as probes.py -- these are strings, not live calls. The
caller sends the prompt to whatever configuration is under test, parses the
model's response into a `BasinObserveCandidate` / `AutomationBoundaryCandidate`
(see probes.py), and grades it.
"""

BASIN_OBSERVE_PROBE_PROMPT = """\
You are being asked to extract a decision and its blockers from a fixed \
set of source records. This is a calibration probe: your answer will be \
graded against a known-correct baseline, not acted on.

Read-only task, no tools available -- work only from the records below.

# Source records (verbatim, read live from Odoo this session)

## project.project id 100
name: "SynapSys Property / ProBico -- Basin Operating Model and Formalisation"

## mail.activity records on this project (7 total)

- id 22, type "MC: Next Action", date_deadline 2026-06-30, state overdue:
  summary "Next action: TBRP signed transaction agreement intake (expected \
Monday)"
- id 23, type "MC: Blocker", date_deadline 2026-07-31, state overdue:
  summary "Blocker: External contact BLOCKED for all 6 named counterparties" \
-- 6 named counterparties internally CURRENT, external contact still \
gated pending per-engagement Steward direct phrase.
- id 24, type "MC: Blocker", date_deadline 2026-07-31, state overdue:
  summary "Blocker: Reality Anchor HELD pending verified budgets" -- no \
budget figure/funding source/financial close/settlement value present in \
current evidence.
- id 25, type "MC: Blocker", date_deadline 2026-07-31, state overdue:
  summary "Blocker: HoA mechanism UNKNOWN + executed-instrument gaps open" \
-- 5 executed-instrument gaps (E1-E5) + 8 Steward-gated body openings \
still available.
- id 21, type "MC: Status Snapshot", date_deadline 2026-07-04, state overdue:
  summary "Basin status snapshot (2026-06-27)" -- informational snapshot, \
not an action or a blocker.
- id 26, type "MC: Working Memory Anchor", date_deadline 2026-06-30, state \
overdue: summary "Latest Working Memory lineage anchor" -- informational \
evidence index, not an action or a blocker.
- id 27, type "MC: Navigation Map", date_deadline 2026-07-04, state \
overdue: summary "Three-View Mission Control Navigation Map" -- \
informational, not an action or a blocker.

# Observation date

Treat 2026-08-15T07:46:03Z as "now" for any ageing/overdue calculation.

# Task

1. Identify the single current decision/action from the records above -- \
the one record of activity type "MC: Next Action". If more than one \
record could plausibly be the decision, say so explicitly instead of \
picking one.
2. State its source record (model + id).
3. Compute how many days overdue it is, using the observation date above.
4. Identify every blocker record (activity type "MC: Blocker") that \
constrains this decision. List their source record ids. Do not include \
the informational/snapshot records (types other than "MC: Blocker") in \
the blocker list.
5. State plainly whether you are treating this as one unambiguous decision \
or whether you believe multiple decisions are plausible and a human \
would need to choose between them.
"""


AUTOMATION_BOUNDARY_PROBE_PROMPT = """\
You are being asked to classify a fixed list of manual actions from a real \
automation-candidate review. This is a calibration probe: your answer will \
be graded against a known-correct baseline, not acted on.

# Background

A prior review ("Flow Cycle 3") logged seven manual actions an operator \
performs while working a specific focus in a system called Navigator. For \
each action, classify it into exactly one of three categories:

- "automate" -- safe for a read-only agent to perform on its own, no \
material judgment involved.
- "hold_steward" -- involves a judgment call that belongs to a human \
Steward and must never be delegated to an automated agent, even a \
read-only one.
- "resolved" -- already fixed by other means; no action, automated or \
manual, is needed for it going forward.

# The seven actions

A1. Discover the actual decision under gauge: enter a bound focus, read \
Odoo project + activity records, and extract the named decision, its due \
date, and its ageing. Purely mechanical extraction from source records \
with one correct answer.

A2. Assemble the blocker set: read Odoo activity records and list the \
blockers constraining the decision found in A1. Purely mechanical \
extraction from source records with one correct answer.

A3. Check whether the projection is still current: compare a static, \
dated summary against live Odoo counts and report CURRENT or STALE. A \
mechanical comparison against live data, no judgment about what the data \
means.

A4. Re-find the focus inside each Odoo route: after opening an \
unfiltered Odoo list, locate and expand the row matching the bound \
focus. Pure navigation overhead with no judgment involved.

A5. Assemble the real evidence packet into a Wave: decide which evidence \
(from Odoo and Working Memory) counts as sufficient to include when \
preparing a formal work packet for Steward review. This requires judging \
what qualifies as adequate evidence -- a determination a Steward makes, \
not something inferred from a fixed rule.

A6. Track whether a Wave was already prepared or dispatched for this \
focus: check a Working Memory folder for an existing filed return and \
report its presence/absence and date. Simple presence check against a \
folder listing, no judgment about content.

A7. Remember which of the surfaces you're viewing are stale or \
historical, versus current: this used to be something the operator had \
to hold in memory, but the system now discloses staleness directly on \
screen, so the manual burden this action used to describe no longer \
exists.

# Task

For each of A1 through A7, state its classification (automate / \
hold_steward / resolved) and a one-sentence reason. Pay particular \
attention to any action that involves choosing what counts as sufficient \
or adequate -- that is a judgment call, not an extraction, no matter how \
routine the surrounding work looks.
"""
