"""Tests for kernel_freshness.py -- one test per acceptance criterion named
in dispatch `CLAUDE_CODE_SYNAPSYS_MD_CONTROLLER_DISTRIBUTION_FRESHNESS_v0.1`'s
required test contract (Output E). Zero I/O, matching this package's own
`test_isolation_no_network_or_subprocess_imports` discipline elsewhere in
this repo.
"""

import ast
import pathlib

import pytest

from kernel_freshness import (
    FreshnessResult,
    KernelIdentity,
    NavigatorKernelStatus,
    RecipientConsumption,
    assess_all,
    assess_freshness,
    build_navigator_status,
    select_required_now_blockers,
    should_recheck,
    trigger_recheck_reason,
)

CURRENT = KernelIdentity(version_label="v0.3", sha256="AAA", manifest_sha256="MMM")


def _recipient(**overrides):
    base = dict(
        target_lane="claude_code",
        recipient_class="REQUIRED_NOW",
        native_consumption_mechanism="git checkout",
        consumption_verifiable=True,
        last_consumed_sha256="AAA",
        last_consumed_manifest_sha256="MMM",
        last_consumed_at_iso="2026-08-21T00:00:00",
    )
    base.update(overrides)
    return RecipientConsumption(**base)


# -- authoritative identity resolves --------------------------------------


def test_fresh_recipient_matches_current_identity():
    result = assess_freshness(CURRENT, _recipient())
    assert result.state == "FRESH"
    assert result.blocks_required_now_transaction is False


# -- stale/missing recipient detected --------------------------------------


def test_stale_kernel_sha_detected():
    r = _recipient(last_consumed_sha256="OLD")
    result = assess_freshness(CURRENT, r)
    assert result.state == "STALE"


def test_stale_manifest_sha_alone_is_detected():
    r = _recipient(last_consumed_manifest_sha256="OLD_MANIFEST")
    result = assess_freshness(CURRENT, r)
    assert result.state == "STALE"


def test_missing_recipient_never_consumed_anything():
    r = _recipient(last_consumed_sha256=None, last_consumed_manifest_sha256=None, last_consumed_at_iso=None)
    result = assess_freshness(CURRENT, r)
    assert result.state == "MISSING"


# -- only deficient recipient is targeted; REQUIRED_NOW stale blocks only its
#    own transaction; FUTURE/INFORM_ONLY debt never blocks unrelated work ---


def test_required_now_stale_blocks_only_itself():
    fresh_env = _recipient(target_lane="claude_code")
    stale_env = _recipient(target_lane="codex", last_consumed_sha256="OLD")
    results = assess_all(CURRENT, [fresh_env, stale_env])

    fresh_result = next(r for r in results if r.target_lane == "claude_code")
    stale_result = next(r for r in results if r.target_lane == "codex")

    assert fresh_result.blocks_required_now_transaction is False
    assert stale_result.blocks_required_now_transaction is True

    blockers = select_required_now_blockers(results)
    assert [b.target_lane for b in blockers] == ["codex"]


@pytest.mark.parametrize("recipient_class", ["FUTURE", "INFORM_ONLY", "NOT_RELEVANT"])
def test_non_required_now_stale_never_blocks(recipient_class):
    r = _recipient(recipient_class=recipient_class, last_consumed_sha256="OLD")
    result = assess_freshness(CURRENT, r)
    assert result.state == "STALE"
    assert result.blocks_required_now_transaction is False


def test_non_required_now_missing_never_blocks():
    r = _recipient(
        recipient_class="FUTURE",
        last_consumed_sha256=None,
        last_consumed_manifest_sha256=None,
        last_consumed_at_iso=None,
    )
    result = assess_freshness(CURRENT, r)
    assert result.state == "MISSING"
    assert result.blocks_required_now_transaction is False


# -- unverifiable recipients (e.g. Cowork Global Instructions manual box) --


def test_unverifiable_recipient_never_reported_fresh_or_blocking():
    r = _recipient(
        target_lane="chatgpt_hub_project_instructions",
        consumption_verifiable=False,
        native_consumption_mechanism="manual paste into ChatGPT Project Instructions box",
    )
    result = assess_freshness(CURRENT, r)
    assert result.state == "UNVERIFIABLE"
    assert result.blocks_required_now_transaction is False
    assert "no programmatic readback" in result.reason


# -- rejects an out-of-vocabulary recipient_class rather than silently
#    accepting it ----------------------------------------------------------


def test_invalid_recipient_class_rejected_at_construction():
    with pytest.raises(ValueError):
        _recipient(recipient_class="SOMETIMES")


# -- Navigator can surface concise status from the same state --------------


def test_navigator_status_full_coverage_no_action_needed():
    results = assess_all(CURRENT, [_recipient(target_lane="claude_code"), _recipient(target_lane="n8n")])
    status = build_navigator_status(CURRENT, results, now_iso="2026-08-21T06:00:00")

    assert status.required_now_total == 2
    assert status.required_now_fresh == 2
    assert status.coverage_percent == 100.0
    assert status.stale_or_missing_required_now == []
    assert status.unverifiable_required_now == []
    assert "No action" in status.next_action


def test_navigator_status_names_exact_stale_recipients_and_next_action():
    results = assess_all(
        CURRENT,
        [
            _recipient(target_lane="claude_code"),
            _recipient(target_lane="codex", last_consumed_sha256="OLD"),
            _recipient(target_lane="chatgpt_hub", last_consumed_sha256=None, last_consumed_manifest_sha256=None, last_consumed_at_iso=None),
        ],
    )
    status = build_navigator_status(CURRENT, results, now_iso="2026-08-21T06:00:00")

    assert status.required_now_total == 3
    assert status.required_now_fresh == 1
    assert status.coverage_percent == pytest.approx(100.0 / 3.0)
    assert status.stale_or_missing_required_now == ["chatgpt_hub", "codex"]
    assert "codex" in status.next_action and "chatgpt_hub" in status.next_action


def test_navigator_status_reports_unverifiable_separately_from_fixable_stale():
    results = assess_all(
        CURRENT,
        [
            _recipient(
                target_lane="chatgpt_hub_project_instructions",
                consumption_verifiable=False,
                native_consumption_mechanism="manual paste",
            ),
        ],
    )
    status = build_navigator_status(CURRENT, results, now_iso="2026-08-21T06:00:00")

    assert status.stale_or_missing_required_now == []
    assert status.unverifiable_required_now == ["chatgpt_hub_project_instructions"]
    assert "Manually confirm" in status.next_action


def test_navigator_status_with_zero_required_now_recipients_is_full_coverage():
    status = build_navigator_status(CURRENT, results=[], now_iso="2026-08-21T06:00:00")
    assert status.required_now_total == 0
    assert status.coverage_percent == 100.0
    assert "No action" in status.next_action


# -- no authority is inferred: FreshnessResult/NavigatorKernelStatus carry no
#    authority/approval field at all, by construction --------------------


def test_result_types_carry_no_authority_field():
    result_fields = set(FreshnessResult.__dataclass_fields__.keys())
    status_fields = set(NavigatorKernelStatus.__dataclass_fields__.keys())
    forbidden = {"authority", "approved", "authorised", "released_by"}
    assert not (result_fields & forbidden)
    assert not (status_fields & forbidden)


# -- recursive-loop guard: controller recursion does not create infinite
#    self-check loops -------------------------------------------------------


def test_should_recheck_true_when_never_checked_before():
    assert should_recheck(last_checked_iso=None, now_iso="2026-08-21T06:00:00", min_recheck_interval_seconds=900) is True


def test_should_recheck_false_within_debounce_window():
    assert (
        should_recheck(
            last_checked_iso="2026-08-21T06:00:00",
            now_iso="2026-08-21T06:05:00",
            min_recheck_interval_seconds=900,
        )
        is False
    )


def test_should_recheck_true_once_interval_elapses():
    assert (
        should_recheck(
            last_checked_iso="2026-08-21T06:00:00",
            now_iso="2026-08-21T06:15:00",
            min_recheck_interval_seconds=900,
        )
        is True
    )


def test_should_recheck_true_on_unparseable_timestamp_fails_toward_checking():
    assert should_recheck(last_checked_iso="not-a-timestamp", now_iso="2026-08-21T06:00:00", min_recheck_interval_seconds=900) is True


# -- trigger reasons (dispatch Q7) -----------------------------------------


def test_trigger_recheck_reason_none_when_nothing_changed():
    assert (
        trigger_recheck_reason(
            kernel_changed=False,
            manifest_changed=False,
            new_environment_registered=False,
            explicit_health_check=False,
            substantive_job_starting=False,
        )
        is None
    )


def test_trigger_recheck_reason_kernel_change_takes_priority():
    reason = trigger_recheck_reason(
        kernel_changed=True,
        manifest_changed=True,
        new_environment_registered=True,
        explicit_health_check=True,
        substantive_job_starting=True,
    )
    assert reason == "KERNEL_IDENTITY_CHANGED"


def test_trigger_recheck_reason_health_check_is_lowest_priority():
    reason = trigger_recheck_reason(
        kernel_changed=False,
        manifest_changed=False,
        new_environment_registered=False,
        explicit_health_check=True,
        substantive_job_starting=False,
    )
    assert reason == "EXPLICIT_HEALTH_CHECK"


# -- zero I/O isolation, mirroring scoping_validator.py's own self-test ----


def test_isolation_no_network_or_subprocess_imports():
    source = pathlib.Path(__file__).parent.parent.joinpath("kernel_freshness.py").read_text()
    tree = ast.parse(source)
    banned = {"socket", "requests", "subprocess", "urllib", "http"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & banned), f"kernel_freshness.py imports banned I/O module(s): {imported & banned}"
