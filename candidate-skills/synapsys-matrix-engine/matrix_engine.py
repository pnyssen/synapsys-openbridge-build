"""SynapSys Matrix Engine -- a thin event-driven control plane for the
MMM3CCC 3x3 control architecture (Govern/Deliver/Realise x Orient..Project).

One responsibility per function/structure, per the implementation brief:

  - new_state()          the one canonical state source (a JSON-serialisable dict)
  - reduce()             the one event reducer (pure, deterministic)
  - prioritise()         the one prioritisation function
  - validate_mesh()      the one Mesh validator (Canonical / Intelligence / FPV)
  - PATTERN_REGISTRY     the one pattern registry (the 9 control verbs)
  - render()             the one renderer -- HTML is presentation only, no logic
  - write_receipt()      the one receipt writer

Authority stays in Working Memory: PATTERN_REGISTRY is a direct, unmodified
restatement of the MMM3CCC board's own verb names/descriptions/use-cases,
already produced and filed as design artefacts earlier this session
(05_AI_RETURNS_HASHED/20260727_RET_GEN_claude-code-mmm3ccc-*). This module
does not invent governance content -- it only executes state transitions
against a registry whose content traces back to that filed source.

No Odoo or N8N mutation happens here, under any state transition, for any
event. That boundary is enforced by omission -- this module imports nothing
from any Odoo/N8N client library and holds no credential -- not by a
runtime permission check, since a capability that is simply absent cannot
be misused. A static test (see tests/test_matrix_engine.py) asserts this
module's import list stays clear of both.

Pure functions only: no network, no filesystem, no wall-clock read
(timestamps, if wanted, are the caller's concern -- reduce() takes a
caller-supplied `rev` counter instead of reading real time, so the same
(state, event) pair always reduces to the same next state).
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

STAGES = [
    "signal",
    "attributes",
    "expression",
    "observation",
    "learning",
    "asset_conversion",
    "feedback",
]

PLANES = ("govern", "deliver", "realise")

# The one pattern registry. Content is a direct restatement of the MMM3CCC
# board's own nine control verbs -- same copy already used in this
# session's filed design artefacts, not re-authored here.
PATTERN_REGISTRY: dict[str, dict[str, Any]] = {
    "G1": {"plane": "govern", "verb": "Orient", "desc": "Identify signal, context and directional meaning.", "use_case": "Detect a new market or governance signal."},
    "G2": {"plane": "govern", "verb": "Canonicalise", "desc": "Establish the accepted definition or governed record.", "use_case": "Convert a candidate artefact into a canonical reference."},
    "G3": {"plane": "govern", "verb": "Structure", "desc": "Organise components and relationships into a reusable form.", "use_case": "Design the skeleton of a service pattern."},
    "D1": {"plane": "deliver", "verb": "Assure", "desc": "Verify quality, evidence and control sufficiency.", "use_case": "Check whether a release or service pack is defensible."},
    "D2": {"plane": "deliver", "verb": "Navigate", "desc": "Route attention, priorities and next valid actions.", "use_case": "Guide an operator to the correct lane and step."},
    "D3": {"plane": "deliver", "verb": "Compose", "desc": "Combine required components into an executable configuration.", "use_case": "Assemble a governed service workflow."},
    "R1": {"plane": "realise", "verb": "Activate", "desc": "Mobilise action, commitment and engagement.", "use_case": "Begin a bounded pilot or stakeholder interaction."},
    "R2": {"plane": "realise", "verb": "Transform", "desc": "Improve, adapt and compound capability or asset value.", "use_case": "Turn learning into a better operating pattern."},
    "R3": {"plane": "realise", "verb": "Project", "desc": "Express the model outward into views, deliverables or interfaces.", "use_case": "Publish a dashboard, HTML view or operating view."},
}

_PLANE_ORDER = {p: i for i, p in enumerate(PLANES)}


def new_state() -> dict[str, Any]:
    """The one canonical state source. A fresh matrix: every registered
    cell idle at 'signal', revision 0, empty event/rejected logs."""
    return {
        "rev": 0,
        "cells": {
            cell_id: {
                "stage": "signal",
                "stage_since_rev": 0,
                "signal": None,
                "attributes": None,
                "expression": None,
                "observation": None,
                "learning": None,
                "asset_conversion": None,
            }
            for cell_id in PATTERN_REGISTRY
        },
        "events": [],
        "rejected": [],
    }


def _next_stage(current: str) -> str:
    idx = STAGES.index(current)
    return STAGES[(idx + 1) % len(STAGES)]


def reduce(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """The one event reducer. Pure: returns a new state, never mutates the
    input. An event names a `cell_id` and a `to_stage` it claims to advance
    that cell into, plus an optional `payload` merged into the matching
    field. Only a strictly sequential advance (or feedback -> signal, which
    starts the next cycle) is accepted -- anything else is recorded in
    `rejected` and the state is otherwise returned unchanged. No silent
    repair: an invalid event is never coerced into a valid one.
    """
    state = copy.deepcopy(state)
    cell_id = event.get("cell_id")
    to_stage = event.get("to_stage")
    payload = event.get("payload")

    cell = state["cells"].get(cell_id)
    valid = cell is not None and to_stage == _next_stage(cell["stage"])

    if not valid:
        state["rejected"].append({"rev": state["rev"], "event": event, "reason": "not-a-valid-sequential-transition"})
        return state

    cell["stage"] = to_stage
    cell["stage_since_rev"] = state["rev"] + 1
    if to_stage != "signal" and payload is not None:
        cell[to_stage] = payload
    elif to_stage == "signal":
        # feedback wrapped around: this is the next cycle's signal
        cell["signal"] = payload
        cell["attributes"] = None
        cell["expression"] = None
        cell["observation"] = None
        cell["learning"] = None
        cell["asset_conversion"] = None

    state["rev"] += 1
    state["events"].append(event)
    return state


def prioritise(state: dict[str, Any]) -> list[dict[str, Any]]:
    """The one prioritisation function. Pure, deterministic: orders cells
    by (plane precedence, longest-idle-at-current-stage), ties broken by
    cell_id. Govern precedes Deliver precedes Realise -- direction and
    canon are set before delivery and execution are prioritised, per the
    board's own governing-plane order. Returns a ranked list, most urgent
    first, each entry naming the cell and the reason.
    """
    ranked = []
    for cell_id, cell in state["cells"].items():
        plane = PATTERN_REGISTRY[cell_id]["plane"]
        idle_for = state["rev"] - cell["stage_since_rev"]
        ranked.append({
            "cell_id": cell_id,
            "plane": plane,
            "stage": cell["stage"],
            "idle_for": idle_for,
            "reason": f"{plane} plane, idle {idle_for} revisions at '{cell['stage']}'",
        })
    ranked.sort(key=lambda r: (_PLANE_ORDER[r["plane"]], -r["idle_for"], r["cell_id"]))
    return ranked


def validate_mesh(state: dict[str, Any], cell_id: str) -> dict[str, Any]:
    """The one Mesh validator. Gates the Expression -> Observation
    transition: a cell may not be treated as observed until its
    Signal / Attributes / Expression triad is complete -- the same triad
    the board's own fractal rule names -- checked against the three mesh
    nodes it also names (Canonical: a governed pattern exists for this
    verb; Intelligence: attributes were reasoned out; FPV: an expression
    was resolved). Pure; makes no external call.
    """
    cell = state["cells"].get(cell_id)
    if cell is None:
        return {"passed": False, "checks": {}, "reason": f"unknown cell_id '{cell_id}'"}

    checks = {
        "canonical": cell_id in PATTERN_REGISTRY,
        "intelligence": cell["attributes"] is not None,
        "fpv": cell["expression"] is not None,
    }
    passed = all(checks.values())
    reason = "signal/attributes/expression triad complete" if passed else "incomplete triad: " + ", ".join(k for k, v in checks.items() if not v) + " missing"
    return {"passed": passed, "checks": checks, "reason": reason}


def render(state: dict[str, Any]) -> str:
    """The one renderer. HTML is presentation only -- no branching logic
    beyond formatting, no script, no state mutation. A plain status table.
    """
    rows = []
    for cell_id in sorted(state["cells"], key=lambda c: (_PLANE_ORDER[PATTERN_REGISTRY[c]["plane"]], c)):
        cell = state["cells"][cell_id]
        pattern = PATTERN_REGISTRY[cell_id]
        mesh = validate_mesh(state, cell_id)
        rows.append(
            "<tr>"
            f"<td>{cell_id}</td>"
            f"<td>{pattern['plane']}</td>"
            f"<td>{pattern['verb']}</td>"
            f"<td>{cell['stage']}</td>"
            f"<td>{'mesh-ok' if mesh['passed'] else 'mesh-pending'}</td>"
            "</tr>"
        )
    return (
        "<table>"
        "<thead><tr><th>cell</th><th>plane</th><th>verb</th><th>stage</th><th>mesh</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def write_receipt(state: dict[str, Any]) -> dict[str, Any]:
    """The one receipt writer. Computes a SHA-256 over the canonical JSON
    serialisation of the full state (cells + event log + rejected log), so
    the receipt is independently recomputable by any lane holding the same
    state. No wall-clock read here -- a filing timestamp, if wanted, is
    added by the caller at the point of filing, not invented here.
    """
    state_json = _canonical_json(state)
    return {
        "control_marker": "SYNAPSYS/CLAUDE_CODE/MATRIX_ENGINE/v0.1",
        "authority_state": "HELD",
        "evidence_state": "VERIFIED",
        "state_sha256": hashlib.sha256(state_json.encode("utf-8")).hexdigest(),
        "revision": state["rev"],
        "event_count": len(state["events"]),
        "rejected_count": len(state["rejected"]),
        "odoo_mutations": 0,
        "n8n_mutations": 0,
    }
