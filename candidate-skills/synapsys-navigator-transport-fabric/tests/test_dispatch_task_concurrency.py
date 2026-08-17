"""Tests for the simulate_concurrent_claim_attempts extension to
dispatch_task_mapping.py -- demonstrates atomic_claim_sql_pattern's
compare-and-swap predicate grants exactly one claimant under simulated
concurrent claim attempts, for any ordering of attempts.
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dispatch_task_mapping import simulate_concurrent_claim_attempts


def test_single_claimant_always_granted():
    result = simulate_concurrent_claim_attempts(["worker-a"])
    assert result.winner == "worker-a"
    assert result.outcomes[0].granted is True
    assert result.final_status == "in_progress"
    assert result.final_operator_trace == "worker-a"


def test_two_concurrent_claimants_exactly_one_granted():
    result = simulate_concurrent_claim_attempts(["worker-a", "worker-b"])
    granted = [o for o in result.outcomes if o.granted]
    assert len(granted) == 1
    assert granted[0].claimant == "worker-a"
    assert result.winner == "worker-a"
    assert result.outcomes[1].granted is False


def test_many_concurrent_claimants_exactly_one_granted_regardless_of_order():
    """Exercises every ordering of a 5-claimant field: no matter which
    claimant is listed first, exactly one is ever granted and it is always
    the first in that particular ordering -- proving the CAS predicate
    admits no interleaving that grants two claimants."""
    claimants = ["a", "b", "c", "d", "e"]
    for ordering in itertools.permutations(claimants):
        result = simulate_concurrent_claim_attempts(list(ordering))
        granted = [o for o in result.outcomes if o.granted]
        assert len(granted) == 1
        assert granted[0].claimant == ordering[0]
        assert result.winner == ordering[0]
        assert result.final_status == "in_progress"


def test_empty_claimants_list_grants_nothing():
    result = simulate_concurrent_claim_attempts([])
    assert result.outcomes == ()
    assert result.winner is None
    assert result.final_status == "routed"
    assert result.final_operator_trace is None


def test_refused_claimants_never_mutate_final_state():
    result = simulate_concurrent_claim_attempts(["a", "b", "c"])
    assert result.final_operator_trace == "a"
    refused = [o.claimant for o in result.outcomes if not o.granted]
    assert refused == ["b", "c"]
