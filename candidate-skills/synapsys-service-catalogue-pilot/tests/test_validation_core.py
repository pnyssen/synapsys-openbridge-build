import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _validation_core import (  # noqa: E402
    Finding,
    check_required_fields,
    check_vocabulary,
    default_absent,
    odoo_absent,
)


def test_required_field_present_produces_no_error():
    errors = check_required_fields({"name": "present"}, ["name"])
    assert errors == []


def test_required_field_missing_key_produces_error():
    errors = check_required_fields({}, ["name"])
    assert len(errors) == 1
    assert "name" in errors[0]


def test_blank_string_treated_as_absent_under_default_predicate():
    errors = check_required_fields({"name": "   "}, ["name"], is_absent=default_absent)
    assert len(errors) == 1
    assert "name" in errors[0]


def test_false_treated_as_absent_under_odoo_predicate():
    errors = check_required_fields({"flag": False}, ["flag"], is_absent=odoo_absent)
    assert len(errors) == 1
    assert "flag" in errors[0]


def test_zero_like_value_present_under_odoo_predicate():
    # 0 / 0.0 is a legitimate value under the Odoo convention -- only
    # False/None/blank-string are absent. "Zero means unset" is a
    # field-specific business rule (see scoping_validator.check_sla_metric),
    # deliberately not baked into the generic predicate.
    errors = check_required_fields({"count": 0, "amount": 0.0}, ["count", "amount"], is_absent=odoo_absent)
    assert errors == []


def test_zero_like_value_absent_under_default_predicate_when_string():
    # default_absent only reasons about strings/None; a literal 0 is not
    # a string, so it is never judged absent by this predicate either --
    # documented here so the two predicates' actual disagreement (over
    # False, not over 0) is explicit rather than assumed.
    errors = check_required_fields({"count": 0}, ["count"], is_absent=default_absent)
    assert errors == []


def test_custom_absence_predicate():
    is_negative = lambda v: isinstance(v, (int, float)) and v < 0
    errors = check_required_fields({"balance": -5}, ["balance"], is_absent=is_negative)
    assert len(errors) == 1
    assert "balance" in errors[0]

    errors_ok = check_required_fields({"balance": 5}, ["balance"], is_absent=is_negative)
    assert errors_ok == []


def test_custom_messages_distinguish_missing_key_from_absent_value():
    errors_missing = check_required_fields(
        {},
        ["x"],
        missing_key_message=lambda f: f"NO KEY: {f}",
        absent_value_message=lambda f: f"EMPTY: {f}",
    )
    assert errors_missing == ["NO KEY: x"]

    errors_empty = check_required_fields(
        {"x": ""},
        ["x"],
        missing_key_message=lambda f: f"NO KEY: {f}",
        absent_value_message=lambda f: f"EMPTY: {f}",
    )
    assert errors_empty == ["EMPTY: x"]


def test_allowed_vocabulary_value_passes():
    assert check_vocabulary("SUBMITTED", {"SUBMITTED", "WORKING"}, "status") is None


def test_invalid_vocabulary_value_fails():
    error = check_vocabulary("BOGUS", {"SUBMITTED", "WORKING"}, "status")
    assert error is not None
    assert "status" in error
    assert "BOGUS" in error


def test_none_vocabulary_value_is_not_judged():
    # Absence of the field is a separate concern (check_required_fields);
    # this function only judges membership when a value is actually present.
    assert check_vocabulary(None, {"SUBMITTED"}, "status") is None


def test_deterministic_finding_order():
    errors = check_required_fields({}, ["first", "second", "third"])
    assert errors == [
        "Missing required field: 'first'",
        "Missing required field: 'second'",
        "Missing required field: 'third'",
    ]


def test_finding_merge_preserves_order_and_folds_ok():
    a = Finding()
    a.add_error("a-error")
    a.add_warning("a-warning")

    b = Finding()
    b.add_warning("b-warning")

    a.merge(b)
    assert a.ok is False
    assert a.errors == ["a-error"]
    assert a.warnings == ["a-warning", "b-warning"]


def test_finding_defaults_to_ok_true_with_no_findings():
    f = Finding()
    assert f.ok is True
    assert f.errors == []
    assert f.warnings == []


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = Path(__file__).resolve().parents[1].joinpath("_validation_core.py").read_text()
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules
