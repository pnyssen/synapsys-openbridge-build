"""Scan harness (CAP-009): score a lane's call log against probes P1 to P5
(PKT-20261031-AVL-004).

A harness cannot watch another lane's tool calls, so each lane files its own
call log and this module scores that log offline. Call-log shape:

  {"lane": "...", "probes": [
     {"id": "P1",
      "calls": [{"tool": "read"|"search", "path": "...", "query": "...", "result": "hit"|"miss"}],
      "answer_paths": ["..."],           # sources the answer cites
      "states_gap": false}               # P2 only: answer says "no F-row for roles"
  ]}

Scores: resolver layers read before the first keyword search (of 5), terms tried
per probe, hit/miss per probe, misses later corrected by a read, calls used.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

PROBES = {
    "P1": {"ask": "Where does the cross-AI bridge live and how do requirements move between AIs?",
           "expected_sources": ["MESH_QUEUE/CURRENT.md", "MESH_QUEUE/LENS/HANDOVER_QUEUE.json",
                                "05_AI_RETURNS_HASHED/SYNAPSYS_CAPABILITY_ACTIVATION_REGISTER_CANDIDATE_v0.1.md"]},
    "P2": {"ask": "Where do roles and accountability live in the model?",
           "expected_gap": True, "expected_sources": ["MESH_QUEUE/KIT/FOUNDATION_INDEX_v1.md"]},
    "P3": {"ask": "Who is the owner of the Avalira Benefits and what type is the owner field?",
           "expected_sources": ["MESH_QUEUE/HEALTH/REVIEWS_APPEND_20261031_AVL2.md",
                                "MESH_QUEUE/RETURNS/S2-AVL-R3-20261030--return.md"]},
    "P4": {"ask": "What was ruled on the Avalira Asset called Business?",
           "expected_sources": ["MESH_QUEUE/HEALTH/REVIEWS_APPEND_20261030_S2E.md"]},
    "P5": {"ask": "What is queued next for Avalira and who validates it?",
           "expected_sources": ["MESH_QUEUE/LENS/HANDOVER_QUEUE.json"]},
}

LAYERS = (
    ("capsule", re.compile(r"NAVIGATOR_STATE_CAPSULE", re.I)),
    ("index", re.compile(r"FOUNDATION_INDEX", re.I)),
    ("prior_decisions", re.compile(r"/(REVIEWS|DECISIONS)", re.I)),
    ("queue_view", re.compile(r"HANDOVER_QUEUE|NAVIGATOR_VIEW", re.I)),
    ("streams_returns", re.compile(r"/(STREAMS|RETURNS)/", re.I)),
)


def layer_of(path: str) -> str:
    for name, pat in LAYERS:
        if pat.search(path or ""):
            return name
    return ""


def _norm(p: str) -> str:
    return (p or "").strip().lstrip("/")


def score_lane(log: Dict[str, Any]) -> Dict[str, Any]:
    layers_before_search: set = set()
    searched = False
    calls_total = 0
    per_probe: List[Dict[str, Any]] = []
    for pr in log.get("probes", []):
        spec = PROBES.get(pr["id"])
        if spec is None:
            raise ValueError(f"unknown probe id {pr['id']!r}")
        terms, miss_seen, corrected = [], False, False
        for call in pr.get("calls", []):
            calls_total += 1
            if call.get("tool") == "search":
                searched = True
                terms.append(call.get("query", ""))
                miss_seen = miss_seen or call.get("result") == "miss"
            elif call.get("tool") == "read":
                if not searched:
                    layer = layer_of(call.get("path", ""))
                    if layer:
                        layers_before_search.add(layer)
                if miss_seen and _norm(call.get("path", "")) in map(_norm, spec["expected_sources"]):
                    corrected = True
        cited = {_norm(p) for p in pr.get("answer_paths", [])}
        expected = {_norm(p) for p in spec["expected_sources"]}
        if spec.get("expected_gap"):
            hit = bool(pr.get("states_gap")) and bool(cited & expected)
        else:
            hit = bool(cited & expected)
        per_probe.append({"id": pr["id"], "hit": hit, "path_cited": sorted(cited & expected) or "[unobserved]",
                          "search_terms": terms, "miss_corrected": bool(miss_seen and corrected),
                          "calls": len(pr.get("calls", []))})
    return {
        "lane": log.get("lane", "[unobserved]"),
        "layers_read_before_first_search": sorted(layers_before_search),
        "layers_read_before_first_search_n": f"{len(layers_before_search)}/5",
        "probes_passed": f"{sum(p['hit'] for p in per_probe)}/{len(PROBES)}",
        "probes_scored": len(per_probe),
        "misses_corrected": sum(p["miss_corrected"] for p in per_probe),
        "calls_used": calls_total,
        "per_probe": per_probe,
        "scored_by": "scan harness (offline). Drafter never validates its own return; a second lane scores it.",
    }
