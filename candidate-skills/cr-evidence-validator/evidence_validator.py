"""Change Request evidence-completeness validator.

Third real consumer of the shared validation core
(`../synapsys-service-catalogue-pilot/_validation_core.py`), proving it
generalises beyond the Service Catalogue pilot's own `validator.py`/
`scoping_validator.py` pair. See this package's README.md for the full
discovery trail; the short version:

This repository's only authoritative source for required CR evidence
fields is `CLAUDE.md`'s "GitHub Change Control Rule" section (CR
CHG-2026-410): "CR needs `x_test_evidence` and `x_rollback_plan`
populated before the action". No Odoo `x_change_request` model or
similar schema exists in this repo to source additional required fields
against, so only those two are REQUIRED here. Four further fields named
in Wave 3's own suggested list (`x_change_reason`, `x_risk_assessment`,
`x_implementation_plan`, `x_validation_result`) are recognised if
present -- warned on when blank, never required, never given an
invented rule.

This module checks evidence COMPLETENESS only -- it has no authority to
approve a Change Request, no Odoo/N8N access, and performs no
mutation. Zero network access, zero subprocess calls, zero filesystem
writes, same isolation discipline as its sibling validators.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_PILOT_DIR = Path(__file__).resolve().parents[1] / "synapsys-service-catalogue-pilot"
if str(_PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(_PILOT_DIR))

from _validation_core import Finding  # noqa: E402
from _validation_core import check_required_fields as _check_required_fields  # noqa: E402
from _validation_core import check_vocabulary as _check_vocabulary  # noqa: E402
from _validation_core import odoo_absent as _odoo_absent  # noqa: E402

# Sourced verbatim from CLAUDE.md's "GitHub Change Control Rule" section
# (CHG-2026-410) -- the only CR evidence fields this repository actually
# names as required before a CR-gated action.
REQUIRED_CR_EVIDENCE_FIELDS = ("x_test_evidence", "x_rollback_plan")

# Recognised if present, never required, never given an invented rule --
# named in Wave 3's own suggested field list but not sourced anywhere in
# this repository's Change Control documentation.
OPTIONAL_CR_EVIDENCE_FIELDS = (
    "x_change_reason",
    "x_risk_assessment",
    "x_implementation_plan",
    "x_validation_result",
)

# This programme's own standing VERDICT OPTIONS vocabulary (see the
# thread's PROGRAMME control text) -- the only evidenced vocabulary
# available for an evidence record's optional self-declared outcome
# label. No CR-specific status enum exists elsewhere in this repository.
ALLOWED_EVIDENCE_VERDICTS = {
    "PASS",
    "PASS_WITH_CONDITIONS",
    "HOLD",
    "FAIL",
    "SOURCE_OR_BASELINE_CONFLICT",
    "TESTS_NOT_RUN",
    "AUTHORITY_REQUIRED",
}


def validate_cr_evidence(record: dict) -> Finding:
    """Validate one Change Request evidence record dict (`x_`-prefixed
    keys, matching this ecosystem's own field-naming convention).
    Presence uses the `False`/`None`/blank-string-absent convention
    already established in this repo by `scoping_validator.py` for
    `x_`-prefixed field records -- zero-like values are not treated as
    absent by that convention, unchanged here.

    Never mutates `record`, never touches Odoo/N8N/GitHub, never
    approves anything -- reports evidence completeness only. Fails
    closed: any required field missing or blank makes `ok` False.
    """
    result = Finding()

    missing = _check_required_fields(
        record,
        REQUIRED_CR_EVIDENCE_FIELDS,
        is_absent=_odoo_absent,
        missing_key_message=lambda f: (
            f"CR evidence field not read/selected: {f!r} -- required by "
            "CHG-2026-410 before a CR-gated action"
        ),
        absent_value_message=lambda f: (
            f"CR evidence field not populated: {f!r} -- required by "
            "CHG-2026-410 before a CR-gated action (fails closed)"
        ),
    )
    for message in missing:
        result.add_error(message)

    for opt_field in OPTIONAL_CR_EVIDENCE_FIELDS:
        if opt_field in record and _odoo_absent(record[opt_field]):
            result.add_warning(
                f"Optional CR field {opt_field!r} present but blank -- not "
                "required by any repository-evidenced rule, recorded as a "
                "gap only."
            )

    verdict = record.get("verdict")
    verdict_error = _check_vocabulary(verdict, ALLOWED_EVIDENCE_VERDICTS, "verdict")
    if verdict_error:
        result.add_error(verdict_error)

    return result


def validate_cr_evidence_records(records: list[dict]) -> dict[str, Finding]:
    """Batch entry point, keyed by `cr_reference` -- mirrors
    `scoping_validator.validate_service_records`'s batch shape for a
    consistent cross-consumer calling convention. Read-only, reports
    gaps -- does not write, approve, or correct anything."""
    out: dict[str, Finding] = {}
    for rec in records:
        res = validate_cr_evidence(rec)
        key = rec.get("cr_reference") or f"<no-cr-reference:{id(rec)}>"
        out[key] = res
    return out
