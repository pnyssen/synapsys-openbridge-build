"""One-off runner: feeds this session's already-fetched, real live data
through `reconciliation_engine.py` and prints the actual result.

Not a live tool -- the data below is a verbatim copy of two things this
session already read this session via genuine read-only calls:

1. `search_odoo(model="x_ss_asset_register", fields=["id","x_name",
   "x_parent_asset_id","x_retired_to_successor_id"], limit=1000)` --
   all 120 real records.
2. The real text found in `Obsidian/ASSETS_SUITE/ASSETS_SUITE_CANVAS_v0.1.canvas`
   via `sp_read`, asserting "115 live records" and "0 of 115 assets have
   either field set."

Re-running this script performs no network calls -- it replays already-
captured evidence through the new engine. A true second live run (calling
search_odoo again) is the actual replay step named in the receipt below,
and would need to be executed in a session with live tool access.
"""

from reconciliation_engine import (
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

# Verbatim from this session's live search_odoo call, 2026-07-24.
_RAW = [
    (8, "AST-AVA-X-001", None), (9, "AST-AVA-Y-001", None), (10, "AST-UNL-X-001", None),
    (59, "AST-PRG-SS-001-X", None), (60, "AST-PRG-SS-001-Y", None), (61, "AST-PRG-SS-001-Z", None),
    (65, "AST-PRG-UNL-00-X", None), (66, "AST-PRG-UNL-00-Y", None), (67, "AST-PRG-UNL-00-Z", None),
    (72, "AST-HEEP-001", None), (76, "AST-HEEP-002", 72), (77, "AST-HEEP-003", 76),
    (78, "AST-HEEP-004", 100), (80, "AST-HEEP-005", None), (82, "AST-HEEP-006", 80),
    (85, "AST-HEEP-007", 72), (87, "AST-HEEP-008", 100), (88, "AST-HEEP-009", 78),
    (90, "AST-HEEP-010", 88), (91, "AST-HEEP-011", 76), (97, "AST-HEEP-012", 76),
    (98, "AST-HEEP-013", 78), (99, "AST-HEEP-014", 72), (100, "AST-HEEP-015", 72),
    (101, "AST-HEEP-016", 87), (102, "AST-HEEP-017", 82), (103, "AST-SS-DEL-001", None),
    (104, "AST-SS-DEL-002", None), (105, "AST-SS-DEL-003", None), (106, "AST-SS-DEL-004", None),
    (107, "AST-SS-DEL-005", None), (111, "AST-VU-HEALTH-001", None), (112, "AST-SS-DEL-006-BASELINE", None),
    (113, "AST-VU-TRANSPORT-001", None), (116, "AST-AVA-UPLIFT-001-Y", None), (132, "AST-CR179-X", 136),
    (133, "AST-CR179-Y", None), (134, "AST-CR179-Z", None), (135, "AST-CR180-Y", None),
    (136, "AST-CR180-X", None), (137, "AST-CR180-Z", None), (138, "AST-DEL-CONSOL-001-Y", None),
    (139, "AST-CR181-X", None), (143, "AST-CR-COLLIS-001-X", None), (144, "AST-PORTAL-R1-VFY-Y", 145),
    (145, "AST-PORTAL-R1-SCOPE-X", None), (146, "AST-CR183-Z", 145), (148, "AST-EDIM-COV-VER-Y-001", None),
    (149, "AST-CR185-Y", None), (150, "AST-CR185-Z", 149), (152, "AST-SS-SOP-LINKAGE-COVERAGE-X", None),
    (153, "AST-SS-SOP-BINDING-PATTERN-Y", None), (154, "AST-SS-CR-186-SOP-LINKAGE-TRACE-Z", 152),
    (156, "AST-CR187-X", None), (157, "AST-CR187-Z", 156), (158, "AST-VU-METHOD-PACK-001-Y", None),
    (161, "AST-CR189-Z", 163), (162, "AST-CR188-Y", None), (163, "AST-CR189-X", None),
    (164, "AST-CR188-Z", 162), (165, "AST-CR189-Z2", 163), (166, "AST-CR190-Z", 167),
    (167, "AST-CR190-Y", None), (168, "AST-CR190-X", 167), (172, "AST-CR191-Y", None),
    (174, "AST-CR192-X", None), (175, "AST-CR192-Y", None), (176, "AST-CR192-Z", None),
    (177, "AST-CR194-X", None), (178, "AST-CR194-Y", None), (179, "AST-CR194-Z", None),
    (180, "AST-CR195-X", None), (181, "AST-CR195-Y", None), (182, "AST-CR195-Z", None),
    (189, "AST-CR196-X", None), (190, "AST-CR196-Y", None), (191, "AST-CR196-Z", None),
    (192, "AST-CR197-X", None), (193, "AST-CR197-Z", 192), (200, "AST-CR193-X", 106),
    (201, "AST-CR193-Y", None), (202, "AST-CR193-Z", 106), (203, "AST-CR198-X", None),
    (204, "AST-CR198-Y", None), (205, "AST-CR198-Z", None), (206, "AST-CR200-Y", None),
    (207, "AST-CR200-Z", None), (211, "AST-CR202-X", None), (212, "AST-CR202-Y", None),
    (213, "AST-CR202-Z", None), (214, "AST-CR201-Y", None), (215, "AST-CR201-Z", 214),
    (218, "AST-CR205-Y", None), (219, "AST-CR205-Z", 218), (232, "AST-CR203-X", None),
    (233, "AST-CR203-Y", None), (234, "AST-CR203-Z", None), (235, "AST-CR216-Y", None),
    (236, "AST-CR217-Y", None), (237, "AST-CR217-Z", None), (238, "AST-CR218-Z", None),
    (239, "AST-UX-WAVE-001-X", None), (242, "AST-CR219-Y", None), (243, "AST-CR219-Z", 242),
    (269, "AST-CR220-Y", None), (270, "AST-CR220-Z", None), (271, "AST-CR221-Y", None),
    (272, "AST-CR221-Z", None), (273, "AST-CR222-Y", None), (274, "AST-CR222-Z", 273),
    (317, "AST-CR238-Y", None), (318, "AST-CR238-Z", 317), (351, "AST-HEEP-017-EVD-B", 102),
    (352, "AST-CR190-Z-EVD-B", 167), (353, "AST-CR190-X-EVD-B", 167), (358, "AST-FMYC-CAP-001-Y", None),
    (359, "AST-FMYC-REL-001-X", None), (363, "AST-CR216-X", None), (364, "AST-CR216-Z", None),
    (365, "AST-CR218-Y", None),
]

LIVE_RECORDS = [AssetRecord(id=i, name=n, parent_id=p) for i, n, p in _RAW]

REAL_CANVAS_TEXT = (
    "115 live records. 0 of 115 assets have either field set "
    "(x_parent_asset_id or x_retired_to_successor_id)."
)


def main():
    assert len(LIVE_RECORDS) == 120, f"expected 120, got {len(LIVE_RECORDS)}"

    summary = extract_relationship_population(LIVE_RECORDS)
    claim = parse_obsidian_asset_claim(REAL_CANVAS_TEXT)

    parent_result = reconcile_relationship_field(
        contract_id="RECON-ASSET-PARENT-001",
        live_records=LIVE_RECORDS,
        field_getter=lambda r: r.parent_id,
        obsidian_claim=claim,
        claimed_populated_attr="claimed_either_field_populated",
    )

    self_loops = detect_self_loops(LIVE_RECORDS)
    cycles = detect_cycles(LIVE_RECORDS)
    duplicates = detect_duplicate_identities(LIVE_RECORDS)
    orphans = detect_orphan_references(LIVE_RECORDS)

    print("=== Live summary ===")
    print(summary)
    print("=== Obsidian claim parsed ===")
    print(claim)
    print("=== Reconciliation result (x_parent_asset_id) ===")
    print(parent_result)
    print("=== Integrity checks on real production data ===")
    print("self_loops:", self_loops)
    print("cycles:", cycles)
    print("duplicate_identities:", duplicates)
    print("orphan_references:", orphans)

    canvas = build_deterministic_canvas(LIVE_RECORDS)
    print("=== Generated canvas ===")
    print(f"{len(canvas['nodes'])} nodes, {len(canvas['edges'])} edges")
    return summary, claim, parent_result, self_loops, cycles, duplicates, orphans, canvas


if __name__ == "__main__":
    main()
