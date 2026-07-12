"""
synapsys-agentic-safety (CANDIDATE)

In-process iteration/budget/timeout guardrail. No network, no filesystem
writes, no subprocess, no credential handling.

Independently written for SynapSys. Not derived from, and does not import,
copy, or execute, any code from AgentBudget/agentbudget or any other
external repository — only the *pattern* (hard caps via a wrapper layer,
specific catchable exceptions per violated boundary) is structurally
inspired by it.
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass, field


class GuardViolation(Exception):
    """Base class for all guard violations. Never caught internally — always
    propagates to the caller."""


class IterationLimitExceeded(GuardViolation):
    pass


class BudgetExhausted(GuardViolation):
    pass


class TimeoutExceeded(GuardViolation):
    pass


class LoopDetected(GuardViolation):
    pass


@dataclass
class Guard:
    max_iterations: int | None = None
    max_cost: float | None = None
    max_seconds: float | None = None
    loop_repeat_threshold: int = 3

    _start_time: float | None = field(default=None, init=False, repr=False)
    _iterations: int = field(default=0, init=False)
    _spent: float = field(default=0.0, init=False)
    _call_history: list[str] = field(default_factory=list, init=False)

    def start(self) -> None:
        """Idempotent — calling start() twice does not reset an in-progress guard."""
        if self._start_time is None:
            self._start_time = time.monotonic()

    def _elapsed(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time

    def check_and_record(self, call_signature: str, cost: float = 0.0) -> dict:
        """Call before executing a guarded action. Raises the specific
        GuardViolation subclass the instant any cap is crossed; never
        silently continues past a violated boundary."""
        self.start()

        elapsed = self._elapsed()
        if self.max_seconds is not None and elapsed > self.max_seconds:
            raise TimeoutExceeded(
                f"elapsed {elapsed:.2f}s exceeds max_seconds={self.max_seconds}"
            )

        self._iterations += 1
        if self.max_iterations is not None and self._iterations > self.max_iterations:
            raise IterationLimitExceeded(
                f"iteration {self._iterations} exceeds max_iterations={self.max_iterations}"
            )

        self._spent += cost
        if self.max_cost is not None and self._spent > self.max_cost:
            raise BudgetExhausted(
                f"spent {self._spent:.4f} exceeds max_cost={self.max_cost}"
            )

        self._call_history.append(call_signature)
        window = self._call_history[-self.loop_repeat_threshold:]
        if len(window) == self.loop_repeat_threshold and len(set(window)) == 1:
            raise LoopDetected(
                f"last {self.loop_repeat_threshold} calls were all "
                f"identical: {call_signature!r}"
            )

        return self.summary()

    def summary(self) -> dict:
        """Returns a plain dict. Never writes to a file — persistence, if
        wanted, is the caller's decision, not this module's."""
        return {
            "iterations": self._iterations,
            "spent": self._spent,
            "elapsed_seconds": self._elapsed(),
            "call_count": len(self._call_history),
        }

    def wrap(self, fn):
        """Decorator form. Guarded function must accept an optional `cost`
        keyword; it is popped before the wrapped function is called."""
        @functools.wraps(fn)
        def wrapper(*args, cost: float = 0.0, **kwargs):
            signature = f"{fn.__name__}:{args!r}:{kwargs!r}"
            self.check_and_record(signature, cost=cost)
            return fn(*args, **kwargs)
        return wrapper
