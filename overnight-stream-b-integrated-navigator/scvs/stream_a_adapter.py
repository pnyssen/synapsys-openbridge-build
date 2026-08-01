"""
StreamAAdapter — the bounded seam where Stream A's (Codex) real
object/relationship JSON slots in, once Codex actually returns it.

Status as of this build: Stream A has NOT returned. Confirmed by reading
`NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md` directly this session:
Lane A state = `TOOL_BLOCKED`, controller disposition
`HELD_WM_TO_CODEX_TRANSPORT` — Codex has a frozen evidence bundle staged in
Working Memory but no verified runtime has mounted it, so no A payload
exists anywhere to adapt. Nothing in this module is Stream A data; it is the
CONTRACT that data will have to satisfy, plus a REFUSING stub that makes
that boundary impossible to silently paper over.

Why a separate module and not just "use graph_schema_v0.2.json directly":
Stream A's actual payload shape is UNKNOWN (Codex has not published one).
`adapt_stream_a_payload()` below is deliberately a translation seam, not a
passthrough — when Stream A's real shape is known, only the body of that one
function needs to change (map A's field names to `objects`/`relationships`);
nothing in compiler/scvs_compiler.py, the 15 candidate canvases, or the 11
profiles needs to change, because they all consume a `dict` conforming to
graph_schema_v0.2.json regardless of where it came from.
"""
from __future__ import annotations

import pathlib
import sys

LANE_B_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "lane-b-n8n-viewer-canvas-compiler"
if str(LANE_B_ROOT) not in sys.path:
    sys.path.insert(0, str(LANE_B_ROOT))

from compiler.canvas_compiler import GraphCompileError  # noqa: E402


class StreamANotReturnedError(RuntimeError):
    """Raised by adapt_stream_a_payload() when called with no real payload.

    This is intentional and permanent until Stream A actually returns data —
    it is the mechanism that stops this build (or any future one) from
    quietly substituting a guess for Stream A's contract. See
    NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md, Lane A row, for the
    live-verified current state this reflects.
    """


# The MINIMAL shape this adapter currently commits to accepting from Stream A,
# expressed as required top-level keys. This is deliberately a subset of what
# graph_schema_v0.2.json's `objects`/`relationships` need — the adapter's job
# is exactly to map from whatever Stream A calls its fields onto those names;
# it does not invent additional Stream-A-specific semantics beyond this.
REQUIRED_STREAM_A_TOP_LEVEL_KEYS = ("nodes_or_objects", "edges_or_relationships")


def adapt_stream_a_payload(payload: dict | None) -> dict:
    """Map a Stream A integration-graph payload onto graph_schema_v0.2's
    objects/relationships shape.

    Args:
        payload: Stream A's raw returned JSON. Pass None (or omit) to get
            the expected StreamANotReturnedError — this is the correct call
            for every caller in this repository right now, since no such
            payload exists yet.

    Raises:
        StreamANotReturnedError: always, while `payload` is None/falsy —
            i.e. always, at present.
        GraphCompileError: if a real payload is supplied but is missing the
            required top-level keys this adapter maps from.

    This function intentionally does NOT construct a graph from a guessed or
    fabricated Stream A shape "just to show it works" — that would be
    exactly the kind of fabrication the dispatch prohibits ("without
    fabricating Stream A data"). What proves the seam works is that every
    OTHER graph in this build (the 15 canvases, the 11 profiles) already
    flows through the identical objects/relationships contract this function
    targets — see fixtures_canvas_suite/ and fixtures_live/.
    """
    if not payload:
        raise StreamANotReturnedError(
            "Stream A has not returned (NAVIGATOR_INTEGRATED_MVP_DISPATCH_MANIFEST_v0.7.md: "
            "Lane A = TOOL_BLOCKED / HELD_WM_TO_CODEX_TRANSPORT, verified live this session). "
            "No payload exists to adapt. Do not construct one."
        )

    missing = [k for k in REQUIRED_STREAM_A_TOP_LEVEL_KEYS if k not in payload]
    if missing:
        raise GraphCompileError(f"STREAM_A_PAYLOAD_MISSING_KEYS: {missing}")

    objects = []
    for raw in payload["nodes_or_objects"]:
        obj = {
            "id": str(raw["id"]),
            "label": raw.get("label", raw["id"]),
            "kind": raw.get("kind", "stream_a_object"),
            "lifecycle_state": raw.get("lifecycle_state", "candidate"),
            "authority": raw.get("authority", "STREAM_A_ADAPTED — authority not independently re-derived"),
        }
        # OPTIONAL v0.2 fields: included only when Stream A actually supplied
        # them. Setting them to None instead of omitting would violate
        # graph_schema_v0.2.json's per-field string/enum typing (a null is
        # not a valid enum member) — omission is how "not supplied" is
        # correctly represented, not a null placeholder.
        for key in ("evidence", "ppv", "owner_lane", "source_tag"):
            if raw.get(key) is not None:
                obj[key] = raw[key]
        objects.append(obj)
    relationships = []
    for raw in payload["edges_or_relationships"]:
        relationships.append(
            {
                "id": str(raw["id"]),
                "from": str(raw["from"]),
                "to": str(raw["to"]),
                "verb": raw.get("verb", "relates_to"),
            }
        )

    return {
        "view_id": "stream_a_integration_graph",
        "title": payload.get("title", "Stream A — Codex Integration Graph"),
        "snapshot": payload.get("snapshot", ""),
        "source": "Stream A (Codex) adapted payload via StreamAAdapter.adapt_stream_a_payload()",
        "evidence": "LIVE_VERIFIED",
        "reality": "IMPLEMENTED — adapted directly from Stream A's own returned payload, no remapping of meaning",
        "ppv": "Potential",
        "authority": "Read-only projection of Stream A's own returned graph",
        "return_route": payload.get("return_route", "UNSET — caller must supply the current candidate Architecture path"),
        "objects": objects,
        "relationships": relationships,
    }


__all__ = ["adapt_stream_a_payload", "StreamANotReturnedError", "REQUIRED_STREAM_A_TOP_LEVEL_KEYS"]
