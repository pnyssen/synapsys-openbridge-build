"""Job Contract -- the transport schema for work items relayed between
SynapSys AI lanes (this lane <-> Navigator <-> other lanes). Component
5.3 of the filed design
(05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
20260814--claude-code--design-candidate--synapsys-agent-full-ecosystem-integration-design--v1-0.md).

DRAFT v0.1, pending Navigator field-shape reconciliation: the Navigator's
own rev-199 "Ask / Analyse" Level 2 route generates a bounded prompt from
Context/Work Object/PPV/authority/required-return fields; this lane could
not read that route's exact field shape this session (no browser access,
no direct HTML/JS read). This schema is built instead from what IS
already known and proven -- the sk07-agent-handoff 15-field work object
shape (loaded this session; SANDBOX/TEST ONLY candidate skill,
RUNTIME_ACTIVATION=NO -- its shape is reused here as a well-specified
template, not as an authorising mechanism) -- and should be reconciled
against the Navigator's actual field shape once shared, not treated as
final.

Pure schema + validation only: no network, no filesystem, no subprocess,
no wall-clock call. Callers supply all timestamps and I/O results.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

PROCESSOR_VALUES = (
    "gpt", "fable", "codex", "claude_code", "subagent",
    "gemini_d009", "n8n", "odoo", "human",
)

STATUS_VALUES = ("proposed", "active", "blocked", "returned", "closed")

# The ACB closed enum -- the five-lane classification (OpenBridge
# runtime-control / Platform Capability Activation / Evidence-Corpus /
# Model-Capability Integration / Commercial Activation) is carried as
# free text inside a rendered packet per sk07-agent-handoff, not as a
# 16th structured field here.
STREAM_VALUES = ("S1", "S2", "S3", "openbridge", "platform-capability")

DISTRIBUTION_CLASS_VALUES = ("centre", "mid", "edge")

# Reused verbatim from sk07-agent-handoff v0.4's own role table so this
# module doesn't quietly drift from it -- re-derive from a fresh skill
# read if the two ever disagree, not patched from assumption here.
PROCESSOR_ROLE_TABLE = {
    "gpt": {
        "may": ("arbitrate", "route", "sequence", "reconcile", "challenge", "produce next-step packets"),
        "must_not": ("execute", "mutate", "approve", "infer authority"),
    },
    "fable": {
        "may": ("produce governed artefacts", "schemas", "packets", "specs", "work orders", "scorecards", "candidate plans"),
        "must_not": ("approve", "mutate", "deploy", "promote canon", "infer authority"),
    },
    "codex": {
        "may": ("verify evidence reality read-only", "inspect files/repos/connectors", "compute hashes", "compare implementation claims", "return gaps"),
        "must_not": ("design", "mutate", "approve", "deploy", "infer authority"),
    },
    "gemini_d009": {
        "may": ("challenge", "contradict", "detect false readiness", "propose disconfirming tests"),
        "must_not": ("approve", "repair", "produce", "adjudicate its own challenges"),
    },
    "claude_code": {
        "may": ("file/repo/workspace execution", "structured file production", "technical validation under explicit packet"),
        "must_not": ("approve", "mutate systems-of-record without Gate F/CR authority", "infer authority"),
    },
    "subagent": {
        "may": ("execute one bounded read/draft task under its orchestrator's packet",),
        "must_not": ("file", "mutate", "emit authority language", "expand scope", "spawn further agents"),
    },
    "n8n": {
        "may": ("execute deterministic authorised workflows",),
        "must_not": ("interpret", "approve", "expand scope"),
    },
    "odoo": {
        "may": ("act as operational system of record when authorised",),
        "must_not": ("be treated as approval authority",),
    },
    "human": {
        "may": ("approve", "reject", "hold", "redirect", "grant explicit authority within scope"),
        "must_not": (),
    },
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobContract:
    """The 15-field work object, per sk07-agent-handoff's shape. Closed-
    vocabulary fields are not enforced by the type system -- a caller can
    still construct an out-of-vocabulary instance so validate_job_contract()
    can report the exact error, rather than a raw exception at
    construction time."""
    work_object_id: str
    origin_signal: str
    stream: str
    owner: str
    processor: str
    processor_route: str
    distribution_class: str
    authority_state: str
    evidence_state: str
    filing_state: str
    return_packet: str
    next_valid_action: str
    exception_route: str
    replay_hash: str
    status: str


def role_table_for(processor: str) -> Optional[dict]:
    return PROCESSOR_ROLE_TABLE.get(processor)


def compute_replay_hash(job: JobContract) -> str:
    """SHA-256 of the canonical (sorted-key) JSON serialisation of the
    work object, per sk07-agent-handoff's own rule: 'replay_hash = SHA-256
    of the serialised work object at send.' Excludes the replay_hash field
    itself -- a field cannot hash itself; callers set replay_hash to this
    function's output after constructing the rest of the object."""
    payload = asdict(job)
    payload.pop("replay_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_MULTI_ACTION_MARKERS = (";", " and then ", "\n2.", "\n2)", "\n1. ", "\n1)")


def looks_like_multiple_actions(next_valid_action: str) -> bool:
    """Heuristic only, per sk07-agent-handoff's 'Plural -> HOLD (split
    into multiple handoffs)' rule. Flags likely multi-action text for a
    human/caller to actually judge -- this function does not itself
    reject anything; validate_job_contract() decides what to do with the
    flag."""
    text = next_valid_action.lower()
    return any(marker in text for marker in _MULTI_ACTION_MARKERS)


def validate_job_contract(job: JobContract) -> ValidationResult:
    errors: List[str] = []

    if not job.work_object_id.strip():
        errors.append("work_object_id must not be empty (HOLD per sk07: missing work_object_id)")

    if job.processor not in PROCESSOR_VALUES:
        errors.append(
            f"processor '{job.processor}' is outside the closed vocabulary "
            f"{PROCESSOR_VALUES} (HOLD per sk07: enum outside closed vocabulary)"
        )

    if job.status not in STATUS_VALUES:
        errors.append(
            f"status '{job.status}' is outside the closed vocabulary "
            f"{STATUS_VALUES} (HOLD per sk07: enum outside closed vocabulary)"
        )

    if job.stream not in STREAM_VALUES:
        errors.append(
            f"stream '{job.stream}' is outside the closed vocabulary "
            f"{STREAM_VALUES} (HOLD per sk07: enum outside closed vocabulary)"
        )

    if job.distribution_class not in DISTRIBUTION_CLASS_VALUES:
        errors.append(
            f"distribution_class '{job.distribution_class}' is outside the "
            f"closed vocabulary {DISTRIBUTION_CLASS_VALUES} (HOLD per sk07: "
            f"enum outside closed vocabulary)"
        )

    if not job.next_valid_action.strip():
        errors.append("next_valid_action must not be empty (HOLD per sk07: zero next_valid_action)")
    elif looks_like_multiple_actions(job.next_valid_action):
        errors.append(
            "next_valid_action looks like it names more than one action "
            "(HOLD per sk07: plural next_valid_action -> split into "
            "multiple handoffs); this is a heuristic flag for a human to "
            "judge, not a hard structural determination"
        )

    if not job.authority_state.strip():
        errors.append("authority_state must not be empty (HOLD per sk07: indeterminable mandatory field)")

    if not job.evidence_state.strip():
        errors.append("evidence_state must not be empty (HOLD per sk07: indeterminable mandatory field)")

    if not job.replay_hash.strip():
        errors.append(
            "replay_hash must not be empty (HOLD per sk07: uncomputable "
            "replay_hash); call compute_replay_hash() before filing"
        )

    return ValidationResult(ok=not errors, errors=errors)


_AUTHORITY_GRANT_VERBS = (
    "approved for execution", "authorised to proceed",
    "granted authority", "cleared for deployment",
)


def detect_unquoted_authority_claim(authority_state: str, carries_quoted_reference: bool) -> Optional[str]:
    """Per sk07's hard default #1: 'authority_state defaults HELD, copied
    byte-unchanged unless the packet quotes a Steward/D001 decision
    reference verbatim.' Flags text that reads like an authority grant
    when the caller states no quoted reference is attached. Does not
    parse the packet for a citation itself (unreliable text-matching);
    the caller states whether a real quoted reference exists. Returns the
    matched phrase, or None if clean."""
    if carries_quoted_reference:
        return None
    text = authority_state.lower()
    for verb in _AUTHORITY_GRANT_VERBS:
        if verb in text:
            return verb
    return None


def to_dict(job: JobContract) -> dict:
    return asdict(job)


def from_dict(data: dict) -> JobContract:
    """Round-trip constructor. Raises ValueError (never silently drops or
    ignores fields) on a missing required key or an unknown extra one --
    per sk07's own 'missing skeleton field on inbound -> HOLD' rule, this
    surfaces as an exception the caller must handle, not a partial
    object."""
    expected = set(JobContract.__dataclass_fields__.keys())
    got = set(data.keys())
    missing = expected - got
    extra = got - expected
    if missing:
        raise ValueError(f"from_dict: missing required field(s): {sorted(missing)}")
    if extra:
        raise ValueError(f"from_dict: unknown field(s) present: {sorted(extra)}")
    return JobContract(**data)
