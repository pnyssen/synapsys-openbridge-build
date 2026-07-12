---
name: synapsys-agentic-safety
status: CANDIDATE — not adopted, not installed, not activated
work_object: D001-AGENTBUDGET-RULING (direct-chat Steward ruling, hash e96cae5d20816c80f3e9090c5aa990fd467b98f73c2bb6a72fd9b77f34299b66)
version: 0.1
---

# synapsys-agentic-safety (CANDIDATE)

In-process iteration/budget/timeout guardrail for agent tool-call sequences.
Pattern derived from the *structure* of `AgentBudget` (hard caps enforced via
a wrapper layer, `BudgetExhausted`/`LoopDetected`-style exceptions) —
independently reimplemented, no code copied from that source.

## What it does

Wraps a sequence of tool/function calls with:
- a hard iteration cap
- a dollar-denominated cost cap (caller supplies per-call cost)
- a wall-clock timeout for the whole guarded session
- basic loop detection (N identical consecutive call signatures)

Raises a specific, catchable exception the moment any cap is exceeded:
`IterationLimitExceeded`, `BudgetExhausted`, `TimeoutExceeded`, `LoopDetected`.

## What it deliberately does not do

- **No network calls of any kind** — not even the optional webhook AgentBudget
  itself offers. Zero network surface, by design, not by configuration.
- **No filesystem writes.** `summary()` returns a plain dict; the caller
  decides whether to log, print, or persist it. This candidate never opens a
  file.
- **No subprocess or git invocation.**
- **No credential handling of any kind** — it has no concept of an API key,
  token, or session; it only counts calls, dollars, and elapsed time that the
  caller reports to it.
- **No auto-remediation.** It raises; it never catches its own exception to
  retry, patch, or continue silently.

## Usage

```python
from guardrail import Guard, BudgetExhausted, IterationLimitExceeded, TimeoutExceeded, LoopDetected

g = Guard(max_cost=5.00, max_iterations=50, max_seconds=300)
g.start()
for step in plan:
    g.check_and_record(call_signature=step.name, cost=step.estimated_cost)
    step.run()
```

## Authority state

CANDIDATE. Not filed as an adopted SynapSys skill. Requires D009 assurance
challenge and D002 method review before any adoption consideration, per the
direct Steward ruling that authorised this build (hash cited above) — no
D007 required for this item specifically, since it involves no platform or
permission change.
