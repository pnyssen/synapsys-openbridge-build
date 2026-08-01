"""
Deterministic, generic adapter: accepted Obsidian Canvas JSON (the 15 files
at Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/*.canvas) -> graph_schema_v0.2
objects/relationships.

This is ONE conversion function applied identically to all 15 files — no
per-canvas special-casing — consistent with "one generator/grammar, not
per-view handcrafted renderers".

Mapping rules (all pure functions of the original node/edge data, nothing
invented):
  - id: original node/edge id, used verbatim (already schema-pattern-safe:
    n1, e1, control_v02, hub, a, b, ...).
  - label: first line of the original `text` field.
  - kind: "control_return_block" for the control node (id containing
    "control"), else "canvas_object".
  - lifecycle_state: keyword-scanned from the full original text
    (case-insensitive): "SUPERSEDED"->superseded, "HELD"->held,
    "CANDIDATE"->candidate, else "active". This is a literal substring scan,
    not an interpretation — the same rule for every node in every canvas.
  - authority: carried verbatim from the canvas's own metadata.authority
    field (e.g. "HELD"), annotated as carried-not-rederived.
  - group: "col_NN" from original x // 400, so the compiler's deterministic
    column layout roughly preserves the original left-to-right reading order
    without copying the original's exact hand-placed coordinates.
  - evidence / ppv: not set per-object (falls back to the view-level
    evidence/ppv the compiler already requires) — the accepted canvases
    don't carry a distinct per-node evidence/PPV value, so none is invented.
  - relationships: id/from/to verbatim; verb = original edge label, or
    "relates_to" when the original edge carries no label (5 of the 15
    canvases have at least one unlabelled edge — see NOTE below).

The resulting graph's view-level fields:
  - view_id: canvas filename stem, lower-cased, non-alnum -> "_".
  - evidence: "ADAPTED_FROM_ACCEPTED_CANVAS" (schema v0.2's new enum value
    for exactly this situation).
  - reality: states plainly that the accepted original remains the current
    filed version and this is a regenerated candidate, not a replacement.
  - return_route: the candidate Architecture v1.3 path (passed in by the
    caller — this adapter does not hardcode it, so the caller controls
    where "current candidate" points).
"""
from __future__ import annotations

import re

_LIFECYCLE_KEYWORDS = [
    ("SUPERSEDED", "superseded"),
    ("HELD", "held"),
    ("CANDIDATE", "candidate"),
]


def _lifecycle_from_text(text: str) -> str:
    upper = text.upper()
    for keyword, state in _LIFECYCLE_KEYWORDS:
        if keyword in upper:
            return state
    return "active"


def _view_id_from_filename(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


def adapt_accepted_canvas(filename: str, raw_canvas: dict, return_route: str, snapshot: str) -> dict:
    objects = []
    for node in raw_canvas["nodes"]:
        text = node.get("text", node["id"])
        label = text.split("\n", 1)[0]
        kind = "control_return_block" if "control" in node["id"].lower() else "canvas_object"
        col = int(node.get("x", 0)) // 400
        objects.append(
            {
                "id": node["id"],
                "label": label,
                "kind": kind,
                "lifecycle_state": _lifecycle_from_text(text),
                "authority": f"carried from accepted canvas metadata.authority "
                             f"({raw_canvas['metadata'].get('authority', 'unspecified')}) — not independently re-derived per node",
                "detail": text,
                "group": f"col_{col:02d}",
            }
        )

    relationships = []
    for edge in raw_canvas["edges"]:
        relationships.append(
            {
                "id": edge["id"],
                "from": edge["fromNode"],
                "to": edge["toNode"],
                "verb": edge.get("label") or "relates_to",
            }
        )

    meta = raw_canvas["metadata"]
    return {
        "view_id": _view_id_from_filename(filename),
        "title": meta.get("title", filename) + " (candidate regeneration)",
        "snapshot": snapshot,
        "source": f"adapted from accepted canvas Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/{filename} "
                  f"(read live via sp_read this session; original snapshot {meta.get('snapshot', 'unknown')})",
        "evidence": "ADAPTED_FROM_ACCEPTED_CANVAS",
        "reality": (
            f"CANDIDATE_REGENERATION — the accepted canvas at "
            f"Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/{filename} remains the current filed version and is "
            f"UNCHANGED by this build; this is a compiler-regenerated candidate rendering of the same "
            f"node/edge content through the SCVS-integrated compiler, not a replacement"
        ),
        "ppv": "Potential",
        "authority": meta.get("authority", "HELD"),
        "return_route": return_route,
        "objects": objects,
        "relationships": relationships,
    }


__all__ = ["adapt_accepted_canvas"]
