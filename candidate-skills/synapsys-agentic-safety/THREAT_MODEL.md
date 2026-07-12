# Threat Model — synapsys-agentic-safety (CANDIDATE)

## Permission declaration

| Capability | Used? | Notes |
|---|---|---|
| Filesystem read | No | Never opens any file |
| Filesystem write | **No** | `summary()` returns a dict; nothing is ever written to disk by this module |
| Network | **No** | Zero network calls — not even AgentBudget's own optional webhook feature was carried over. Lowest network surface of any candidate built this session |
| Subprocess / shell exec | **No** | No `subprocess`, `os.system`, `os.popen` |
| Git operations | **No** | No `git` invocation of any kind |
| Credentials / secrets use | No | The module has no concept of a credential — it only receives call names, costs, and timestamps from the caller |
| Time source | Yes | `time.monotonic()` only — never reads wall-clock/calendar time, so it can't be used to infer anything about the host system's clock/locale |

## Compared to AgentBudget (source pattern)

AgentBudget offers an optional webhook for cost-event notification and patches OpenAI/Anthropic SDKs process-wide. This candidate:
- drops the webhook option entirely — no network code path exists to misconfigure, rather than an off-by-default flag;
- does not patch any SDK or global state — it's an explicit `Guard` object the caller constructs and calls directly, so there's no process-wide monkeypatching to reason about;
- does not ship built-in per-model pricing tables (AgentBudget's "40+ models" pricing data) — cost is entirely caller-supplied per call, which is less convenient but removes an entire category of "is the pricing table stale/wrong" risk from this candidate.

## Failure behaviour

- Every cap violation raises immediately and specifically — there is no code path that catches a `GuardViolation` subclass internally and continues. A caller that doesn't handle the exception will see their guarded loop stop hard, which is the intended fail-closed behaviour.
- `start()` is idempotent — calling it multiple times does not reset an in-progress timer, preventing a caller from accidentally resetting their own timeout budget by calling `start()` again mid-run.

## Known gaps (not resolved by this candidate)

- Loop detection is exact-string-match on a caller-supplied signature over a fixed trailing window — it will not catch semantically-identical-but-differently-formatted calls, or loops longer than the window. A more sophisticated detector (e.g. AgentBudget's or reivo-guard's EWMA-anomaly approach, per the earlier research pass) would be a real capability gap versus more mature tools in this space — not resolved here, by design, to keep this candidate small and its boundaries easy to verify.
- Cost accounting trusts the caller entirely — this module cannot independently verify that a reported `cost=` value is accurate. It is a guardrail against a cooperating caller's own runaway loop, not a defense against an adversarial or buggy cost-reporting caller.
- No persistence between process restarts — a `Guard` instance's state is lost if the process crashes and restarts, unlike tools that checkpoint spend to disk or a remote store. This is a direct consequence of the "no filesystem write" boundary above and is an intentional trade, not an oversight.

## STOP conditions

This tool must not be modified, in any future iteration, to add: network calls (including the webhook AgentBudget itself offers), filesystem persistence, subprocess/shell execution, or automatic retry/remediation on a raised violation, without a separate authority decision and a corresponding new threat-model version.
