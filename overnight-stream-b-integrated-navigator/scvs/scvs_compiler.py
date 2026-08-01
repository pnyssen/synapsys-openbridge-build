"""
The ONE compiler for this overnight integrated build. It does not duplicate or
redesign the consumed Lane B compiler — it imports and reuses
lane-b-n8n-viewer-canvas-compiler/compiler/canvas_compiler.py exactly as
filed (same file, byte-identical, still covered by its own consumed manifest
row `compiler/canvas_compiler.py` in
LANE_B_CANDIDATE_BUILD_v0.2/CANDIDATE_MANIFEST_SHA256.csv — this module never
edits that file) and layers the SCVS v0.2.1 visual grammar on top as a pure
post-processing pass over the already-compiled canvas dict.

Every profile in this overnight build — the 15 candidate canvases, the 11
Lane B profiles, and the N8N viewer's node data — goes through
`compile_canvas_scvs()`. There is still exactly one node/edge grammar
(inherited unchanged from Lane B's `compile_canvas`) and exactly one SCVS
chip-line grammar (added here). No per-view branching exists in either.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

LANE_B_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "lane-b-n8n-viewer-canvas-compiler"
if str(LANE_B_ROOT) not in sys.path:
    sys.path.insert(0, str(LANE_B_ROOT))

from compiler.canvas_compiler import (  # noqa: E402  (Lane B's own module, unmodified)
    GraphCompileError,
    canonical_dumps,
    compile_canvas,
    structural_only,
)

SCHEMA_V02_PATH = pathlib.Path(__file__).resolve().parent.parent / "schema" / "graph_schema_v0.2.json"

# SCVS §2.1 lifecycle border vocabulary, expressed as a text prefix on the
# node's chip line (Obsidian Canvas JSON nodes have no border-style property,
# only fill colour — colour is retained, unchanged, from Lane B's mapping;
# this text prefix is the non-colour-dependent encoding SCVS requires, so
# nothing here is colour-only).
_LIFECYCLE_BORDER_WORD = {
    "active": "solid",
    "candidate": "dashed",
    "proposed": "dashed",
    "draft": "dotted",
    "conceptual": "dotted",
    "held": "dashed",
    "failed": "solid",
    "superseded": "double-struck (SUPERSEDED)",
    "retired": "double-struck (SUPERSEDED)",
    "canonical": "double (CANONICAL)",
}


def load_schema_v02() -> dict:
    with open(SCHEMA_V02_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _scvs_chip_line(obj: dict, view: dict) -> str:
    owner = obj.get("owner_lane", "")
    evidence = obj.get("evidence", view.get("evidence", "UNKNOWN"))
    ppv = obj.get("ppv", view.get("ppv", "Potential"))
    border = _LIFECYCLE_BORDER_WORD.get(obj["lifecycle_state"], obj["lifecycle_state"])
    parts = []
    if owner:
        parts.append(owner)
    parts.append(f"BORDER: {border}")
    parts.append(f"E: {evidence}")
    parts.append(f"PPV: {ppv}")
    parts.append(f"AUTH: {obj['authority']}")
    if obj.get("stop_hold"):
        parts.append(f"⚠ STOP/HOLD: {obj['stop_hold']}")
    return " · ".join(parts)


def _source_corner(obj: dict) -> str:
    tag = obj.get("source_tag")
    return f"[{tag}]" if tag else ""


def compile_canvas_scvs(graph: dict, schema: dict | None = None) -> dict:
    """Compile via Lane B's unmodified compile_canvas(), then add the SCVS
    chip line as an extra line in every object node's text and an SCVS
    grammar-version marker in the metadata block. Fails closed exactly as
    compile_canvas() does — this function adds no new failure-suppression
    path, only additional text content on an already-valid compile.
    """
    schema = schema or load_schema_v02()
    canvas = compile_canvas(graph, schema)

    object_by_id = {o["id"]: o for o in graph["objects"]}
    for node in canvas["nodes"]:
        obj = object_by_id.get(node["id"])
        if obj is None:
            continue  # the two fixed structural nodes (meta panel, home-return) carry no SCVS chip line
        corner = _source_corner(obj)
        chip_line = _scvs_chip_line(obj, graph)
        node["text"] = node["text"] + "\n" + chip_line
        if corner:
            node["text"] = corner + " " + node["text"]

    canvas["metadata"]["grammar"] = canvas["metadata"]["grammar"] + " + SCVS-v0.2.1-chip-line"
    canvas["metadata"]["scvs_version"] = "SCVS v0.2.1 (Lane C consumed)"
    return canvas


__all__ = ["compile_canvas_scvs", "load_schema_v02", "GraphCompileError", "canonical_dumps", "structural_only"]
