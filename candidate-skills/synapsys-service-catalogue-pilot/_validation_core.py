"""Generic validation primitives shared by this pilot's artefact- and
record-level validators (`validator.py`, `scoping_validator.py`).

Extracted because both modules independently reimplemented the same two
shapes of logic against different data conventions: "is this required
field present" and "is this value in an allowed vocabulary". This module
holds only the generic mechanics of those checks. It intentionally knows
nothing about SynapSys artefact types, field names, vocabularies, or
business rules (front-matter parsing, self-hash boundaries, WM_03 fields,
six-field scoping, SLA gating, role exclusivity) -- those stay in the
modules that own them, per this Wave's scope.

Zero network access, zero subprocess calls, zero filesystem writes -- same
isolation discipline as its callers (see
`tests/test_isolation_no_network_or_subprocess_imports`-style checks in
each consumer's test module).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

AbsencePredicate = Callable[[object], bool]
MessageFn = Callable[[str], str]


def default_absent(value: object) -> bool:
    """Front-matter/artefact convention: a missing value, or a string
    that is empty or whitespace-only, is absent. Front-matter values are
    always strings (see `validator.parse_front_matter`), so this never
    needs to reason about numeric or boolean falsiness."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def odoo_absent(value: object) -> bool:
    """Odoo `search_read`/`read` convention: unset scalar fields come
    back as `False` (not `None`, not `''`). `False`, `None`, and
    empty/whitespace-only strings are absent; numeric zero is NOT absent
    -- zero is a legitimate value for many fields, and "zero means
    unset" is a field-specific business rule (see
    `scoping_validator.check_sla_metric`), not a generic Odoo
    convention, so it is deliberately left to the caller."""
    if value is False or value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


@dataclass
class Finding:
    """Generic ok/errors/warnings accumulator. Available for reuse by
    any validator that wants a shared result shape; existing callers in
    this pilot keep their own richer dataclasses (`ValidationResult`,
    `ScopingResult`) unchanged and are not required to adopt this type."""

    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: "Finding") -> None:
        """Append `other`'s errors/warnings in order and fold its `ok`
        into this one. Never resets `ok` back to True."""
        if not other.ok:
            self.ok = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def check_required_fields(
    record: dict,
    required_fields: Iterable[str],
    is_absent: AbsencePredicate = default_absent,
    missing_key_message: Optional[MessageFn] = None,
    absent_value_message: Optional[MessageFn] = None,
) -> list[str]:
    """Return one error string per required field that is either not a
    key in `record` at all, or present but judged absent by `is_absent`.

    Deterministic order: iterates `required_fields` in the order given
    (a tuple/list, not a set), so output order never depends on dict or
    hash-set iteration order.

    `missing_key_message`/`absent_value_message` let a caller preserve
    its own existing wording for the two cases; both default to a
    generic "Missing required field" message if not supplied. Passing
    the same function for both reproduces a validator that does not
    distinguish "key absent" from "key present but empty".
    """
    errors: list[str] = []
    for name in required_fields:
        if name not in record:
            msg = missing_key_message(name) if missing_key_message else f"Missing required field: {name!r}"
            errors.append(msg)
        elif is_absent(record[name]):
            msg = absent_value_message(name) if absent_value_message else f"Missing required field: {name!r}"
            errors.append(msg)
    return errors


def check_vocabulary(
    value: Optional[str],
    allowed: Iterable[str],
    field_name: str,
) -> Optional[str]:
    """Return an error string if `value` is not `None` and not a member
    of `allowed`, else `None`. A `None` value is reported as neither
    valid nor invalid here -- callers that require the field to be
    present at all report that separately via `check_required_fields`."""
    if value is None:
        return None
    allowed_set = set(allowed)
    if value not in allowed_set:
        return f"{field_name} {value!r} not in allowed vocabulary {sorted(allowed_set)}"
    return None
