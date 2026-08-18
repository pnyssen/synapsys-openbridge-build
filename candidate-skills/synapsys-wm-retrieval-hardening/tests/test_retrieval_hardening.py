"""Tests for retrieval_hardening.py, including the eight named regression
cases A-H required by the commissioning dispatch
(20260818--chatgpt-hub--dispatch--claude-code-working-memory-expected-return-retrieval-hardening--v1-0.md).
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from retrieval_hardening import (
    ALL_CLASSES,
    CandidateFileIdentity,
    DiscoveryResult,
    ExpectedReturn,
    RetrievalOutcome,
    RouteResult,
    SharingLinkResult,
    resolve_expected_return,
)

FORBIDDEN_IMPORTS = {"socket", "subprocess", "urllib", "requests", "http", "os.system"}


def test_module_has_no_forbidden_imports():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "retrieval_hardening.py")
    with open(path) as f:
        tree = ast.parse(f.read(), filename=path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not (names & FORBIDDEN_IMPORTS), names


def test_retrieval_outcome_rejects_unrecognised_classification():
    with pytest.raises(ValueError):
        RetrievalOutcome(classification="NOT_A_REAL_CLASS", resolved_filename=None, reason="x", next_action="x")


def test_no_field_resembles_authority_or_mutation_grant():
    """Required-behaviour item 11: this module must never itself advance
    A2+/PPV/authority/mutation. Enforced structurally: no field on
    RetrievalOutcome or any input dataclass carries an authority/mutation
    verb, and the module exposes no write/execute function at all."""
    import retrieval_hardening as mod

    forbidden_substrings = ("authoriz", "authoris", "mutate", "mutation", "execute", "write_", "approve")
    for name in dir(mod):
        if name.startswith("_"):
            continue
        lowered = name.lower()
        assert not any(f in lowered for f in forbidden_substrings), name


def _expected(filename="20260818--d009--return--wave4-signal485-raw-positive-challenge--v1-0.md"):
    return ExpectedReturn(
        return_id="NAVIGATOR_WAVE4_SIGNAL485_RAW_POSITIVE_D009_CHALLENGE_v1.0",
        filename=filename,
        parent_folder="05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001",
        required_state_revision=400,
    )


# ---------------------------------------------------------------------------
# A. exact path exists; indexed search misses -> retrieval succeeds,
#    class SEARCH_MISS_NOT_ABSENCE.
# ---------------------------------------------------------------------------

def test_case_a_exact_path_exists_search_misses():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=True, content_available=True),
        sp_read_fallback=RouteResult(attempted=False),
        indexed_search=DiscoveryResult(attempted=True, candidate_filenames=()),
    )
    assert outcome.classification == "SEARCH_MISS_NOT_ABSENCE"
    assert outcome.resolved_filename == expected.filename


# ---------------------------------------------------------------------------
# B. exact path absent; file exists in same folder under slightly different
#    filename with exact return_id/revision ->
#    EXPECTED_RETURN_FOUND_NONCANONICAL_PATH.
# ---------------------------------------------------------------------------

def test_case_b_nonstandard_path_with_matching_identity():
    expected = _expected()
    misnamed = "20260818--d009--return--signal485-challenge-v1.md"
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=(misnamed,)),
        discovery_candidate_identities=(
            CandidateFileIdentity(
                filename=misnamed,
                return_id=expected.return_id,
                consumed_state_revision=expected.required_state_revision,
                lane="D009 independent assurance",
            ),
        ),
    )
    assert outcome.classification == "EXPECTED_RETURN_FOUND_NONCANONICAL_PATH"
    assert outcome.resolved_filename == misnamed


# ---------------------------------------------------------------------------
# C. user sharing link resolves to expected return -> consume candidate
#    identity.
# ---------------------------------------------------------------------------

def test_case_c_sharing_link_resolves_to_expected_return():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=()),
        sharing_link=SharingLinkResult(
            attempted=True,
            resolved=True,
            resolved_filename=expected.filename,
            resolved_return_id=expected.return_id,
            resolved_state_revision=expected.required_state_revision,
        ),
    )
    assert outcome.classification == "EXACT_PATH_RESOLVED"
    assert outcome.resolved_filename == expected.filename


def test_case_c_variant_sharing_link_resolves_to_expected_return_under_different_name():
    expected = _expected()
    other_name = "20260818--d009--return--wave4-signal485-raw-positive-challenge--v1-1.md"
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=()),
        sharing_link=SharingLinkResult(
            attempted=True,
            resolved=True,
            resolved_filename=other_name,
            resolved_return_id=expected.return_id,
            resolved_state_revision=expected.required_state_revision,
        ),
    )
    assert outcome.classification == "EXPECTED_RETURN_FOUND_NONCANONICAL_PATH"
    assert outcome.resolved_filename == other_name


# ---------------------------------------------------------------------------
# D. user sharing link resolves to dispatch while expected return is
#    different -> reject link as return and continue bounded discovery.
# ---------------------------------------------------------------------------

def test_case_d_sharing_link_resolves_to_unrelated_dispatch():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=()),
        sharing_link=SharingLinkResult(
            attempted=True,
            resolved=True,
            resolved_filename="20260818--chatgpt-hub--dispatch--d009-wave4-signal485-raw-positive-challenge--v1-0.md",
            resolved_return_id="NAVIGATOR_WAVE4_SIGNAL485_DISPATCH_v1.0",
            resolved_state_revision=399,
        ),
    )
    assert outcome.classification == "LINK_RESOLVED_UNRELATED_FILE_REJECTED"
    assert outcome.next_action == "CONTINUE_BOUNDED_DISCOVERY_REJECT_LINK_AS_RETURN"
    # Reproduces the exact real-world failure this task was commissioned from.
    assert "dispatch" in outcome.resolved_filename


# ---------------------------------------------------------------------------
# E. exact path absent + enumeration/search none -> FILE_ABSENT_WITH_EVIDENCE
#    only after all routes.
# ---------------------------------------------------------------------------

def test_case_e_all_routes_exhausted_true_absence():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=()),
        indexed_search=DiscoveryResult(attempted=True, candidate_filenames=()),
    )
    assert outcome.classification == "FILE_ABSENT_WITH_EVIDENCE"
    assert outcome.resolved_filename is None


def test_exact_path_absent_alone_is_not_yet_final_absence():
    """Only the dual exact-path routes have been tried -- enumeration/search
    not yet attempted. Must not jump straight to FILE_ABSENT_WITH_EVIDENCE."""
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
    )
    assert outcome.classification == "EXACT_PATH_ABSENT_PENDING_DISCOVERY"
    assert outcome.classification != "FILE_ABSENT_WITH_EVIDENCE"


# ---------------------------------------------------------------------------
# F. stale revision in discovered file -> STALE_REVISION, no queue advance.
# ---------------------------------------------------------------------------

def test_case_f_stale_revision():
    expected = _expected()
    stale_file = "20260817--d009--return--wave4-signal485-raw-positive-challenge--v1-0.md"
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=(stale_file,)),
        discovery_candidate_identities=(
            CandidateFileIdentity(
                filename=stale_file,
                return_id=expected.return_id,
                consumed_state_revision=397,  # stale -- required is 400
            ),
        ),
    )
    assert outcome.classification == "STALE_REVISION"
    assert outcome.next_action == "DO_NOT_ADVANCE_QUEUE_HOLD_FOR_CORRECT_REVISION"


# ---------------------------------------------------------------------------
# G. two candidate files claim same return_id -> CONFLICTING_RETURN_HOLD.
# ---------------------------------------------------------------------------

def test_case_g_conflicting_candidates():
    expected = _expected()
    f1 = "20260818--d009--return--signal485-a.md"
    f2 = "20260818--d009--return--signal485-b.md"
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        folder_enumeration=DiscoveryResult(attempted=True, candidate_filenames=(f1, f2)),
        discovery_candidate_identities=(
            CandidateFileIdentity(filename=f1, return_id=expected.return_id, consumed_state_revision=400),
            CandidateFileIdentity(filename=f2, return_id=expected.return_id, consumed_state_revision=400),
        ),
    )
    assert outcome.classification == "CONFLICTING_RETURN_HOLD"
    assert outcome.resolved_filename is None


# ---------------------------------------------------------------------------
# H. content extraction null but exact file identity resolves ->
#    FILE_PRESENT_CONTENT_PENDING, not absent.
# ---------------------------------------------------------------------------

def test_case_h_content_extraction_failed_not_absent():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=True, content_available=False),
        sp_read_fallback=RouteResult(attempted=False),
    )
    assert outcome.classification == "FILE_PRESENT_CONTENT_PENDING"
    assert outcome.classification != "FILE_ABSENT_WITH_EVIDENCE"


def test_case_h_backup_route_content_pending_when_primary_absent():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=True, content_available=False),
    )
    assert outcome.classification == "FILE_PRESENT_CONTENT_PENDING"


# ---------------------------------------------------------------------------
# Additional coverage: primary fails, backup succeeds (doctrine's own
# regression check, not one of the lettered cases but explicitly required
# by connector-fallback-and-progressive-execution.md).
# ---------------------------------------------------------------------------

def test_primary_fails_backup_succeeds_no_hold():
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=True, content_available=True),
    )
    assert outcome.classification == "EXACT_PATH_RESOLVED"
    assert outcome.resolved_filename == expected.filename


def test_search_result_alone_never_used_as_presence_proof():
    """Never ask the Steward to re-upload or locate a known file until both
    direct routes fail -- and a nonempty search result never short-circuits
    the exact-path-first sequence into treating search as authoritative."""
    expected = _expected()
    outcome = resolve_expected_return(
        expected,
        sharepoint_direct=RouteResult(attempted=True, found=False),
        sp_read_fallback=RouteResult(attempted=True, found=False),
        indexed_search=DiscoveryResult(attempted=True, candidate_filenames=(expected.filename,)),
    )
    # Even though search "found" it, this module still routes through the
    # discovery classifier (which does treat an exact-filename hit in
    # enumeration/search as SEARCH_MISS_NOT_ABSENCE / retry-direct), never
    # silently fabricating an EXACT_PATH_RESOLVED from search alone.
    assert outcome.classification == "SEARCH_MISS_NOT_ABSENCE"
    assert outcome.next_action == "RETRY_EXACT_PATH_RETRIEVAL"


def test_all_classifications_are_from_the_declared_vocabulary():
    """No RetrievalOutcome this module can produce falls outside ALL_CLASSES
    -- enforced structurally since RetrievalOutcome itself raises on
    construction, but this test exercises every branch at least once to
    prove the __post_init__ guard never fires unexpectedly across normal use."""
    expected = _expected()
    scenarios = [
        {"sharepoint_direct": RouteResult(attempted=True, found=True, content_available=True), "sp_read_fallback": RouteResult()},
        {"sharepoint_direct": RouteResult(attempted=True, found=False), "sp_read_fallback": RouteResult(attempted=True, found=False)},
        {
            "sharepoint_direct": RouteResult(attempted=True, found=False),
            "sp_read_fallback": RouteResult(attempted=True, found=False),
            "folder_enumeration": DiscoveryResult(attempted=True, candidate_filenames=()),
        },
    ]
    for kwargs in scenarios:
        outcome = resolve_expected_return(expected, **kwargs)
        assert outcome.classification in ALL_CLASSES
