"""
Registry of the 10 view profiles the dispatch requires: enterprise, psa,
three_by_three_by_three, nine_verbs, mesh, signal_to_asset,
service_pattern_method_canonical, work_object_queue, n8n_topology (+ the
n8n_workflow_detail variant for a single workflow), and odoo_app_menu_object.

Every profile here just loads a JSON file conforming to schema/graph_schema.json
from fixtures/ — there is no per-profile rendering logic. The one and only
renderer is compiler.canvas_compiler.compile_canvas(). This module's whole
job is "which fixture/live file backs which profile ID", which is exactly
the seam Stream A's real object/relationship JSON will slot into later
(swap the file this function loads; compile_canvas and everything downstream
is unchanged).
"""
from __future__ import annotations

import json
import pathlib

_FIXTURES_DIR = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# profile_id -> backing fixture/live-data filename (without .json)
PROFILE_SOURCE_FILE = {
    "enterprise": "enterprise",
    "psa": "psa",
    "three_by_three_by_three": "three_by_three_by_three",
    "nine_verbs": "nine_verbs",
    "mesh": "mesh",
    "signal_to_asset": "signal_to_asset",
    "service_pattern_method_canonical": "service_pattern_method_canonical",
    "work_object_queue": "work_object_queue",
    "n8n_topology": "n8n_topology_overview",
    "n8n_workflow_detail": "d007_workflow_topology",
    "odoo_app_menu_object": "odoo_menu_govern",
}

LIVE_PROFILES = {"n8n_topology", "n8n_workflow_detail", "odoo_app_menu_object"}
FIXTURE_PROFILES = set(PROFILE_SOURCE_FILE) - LIVE_PROFILES


def available_profiles() -> list[str]:
    return sorted(PROFILE_SOURCE_FILE.keys())


def load_profile_graph(profile_id: str) -> dict:
    if profile_id not in PROFILE_SOURCE_FILE:
        raise KeyError(
            f"UNKNOWN_VIEW_PROFILE: {profile_id!r} is not one of {sorted(PROFILE_SOURCE_FILE)}"
        )
    path = _FIXTURES_DIR / f"{PROFILE_SOURCE_FILE[profile_id]}.json"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
