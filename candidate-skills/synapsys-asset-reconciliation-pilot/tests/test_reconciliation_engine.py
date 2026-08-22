import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reconciliation_engine import (  # noqa: E402
    MATCHED,
    STALE_PROJECTION,
    UNKNOWN,
    AssetRecord,
    build_deterministic_canvas,
    detect_cycles,
    detect_duplicate_identities,
    detect_orphan_references,
    detect_self_loops,
    extract_relationship_population,
    parse_obsidian_asset_claim,
    reconcile_relationship_field,
)

# --- The exact 8-condition synthetic fixture named in this session's own
# --- discovery report (Section 4, row 9) as "constructed but nothing
# --- existed to run it against." It exists now.

FIXTURE = [
    AssetRecord(id=1, name="Asset-1", parent_id=None),          # no parent
    AssetRecord(id=2, name="Asset-2", parent_id=1),              # valid parent
    AssetRecord(id=3, name="Asset-3", parent_id=1),              # valid parent
    AssetRecord(id=4, name="Asset-4", parent_id=4),              # self-loop
    AssetRecord(id=5, name="Asset-5", parent_id=999),            # orphan reference
]
FIXTURE_CYCLE = [
    AssetRecord(id=10, name="Cyc-A", parent_id=11),
    AssetRecord(id=11, name="Cyc-B", parent_id=10),              # A<->B cycle
]
FIXTURE_DUPLICATE = [
    AssetRecord(id=1, name="Asset-1-first", parent_id=None),
    AssetRecord(id=1, name="Asset-1-duplicate", parent_id=None),  # duplicate id
]


def test_fixture_detects_self_loop():
    assert detect_self_loops(FIXTURE) == [4]


def test_fixture_detects_orphan_reference():
    assert detect_orphan_references(FIXTURE) == [(5, 999)]


def test_fixture_detects_no_false_positive_cycles_in_acyclic_data():
    assert detect_cycles(FIXTURE) == []


def test_fixture_detects_real_cycle():
    cycles = detect_cycles(FIXTURE_CYCLE)
    assert len(cycles) == 1
    assert set(cycles[0]) == {10, 11}


def test_fixture_detects_duplicate_identity():
    assert detect_duplicate_identities(FIXTURE_DUPLICATE) == [1]


def test_fixture_population_summary():
    summary = extract_relationship_population(FIXTURE)
    assert summary["total"] == 5
    # parent_id populated on 2, 3, 4, 5 (self-loop and orphan reference
    # both still count as "populated" for a raw count -- they're validity
    # defects caught separately by detect_self_loops/detect_orphan_references,
    # not absences of a value)
    assert summary["parent_populated"] == 4


def test_fixture_zero_successor_relationships_matches_stale_obsidian_baseline():
    # The 8th fixture condition: "zero successor relationships" -- this
    # session's real live re-read this same day found x_retired_to_successor_id
    # populated on 0/120 real assets, matching this synthetic condition exactly.
    no_successor_records = [
        AssetRecord(id=r.id, name=r.name, parent_id=r.parent_id, successor_id=None)
        for r in FIXTURE
    ]
    summary = extract_relationship_population(no_successor_records)
    assert summary["successor_populated"] == 0


# --- Obsidian claim parsing, against the exact phrasing found live this
# --- session in Obsidian/ASSETS_SUITE/ASSETS_SUITE_CANVAS_v0.1.canvas

STALE_CANVAS_TEXT = (
    "This canvas documents 115 live records in the Asset Register. "
    "0 of 115 assets have either field set (x_parent_asset_id or "
    "x_retired_to_successor_id)."
)


def test_parse_obsidian_asset_claim_extracts_stale_baseline():
    claim = parse_obsidian_asset_claim(STALE_CANVAS_TEXT)
    assert claim.claimed_total == 115
    assert claim.claimed_either_field_populated == 0


def test_parse_obsidian_asset_claim_returns_none_when_absent():
    claim = parse_obsidian_asset_claim("This canvas has no factual counts at all.")
    assert claim.claimed_total is None
    assert claim.claimed_either_field_populated is None


# --- Reconciliation classification

def test_reconcile_matched_when_live_and_claim_agree():
    records = [AssetRecord(id=i, name=f"A{i}", parent_id=(1 if i > 1 else None)) for i in range(1, 6)]
    claim = parse_obsidian_asset_claim("5 live records. 4 of 5 assets have either field set.")
    result = reconcile_relationship_field(
        contract_id="RECON-ASSET-PARENT",
        live_records=records,
        field_getter=lambda r: r.parent_id,
        obsidian_claim=claim,
        claimed_populated_attr="claimed_either_field_populated",
    )
    assert result.state == MATCHED


def test_reconcile_stale_projection_on_total_drift():
    # Reproduces this session's real finding: live total (120) != claimed (115)
    records = [AssetRecord(id=i, name=f"A{i}") for i in range(1, 121)]
    claim = parse_obsidian_asset_claim(STALE_CANVAS_TEXT)
    result = reconcile_relationship_field(
        contract_id="RECON-ASSET-PARENT",
        live_records=records,
        field_getter=lambda r: r.parent_id,
        obsidian_claim=claim,
        claimed_populated_attr="claimed_either_field_populated",
    )
    assert result.state == STALE_PROJECTION
    assert result.live_total == 120
    assert result.claimed_total == 115


def test_reconcile_stale_projection_on_population_drift_same_total():
    # Reproduces this session's real finding on x_parent_asset_id: claimed
    # total matches (fabricate 115 records to match the claim exactly) but
    # claimed population (0) doesn't match live population (37-equivalent).
    records = [AssetRecord(id=i, name=f"A{i}", parent_id=(1 if i <= 37 and i > 1 else None)) for i in range(1, 116)]
    claim = parse_obsidian_asset_claim(STALE_CANVAS_TEXT)  # claims 0 of 115
    result = reconcile_relationship_field(
        contract_id="RECON-ASSET-PARENT",
        live_records=records,
        field_getter=lambda r: r.parent_id,
        obsidian_claim=claim,
        claimed_populated_attr="claimed_either_field_populated",
    )
    assert result.state == STALE_PROJECTION
    assert result.live_total == claim.claimed_total == 115
    assert result.live_populated != result.claimed_populated


def test_reconcile_unknown_when_projection_makes_no_claim():
    records = [AssetRecord(id=1, name="A1")]
    claim = parse_obsidian_asset_claim("No factual counts here.")
    result = reconcile_relationship_field(
        contract_id="RECON-ASSET-PARENT",
        live_records=records,
        field_getter=lambda r: r.parent_id,
        obsidian_claim=claim,
        claimed_populated_attr="claimed_either_field_populated",
    )
    assert result.state == UNKNOWN


def test_reconcile_never_returns_matched_on_silence():
    # Guards the "no silent repair / no assumed match" discipline: an
    # UNKNOWN result must never be mistakable for MATCHED by a caller
    # that only checks truthiness.
    records = [AssetRecord(id=1, name="A1")]
    claim = parse_obsidian_asset_claim("nothing extractable")
    result = reconcile_relationship_field(
        contract_id="X", live_records=records, field_getter=lambda r: r.parent_id,
        obsidian_claim=claim, claimed_populated_attr="claimed_either_field_populated",
    )
    assert result.state != MATCHED


# --- Deterministic canvas generation

def test_canvas_uses_deterministic_governed_ids_not_ad_hoc():
    records = [
        AssetRecord(id=72, name="AST-HEEP-001", parent_id=None),
        AssetRecord(id=76, name="AST-HEEP-002", parent_id=72),
    ]
    canvas = build_deterministic_canvas(records)
    node_ids = {n["id"] for n in canvas["nodes"]}
    assert node_ids == {"AST-72", "AST-76"}
    assert canvas["edges"][0]["id"] == "REL-AST-76-PARENT-AST-72"
    # No node/edge id looks like the ad hoc "obj_01" style this session
    # found live in the real vault's ASSETS_SUITE_CANVAS_v0.1.canvas
    assert not any(nid.startswith("obj_") for nid in node_ids)


def test_canvas_is_deterministic_across_repeated_calls():
    records = [AssetRecord(id=1, name="A", parent_id=None), AssetRecord(id=2, name="B", parent_id=1)]
    assert build_deterministic_canvas(records) == build_deterministic_canvas(records)


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = (
        Path(__file__).resolve().parents[1].joinpath("reconciliation_engine.py").read_text()
    )
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules
