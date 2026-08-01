#!/usr/bin/env python3
"""
Single build entrypoint for the overnight integrated candidate.

Produces, deterministically, from the inputs captured this session:
  - generated/candidate_canvases/*.canvas   (15, adapted from the accepted suite)
  - generated/candidate_profiles/*.canvas   (11, re-derived from Lane B's fixtures)
  - fixtures_canvas_suite/*.json            (the 15 graphs, for inspection/reuse)
  - fixtures_live/*.json                    (the 11 graphs, for inspection/reuse)

Run: python3 build_overnight_candidate.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from adapters.accepted_canvas_raw_capture import parsed as parsed_accepted_canvases  # noqa: E402
from adapters.existing_canvas_adapter import adapt_accepted_canvas  # noqa: E402
from scvs.scvs_compiler import canonical_dumps, compile_canvas_scvs, load_schema_v02  # noqa: E402

LANE_B_ROOT = ROOT.parent / "lane-b-n8n-viewer-canvas-compiler"

# Real clock read taken this session (`date -u +"%Y-%m-%dT%H:%M:%SZ"`), not fabricated.
SNAPSHOT = "2026-08-01T16:48:19Z"

# Single clean path (no arrow notation) to where this build's candidate
# Architecture v1.3 is filed. Every candidate canvas/profile this build
# produces returns here, per the dispatch: "Apply replay-safe return routes
# to the single candidate Architecture v1.3 path."
V1_3_RETURN_ROUTE = (
    "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
    "WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/OVERNIGHT_STREAM_B_OUTPUT_v0.1/"
    "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"
)

# Source tag inferred deterministically from each Lane B profile's view_id —
# not invented per-object, a single rule applied uniformly.
_PROFILE_SOURCE_TAG = {
    "n8n_topology": "N8N",
    "n8n_workflow_detail": "N8N",
    "odoo_app_menu_object": "ODOO",
}


def _augment_lane_b_graph_to_v02(graph: dict) -> dict:
    """Add the OPTIONAL v0.2 fields (source_tag) to a Lane B v0.1 graph.
    Everything else is passed through untouched — this is additive, not a
    redesign of Lane B's fixtures. return_route is repointed at the v1.3
    candidate path (see V1_3_RETURN_ROUTE docstring above); snapshot is
    updated to this build's real capture time for the same reason Lane B's
    own Correction v0.1 required an honest, non-fabricated timestamp.
    """
    graph = json.loads(json.dumps(graph))  # deep copy, stdlib-only
    tag = _PROFILE_SOURCE_TAG.get(graph["view_id"])
    for obj in graph["objects"]:
        if tag:
            obj["source_tag"] = tag
    graph["snapshot"] = SNAPSHOT
    graph["return_route"] = V1_3_RETURN_ROUTE
    return graph


def build_candidate_canvas_suite(schema: dict) -> list[tuple[str, dict, dict]]:
    """Returns [(output_filename, graph, compiled_canvas), ...] for the 15
    accepted canvases, adapted then compiled through the SCVS compiler.
    """
    results = []
    accepted = parsed_accepted_canvases()
    fixtures_dir = ROOT / "fixtures_canvas_suite"
    out_dir = ROOT / "generated" / "candidate_canvases"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename in sorted(accepted.keys()):
        raw = accepted[filename]
        graph = adapt_accepted_canvas(filename, raw, V1_3_RETURN_ROUTE, SNAPSHOT)
        (fixtures_dir / f"{graph['view_id']}.json").write_text(
            json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        canvas = compile_canvas_scvs(graph, schema)
        out_name = filename.replace(".canvas", "_CANDIDATE.canvas")
        (out_dir / out_name).write_text(canonical_dumps(canvas), encoding="utf-8")
        results.append((out_name, graph, canvas))
    return results


def build_candidate_profiles(schema: dict) -> list[tuple[str, dict, dict]]:
    """Returns [(output_filename, graph, compiled_canvas), ...] for the 11
    Lane B profiles, re-derived from the already-consumed Lane B fixtures
    (lane-b-n8n-viewer-canvas-compiler/fixtures/*.json, read but NOT
    modified) with the v0.2 optional fields added and re-pointed at the
    v1.3 candidate return route.
    """
    lane_b_fixtures_dir = LANE_B_ROOT / "fixtures"
    profile_files = {
        "enterprise": "enterprise.json",
        "psa": "psa.json",
        "three_by_three_by_three": "three_by_three_by_three.json",
        "nine_verbs": "nine_verbs.json",
        "mesh": "mesh.json",
        "signal_to_asset": "signal_to_asset.json",
        "service_pattern_method_canonical": "service_pattern_method_canonical.json",
        "work_object_queue": "work_object_queue.json",
        "n8n_topology": "n8n_topology_overview.json",
        "n8n_workflow_detail": "d007_workflow_topology.json",
        "odoo_app_menu_object": "odoo_menu_govern.json",
    }
    out_name_map = {
        "n8n_topology": "N8N_OVERVIEW_CANDIDATE.canvas",
        "n8n_workflow_detail": "D007_WORKFLOW_TOPOLOGY_CANDIDATE.canvas",
    }

    results = []
    fixtures_dir = ROOT / "fixtures_live"
    out_dir = ROOT / "generated" / "candidate_profiles"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    for profile_id, fname in sorted(profile_files.items()):
        with open(lane_b_fixtures_dir / fname, "r", encoding="utf-8") as fh:
            base_graph = json.load(fh)
        graph = _augment_lane_b_graph_to_v02(base_graph)
        (fixtures_dir / fname).write_text(
            json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        canvas = compile_canvas_scvs(graph, schema)
        out_name = out_name_map.get(profile_id, f"DEMO_{profile_id.upper()}_CANDIDATE.canvas")
        (out_dir / out_name).write_text(canonical_dumps(canvas), encoding="utf-8")
        results.append((out_name, graph, canvas))
    return results


def main() -> int:
    schema = load_schema_v02()
    canvas_suite = build_candidate_canvas_suite(schema)
    profiles = build_candidate_profiles(schema)

    print(f"{'file':45} {'evidence':28} {'nodes':>6} {'edges':>6}")
    for name, graph, canvas in canvas_suite + profiles:
        print(f"{name:45} {graph['evidence']:28} {len(canvas['nodes']):6} {len(canvas['edges']):6}")
    print(f"\n{len(canvas_suite)} candidate canvases + {len(profiles)} candidate profiles = "
          f"{len(canvas_suite) + len(profiles)} total .canvas files written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
