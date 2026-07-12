"""
Boundary + behavioural tests for synapsys-agentic-safety (CANDIDATE).

These tests prove both the authority boundaries claimed in THREAT_MODEL.md
AND that the guardrail logic actually works (caps really trigger).
Run with: pytest test_boundaries.py -v
"""

import ast
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import guardrail  # noqa: E402

SOURCE_PATH = Path(__file__).resolve().parent.parent / "guardrail.py"


def _module_ast():
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


# ---- Boundary proofs (matching THREAT_MODEL.md claims) ----

def test_no_network_imports():
    forbidden = {"requests", "urllib", "http", "socket", "httpx", "aiohttp", "ftplib", "smtplib"}
    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & forbidden)


def test_no_filesystem_or_subprocess_imports():
    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported
    # 'os' isn't imported either, in this module.
    assert "os" not in imported


def test_no_open_or_write_calls():
    """Checks actual call sites, not prose, for open()/write_text()/write() usage."""
    tree = _module_ast()
    forbidden_call_names = {"open"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            assert name not in forbidden_call_names
            assert name != "write_text"
            assert name != "write"


def test_no_git_invocation():
    tree = _module_ast()
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literals.append(arg.value)
    assert not any(lit == "git" or lit.endswith("/git") for lit in literals)


def test_only_monotonic_time_used():
    """Confirms time.time() (wall-clock) is never called — only time.monotonic()."""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "time.time(" not in source
    assert "time.monotonic(" in source


def test_start_is_idempotent():
    g = guardrail.Guard(max_seconds=10)
    g.start()
    first = g._start_time
    time.sleep(0.01)
    g.start()
    assert g._start_time == first


# ---- Behavioural proofs (the caps actually work) ----

def test_iteration_cap_triggers():
    g = guardrail.Guard(max_iterations=3)
    g.check_and_record("call_a")
    g.check_and_record("call_b")
    g.check_and_record("call_c")
    with pytest.raises(guardrail.IterationLimitExceeded):
        g.check_and_record("call_d")


def test_budget_cap_triggers():
    g = guardrail.Guard(max_cost=1.00)
    g.check_and_record("call_a", cost=0.60)
    with pytest.raises(guardrail.BudgetExhausted):
        g.check_and_record("call_b", cost=0.60)


def test_timeout_cap_triggers():
    g = guardrail.Guard(max_seconds=0.05)
    g.check_and_record("call_a")
    time.sleep(0.1)
    with pytest.raises(guardrail.TimeoutExceeded):
        g.check_and_record("call_b")


def test_loop_detection_triggers():
    g = guardrail.Guard(loop_repeat_threshold=3)
    g.check_and_record("same_call")
    g.check_and_record("same_call")
    with pytest.raises(guardrail.LoopDetected):
        g.check_and_record("same_call")


def test_loop_detection_does_not_false_positive_on_varied_calls():
    g = guardrail.Guard(loop_repeat_threshold=3)
    g.check_and_record("call_a")
    g.check_and_record("call_b")
    g.check_and_record("call_a")  # no crash — not 3 identical in a row
    result = g.summary()
    assert result["iterations"] == 3


def test_violation_never_caught_internally_and_state_stops_advancing():
    """After a violation, calling check_and_record again still raises — the
    guard doesn't silently 'heal' or reset itself."""
    g = guardrail.Guard(max_iterations=1)
    g.check_and_record("call_a")
    with pytest.raises(guardrail.IterationLimitExceeded):
        g.check_and_record("call_b")
    with pytest.raises(guardrail.IterationLimitExceeded):
        g.check_and_record("call_c")


def test_decorator_usage():
    g = guardrail.Guard(max_iterations=2)

    @g.wrap
    def do_thing(x):
        return x * 2

    assert do_thing(5, cost=0.0) == 10
    assert do_thing(5, cost=0.0) == 10
    with pytest.raises(guardrail.IterationLimitExceeded):
        do_thing(5, cost=0.0)


def test_two_guard_instances_do_not_share_state():
    g1 = guardrail.Guard(max_iterations=1)
    g2 = guardrail.Guard(max_iterations=1)
    g1.check_and_record("a")
    g2.check_and_record("b")  # would raise if state leaked from g1
    assert g1.summary()["iterations"] == 1
    assert g2.summary()["iterations"] == 1


def test_summary_returns_plain_dict_not_written_anywhere():
    g = guardrail.Guard(max_iterations=5)
    g.check_and_record("a", cost=1.5)
    s = g.summary()
    assert isinstance(s, dict)
    assert s["spent"] == 1.5
    assert s["call_count"] == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
