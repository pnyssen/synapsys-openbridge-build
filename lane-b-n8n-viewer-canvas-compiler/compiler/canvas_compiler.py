"""
Deterministic compiler: governed objects/relationships (the adapter contract in
schema/graph_schema.json) -> one Obsidian JSON Canvas grammar.

One compiler, not ad hoc per-view renderers: every view profile in
view_profiles.py produces a graph dict conforming to graph_schema.json, and
every graph dict passes through the same compile_canvas() below. Nothing here
is aware of "enterprise" vs "n8n_topology" vs any other view — that
distinction lives entirely in the data each profile supplies.

Determinism contract: compile_canvas(graph) is a pure function of graph's
structural fields (objects, relationships, view_id, title, group membership).
It never reads the clock, environment, or randomness, and node/edge ordering
is always derived by sorting on stable IDs. The `snapshot` field is carried
through into the metadata panel's text (informational) but is EXCLUDED from
the structural comparison tests/test_determinism.py uses to prove "unchanged
input produces unchanged structural output" — two graphs identical except for
`snapshot` must still produce identical nodes[]/edges[] (order, geometry,
text, color), which is exactly what lets a re-run pick up a fresher
`snapshot` without perturbing the rest of the canvas.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import jsonschema

_SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schema" / "graph_schema.json"

NODE_WIDTH = 340
NODE_HEIGHT = 160
GAP_X = 80
GAP_Y = 40
COLUMN_HEADER_HEIGHT = 80
TOP_MARGIN = 0

# Obsidian JSON Canvas built-in color slots (1..6). Anything not mapped here
# is left uncolored (default canvas styling) rather than guessed.
_LIFECYCLE_COLOR = {
    "active": "4",       # green
    "candidate": "5",    # cyan
    "proposed": "5",     # cyan
    "draft": "3",        # yellow
    "held": "3",         # yellow
    "failed": "1",       # red
    "superseded": "6",   # purple
    "retired": "6",      # purple
}

HOME_RETURN_NODE_ID = "__return_to_navigator_home__"
META_PANEL_NODE_ID = "__source_evidence_authority_panel__"


class GraphCompileError(ValueError):
    """Raised when a graph fails schema validation or a fail-closed structural check."""


def load_schema() -> dict:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_graph(graph: dict, schema: dict | None = None) -> None:
    """Schema-validate, then apply the fail-closed structural checks the
    dispatch requires that JSON Schema alone can't express:
      - every relationship.from/to must resolve to a known object id
      - every object id must be unique
    Raises GraphCompileError with a specific reason on any violation.
    """
    schema = schema or load_schema()
    try:
        jsonschema.validate(instance=graph, schema=schema)
    except jsonschema.ValidationError as exc:
        raise GraphCompileError(f"SCHEMA_VALIDATION_FAILED: {exc.message} at {list(exc.path)}") from exc

    object_ids = [o["id"] for o in graph["objects"]]
    seen = set()
    for oid in object_ids:
        if oid in seen:
            raise GraphCompileError(f"DUPLICATE_OBJECT_ID: {oid!r}")
        seen.add(oid)

    known_ids = set(object_ids)
    for rel in graph["relationships"]:
        if rel["from"] not in known_ids:
            raise GraphCompileError(
                f"UNKNOWN_RELATIONSHIP_ENDPOINT: relationship {rel['id']!r} references "
                f"unknown from-id {rel['from']!r}"
            )
        if rel["to"] not in known_ids:
            raise GraphCompileError(
                f"UNKNOWN_RELATIONSHIP_ENDPOINT: relationship {rel['id']!r} references "
                f"unknown to-id {rel['to']!r}"
            )
        if not rel.get("verb", "").strip():
            raise GraphCompileError(f"MISSING_VERB: relationship {rel['id']!r} has no verb")

    for obj in graph["objects"]:
        if not obj.get("authority", "").strip():
            raise GraphCompileError(f"MISSING_AUTHORITY_METADATA: object {obj['id']!r} has no authority")

    for required_field in ("evidence", "reality", "ppv", "authority", "source"):
        if not str(graph.get(required_field, "")).strip():
            raise GraphCompileError(f"MISSING_VIEW_AUTHORITY_METADATA: view field {required_field!r} is empty")


def _layout(graph: dict) -> dict[str, tuple[int, int]]:
    """Deterministic grid layout: objects are grouped into columns by their
    `group` field (default column "_ungrouped"), columns ordered
    alphabetically, and within a column objects are ordered by id ascending.
    Position is a pure function of (group, id) — no randomness, no
    input-order dependence, so re-running on the same object set (even if the
    caller iterated it in a different order) always yields the same layout.
    """
    objects = sorted(graph["objects"], key=lambda o: o["id"])
    columns: dict[str, list[dict]] = {}
    for obj in objects:
        columns.setdefault(obj.get("group", "_ungrouped"), []).append(obj)

    positions: dict[str, tuple[int, int]] = {}
    for col_index, group_name in enumerate(sorted(columns.keys())):
        col_objects = sorted(columns[group_name], key=lambda o: o["id"])
        x = col_index * (NODE_WIDTH + GAP_X)
        for row_index, obj in enumerate(col_objects):
            y = TOP_MARGIN + COLUMN_HEADER_HEIGHT + row_index * (NODE_HEIGHT + GAP_Y)
            positions[obj["id"]] = (x, y)
    return positions


def _column_of(graph: dict, object_id: str) -> str:
    for obj in graph["objects"]:
        if obj["id"] == object_id:
            return obj.get("group", "_ungrouped")
    raise GraphCompileError(f"UNKNOWN_RELATIONSHIP_ENDPOINT: {object_id!r}")


def _node_text(obj: dict) -> str:
    lines = [obj["label"], f"kind: {obj['kind']}", f"state: {obj['lifecycle_state']}", f"authority: {obj['authority']}"]
    if obj.get("detail"):
        lines.append(obj["detail"])
    return "\n".join(lines)


def _metadata_panel_text(graph: dict) -> str:
    return "\n".join(
        [
            f"SOURCE / FRESHNESS / EVIDENCE / REALITY / PPV / AUTHORITY — {graph['title']}",
            f"source: {graph['source']}",
            f"freshness (snapshot): {graph['snapshot']}",
            f"evidence: {graph['evidence']}",
            f"reality: {graph['reality']}",
            f"ppv: {graph['ppv']}",
            f"authority: {graph['authority']}",
            f"view_id: {graph['view_id']}",
            f"objects: {len(graph['objects'])}  relationships: {len(graph['relationships'])}",
        ]
    )


def compile_canvas(graph: dict, schema: dict | None = None) -> dict:
    """Compile a validated graph dict into an Obsidian .canvas JSON dict.

    Fails closed (raises GraphCompileError) rather than emitting a partial or
    best-guess canvas on any schema violation, unknown relationship endpoint,
    or missing authority metadata.
    """
    validate_graph(graph, schema)

    positions = _layout(graph)
    max_col_x = max((x for x, _y in positions.values()), default=0)
    max_row_y = max((y for _x, y in positions.values()), default=0)

    nodes: list[dict] = []
    for obj in sorted(graph["objects"], key=lambda o: o["id"]):
        x, y = positions[obj["id"]]
        node: dict[str, Any] = {
            "id": obj["id"],
            "type": "text",
            "text": _node_text(obj),
            "x": x,
            "y": y,
            "width": NODE_WIDTH,
            "height": NODE_HEIGHT,
        }
        color = _LIFECYCLE_COLOR.get(obj["lifecycle_state"])
        if color:
            node["color"] = color
        nodes.append(node)

    edges: list[dict] = []
    for rel in sorted(graph["relationships"], key=lambda r: r["id"]):
        same_column = _column_of(graph, rel["from"]) == _column_of(graph, rel["to"])
        from_side, to_side = ("bottom", "top") if same_column else ("right", "left")
        label = rel["verb"]
        if rel.get("lifecycle_state"):
            label = f"{label} ({rel['lifecycle_state']})"
        edges.append(
            {
                "id": rel["id"],
                "fromNode": rel["from"],
                "toNode": rel["to"],
                "fromSide": from_side,
                "toSide": to_side,
                "label": label,
            }
        )

    meta_y = max_row_y + NODE_HEIGHT + GAP_Y * 2
    meta_width = max(max_col_x + NODE_WIDTH, 900)
    nodes.append(
        {
            "id": META_PANEL_NODE_ID,
            "type": "text",
            "text": _metadata_panel_text(graph),
            "x": 0,
            "y": meta_y,
            "width": meta_width,
            "height": 220,
        }
    )

    return_y = meta_y + 220 + GAP_Y
    nodes.append(
        {
            "id": HOME_RETURN_NODE_ID,
            "type": "text",
            "text": f"Return to Navigator Home\n{graph['return_route']}",
            "x": 0,
            "y": return_y,
            "width": 360,
            "height": 100,
        }
    )
    edges.append(
        {
            "id": "__edge_meta_to_home__",
            "fromNode": META_PANEL_NODE_ID,
            "toNode": HOME_RETURN_NODE_ID,
            "fromSide": "bottom",
            "toSide": "top",
            "label": "return",
        }
    )

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "title": graph["title"],
            "view_id": graph["view_id"],
            "snapshot": graph["snapshot"],
            "source": graph["source"],
            "evidence": graph["evidence"],
            "reality": graph["reality"],
            "ppv": graph["ppv"],
            "authority": graph["authority"],
            "return_route": graph["return_route"],
            "compiler": "lane-b-canvas-compiler v0.1",
            "grammar": "synapsys-obsidian-canvas-v0.2 (nodes/edges per JSON Canvas + metadata panel node + Home return node/edge)",
        },
    }


def canonical_dumps(canvas: dict) -> str:
    """Stable JSON serialisation for hashing/diffing: sorted keys, fixed
    separators, trailing newline. Two compiles of the same graph produce
    byte-identical output through this function.
    """
    return json.dumps(canvas, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def structural_only(canvas: dict) -> dict:
    """Strip the one legitimately-volatile field (snapshot, which is allowed
    to advance on every live re-run) so determinism tests — and any future
    structural/visual diff tooling — compare everything that SHOULD be
    stable: node/edge geometry, text, color, ordering, and all other metadata
    fields. The snapshot value is stamped in two places (the top-level
    metadata.snapshot field, and as a "freshness (snapshot): ..." line inside
    the metadata-panel node's own text so a human reading the canvas sees it
    too) — both are scrubbed here, on the same basis: a freshness-only
    re-run is not a structural change and must not register as one.
    """
    import copy
    import re

    c = copy.deepcopy(canvas)
    c.get("metadata", {}).pop("snapshot", None)
    for node in c.get("nodes", []):
        if node.get("id") == META_PANEL_NODE_ID and "text" in node:
            node["text"] = re.sub(r"(?m)^freshness \(snapshot\): .*$", "freshness (snapshot): <scrubbed>", node["text"])
    return c
