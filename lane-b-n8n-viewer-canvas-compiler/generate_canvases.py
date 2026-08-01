#!/usr/bin/env python3
"""
Deterministic CLI: compile every view profile in compiler/view_profiles.py
into generated/<PROFILE>.canvas, and verify each is valid Obsidian JSON
Canvas + passes the same schema/link/authority checks compile_canvas()
enforces at compile time (already fail-closed there — this script's own
value is producing the on-disk artefacts and printing a summary table used
by TEST_REPORT.md).

Usage: python3 generate_canvases.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from compiler.canvas_compiler import canonical_dumps, compile_canvas, load_schema
from compiler.view_profiles import available_profiles, load_profile_graph

GENERATED_DIR = pathlib.Path(__file__).resolve().parent / "generated"

# profile_id -> output filename (the two REQUIRED deliverables get the exact
# names the dispatch asked for; the rest are demonstration canvases proving
# every profile goes through the one compiler)
OUTPUT_NAME = {
    "n8n_topology": "N8N_OVERVIEW.canvas",
    "n8n_workflow_detail": "D007_WORKFLOW_TOPOLOGY.canvas",
    "enterprise": "DEMO_ENTERPRISE.canvas",
    "psa": "DEMO_PSA.canvas",
    "three_by_three_by_three": "DEMO_3X3X3.canvas",
    "nine_verbs": "DEMO_NINE_VERBS.canvas",
    "mesh": "DEMO_MESH.canvas",
    "signal_to_asset": "DEMO_SIGNAL_TO_ASSET.canvas",
    "service_pattern_method_canonical": "DEMO_SERVICE_PATTERN_METHOD_CANONICAL.canvas",
    "work_object_queue": "DEMO_WORK_OBJECT_QUEUE.canvas",
    "odoo_app_menu_object": "DEMO_ODOO_APP_MENU_OBJECT.canvas",
}


def main() -> int:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    schema = load_schema()
    rows = []
    for profile_id in available_profiles():
        graph = load_profile_graph(profile_id)
        canvas = compile_canvas(graph, schema)
        out_path = GENERATED_DIR / OUTPUT_NAME[profile_id]
        out_path.write_text(canonical_dumps(canvas), encoding="utf-8")
        rows.append(
            (
                profile_id,
                out_path.name,
                graph["evidence"],
                len(canvas["nodes"]),
                len(canvas["edges"]),
            )
        )

    print(f"{'profile':38} {'file':42} {'evidence':20} {'nodes':>6} {'edges':>6}")
    for profile_id, fname, evidence, n_nodes, n_edges in rows:
        print(f"{profile_id:38} {fname:42} {evidence:20} {n_nodes:6} {n_edges:6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
