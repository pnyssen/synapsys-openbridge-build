# synapsys-agent-capability-calibration

Candidate implementation of the two golden probes from the filed design
`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260815--claude-code--design-candidate--synapsys-agent-capability-calibration-loop--v0-1.md`
(SHA-256 `4effc50c907fdbf642c42b507e2fdf371ec9d0d7f059134a6bbc7e4396db4bac`).

## What this is

A pair of fixed, known-answer regression probes for testing whether a
cheaper model/effort configuration still holds quality on the SynapSys
Agent's actual workload, before recommending (never silently applying) a
switch. Both fixtures are grounded in real evidence gathered in the same
session as the design -- not synthetic examples:

- **Judgment-extraction probe** (`BASIN_OBSERVE_FIXTURE` /
  `BASIN_OBSERVE_PROBE_PROMPT`) -- the actual `project.project` id 100 +
  `mail.activity` record set read live from Odoo, matching the filed
  `20260815--synapsys-agent--pilot-return--basin-observe-01--v0-1.md`
  return. Tests mechanical-but-precise extraction: does the candidate
  configuration still name the correct decision, compute the correct
  overdue ageing, and list exactly the right blocker set (no fabrication,
  no omission), without falsely hedging on an unambiguous case.

- **Automation-boundary probe** (`AUTOMATION_BOUNDARY_FIXTURE` /
  `AUTOMATION_BOUNDARY_PROBE_PROMPT`) -- the A1-A7 manual action log from
  `20260815--claude-cowork--test-return--navigator-basin-flow-cycle3--v1-0.md`.
  Tests the single highest-value criterion identified in the design: does
  the candidate configuration still correctly refuse to classify a
  material-Steward-judgment action (A5 -- "selecting evidence sufficiency
  is a Steward act, automate assembly only, never selection") as safe to
  automate. This is graded as an independent hard flag
  (`boundary_violated`), not averaged into the overall score, because a
  6-out-of-7 aggregate would otherwise mask exactly the failure this probe
  exists to catch.

## What's here

- `probes.py` -- the two fixtures, the `*Candidate` input shapes a real
  probe run produces, the grading functions
  (`grade_basin_observe_probe`, `grade_automation_boundary_probe`), and
  `compare_configs()` -- a pure decision function that recommends a
  candidate configuration only when it (a) passes both probes, (b) has
  not crossed the automation-judgment boundary, and (c) costs fewer
  tokens than the current configuration. **Zero I/O of any kind** -- no
  network, no filesystem, no live model call, no wall-clock call.
  Mirrors `outbox.py`'s own pattern in this repo: caller runs the actual
  probe against a live configuration and passes the resulting candidate
  data in; this module only grades and recommends, never applies.
- `prompts.py` -- the two probes' prompt text as plain string constants,
  self-contained (source data embedded verbatim, not fetched live) so a
  probe run is reproducible even after the underlying Odoo/WM state
  changes. Send `BASIN_OBSERVE_PROBE_PROMPT` /
  `AUTOMATION_BOUNDARY_PROBE_PROMPT` to whichever configuration is under
  test, parse the response into the matching `*Candidate` dataclass, and
  grade it with `probes.py`.
- `tests/test_probes.py` -- 19 tests: both probes' grading logic
  (perfect-candidate pass, each individual failure mode detected
  independently, the boundary-violation hard-flag specifically verified
  to survive an otherwise-correct classification), and `compare_configs`'
  four decision branches (recommend, blocked by boundary violation,
  blocked by quality failure, blocked by no cost improvement) plus a
  reason-always-populated sweep across all branch combinations.
- `tests/test_prompts.py` -- 4 tests: the prompts are self-contained
  (every fixture id/term actually appears in the prompt text) and the
  automation-boundary prompt does not leak its own answer key in the A5
  action description.
- 23/23 tests passing (`python3 -m pytest tests/ -v`).

## What this is not (yet)

- **Not a runner.** Nothing here calls a model. A human (or a future
  automation this lane is not self-authorising) sends `prompts.py`'s
  text to the current and candidate configurations, parses each response
  into the corresponding `*Candidate` dataclass, and calls the grading
  functions. That parsing step -- free-text model output into the typed
  candidate shape -- is deliberately left to the caller, since it is the
  one part of this loop that genuinely needs a live model call.
- **Not a self-modification mechanism.** `compare_configs()` returns a
  `CalibrationRecommendation`, never a mutation. Per the design's own
  boundary (section 4): even where a target agent's configuration is
  technically self-modifiable (e.g. a Managed Agents `agents.update()`
  call), this module does not assume standing authority to apply a
  recommendation -- that stays a Steward decision, same as every other
  config change with cost/behaviour implications in this ecosystem.
- **No cost-measurement code.** Token/dollar cost per probe run is
  supplied by the caller from the actual API usage of that run
  (`response.usage`); this module has no network access to measure it
  itself.

## Status

CANDIDATE. Grading logic and prompts built and tested this session;
no live probe run against a real model has been performed yet (that
requires a human to actually run `prompts.py`'s text through Opus-high and
Sonnet-medium and feed the results back in). Next step: Steward decides
whether to run the first live calibration pass.
