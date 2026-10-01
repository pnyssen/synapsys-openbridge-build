import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evidence_validator import (  # noqa: E402
    ALLOWED_EVIDENCE_VERDICTS,
    OPTIONAL_CR_EVIDENCE_FIELDS,
    REQUIRED_CR_EVIDENCE_FIELDS,
    validate_cr_evidence,
    validate_cr_evidence_records,
)

# Real convention, taken from CLAUDE.md's own CHG-2026-410 entries (e.g.
# "Merged via PR #4, sha `ba79af87...`") -- not synthesised business data,
# just a representative evidence record shaped the way this repo's own
# CR filings describe evidence.
COMPLETE_CR = {
    "cr_reference": "CHG-2026-999",
    "x_test_evidence": "41/41 pytest passed, see Wave 2 receipt",
    "x_rollback_plan": "git revert <sha>; no data migration involved",
}


def test_complete_cr_evidence_passes():
    result = validate_cr_evidence(COMPLETE_CR)
    assert result.ok, result.errors
    assert result.errors == []


def test_missing_test_evidence_fails():
    record = dict(COMPLETE_CR)
    del record["x_test_evidence"]
    result = validate_cr_evidence(record)
    assert not result.ok
    assert any("x_test_evidence" in e for e in result.errors)


def test_missing_rollback_plan_fails():
    record = dict(COMPLETE_CR)
    del record["x_rollback_plan"]
    result = validate_cr_evidence(record)
    assert not result.ok
    assert any("x_rollback_plan" in e for e in result.errors)


def test_blank_required_value_fails():
    record = dict(COMPLETE_CR)
    record["x_rollback_plan"] = "   "
    result = validate_cr_evidence(record)
    assert not result.ok
    assert any("x_rollback_plan" in e and "not populated" in e for e in result.errors)


def test_false_and_none_handling_matches_odoo_convention():
    # This validator uses the odoo_absent convention (matching this
    # repo's existing scoping_validator.py precedent for x_-prefixed
    # fields): False and None are absent, but a zero-like value is not.
    record_false = dict(COMPLETE_CR)
    record_false["x_test_evidence"] = False
    result_false = validate_cr_evidence(record_false)
    assert not result_false.ok
    assert any("x_test_evidence" in e for e in result_false.errors)

    record_none = dict(COMPLETE_CR)
    record_none["x_rollback_plan"] = None
    result_none = validate_cr_evidence(record_none)
    assert not result_none.ok
    assert any("x_rollback_plan" in e for e in result_none.errors)


def test_deterministic_finding_order():
    record = {"cr_reference": "CHG-2026-000"}  # both required fields missing
    result = validate_cr_evidence(record)
    assert not result.ok
    assert len(result.errors) == 2
    assert "x_test_evidence" in result.errors[0]
    assert "x_rollback_plan" in result.errors[1]


def test_optional_fields_warn_when_blank_but_never_required():
    record = dict(COMPLETE_CR)
    for opt_field in OPTIONAL_CR_EVIDENCE_FIELDS:
        record[opt_field] = False
    result = validate_cr_evidence(record)
    assert result.ok, result.errors  # optional blanks never fail closed
    assert len(result.warnings) == len(OPTIONAL_CR_EVIDENCE_FIELDS)


def test_optional_fields_absent_entirely_produce_no_finding():
    result = validate_cr_evidence(COMPLETE_CR)  # none of the optional keys present at all
    assert result.warnings == []


def test_allowed_evidence_verdict_passes():
    record = dict(COMPLETE_CR)
    record["verdict"] = "PASS_WITH_CONDITIONS"
    assert "PASS_WITH_CONDITIONS" in ALLOWED_EVIDENCE_VERDICTS
    result = validate_cr_evidence(record)
    assert result.ok, result.errors


def test_invalid_evidence_verdict_fails():
    record = dict(COMPLETE_CR)
    record["verdict"] = "MADE_UP_VERDICT"
    result = validate_cr_evidence(record)
    assert not result.ok
    assert any("verdict" in e for e in result.errors)
    assert "MADE_UP_VERDICT" not in ALLOWED_EVIDENCE_VERDICTS


def test_missing_verdict_is_not_judged():
    # verdict is optional -- absence of the key is not itself an error.
    result = validate_cr_evidence(COMPLETE_CR)
    assert result.ok, result.errors


def test_no_mutation_of_input_record():
    record = copy.deepcopy(COMPLETE_CR)
    before = copy.deepcopy(record)
    validate_cr_evidence(record)
    assert record == before


def test_batch_validation_keyed_by_cr_reference():
    incomplete = {"cr_reference": "CHG-2026-001", "x_test_evidence": "some evidence"}
    results = validate_cr_evidence_records([COMPLETE_CR, incomplete])
    assert set(results.keys()) == {"CHG-2026-999", "CHG-2026-001"}
    assert results["CHG-2026-999"].ok
    assert not results["CHG-2026-001"].ok


def test_required_fields_constant_matches_claude_md_source():
    # CLAUDE.md's GitHub Change Control Rule names exactly these two
    # fields as required before a CR-gated action -- see this package's
    # README.md discovery trail. Locks the constant to that source.
    assert REQUIRED_CR_EVIDENCE_FIELDS == ("x_test_evidence", "x_rollback_plan")


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = Path(__file__).resolve().parents[1].joinpath("evidence_validator.py").read_text()
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules
