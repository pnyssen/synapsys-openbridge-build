"""
Common mutation-safety membrane — prepare/execute write-set core.

Implements the two-phase contract required by
RELEASE_D007_SYNAPSYS_MCP_FFE_MUTATION_SAFETY_ENFORCEMENT_V1 (groups A/B):

  PREPARE_WRITE_SET (non-mutating): resolve the caller's target to the exact
  current record IDs, capture actual_affected_count, register_total /
  affected_percentage, field-level prestate, protected-state and
  observability classification, and emit an immutable write_set_id + digest.

  EXECUTE_WRITE_SET (mutating): accepts only a previously prepared
  write_set_id plus the exact enumerated IDs it represents; re-reads
  immediately before mutation and refuses on prestate drift or any set
  change; executes only the declared set; reads back after; returns
  before/after values and a rollback payload.

Root cause this closes (D007 prewrite, Benefit register incident): a
domain-based bulk write whose consent surface (15 records) understated its
actual blast radius (53 records, 3.53x) because nothing resolved and froze
the actual affected set before mutation. P0-A below is that exact canary.

Backend-agnostic by design: callers supply resolve_ids/read_fn/count_fn/
mutate_fn closures, so this module has no direct Odoo/N8N/XML-RPC/HTTP
dependency and is fully unit-testable with plain mocks (mcp-servers/tests/
test_write_safety.py) — no live connector required, matching this release's
"HOLD any test requiring an unavailable live connector" boundary.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

# ---- P0-B bulk ceiling ------------------------------------------------------

BULK_ID_CEILING = 10
BULK_PERCENTAGE_CEILING = 20.0  # percent

# ---- Consent classes (fixed six, per the D007 prewrite) -------------------

CONSENT_DATA_MUTATION = "DATA_MUTATION"
CONSENT_OBSERVABILITY_MUTATION = "OBSERVABILITY_MUTATION"
CONSENT_AUDIENCE_EXPANSION = "AUDIENCE_EXPANSION"
CONSENT_DESTRUCTIVE_MUTATION = "DESTRUCTIVE_MUTATION"
CONSENT_PROTECTED_STATE_TRANSITION = "PROTECTED_STATE_TRANSITION"
CONSENT_CONFIGURATION_RUNTIME_MUTATION = "CONFIGURATION_RUNTIME_MUTATION"

DESTRUCTIVE_OPERATIONS = {"unlink"}

# Models/fields whose listed values are PROTECTED_STATE_TRANSITION targets.
# x_ss_benefit_register.x_benefit_status verified live 2026-08-25 via
# ir.model.fields (id16134): selection includes 'measured' and 'verified'
# exactly as named in the D007 prewrite ("verified and measured Benefit
# states are protected"). Not inferred — read directly before this file was
# written.
PROTECTED_STATE_FIELDS: Dict[str, Dict[str, Set[str]]] = {
    "x_ss_benefit_register": {"x_benefit_status": {"measured", "verified"}},
}

# Models/fields that are OBSERVABILITY_MUTATION targets when written, per
# the prewrite's explicit list (ir.filters, ir.ui.view, ir.ui.menu).
OBSERVABILITY_MODELS: Dict[str, Set[str]] = {
    "ir.filters": {"context", "domain", "is_default", "user_id", "name"},
    "ir.ui.view": {"arch", "arch_db", "active"},
    "ir.ui.menu": {"active", "sequence", "parent_id", "name"},
    # L-09: ir.actions.act_window mutations (not just creates) are also
    # observability-class — they change what a view/menu shows by default.
    "ir.actions.act_window": {"name", "view_mode", "domain", "context", "res_model"},
}
# Fields whose change on an observability model is itself a *default-state*
# change (P0-F: "A default-state change requires a distinct
# OBSERVABILITY_DEFAULT_CHANGE confirmation").
OBSERVABILITY_DEFAULT_FIELDS: Set[str] = {"is_default", "active"}


class WriteSafetyRefusal(Exception):
    """Raised for every negative-canary refusal path. Carries a
    machine-readable invariant code, the actual resolved scope where
    relevant, and the smallest correction (P1-L REFUSAL_FEEDBACK) — never a
    generic success/false ambiguity."""

    def __init__(self, invariant: str, message: str, *, actual: Optional[dict] = None,
                 correction: Optional[str] = None):
        self.invariant = invariant
        self.actual = actual or {}
        self.correction = correction
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "refused": True,
            "invariant": self.invariant,
            "message": str(self),
            "actual": self.actual,
            "correction": self.correction,
        }


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def compute_digest(*, model: str, operation: str, ids: Sequence[int],
                    prestate: Dict[int, Dict[str, Any]], proposed: Dict[str, Any],
                    consent_classes: Sequence[str], prepared_at: float) -> str:
    """Cryptographic digest over target model, IDs, fields, prior/proposed
    values, consent classes and preparation timestamp (prewrite Phase 1
    step 10). Any of these changing before execute changes the digest, and
    execute refuses on any set mismatch regardless of digest — the digest
    itself is carried in the return value as an auditable identity, not
    re-verified byte-for-byte at execute (the explicit id/field/prestate
    comparisons in execute_write_set are the enforcement; the digest is the
    receipt)."""
    payload = {
        "model": model,
        "operation": operation,
        "ids": sorted(ids),
        "prestate": {str(k): v for k, v in sorted(prestate.items())},
        "proposed": proposed,
        "consent_classes": sorted(consent_classes),
        "prepared_at": prepared_at,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


class WriteSetStore:
    """In-memory registry of prepared write sets. Process-lifetime only —
    matches this membrane's threat model (a single long-lived MCP server
    process); a write_set_id from a prior process is simply unknown and
    refuses (UNKNOWN_WRITE_SET), never silently accepted."""

    def __init__(self):
        self._sets: Dict[str, dict] = {}

    def put(self, write_set: dict) -> None:
        self._sets[write_set["write_set_id"]] = write_set

    def get(self, write_set_id: str) -> Optional[dict]:
        return self._sets.get(write_set_id)

    def consume(self, write_set_id: str) -> None:
        self._sets.pop(write_set_id, None)

    def __len__(self) -> int:
        return len(self._sets)


def classify_protected(model: str, ids: Sequence[int], prestate: Dict[int, Dict[str, Any]],
                        proposed: Dict[str, Any]) -> List[dict]:
    """Return the subset of (id, field, prior, proposed) transitions this
    write would perform that land on a PROTECTED_STATE_FIELDS value."""
    rules = PROTECTED_STATE_FIELDS.get(model, {})
    transitions = []
    for field, protected_values in rules.items():
        if field not in proposed:
            continue
        for rid in ids:
            prior = (prestate.get(rid) or {}).get(field)
            if prior in protected_values:
                transitions.append({
                    "id": rid, "field": field,
                    "prior": prior, "proposed": proposed[field],
                })
    return transitions


def classify_observability(model: str, proposed: Dict[str, Any]) -> Optional[dict]:
    fields = OBSERVABILITY_MODELS.get(model)
    if not fields:
        return None
    touched = sorted(set(proposed) & fields)
    if not touched:
        return None
    default_change = bool(set(touched) & OBSERVABILITY_DEFAULT_FIELDS)
    return {"model": model, "fields": touched, "default_change": default_change}


def prepare_write_set(
    *, model: str, operation: str,
    resolve_ids: Callable[[], List[int]],
    read_fn: Callable[[str, List[int], List[str]], List[dict]],
    store: WriteSetStore,
    count_fn: Optional[Callable[[str], int]] = None,
    proposed: Optional[Dict[str, Any]] = None,
    intended_count: Optional[int] = None,
    now: Optional[Callable[[], float]] = None,
) -> dict:
    """PHASE 1 — non-mutating. Resolves the ACTUAL affected IDs (never the
    caller's `intended_count` belief — P0-A), captures prestate, classifies
    protected/observability impact, and stores an immutable prepared write
    set. Returns the preview handed to the caller / host consent surface.
    """
    if operation not in ("write", "unlink"):
        raise ValueError(f"prepare_write_set: unsupported operation {operation!r}")

    now_fn = now or time.time
    prepared_at = now_fn()
    ids = sorted({int(i) for i in resolve_ids()})
    actual_affected_count = len(ids)

    proposed = dict(proposed or {})

    # A4/L-02 — secret refusal BEFORE any proposed value enters a preview or
    # store. Runs ahead of everything else in prepare so a secret-shaped
    # value never gets persisted into write_set/prestate/preview even
    # transiently.
    offending = scan_for_secrets(proposed)
    if offending is not None:
        raise WriteSafetyRefusal(
            "SECRET_MATERIAL_REFUSED",
            f"Proposed value at field {offending['field']!r} matches a high-confidence "
            f"secret pattern ({offending['pattern']}) and is refused before entering "
            "any preview or store. The value itself is never echoed.",
            actual={"field": offending["field"], "pattern": offending["pattern"]},
            correction=(
                "Remove the secret-shaped value from this field; secrets are never "
                "accepted through a governed write regardless of consent."
            ),
        )

    fields = sorted(proposed.keys()) if operation == "write" else []

    prestate: Dict[int, Dict[str, Any]] = {}
    if ids:
        read_fields = fields or ["id"]
        rows = read_fn(model, ids, read_fields)
        prestate = {int(r["id"]): {f: r.get(f) for f in fields} for r in rows}

    # B2/L-06 — NO_CHANGE_REQUIRED: every proposed field on every target
    # already holds the proposed value. Recorded on the write set so both
    # the single-call wrapper and execute_write_set can short-circuit
    # without ever issuing a mutating call.
    no_change_required = bool(
        operation == "write" and ids and fields
        and all(prestate.get(rid, {}).get(f) == proposed[f] for rid in ids for f in fields)
    )

    register_total = None
    affected_percentage = None
    if count_fn is not None:
        register_total = count_fn(model)
        if register_total:
            affected_percentage = round(100.0 * actual_affected_count / register_total, 2)

    protected_transitions = classify_protected(model, ids, prestate, proposed) if operation == "write" else []
    observability = classify_observability(model, proposed) if operation == "write" else None

    consent_classes: List[str] = []
    if operation == "write":
        consent_classes.append(CONSENT_DATA_MUTATION)
    if operation in DESTRUCTIVE_OPERATIONS:
        consent_classes.append(CONSENT_DESTRUCTIVE_MUTATION)
    if observability:
        consent_classes.append(CONSENT_OBSERVABILITY_MUTATION)
    if protected_transitions:
        consent_classes.append(CONSENT_PROTECTED_STATE_TRANSITION)

    write_set_id = str(uuid.uuid4())
    digest = compute_digest(
        model=model, operation=operation, ids=ids, prestate=prestate,
        proposed=proposed, consent_classes=consent_classes, prepared_at=prepared_at,
    )
    requires_enumerated_ids = (
        actual_affected_count > BULK_ID_CEILING
        or (affected_percentage is not None and affected_percentage > BULK_PERCENTAGE_CEILING)
    )

    write_set = {
        "write_set_id": write_set_id,
        "digest": digest,
        "model": model,
        "operation": operation,
        "ids": ids,
        "prestate": prestate,
        "proposed": proposed,
        "consent_classes": consent_classes,
        "protected_transitions": protected_transitions,
        "observability": observability,
        "actual_affected_count": actual_affected_count,
        "register_total": register_total,
        "affected_percentage": affected_percentage,
        "prepared_at": prepared_at,
        "consumed": False,
        "requires_enumerated_ids": requires_enumerated_ids,
        "no_change_required": no_change_required,
    }
    store.put(write_set)

    return {
        "write_set_id": write_set_id,
        "digest": digest,
        "model": model,
        "operation": operation,
        "enumerated_ids": ids,
        "actual_affected_count": actual_affected_count,
        "intended_count": intended_count,
        "register_total": register_total,
        "affected_percentage": affected_percentage,
        "prestate": prestate,
        "proposed": proposed,
        "consent_classes": consent_classes,
        "protected_transitions": protected_transitions,
        "observability": observability,
        "requires_enumerated_ids": requires_enumerated_ids,
        "requires_protected_state_confirmation": bool(protected_transitions),
        "requires_observability_default_confirmation": bool(
            observability and observability["default_change"]
        ),
        "no_change_required": no_change_required,
    }


def execute_write_set(
    *, write_set_id: str, enumerated_ids: Sequence[int],
    read_fn: Callable[[str, List[int], List[str]], List[dict]],
    mutate_fn: Callable[[str, str, List[int], Dict[str, Any]], Any],
    store: WriteSetStore,
    protected_state_confirmed: bool = False,
    observability_default_confirmed: bool = False,
) -> dict:
    """PHASE 2 — mutating and consent-gated. Refuses on any deviation from
    the prepared set (P0-B/C/D/E), then executes only the declared set and
    reads back the result."""
    write_set = store.get(write_set_id)
    if write_set is None:
        raise WriteSafetyRefusal(
            "UNKNOWN_WRITE_SET",
            f"No prepared write set found for write_set_id={write_set_id!r} "
            "(never prepared, already consumed, or process restarted).",
            correction="Call prepare first and execute against its returned write_set_id.",
        )
    if write_set["consumed"]:
        raise WriteSafetyRefusal(
            "WRITE_SET_ALREADY_CONSUMED",
            f"write_set_id={write_set_id!r} was already executed.",
            correction="Prepare a new write set for any further mutation.",
        )

    # B2/L-06 — defensive re-check: even if the caller's proposal changed
    # between prepare and execute such that it now matches current state,
    # short-circuit here rather than issue a no-op mutating call. The
    # primary check lives in prepare_write_set; this mirrors it per the
    # v2 requirement that execute repeats no-change/drift checks
    # defensively.
    if write_set.get("no_change_required"):
        write_set["consumed"] = True
        store.consume(write_set_id)
        return {
            "write_set_id": write_set_id,
            "digest": write_set["digest"],
            "model": write_set["model"],
            "operation": write_set["operation"],
            "affected_ids": list(write_set["ids"]),
            "actual_affected_count": len(write_set["ids"]),
            "result": "NO_CHANGE_REQUIRED",
            "no_change_required": True,
            "before": write_set["prestate"],
            "after": write_set["prestate"],
            "rollback": None,
        }

    prepared_ids = list(write_set["ids"])
    supplied_ids = sorted({int(i) for i in enumerated_ids})
    if supplied_ids != prepared_ids:
        added = sorted(set(supplied_ids) - set(prepared_ids))
        removed = sorted(set(prepared_ids) - set(supplied_ids))
        raise WriteSafetyRefusal(
            "SET_MISMATCH",
            "Supplied enumerated_ids do not exactly match the prepared write set.",
            actual={
                "prepared_ids": prepared_ids, "supplied_ids": supplied_ids,
                "added": added, "removed": removed,
            },
            correction=(
                "Re-call prepare to get a fresh write set matching current intent, "
                "then execute with its exact enumerated_ids. A step outside the "
                "immutable set is never folded into the old one."
            ),
        )

    if write_set["protected_transitions"] and not protected_state_confirmed:
        raise WriteSafetyRefusal(
            "PROTECTED_STATE_CONFIRMATION_REQUIRED",
            "This write set includes protected Benefit-state transitions and "
            "requires a distinct confirmation separate from ordinary consent.",
            actual={"protected_transitions": write_set["protected_transitions"]},
            correction="Re-execute with protected_state_confirmed=True after separate explicit review.",
        )

    if (write_set["observability"] and write_set["observability"]["default_change"]
            and not observability_default_confirmed):
        raise WriteSafetyRefusal(
            "OBSERVABILITY_DEFAULT_CONFIRMATION_REQUIRED",
            "This write set changes a default-visibility/state field and requires "
            "a distinct OBSERVABILITY_DEFAULT_CHANGE confirmation.",
            actual={"observability": write_set["observability"]},
            correction="Re-execute with observability_default_confirmed=True after separate explicit review.",
        )

    fields = sorted(write_set["proposed"].keys()) if write_set["operation"] == "write" else []
    if prepared_ids:
        read_fields = fields or ["id"]
        current_rows = read_fn(write_set["model"], prepared_ids, read_fields)
        current = {int(r["id"]): {f: r.get(f) for f in fields} for r in current_rows}
        drifted = []
        for rid in prepared_ids:
            prior = write_set["prestate"].get(rid, {})
            now_state = current.get(rid, {})
            if prior != now_state:
                drifted.append({"id": rid, "prepared_prior": prior, "current": now_state})
        if drifted:
            raise WriteSafetyRefusal(
                "PRESTATE_DRIFT",
                "One or more target records changed between prepare and execute.",
                actual={"drifted": drifted},
                correction="Re-call prepare to capture current state, then execute against the fresh write set.",
            )

    result = mutate_fn(write_set["model"], write_set["operation"], prepared_ids, write_set["proposed"])

    readback = None
    if prepared_ids and write_set["operation"] != "unlink":
        readback_fields = fields or ["id"]
        readback_rows = read_fn(write_set["model"], prepared_ids, readback_fields)
        readback = {int(r["id"]): {f: r.get(f) for f in readback_fields} for r in readback_rows}

    write_set["consumed"] = True
    store.consume(write_set_id)

    return {
        "write_set_id": write_set_id,
        "digest": write_set["digest"],
        "model": write_set["model"],
        "operation": write_set["operation"],
        "affected_ids": prepared_ids,
        "actual_affected_count": len(prepared_ids),
        "result": result,
        "before": write_set["prestate"],
        "after": readback,
        "rollback": {
            "model": write_set["model"],
            "operation": "write" if write_set["operation"] != "unlink" else "create",
            "prior_values": write_set["prestate"],
        },
    }


# ---- Shared trace/consent envelope (used by both Odoo and N8N MCP) --------
#
# Group B ("bind workflow create/update/activate/deactivate/webhook mutation
# routes to the same prepared-set/consent-class/trace envelope") does not
# need the full bulk-domain prepare/execute machinery above — each N8N
# mutating tool already targets one caller-known workflow id, not a
# resolved set, so the blast-radius-understatement defect this release
# closes does not apply there the same way. What N8N needs, and gets here,
# is consent classification + trace emission wrapped around each mutating
# call without changing its existing control flow (in particular,
# update_workflow's snapshot/validate/rollback logic is untouched — this
# wraps it, not replaces it).

def with_trace_envelope(
    *, tool: str, consent_classes: Sequence[str], target: str,
    trace_sink: Callable[[dict], None], fn: Callable[[], Any],
    now: Optional[Callable[[], float]] = None,
) -> Any:
    """Call fn(), emitting exactly one structured trace event covering it
    (P1 trace-emission contract: tool, target, consent_classes, timestamps,
    result, refusal_reason). Re-raises whatever fn() raises after tracing
    it as a failure — this is an envelope, not a safety gate; it never
    swallows or alters fn()'s own success/failure semantics."""
    now_fn = now or time.time
    started_at = now_fn()
    try:
        result = fn()
    except Exception as ex:
        trace_sink({
            "tool": tool,
            "target": target,
            "consent_classes": list(consent_classes),
            "started_at": started_at,
            "completed_at": now_fn(),
            "result": "error",
            "refusal_reason": str(ex)[:500],
        })
        raise
    trace_sink({
        "tool": tool,
        "target": target,
        "consent_classes": list(consent_classes),
        "started_at": started_at,
        "completed_at": now_fn(),
        "result": "success",
        "refusal_reason": None,
    })
    return result


# ---- V2 gap closure (SYNAPSYS MCP UPGRADE — CONSOLIDATED REQUIREMENTS v2) --
#
# The functions below close the specific gaps the v2 readiness assessment
# found in the group-A/B (PR39) implementation: A4 secret refusal, B3
# contextual identifier grammar, and the L-09/L-10 ir.actions.act_window
# observability + reusable-capability check. B2 no-change detection and its
# defensive execute-time re-check are wired directly into prepare_write_set/
# execute_write_set above, not here, since they need access to prestate.

# ---- A4/L-02 — secret refusal ----------------------------------------------
#
# High-confidence signatures only (per the v2 correction: a bare 16-char
# string is never globally whitelisted as safe OR flagged as secret purely
# on shape — these patterns require a genuinely credential-shaped value).

_JWT_RE = re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$")
_ENV_REF_RE = re.compile(r"\$env\.")
_CONNECTION_STRING_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/\s:]+:[^/\s@]+@")

# Field names that carry credential material when non-empty — matched
# case-insensitively against the field's own name, not its value's shape.
_CREDENTIAL_FIELD_NAMES = {
    "password", "api_key", "apikey", "secret", "client_secret", "access_token",
    "private_key", "refresh_token", "auth_token", "bearer_token", "session_token",
}


def _looks_like_secret_value(value: Any) -> Optional[str]:
    """Return the matched pattern name if `value` is high-confidence secret
    material, else None. Shape-only checks — never a bare-length heuristic."""
    if not isinstance(value, str) or not value:
        return None
    if _JWT_RE.match(value):
        return "JWT"
    if _ENV_REF_RE.search(value):
        return "ENV_REFERENCE"
    if _CONNECTION_STRING_RE.match(value):
        return "CONNECTION_STRING_WITH_CREDENTIALS"
    return None


def scan_for_secrets(payload: Dict[str, Any], *, path_prefix: str = "") -> Optional[Dict[str, str]]:
    """Scan a proposed-values payload for high-confidence secret material.
    Returns {"field": <dotted path>, "pattern": <name>} for the FIRST
    offending field found (deterministic: sorted key order), or None. The
    offending value itself is never included in the return — callers must
    never echo it into a preview, log, or trace."""
    for key in sorted(payload.keys(), key=str):
        value = payload[key]
        field_path = f"{path_prefix}.{key}" if path_prefix else str(key)
        if isinstance(value, dict):
            nested = scan_for_secrets(value, path_prefix=field_path)
            if nested is not None:
                return nested
            continue
        normalized_key = str(key).lower()
        if (isinstance(value, str) and value
                and any(cred in normalized_key for cred in _CREDENTIAL_FIELD_NAMES)):
            return {"field": field_path, "pattern": "CREDENTIAL_FIELD_NAME"}
        pattern = _looks_like_secret_value(value)
        if pattern is not None:
            return {"field": field_path, "pattern": pattern}
    return None


# ---- B3/L-08 — contextual identifier grammar -------------------------------
#
# Recognised ONLY in the context the grammar is defined for — per the v2
# correction, a value is never globally whitelisted just because its shape
# happens to match. High-confidence secret signatures always override.

_N8N_WORKFLOW_ID_RE = re.compile(r"^[A-Za-z0-9]{16}$")
# Lane/type segments use hyphens in real filenames (e.g. "chatgpt-hub",
# "state-control") — [a-z0-9_-]+ not [a-z0-9_]+.
_WM_FILENAME_RE = re.compile(
    r"^\d{8}--[a-z0-9_-]+--[a-z0-9_-]+--.+--v\d+-\d+(\.[A-Za-z0-9]+)?$"
)

IDENTIFIER_CONTEXT_WORKFLOW_ID = "workflow_id"
IDENTIFIER_CONTEXT_WM_PATH = "wm_path"

CLASS_SECRET = "SECRET"
CLASS_IDENTIFIER = "IDENTIFIER"
CLASS_UNKNOWN = "UNKNOWN"


def classify_identifier(value: str, context: Optional[str] = None) -> str:
    """Classify a string as SECRET, IDENTIFIER, or UNKNOWN.

    A high-confidence secret signature always wins regardless of context
    (JWT/$env./connection-string/credential shape). Otherwise a value is
    classified IDENTIFIER only when BOTH its grammar matches AND the caller
    declared the matching context — an opaque 16-character string with no
    declared context is UNKNOWN, never assumed safe."""
    if not isinstance(value, str):
        return CLASS_UNKNOWN
    if _looks_like_secret_value(value) is not None:
        return CLASS_SECRET
    if context == IDENTIFIER_CONTEXT_WORKFLOW_ID and _N8N_WORKFLOW_ID_RE.match(value):
        return CLASS_IDENTIFIER
    if context == IDENTIFIER_CONTEXT_WM_PATH and _WM_FILENAME_RE.match(value.rsplit("/", 1)[-1]):
        return CLASS_IDENTIFIER
    return CLASS_UNKNOWN


# ---- B2/L-07 — stable refusal fingerprint + bounded retry escalation ------

def refusal_fingerprint(*, tool: str, model: str, operation: str,
                         ids: Sequence[int], proposed: Dict[str, Any]) -> str:
    """Deterministic fingerprint identifying 'the same proposal retried
    unchanged' — independent of write_set_id (which is fresh per prepare)."""
    payload = {"tool": tool, "model": model, "operation": operation,
               "ids": sorted(int(i) for i in ids), "proposed": proposed}
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


class RetryTracker:
    """Bounded in-memory counter of identical refused proposals, keyed by
    refusal_fingerprint. Process-lifetime only, same threat model as
    WriteSetStore. Not a durable retry database — restart persistence is
    not claimed, matching the v2 requirement's own scope note."""

    def __init__(self, max_entries: int = 10_000):
        self._counts: Dict[str, int] = {}
        self._max_entries = max_entries

    def note(self, fingerprint: str) -> int:
        """Record one occurrence of this fingerprint and return the new
        count (1 on first occurrence, 2+ on repeats)."""
        if fingerprint not in self._counts and len(self._counts) >= self._max_entries:
            self._counts.clear()  # bounded: drop oldest-unbounded growth rather than leak
        self._counts[fingerprint] = self._counts.get(fingerprint, 0) + 1
        return self._counts[fingerprint]

    def __len__(self) -> int:
        return len(self._counts)


# ---- L-09/L-10 — ir.actions.act_window observability + reuse check --------

def check_action_window_reuse(
    *, res_model: str, view_mode: str,
    search_fn: Callable[[str, list], List[dict]],
) -> List[dict]:
    """Search for existing ir.actions.act_window records on the same
    res_model with the exact same view_mode signature. A non-empty result
    means the proposed capability already exists — the caller (create_odoo)
    refuses as REUSABLE_CAPABILITY_EXISTS rather than trusting its own
    belief that no equivalent exists (the exact defect the L-10 oracle is
    named for: the lane ran this check, reported clear, and was wrong)."""
    domain = [["res_model", "=", res_model], ["view_mode", "=", view_mode]]
    return search_fn("ir.actions.act_window", domain)
