"""Tests for prompts.py -- sanity checks that the prompt text stays in
sync with the fixtures it's meant to produce candidates for."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prompts import AUTOMATION_BOUNDARY_PROBE_PROMPT, BASIN_OBSERVE_PROBE_PROMPT  # noqa: E402
from probes import AUTOMATION_BOUNDARY_FIXTURE, BASIN_OBSERVE_FIXTURE  # noqa: E402


def test_basin_observe_prompt_is_nonempty_and_self_contained():
    assert len(BASIN_OBSERVE_PROBE_PROMPT) > 200
    # every id in the fixture's expected blocker set must appear in the
    # prompt's source records, or the probe isn't actually self-contained
    for blocker_id in BASIN_OBSERVE_FIXTURE.expected_blocker_ids:
        numeric_id = blocker_id.split("#")[1]
        assert f"id {numeric_id}" in BASIN_OBSERVE_PROBE_PROMPT
    decision_numeric_id = BASIN_OBSERVE_FIXTURE.decision_source_id.split("#")[1]
    assert f"id {decision_numeric_id}" in BASIN_OBSERVE_PROBE_PROMPT


def test_basin_observe_prompt_contains_required_decision_terms():
    prompt_lower = BASIN_OBSERVE_PROBE_PROMPT.lower()
    for term in BASIN_OBSERVE_FIXTURE.decision_text_required_terms:
        assert term in prompt_lower


def test_automation_boundary_prompt_covers_every_fixture_action():
    for action_id in AUTOMATION_BOUNDARY_FIXTURE.expected_classification:
        assert action_id in AUTOMATION_BOUNDARY_PROBE_PROMPT


def test_automation_boundary_prompt_does_not_leak_the_answer_key():
    """The prompt must describe A5 in a way that requires the candidate to
    reach the hold_steward conclusion itself -- it must not simply state
    the expected classification in the task text, or the probe measures
    nothing."""
    prompt_lower = AUTOMATION_BOUNDARY_PROBE_PROMPT.lower()
    assert "hold_steward" not in prompt_lower.split("# task")[0].split("a5.")[1].split("a6.")[0]
