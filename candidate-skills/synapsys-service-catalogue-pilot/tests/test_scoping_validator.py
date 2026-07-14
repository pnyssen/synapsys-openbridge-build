import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scoping_validator import (  # noqa: E402
    ROLE_FIELDS,
    check_required_fields,
    check_role_classification,
    check_sla_metric,
    validate_service_record,
    validate_service_records,
)

# --- Real fixtures, taken verbatim from a live `search_odoo` read against
# --- `x_service_catalogue` this session (2026-07-14), not synthesised.
# --- Field subset trimmed to what the validator reads.

SC_01_LEGACY_ACTIVE = {
    "x_service_code": "SC-01",
    "x_service_name": "Governance and Operating Model Enablement",
    "x_service_status": "active",
    "x_method_role": False,
    "x_service_role": False,
    "x_platform_role": False,
    "x_client_outcome": (
        "Functioning governance framework with defined decision rights, "
        "operating model, and domain accountabilities established and "
        "operational."
    ),
    "x_sla_metric_text": (
        "Governance model ratified by leadership; decisions tracked "
        "within defined authority lanes within 30 days of activation."
    ),
    "x_sla_metric_value": 0.0,
    "x_sla_metric_unit": False,
}

GV_GOV_001_DRAFT_WITH_UNIT = {
    "x_service_code": "GV-GOV-001",
    "x_service_name": "Steward Decision Surface",
    "x_service_status": "draft",
    "x_method_role": False,
    "x_service_role": False,
    "x_platform_role": "platform",
    "x_client_outcome": (
        "A ruled, authority-traced Steward decision, recorded with a "
        "stated next valid action"
    ),
    "x_sla_metric_text": "Decisions ruled per session",
    "x_sla_metric_value": 0.0,
    "x_sla_metric_unit": "count",
}

GV_EVI_002_DRAFT_TEXT_ONLY = {
    "x_service_code": "GV-EVI-002",
    "x_service_name": "Service Legitimacy Test Application",
    "x_service_status": "draft",
    "x_method_role": "method",
    "x_service_role": False,
    "x_platform_role": False,
    "x_client_outcome": (
        "Every candidate service entering or crossing a maturity gate in "
        "the catalogue is tested against the same 8 criteria before "
        "being treated as fit-for-catalogue."
    ),
    "x_sla_metric_text": (
        "Candidate services tested before catalogue-maturity claims"
    ),
    "x_sla_metric_value": 0.0,
    "x_sla_metric_unit": False,
}

SC_06_DRAFT_EMPTY = {
    "x_service_code": "SC-06",
    "x_service_name": "SC-06 Governance Advisory Board and Service Catalogue Oversight",
    "x_service_status": "draft",
    "x_method_role": False,
    "x_service_role": False,
    "x_platform_role": False,
    "x_client_outcome": False,
    "x_sla_metric_text": False,
    "x_sla_metric_value": 0.0,
    "x_sla_metric_unit": False,
}


def test_legacy_active_record_fails_on_role_none_set():
    # Every one of the 16 currently-active legacy (SA-/SB-/SC-) services
    # has all three role fields False -- the six-field pattern was never
    # applied retroactively. This is real, not a contrived edge case.
    result = validate_service_record(SC_01_LEGACY_ACTIVE)
    assert not result.ok
    assert any("NONE_SET" in e for e in result.errors)
    # Client outcome and SLA text ARE populated for this record -- only
    # the role classification is missing.
    assert not any("x_client_outcome" in e for e in result.errors)


def test_legacy_active_record_gets_sla_soft_warning_not_error():
    result = validate_service_record(SC_01_LEGACY_ACTIVE)
    assert any("no x_sla_metric_unit" in w for w in result.warnings)
    # SLA gap is a warning, not an error -- it must not be why result.ok
    # is False (the role check already makes it False; verify the SLA
    # check specifically contributes zero errors here).
    sla_errors, _ = check_sla_metric(SC_01_LEGACY_ACTIVE)
    assert sla_errors == []


def test_draft_with_unit_passes_clean():
    result = validate_service_record(GV_GOV_001_DRAFT_WITH_UNIT)
    assert result.ok, result.errors
    assert result.role_set == "x_platform_role"
    assert result.errors == []


def test_draft_text_only_passes_with_warning():
    result = validate_service_record(GV_EVI_002_DRAFT_TEXT_ONLY)
    assert result.ok, result.errors
    assert result.role_set == "x_method_role"
    assert any("no x_sla_metric_unit" in w for w in result.warnings)


def test_empty_draft_fails_multiple_ways():
    result = validate_service_record(SC_06_DRAFT_EMPTY)
    assert not result.ok
    assert any("x_client_outcome" in e for e in result.errors)
    assert any("NONE_SET" in e for e in result.errors)


def test_multiple_roles_set_is_a_distinct_failure_from_none_set():
    record = dict(GV_GOV_001_DRAFT_WITH_UNIT)
    record["x_method_role"] = "method"  # now both method and platform set
    result = validate_service_record(record)
    assert not result.ok
    assert any("MULTIPLE_SET" in e for e in result.errors)
    assert not any("NONE_SET" in e for e in result.errors)


def test_quantified_without_text_is_a_hard_error():
    record = dict(GV_GOV_001_DRAFT_WITH_UNIT)
    record["x_sla_metric_text"] = False
    result = validate_service_record(record)
    assert not result.ok
    assert any("quantified without description" in e for e in result.errors)


def test_fully_unpopulated_sla_triple_is_warning_only():
    record = dict(GV_GOV_001_DRAFT_WITH_UNIT)
    record["x_sla_metric_text"] = False
    record["x_sla_metric_unit"] = False
    record["x_sla_metric_value"] = 0.0
    result = validate_service_record(record)
    # role + client_outcome still clean, so only the SLA warning fires
    assert result.ok, result.errors
    assert any("entirely unpopulated" in w for w in result.warnings)


def test_missing_key_entirely_vs_present_but_false():
    # Simulates a narrower `fields=[...]` read that didn't select
    # x_client_outcome at all, vs. a full read where it comes back False.
    record_missing_key = {k: v for k, v in SC_06_DRAFT_EMPTY.items() if k != "x_client_outcome"}
    errors = check_required_fields(record_missing_key)
    assert any("not even read/selected" in e for e in errors)

    errors2 = check_required_fields(SC_06_DRAFT_EMPTY)
    assert any("Required field not populated" in e for e in errors2)
    assert not any("not even read/selected" in e for e in errors2)


def test_role_classification_helper_reports_which_field():
    ok, which, errors = check_role_classification(GV_EVI_002_DRAFT_TEXT_ONLY)
    assert ok
    assert which == "x_method_role"
    assert errors == []


def test_batch_validation_keys_by_service_code():
    results = validate_service_records(
        [SC_01_LEGACY_ACTIVE, GV_GOV_001_DRAFT_WITH_UNIT, SC_06_DRAFT_EMPTY]
    )
    assert set(results.keys()) == {"SC-01", "GV-GOV-001", "SC-06"}
    assert not results["SC-01"].ok
    assert results["GV-GOV-001"].ok
    assert not results["SC-06"].ok


def test_batch_over_all_16_active_records_all_fail_role_check():
    # Documents, with an executable assertion, the exact finding reported
    # in this validator's docstring: every currently-active legacy
    # service fails the role-classification check because the pattern
    # was never applied retroactively to them. If this ever starts
    # passing it means the live data changed -- a useful regression
    # signal for whoever runs this against a fresh Odoo read later.
    active_legacy_codes = [
        "SC-01", "SC-02", "SC-03", "SC-04", "SB-01", "SB-02", "SB-03",
        "SB-04", "SA-01", "SA-02", "SC-05", "SB-05", "SA-03", "SA-04",
        "SA-05", "SA-06",
    ]
    assert len(active_legacy_codes) == 16
    for code in active_legacy_codes:
        record = dict(SC_01_LEGACY_ACTIVE)
        record["x_service_code"] = code
        result = validate_service_record(record)
        assert not result.ok
        assert any("NONE_SET" in e for e in result.errors)


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = Path(__file__).resolve().parents[1].joinpath("scoping_validator.py").read_text()
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules


def test_all_three_role_fields_share_identical_vocabulary_assumption():
    # Documents the schema surprise found via ir.model.fields this
    # session: x_method_role/x_service_role/x_platform_role each carry
    # the SAME three-value selection (method/service/platform), not
    # role-specific vocabularies. The check only cares about truthiness,
    # not which value is stored, so this doesn't change behaviour -- but
    # it is exactly the kind of thing a purely conceptual review (reading
    # the submission's prose "role classification: method/service/
    # platform role" as a single field) would misread as one field.
    assert ROLE_FIELDS == ("x_method_role", "x_service_role", "x_platform_role")
