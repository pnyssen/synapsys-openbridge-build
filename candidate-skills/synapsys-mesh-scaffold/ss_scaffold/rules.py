"""Validators for the four modules (MESH_SCAFFOLD_MODULES_v0-1). Pure functions, no I/O.

Two result kinds, kept apart:
  errors - a rule is broken (e.g. two Accountables). The module instance fails.
  gaps   - a rule is not broken but the cell is unknown or unaccepted ([n]); it does not count
           towards coverage. Unknown stays unknown: never a guessed number.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

UNKNOWN = "[n]"
SHOCKS = ("anchor_lost", "approval_delayed", "finance_shock", "community_opposition", "key_person_lost")
VERDICTS = ("keep", "reframe", "drop")
DEPENDENCE = ("none", "low", "high")
_CELL = re.compile(r"^\s*([RACID])\b(.*)$", re.S)


def _unknown(v: Any) -> bool:
    return v is None or (isinstance(v, str) and (not v.strip() or v.strip().startswith(UNKNOWN)))


def _ratio(n: int, d: int) -> Dict[str, Any]:
    return {"n": n, "of": d, "text": f"{n} of {d}"}


# --- Module 2: RACI ---------------------------------------------------------
def parse_cell(cell: Any) -> Dict[str, Any]:
    """Accepts a structured cell {"role","accepted"} or the pilot-draft string form
    ("C (proposal: ...)", "[n]", ""). A string cell is accepted only if it says so explicitly
    ('accepted') and does not say 'proposal'."""
    if isinstance(cell, dict):
        role = cell.get("role")
        return {"role": role if role in tuple("RACID") else None, "accepted": bool(cell.get("accepted"))}
    if _unknown(cell):
        return {"role": None, "accepted": False}
    m = _CELL.match(str(cell))
    if not m:
        return {"role": None, "accepted": False}
    rest = m.group(2).lower()
    return {"role": m.group(1), "accepted": ("accepted" in rest) and ("proposal" not in rest)}


def _accountable_state(row: Dict[str, Any]) -> Tuple[str, bool]:
    """Returns (accountable text or '', accepted?). Accepted needs a named party, no 'proposal'
    wording, and explicit acceptance evidence on the row."""
    acc = row.get("accountable")
    if _unknown(acc):
        return "", False
    text = acc if isinstance(acc, str) else str(acc.get("party", ""))
    proposal = "proposal" in text.lower() or (isinstance(acc, dict) and not acc.get("accepted"))
    evidenced = bool(row.get("acceptance_evidence")) and not _unknown(row.get("acceptance_evidence"))
    return text, (not proposal) and evidenced


def validate_raci(matrix: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    gaps: List[str] = []
    if _unknown(matrix.get("revision_date")):
        errors.append("matrix has no revision_date")
    covered = 0
    rows = matrix.get("rows", [])
    for row in rows:
        rid = row.get("outcome_id")
        cells = [parse_cell(c) for c in row.get("cells", [])]
        a_cells = [c for c in cells if c["role"] == "A"]
        if len(a_cells) > 1:
            errors.append(f"row {rid}: {len(a_cells)} Accountable cells (exactly one allowed)")
        acc_text, acc_ok = _accountable_state(row)
        if not acc_text and not a_cells:
            gaps.append(f"row {rid}: no Accountable named")
        if any(c["role"] == "D" for c in cells) and not row.get("decision"):
            errors.append(f"row {rid}: Decider present but no real decision recorded (decision: true)")
        proposed = [c for c in cells if c["role"] and not c["accepted"]]
        accepted_R = [c for c in cells if c["role"] == "R" and c["accepted"]]
        if acc_ok and accepted_R and not proposed and len(a_cells) <= 1:
            covered += 1
        elif acc_text and not acc_ok:
            gaps.append(f"row {rid}: Accountable is a proposal or lacks acceptance evidence")
    return {"module": "raci", "errors": errors, "gaps": gaps, "coverage": _ratio(covered, len(rows)),
            "definition": "Outcomes with one accepted Accountable, an accepted Responsible and no cell left as a proposal / all Outcomes"}


# --- Module 1: contribution test with bear case -----------------------------
def validate_contribution(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    gaps: List[str] = []
    complete = 0
    for r in rows:
        b = r.get("benefit")
        verdict = r.get("verdict")
        if verdict not in VERDICTS and not _unknown(verdict):
            errors.append(f"benefit {b}: verdict {verdict!r} not in {VERDICTS}")
        if r.get("has_target") and _unknown(r.get("bear_case")):
            errors.append(f"benefit {b}: has a target and no bear case")
        if r.get("kind") == "operational" and r.get("in_chain") and verdict != "keep":
            errors.append(f"benefit {b}: operational Benefit stays in the chain only with verdict keep")
        fields = ("counterfactual", "contribution", "evidence", "bear_case", "verdict", "owner")
        missing = [f for f in fields if _unknown(r.get(f))]
        if missing:
            gaps.append(f"benefit {b}: unknown {', '.join(missing)}")
        else:
            complete += 1
    return {"module": "contribution", "errors": errors, "gaps": gaps, "coverage": _ratio(complete, len(rows)),
            "definition": "Benefits with a complete contribution row and bear case / all Benefits"}


# --- Module 3: baselines ----------------------------------------------------
def validate_baselines(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    gaps: List[str] = []
    observed = 0
    for r in rows:
        k = r.get("id")
        val, obs = r.get("baseline"), r.get("observed")
        if val == 0 and not obs:
            errors.append(f"{k}: numeric 0 baseline without observed=true (unknown is null, never 0)")
        if obs and (val is None or _unknown(val)):
            errors.append(f"{k}: observed=true but no baseline value")
        if obs and val is not None and not _unknown(val):
            if _unknown(r.get("unit")) or _unknown(r.get("as_at")) or _unknown(r.get("source")):
                errors.append(f"{k}: observed baseline needs unit, as_at and source")
            else:
                observed += 1
        elif r.get("has_target"):
            gaps.append(f"{k}: target without an observed baseline cannot be tested")
    return {"module": "baselines", "errors": errors, "gaps": gaps, "coverage": _ratio(observed, len(rows)),
            "definition": "Outcomes and Benefits with an observed baseline / all"}


# --- Module 4: shock readiness ----------------------------------------------
def validate_shock(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    gaps: List[str] = []
    assessed = 0
    total = 0
    for r in rows:
        k = r.get("id")
        cells = r.get("shocks", {})
        for shock in SHOCKS:
            total += 1
            c = cells.get(shock)
            if not isinstance(c, dict) or _unknown(c.get("dependence")):
                gaps.append(f"{k}/{shock}: not assessed")
                continue
            dep = c.get("dependence")
            if dep not in DEPENDENCE:
                errors.append(f"{k}/{shock}: dependence {dep!r} not in {DEPENDENCE}")
                continue
            if dep == "high" and _unknown(c.get("mitigation")):
                errors.append(f"{k}/{shock}: high dependence with no mitigation")
            if shock == "key_person_lost" and dep != "none":
                if _unknown(c.get("owner")) or _unknown(c.get("successor_role")):
                    errors.append(f"{k}/{shock}: key-person dependence must name an Accountable and a successor role")
            if _unknown(c.get("evidence")):
                gaps.append(f"{k}/{shock}: assessed without evidence")
            else:
                assessed += 1
    return {"module": "shock_readiness", "errors": errors, "gaps": gaps, "coverage": _ratio(assessed, total),
            "definition": "Cells assessed with evidence / all cells"}


def validate_context(doc: Dict[str, Any]) -> Dict[str, Any]:
    """One Context document holds up to four modules. A module that is absent is reported as
    not supplied ([n]); it is never scored 0."""
    out = {}
    if "raci" in doc: out["raci"] = validate_raci(doc["raci"])
    if "contribution_test" in doc: out["contribution"] = validate_contribution(doc["contribution_test"])
    if "baselines" in doc: out["baselines"] = validate_baselines(doc["baselines"])
    if "shock_readiness" in doc: out["shock_readiness"] = validate_shock(doc["shock_readiness"])
    return out
