"""Stage-2 six-field scoping validator for SynapSys Service Catalogue
`x_service_catalogue` records.

Extends the artefact-level `validator.py` (front-matter/hash checking for
markdown filings) with a *record*-level check: does a service record
satisfy the "six-field Stage-2 scoping pattern" described in
`CLAUDE_CODE_INTERNAL_TECHNOLOGY_SERVICES_BOARD_SUBMISSION_v0.1.md` s1,
and offered as CC-SVC-T3 in `CAPABILITY_CARD_claude_code_v0.1.md`?

Zero network access, zero subprocess calls, zero writes. Operates on a
plain dict shaped like an Odoo `search_read` result for
`x_service_catalogue` (or any object with a compatible `.get()`
interface, e.g. a fixture or a JSON export) -- it never calls Odoo
itself. Same isolation discipline as `validator.py` (see
`tests/test_scoping_validator.py::test_isolation_no_network_or_subprocess_imports`).

The six-field pattern was independently re-derived against the LIVE
`ir.model.fields` schema for `x_service_catalogue` this session (not
taken from the submission's field list on trust -- see the board
submission's own s1 table, then cross-checked field-by-field), and two
real corrections to that description surfaced in the process:

1. Role classification is not one field with three choices. It is
   THREE separate selection fields on the live model -- `x_method_role`,
   `x_service_role`, `x_platform_role` -- each independently either
   `False` or one of the same {method, service, platform} values (the
   selection vocabulary is identical across all three, which is itself
   a little surprising and worth a registrar's eye). The Stage-2 pattern
   is "exactly one of the three fields is truthy": zero-set and
   multiple-set are both failures, and are reported as *distinct*
   reasons here because they imply different fixes -- zero-set means an
   unscoped record, multiple-set means a data-entry error, and a
   validator that just says "role check failed" for both is less useful
   than one that says which.

2. The SLA metric triple (`x_sla_metric_text` / `_value` / `_unit`)
   cannot be enforced as a strict "all three or none" boolean rule
   against the live data as it actually exists. `x_sla_metric_value` is
   a `float` field with no NULL state in Odoo's ORM default -- an unset
   value reads back as `0.0`, indistinguishable from a legitimately-zero
   SLA target. Checked against a live read of all 16 currently-`active`
   `x_service_catalogue` records this session: every one of them has
   `x_sla_metric_text` populated, `x_sla_metric_value == 0.0`, and
   `x_sla_metric_unit == False`. A further ~7 of the 15 already-drafted
   records using the new GV-/DL-/VL- code pattern (the ones the
   submission itself cites as proof the pattern works) *also* have text
   without a unit. If "together or not at all" were enforced as a hard
   AND, essentially the whole live corpus -- old and new alike -- would
   fail, which means the rule as literally stated in the submission is
   aspirational, not currently met, regardless of which service era
   produced the record. This validator therefore treats
   `x_sla_metric_value == 0.0` as "not asserted" rather than "present",
   and demotes the SLA-triple check to a WARNING when text is present
   without a unit (a soft, fixable gap) and only raises it to an ERROR
   when unit/value look genuinely populated but text is missing
   entirely (a record that is quantified but undescribed, a stronger
   sign of a broken/partial entry rather than an aspirational one).

Nothing here is a claim that this is the *only* reasonable reading of
the six-field pattern -- it is one defensible, evidence-checked reading,
recorded so the next reader doesn't have to re-derive it from a strict
literal interpretation and get blindsided by 100% of live records
failing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from _validation_core import check_required_fields as _check_required_fields
from _validation_core import odoo_absent as _odoo_absent

ROLE_FIELDS = ("x_method_role", "x_service_role", "x_platform_role")

REQUIRED_RECORD_FIELDS = (
    "x_service_code",
    "x_service_name",
    "x_client_outcome",
)


@dataclass
class ScopingResult:
    ok: bool
    service_code: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    role_set: str | None = None  # which of the three role fields is truthy, if exactly one


def _present(value) -> bool:
    """Odoo read_odoo/search_read convention: unset scalar fields come
    back as `False` (not None, not ''), unset many2one as `False`.
    Truthy non-empty string/number is "present". Thin wrapper over the
    shared core's `odoo_absent` predicate."""
    return not _odoo_absent(value)


def check_required_fields(record: dict) -> list[str]:
    return _check_required_fields(
        record,
        REQUIRED_RECORD_FIELDS,
        is_absent=_odoo_absent,
        missing_key_message=lambda f: f"Record missing key entirely: {f!r} (not even read/selected)",
        absent_value_message=lambda f: f"Required field not populated: {f!r}",
    )


def check_role_classification(record: dict) -> tuple[bool, str | None, list[str]]:
    """Exactly one of x_method_role / x_service_role / x_platform_role
    must be truthy. Returns (ok, which_field_if_exactly_one, errors)."""
    set_fields = [f for f in ROLE_FIELDS if _present(record.get(f, False))]
    if len(set_fields) == 0:
        return False, None, [
            "Role classification: none of x_method_role/x_service_role/"
            "x_platform_role is set -- record is unscoped (NONE_SET)."
        ]
    if len(set_fields) > 1:
        return False, None, [
            "Role classification: more than one role field is set "
            f"({set_fields}) -- exactly one is required (MULTIPLE_SET)."
        ]
    return True, set_fields[0], []


def check_sla_metric(record: dict) -> tuple[list[str], list[str]]:
    """SLA metric triple check, see module docstring point 2 for why this
    is a soft/WARNING-tier check rather than a hard AND of all three
    fields, based on what the live corpus actually looks like."""
    errors: list[str] = []
    warnings: list[str] = []

    text_present = _present(record.get("x_sla_metric_text", False))
    unit_present = _present(record.get("x_sla_metric_unit", False))
    value = record.get("x_sla_metric_value", 0.0)
    value_asserted = _present(value) and value != 0.0

    if not text_present and not unit_present and not value_asserted:
        warnings.append(
            "SLA metric triple entirely unpopulated (text/value/unit all "
            "absent or zero) -- acceptable at Potential PPV, should be "
            "closed before Probable."
        )
        return errors, warnings

    if text_present and not unit_present:
        warnings.append(
            "SLA metric has descriptive text but no x_sla_metric_unit -- "
            "consistent with roughly half the live corpus (both legacy "
            "and already-drafted new-pattern records), treated as a soft "
            "gap rather than a hard failure; see module docstring."
        )

    if (unit_present or value_asserted) and not text_present:
        errors.append(
            "SLA metric has a unit and/or a non-zero value but no "
            "x_sla_metric_text -- quantified without description, a "
            "stronger signal of a broken/partial entry."
        )

    return errors, warnings


def validate_service_record(record: dict) -> ScopingResult:
    """Validate one `x_service_catalogue` record dict against the
    six-field Stage-2 scoping pattern. Never mutates `record`, never
    calls Odoo -- pure function over the dict the caller already read."""
    result = ScopingResult(ok=True, service_code=record.get("x_service_code"))

    for err in check_required_fields(record):
        result.ok = False
        result.errors.append(err)

    role_ok, role_which, role_errors = check_role_classification(record)
    if not role_ok:
        result.ok = False
        result.errors.extend(role_errors)
    else:
        result.role_set = role_which

    sla_errors, sla_warnings = check_sla_metric(record)
    if sla_errors:
        result.ok = False
        result.errors.extend(sla_errors)
    result.warnings.extend(sla_warnings)

    return result


def validate_service_records(records: list[dict]) -> dict[str, ScopingResult]:
    """Batch entry point: validate a list of service record dicts
    (e.g. the direct output of an Odoo `search_odoo` call against
    `x_service_catalogue`), keyed by `x_service_code`. Read-only,
    reports gaps -- does not write corrections itself (per CC-SVC-T3's
    own STOP_HOLD)."""
    out: dict[str, ScopingResult] = {}
    for rec in records:
        res = validate_service_record(rec)
        key = res.service_code or f"<no-code:{id(rec)}>"
        out[key] = res
    return out
