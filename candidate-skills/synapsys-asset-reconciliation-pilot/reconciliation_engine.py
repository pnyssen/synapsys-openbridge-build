"""Read-only cross-system reconciliation engine -- the one capability this
session's own discovery audit (`05_AI_RETURNS_HASHED/
CLAUDE_CODE_CROSS_SYSTEM_RECONCILIATION_CAPABILITY_DISCOVERY_v0.1.md`, CAP-11)
found to have zero implementation anywhere in scope, and that the
follow-on `SYNAPSYS_OBSIDIAN_MMM3CCC_ECOSYSTEM_REPOSITORY_UPGRADE_SUITE_v0.1.md`
independently named as Gate 0/WP-04/WP-05, the smallest live move.

Scope discipline, deliberately narrow:

- Pure functions only. No network, no subprocess, no file writes. The
  caller supplies already-fetched data (e.g. from a live `search_odoo`/
  `count_odoo` call, or Obsidian canvas text already read via `sp_read`) --
  this module never calls Odoo/N8N/SharePoint itself, mirroring the same
  isolation discipline as `synapsys-service-catalogue-pilot/validator.py`
  and `synapsys-obsidian-vault-write-guard/vault_write_guard.py`.
- One relationship shape only: a self-referential `many2one` field on a
  single Odoo model (the exact proof case this session's discovery audit
  used: `x_parent_asset_id` / `x_retired_to_successor_id` on
  `x_ss_asset_register`). This is NOT a general entity/relationship
  framework -- building one was explicitly out of scope for a discovery
  lane, and this module doesn't try to sneak one in under "implementation."
  Widening it to other models/fields is exactly the WP-11 "domain
  expansion" step the upgrade suite says comes *after* this pilot proves
  out, not before.
- No silent repair. `reconcile_relationship_field` only classifies; it
  never proposes or performs a correction. Per the upgrade suite's own
  Section 7.4: "No process may silently repair a discrepancy."
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


# Result states, taken directly from the upgrade suite's Section 7.4
# result-state vocabulary (a strict subset relevant to a single
# self-referential relationship field, not the full cross-entity list).
MATCHED = "MATCHED"
STALE_PROJECTION = "STALE_PROJECTION"
VALUE_CONFLICT = "VALUE_CONFLICT"
CARDINALITY_VIOLATION = "CARDINALITY_VIOLATION"
UNKNOWN = "UNKNOWN"


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class AssetRecord:
    """One row of the live extraction this session performed via
    `search_odoo(model="x_ss_asset_register", fields=["id","x_name",
    "x_parent_asset_id","x_retired_to_successor_id"])`. `parent_id`/
    `successor_id` are `None` when the m2o field is unset (Odoo's `False`),
    otherwise the target record's stable id."""

    id: int
    name: str
    parent_id: Optional[int] = None
    successor_id: Optional[int] = None


def extract_relationship_population(records: list[AssetRecord]) -> dict:
    """Pure summary of a live extraction -- total count, and how many
    records have each relationship field populated. This is CAP-07's
    output shape: a stable-ID relationship extraction, not a raw dump."""
    return {
        "total": len(records),
        "parent_populated": sum(1 for r in records if r.parent_id is not None),
        "successor_populated": sum(1 for r in records if r.successor_id is not None),
    }


# Matches the exact phrasing style this session found live in
# `Obsidian/ASSETS_SUITE/ASSETS_SUITE_CANVAS_v0.1.canvas` -- "115 live
# records", "0 of 115 assets have either field set". Intentionally narrow:
# this is the CAP-04 gap named in the discovery report ("no embedded
# factual-count extraction exists") closed just enough for this one
# reconciliation contract, not a general Obsidian-claim parser.
_TOTAL_RE = re.compile(r"(\d+)\s+live records", re.IGNORECASE)
_ZERO_OF_RE = re.compile(r"(\d+)\s+of\s+(\d+)\s+assets have either field set", re.IGNORECASE)


@dataclass
class ObsidianClaim:
    claimed_total: Optional[int] = None
    claimed_either_field_populated: Optional[int] = None
    raw_matches: list = field(default_factory=list)


def parse_obsidian_asset_claim(canvas_text: str) -> ObsidianClaim:
    """Extract the specific factual assertions this reconciliation contract
    cares about from raw canvas/note text. Returns fields as `None` when
    not found -- callers must not assume absence means zero."""
    claim = ObsidianClaim()
    m_total = _TOTAL_RE.search(canvas_text)
    if m_total:
        claim.claimed_total = int(m_total.group(1))
        claim.raw_matches.append(m_total.group(0))
    m_zero = _ZERO_OF_RE.search(canvas_text)
    if m_zero:
        claim.claimed_either_field_populated = int(m_zero.group(1))
        if claim.claimed_total is None:
            claim.claimed_total = int(m_zero.group(2))
        claim.raw_matches.append(m_zero.group(0))
    return claim


@dataclass
class ReconciliationResult:
    contract_id: str
    state: str
    detail: str
    live_total: int
    live_populated: int
    claimed_total: Optional[int]
    claimed_populated: Optional[int]


def reconcile_relationship_field(
    contract_id: str,
    live_records: list[AssetRecord],
    field_getter,
    obsidian_claim: ObsidianClaim,
    claimed_populated_attr: str,
) -> ReconciliationResult:
    """Compare a live extraction against a parsed Obsidian assertion for
    ONE relationship field and classify the result. `field_getter` is a
    callable `AssetRecord -> Optional[int]` (e.g. `lambda r: r.parent_id`)
    so this same function serves both `x_parent_asset_id` and
    `x_retired_to_successor_id` without duplicating logic per field.
    `claimed_populated_attr` names which `ObsidianClaim` attribute holds
    the count to compare against for this field."""
    live_total = len(live_records)
    live_populated = sum(1 for r in live_records if field_getter(r) is not None)
    claimed_total = obsidian_claim.claimed_total
    claimed_populated = getattr(obsidian_claim, claimed_populated_attr, None)

    if claimed_total is None or claimed_populated is None:
        return ReconciliationResult(
            contract_id=contract_id,
            state=UNKNOWN,
            detail="Obsidian projection made no extractable claim for this field "
            "-- cannot reconcile against silence. Not treated as MATCHED.",
            live_total=live_total,
            live_populated=live_populated,
            claimed_total=claimed_total,
            claimed_populated=claimed_populated,
        )

    if live_total != claimed_total:
        return ReconciliationResult(
            contract_id=contract_id,
            state=STALE_PROJECTION,
            detail=f"Record count drifted: projection claims {claimed_total} total, "
            f"live source has {live_total}. Population comparison is unreliable "
            "against a stale denominator.",
            live_total=live_total,
            live_populated=live_populated,
            claimed_total=claimed_total,
            claimed_populated=claimed_populated,
        )

    if live_populated != claimed_populated:
        return ReconciliationResult(
            contract_id=contract_id,
            state=STALE_PROJECTION,
            detail=f"Population count drifted: projection claims {claimed_populated} "
            f"of {claimed_total}, live source has {live_populated} of {live_total}.",
            live_total=live_total,
            live_populated=live_populated,
            claimed_total=claimed_total,
            claimed_populated=claimed_populated,
        )

    return ReconciliationResult(
        contract_id=contract_id,
        state=MATCHED,
        detail=f"Live source and projection agree: {live_populated} of {live_total}.",
        live_total=live_total,
        live_populated=live_populated,
        claimed_total=claimed_total,
        claimed_populated=claimed_populated,
    )


def detect_self_loops(records: list[AssetRecord]) -> list[int]:
    """IDs of records whose parent_id points at themselves -- prohibited
    per the upgrade suite's relationship-type declaration
    (`self_reference_allowed: false`). Pure, no external graph library
    needed for this (networkx is not installed in this environment,
    confirmed by the earlier discovery audit; a single-field self-loop
    check doesn't need one)."""
    return [r.id for r in records if r.parent_id == r.id]


def detect_cycles(records: list[AssetRecord]) -> list[list[int]]:
    """Detect parent-chain cycles (A parent of B, B parent of A, or longer)
    via plain DFS -- prohibited per `acyclic: true` in the relationship
    type declaration. Returns each distinct cycle found, as the ordered
    list of ids in the cycle."""
    parent_of = {r.id: r.parent_id for r in records}
    cycles: list[list[int]] = []
    seen_in_cycle: set[int] = set()

    for start in parent_of:
        if start in seen_in_cycle:
            continue
        path: list[int] = []
        visited_this_walk: dict[int, int] = {}
        node = start
        while node is not None and node in parent_of:
            if node in visited_this_walk:
                cycle_start_index = visited_this_walk[node]
                cycle = path[cycle_start_index:]
                if len(cycle) > 1 and set(cycle) not in [set(c) for c in cycles]:
                    cycles.append(cycle)
                seen_in_cycle.update(cycle)
                break
            visited_this_walk[node] = len(path)
            path.append(node)
            node = parent_of.get(node)
    return cycles


def detect_duplicate_identities(records: list[AssetRecord]) -> list[int]:
    """IDs that appear more than once in the same extraction -- a data-
    integrity defect (DUPLICATE_IDENTITY per the upgrade suite's Section
    7.4 result-state vocabulary), not a valid relationship state."""
    seen: dict[int, int] = {}
    for r in records:
        seen[r.id] = seen.get(r.id, 0) + 1
    return [rid for rid, count in seen.items() if count > 1]


def detect_orphan_references(records: list[AssetRecord]) -> list[tuple[int, int]]:
    """(record_id, missing_parent_id) pairs where a record's parent_id
    points at an id that doesn't exist anywhere in the extraction --
    a broken reference (UNRESOLVED_LINEAGE), distinct from a record that
    simply has no parent at all."""
    known_ids = {r.id for r in records}
    orphans = []
    for r in records:
        if r.parent_id is not None and r.parent_id not in known_ids:
            orphans.append((r.id, r.parent_id))
    return orphans


def build_deterministic_canvas(records: list[AssetRecord]) -> dict:
    """Produce a JSON Canvas document (nodes/edges) with deterministic IDs
    derived from governed Odoo record IDs, per the upgrade suite's Section
    6.2 -- `node: AST-SS-001` / `edge: REL-...`, never an ad hoc `obj_01`.
    Pure data transform; does not write anywhere."""
    nodes = []
    edges = []
    for r in records:
        node_id = f"AST-{r.id}"
        nodes.append(
            {
                "id": node_id,
                "type": "text",
                "text": f"{r.name}\n(id={r.id})",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 60,
            }
        )
    for r in records:
        if r.parent_id is not None:
            edge_id = f"REL-AST-{r.id}-PARENT-AST-{r.parent_id}"
            edges.append(
                {
                    "id": edge_id,
                    "fromNode": f"AST-{r.id}",
                    "toNode": f"AST-{r.parent_id}",
                    "label": "parent_of | 0..* <-> 0..1 | MATCHED | Odoo",
                }
            )
    return {"nodes": nodes, "edges": edges}
