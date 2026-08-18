"""Job Contract -- the transport schema for work items relayed between
SynapSys AI lanes (this lane <-> Navigator <-> other lanes). Component
5.3 of the filed design
(05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
20260814--claude-code--design-candidate--synapsys-agent-full-ecosystem-integration-design--v1-0.md).

v0.2 -- RECONCILED per ChatGPT Hub's accepted integration basis
(05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
20260814--chatgpt-hub--integration-basis--evolve-view-synapsys-agent--v1-0.md,
verdict ACCEPT_AS_EVOLVE_INTEGRATION_BASIS). That response specified a
17-field merged contract extending the Navigator's own Level-2 prompt-
builder fields (TARGET LANE/ROLE/CONTEXT/WORK OBJECT/OBJECTIVE/
INSTRUCTIONS/RETURN, plus explicit PPV/authority serialization -- flagged
there as currently MISSING from the live builder) reconciled against the
v0.1 sk07-agent-handoff-derived 15-field shape "by semantics ... field
count is secondary to one semantic contract." This module is that
reconciliation: Navigator-aligned field names for the 17 core items,
sk07-heritage fields kept as named extensions where they add real value
beyond the Navigator minimum, none dropped silently.

Field-by-field mapping from v0.1 -> v0.2, for anyone diffing:
  work_object_id    -> work_object_id      (unchanged)
  origin_signal     -> origin_signal       (unchanged; distinct from the
                                             new origin_lane -- narrative
                                             reason vs. which lane filed it)
  owner             -> owner_lane          (renamed, same meaning)
  processor         -> target_lane         (renamed, same meaning;
                                             PROCESSOR_VALUES kept as
                                             TARGET_LANE_VALUES, same set)
  authority_state   -> authority_state     (unchanged)
  evidence_state    -> reality_state       (renamed; Navigator's response
                                             uses "reality_state" for this
                                             exact concept -- what's
                                             actually built vs. claimed)
  return_packet     -> required_return     (renamed; same dual usage: the
                                             expected shape before
                                             completion, the actual filed
                                             receipt path + hash after)
  next_valid_action -> next_action         (renamed, same meaning, same
                                             "exactly one" discipline)
  replay_hash       -> replay_hash         (unchanged, computed)
  status            -> status              (unchanged, same closed vocab)
  stream            -> stream              (kept as a named extension --
                                             not in Navigator's 17, still
                                             useful for ACB-style routing)
  processor_route   -> processor_route     (kept as a named extension)
  distribution_class-> distribution_class  (kept as a named extension)
  filing_state      -> filing_state        (kept as a named extension)
  exception_route   -> exception_route     (kept as a named extension)

New fields added, per Navigator's 17-field list, with no v0.1 counterpart:
  control_marker, origin_lane, role, context_id, state_revision,
  objective, source_refs, ppv_state, stop_hold, replay_validity.

Pure schema + validation only: no network, no filesystem, no subprocess,
no wall-clock call. Callers supply all timestamps and I/O results.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

TARGET_LANE_VALUES = (
    "gpt", "fable", "codex", "claude_code", "subagent",
    "gemini_d009", "n8n", "odoo", "human",
)

STATUS_VALUES = ("proposed", "active", "blocked", "returned", "closed")

# The ACB closed enum -- the five-lane classification (OpenBridge
# runtime-control / Platform Capability Activation / Evidence-Corpus /
# Model-Capability Integration / Commercial Activation) is carried as
# free text inside a rendered packet per sk07-agent-handoff, not as a
# structured field here.
STREAM_VALUES = ("S1", "S2", "S3", "openbridge", "platform-capability")

DISTRIBUTION_CLASS_VALUES = ("centre", "mid", "edge")

# Navigator's own role model (routes.json role_policy, re-verified live
# this session against the Current Navigator).
ROLE_VALUES = ("architect", "steward", "collaborator", "client")

# PPV states as actually observed in real WM filings this session --
# includes the "_HELD" suffix variant (e.g. "Potential_HELD"), not just
# the three bare stems, so validation matches real usage rather than an
# idealised vocabulary.
PPV_STEMS = ("Potential", "Probable", "Verified")

# Reused verbatim from sk07-agent-handoff v0.4's own role table so this
# module doesn't quietly drift from it -- re-derive from a fresh skill
# read if the two ever disagree, not patched from assumption here.
TARGET_LANE_ROLE_TABLE = {
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
    """The reconciled job/handoff contract -- Navigator-aligned core
    fields plus named sk07-heritage extensions. Closed-vocabulary fields
    are not enforced by the type system -- a caller can still construct
    an out-of-vocabulary instance so validate_job_contract() can report
    the exact error, rather than a raw exception at construction time."""

    # --- Navigator-aligned core (per the accepted integration basis) ---
    control_marker: str
    origin_lane: str
    target_lane: str
    role: str
    context_id: str
    work_object_id: str
    state_revision: str
    objective: str
    source_refs: str
    reality_state: str
    ppv_state: str
    authority_state: str
    owner_lane: str
    stop_hold: str
    required_return: str
    next_action: str
    replay_validity: str

    # --- sk07-heritage named extensions, kept for real value beyond the
    #     Navigator minimum ---
    origin_signal: str
    stream: str
    processor_route: str
    distribution_class: str
    filing_state: str
    exception_route: str
    status: str
    replay_hash: str


def role_table_for(target_lane: str) -> Optional[dict]:
    return TARGET_LANE_ROLE_TABLE.get(target_lane)


def compute_replay_hash(job: JobContract) -> str:
    """SHA-256 of the canonical (sorted-key) JSON serialisation of the
    contract, per sk07-agent-handoff's own rule: 'replay_hash = SHA-256
    of the serialised work object at send.' Excludes the replay_hash
    field itself -- a field cannot hash itself; callers set replay_hash
    to this function's output after constructing the rest of the
    object."""
    payload = asdict(job)
    payload.pop("replay_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_MULTI_ACTION_MARKERS = (";", " and then ", "\n2.", "\n2)", "\n1. ", "\n1)")


def looks_like_multiple_actions(next_action: str) -> bool:
    """Heuristic only, per sk07-agent-handoff's 'Plural -> HOLD (split
    into multiple handoffs)' rule. Flags likely multi-action text for a
    human/caller to actually judge -- this function does not itself
    reject anything; validate_job_contract() decides what to do with the
    flag."""
    text = next_action.lower()
    return any(marker in text for marker in _MULTI_ACTION_MARKERS)


def is_recognised_ppv_state(ppv_state: str) -> bool:
    """True if ppv_state is one of the three canonical PPV stems,
    optionally with a suffix (e.g. 'Potential_HELD', matching real usage
    observed in WM filings this session) -- not a rigid three-value
    enum, since real filings vary the suffix while keeping the stem
    meaningful."""
    return any(ppv_state == stem or ppv_state.startswith(stem + "_") for stem in PPV_STEMS)


def validate_job_contract(job: JobContract) -> ValidationResult:
    errors: List[str] = []

    if not job.work_object_id.strip():
        errors.append("work_object_id must not be empty (HOLD per sk07: missing work_object_id)")

    if not job.control_marker.strip():
        errors.append("control_marker must not be empty (Navigator integration basis: every job needs a control_marker/job_id)")

    if job.target_lane not in TARGET_LANE_VALUES:
        errors.append(
            f"target_lane '{job.target_lane}' is outside the closed vocabulary "
            f"{TARGET_LANE_VALUES} (HOLD per sk07: enum outside closed vocabulary)"
        )

    if job.role not in ROLE_VALUES:
        errors.append(
            f"role '{job.role}' is outside the closed vocabulary {ROLE_VALUES} "
            f"(Navigator role model, routes.json role_policy)"
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

    if not is_recognised_ppv_state(job.ppv_state):
        errors.append(
            f"ppv_state '{job.ppv_state}' does not match a recognised PPV stem "
            f"{PPV_STEMS} (with optional '_SUFFIX', e.g. 'Potential_HELD')"
        )

    if not job.next_action.strip():
        errors.append("next_action must not be empty (HOLD per sk07: zero next_valid_action)")
    elif looks_like_multiple_actions(job.next_action):
        errors.append(
            "next_action looks like it names more than one action "
            "(HOLD per sk07: plural next_valid_action -> split into "
            "multiple handoffs); this is a heuristic flag for a human to "
            "judge, not a hard structural determination"
        )

    if not job.authority_state.strip():
        errors.append("authority_state must not be empty (HOLD per sk07: indeterminable mandatory field)")

    if not job.reality_state.strip():
        errors.append("reality_state must not be empty (HOLD per sk07: indeterminable mandatory field)")

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
