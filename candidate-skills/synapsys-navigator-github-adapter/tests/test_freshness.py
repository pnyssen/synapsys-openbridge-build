"""Tests for freshness.py -- behavioural coverage of all five states plus
the isolation check this repo's other candidate validators already use."""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from freshness import classify, FRESHNESS_STATES  # noqa: E402

FORBIDDEN_MODULES = {
    "socket", "subprocess", "urllib", "requests", "http", "os", "sys",
}


def test_isolation_no_forbidden_imports():
    """Mirrors validator.py/evidence_validator.py's own AST isolation check."""
    path = os.path.join(os.path.dirname(__file__), "..", "freshness.py")
    with open(path, "r") as f:
        tree = ast.parse(f.read(), filename=path)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    forbidden_found = found & FORBIDDEN_MODULES
    assert not forbidden_found, f"Forbidden imports found: {forbidden_found}"


def test_read_failed_is_extraction_pending():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:00:00",
        last_successful_read_iso="2026-08-11T23:00:00",
        max_age_seconds=300, read_succeeded=False,
    )
    assert r.state == "CONTENT_EXTRACTION_PENDING"


def test_no_prior_read_is_extraction_pending():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:00:00",
        last_successful_read_iso=None,
        max_age_seconds=300, read_succeeded=True,
    )
    assert r.state == "CONTENT_EXTRACTION_PENDING"


def test_conflict_wins_even_if_read_succeeded_and_fresh():
    r = classify(
        source="wm", checked_at_iso="2026-08-12T00:00:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=300, read_succeeded=True,
        conflict_detected=True, conflict_detail="Odoo says X, WM says Y",
    )
    assert r.state == "CONFLICTED"
    assert "Odoo says X" in r.reason


def test_within_window_is_current_matched():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:05:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "CURRENT_MATCHED"
    assert r.staleness_seconds == 300


def test_exactly_at_window_boundary_is_current_matched():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:10:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "CURRENT_MATCHED"


def test_beyond_window_within_3x_is_non_material_variance():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:20:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "CURRENT_WITH_NON_MATERIAL_VARIANCE"


def test_beyond_3x_window_is_stale_projection():
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T01:00:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "STALE_PROJECTION"


def test_negative_age_is_conflicted_not_clamped():
    """last_successful_read after checked_at is a clock/ordering problem,
    not zero staleness -- must not be silently normalised away."""
    r = classify(
        source="odoo", checked_at_iso="2026-08-12T00:00:00",
        last_successful_read_iso="2026-08-12T00:05:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "CONFLICTED"


def test_unparseable_timestamp_is_extraction_pending_not_guessed():
    r = classify(
        source="odoo", checked_at_iso="not-a-timestamp",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    assert r.state == "CONTENT_EXTRACTION_PENDING"


def test_only_five_states_are_ever_reachable():
    """Regression guard: every branch in classify() must return a state
    from the ruled vocabulary, never a sixth invented one."""
    cases = [
        dict(source="s", checked_at_iso="2026-08-12T00:00:00", last_successful_read_iso=None, max_age_seconds=1, read_succeeded=False),
        dict(source="s", checked_at_iso="2026-08-12T00:00:00", last_successful_read_iso=None, max_age_seconds=1, read_succeeded=True),
        dict(source="s", checked_at_iso="2026-08-12T00:00:00", last_successful_read_iso="2026-08-12T00:00:00", max_age_seconds=1, read_succeeded=True, conflict_detected=True),
        dict(source="s", checked_at_iso="2026-08-12T00:00:05", last_successful_read_iso="2026-08-12T00:00:00", max_age_seconds=10, read_succeeded=True),
        dict(source="s", checked_at_iso="2026-08-12T00:00:20", last_successful_read_iso="2026-08-12T00:00:00", max_age_seconds=10, read_succeeded=True),
        dict(source="s", checked_at_iso="2026-08-12T01:00:00", last_successful_read_iso="2026-08-12T00:00:00", max_age_seconds=10, read_succeeded=True),
        dict(source="s", checked_at_iso="2026-08-12T00:00:00", last_successful_read_iso="2026-08-12T00:00:05", max_age_seconds=10, read_succeeded=True),
        dict(source="s", checked_at_iso="bad", last_successful_read_iso="2026-08-12T00:00:00", max_age_seconds=10, read_succeeded=True),
    ]
    for kwargs in cases:
        r = classify(**kwargs)
        assert r.state in FRESHNESS_STATES, f"Invented state: {r.state}"


def test_no_mutation_of_inputs():
    """classify() must be a pure function -- same inputs, same output,
    no hidden state accumulated across calls."""
    kwargs = dict(
        source="odoo", checked_at_iso="2026-08-12T00:05:00",
        last_successful_read_iso="2026-08-12T00:00:00",
        max_age_seconds=600, read_succeeded=True,
    )
    first = classify(**kwargs)
    second = classify(**kwargs)
    assert first == second
