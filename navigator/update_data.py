"""Refresh the durable DATA projections that are stale after this cycle.

Patched in place (same schema, new snapshot): priority model, delivery
state, benefit realisation. NAVIGATOR_PARALLEL_STREAMS.json and
NAVIGATOR_LANE_RETURNS.json remain accurate and are not redeployed.
Discipline preserved: material_steward_benefits_realised stays empty -
interface outcomes are evidence inputs, not realised Benefits.
"""
import json
import pathlib

import model

HERE = pathlib.Path(__file__).parent
SRC = HERE / "mirror" / "CURRENT" / "DATA"
DST = HERE / "dist" / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" / "DATA"

SNAP = model.SNAPSHOT

PRIORITIES = [
    {"rank": 1, "id": "P1-NAV-ACCEPTANCE",
     "title": "Accept the completed Navigator L1/L2/L3 integration",
     "summary": ("All nine Elements, nine verbs and 243 Level-3 positions are integrated, "
                 "registry-validated, tested and deployed. Steward acceptance is the one open step."),
     "criticality": "CRITICAL", "status": "IMPLEMENTED_PENDING_STEWARD_ACCEPTANCE",
     "anchor": "l1l2l3-routes",
     "contribution": "Closes Priority 1 of the Work Object and unlocks Process/Offering delivery."},
    {"rank": 2, "id": "P2-ODOO-IDENTITY",
     "title": "Release and execute the bounded Odoo Work Object / Service / Method correction",
     "summary": ("The exact D007 packet is prepared and read back. Separately held; explicit release "
                 "is required to create the authoritative Work Object identity and native links."),
     "criticality": "HIGH", "status": "READY_FOR_D007_RELEASE", "anchor": "stream-c",
     "contribution": "Closes the remaining operational-register condition; not a blocker for the interface."},
    {"rank": 3, "id": "P3-NEW-PROCESS-OFFERING",
     "title": "Begin defining new Processes and Offerings as governed candidates",
     "summary": ("Use the New Process & Offering start surface; candidates route V1-V9 with "
                 "activation HELD until authorised."),
     "criticality": "HIGH", "status": "READY", "anchor": "l1l2l3-routes",
     "contribution": "Converts the completed Navigator into delivery capability."},
    {"rank": 4, "id": "P4-MESH-DISCIPLINE",
     "title": "Maintain Mesh, Benefit and evidence discipline on every route",
     "summary": ("Every claim stays evidence-bound; realisation declarations remain with the Steward; "
                 "regression tests guard the routes."),
     "criticality": "MEDIUM", "status": "ONGOING", "anchor": "mesh",
     "contribution": "Prevents recurrence of drift, false realisation and broken-route defect classes."},
    {"rank": 5, "id": "P5-ODOO-REGISTRATION",
     "title": "Prepare bounded Odoo registration of accepted Navigator artefacts",
     "summary": "Only after Steward acceptance, via CR, under existing change-control rules.",
     "criticality": "MEDIUM", "status": "HELD_PENDING_ACCEPTANCE", "anchor": "stream-c",
     "contribution": "Moves accepted artefacts toward the operational register without authority drift."},
]

NEW_OUTCOMES = [
    "Registry-driven L1/L2/L3 integration: 9 Element pages, 9 browser-safe Canvas views, "
    "nine-verb route and 243 Level-3 positions generated from one route registry",
    "All primary routes browser-safe (relative vault paths); obsidian:// reduced to secondary",
    "Governed New Process & Offering candidate start surface installed with V7 Activate HELD",
    "Synthetic fixtures TEST-PROCESS-001 and TEST-OFFERING-001 routed V1-V9 across all Mesh stages",
    "Deterministic 35-test acceptance harness plus nested 9x9x27 assertion sweep passing",
]


def main():
    DST.mkdir(parents=True, exist_ok=True)

    p = json.loads((SRC / "NAVIGATOR_PRIORITY_MODEL.json").read_text(encoding="utf-8"))
    p["snapshot_at"] = SNAP
    p["priorities"] = PRIORITIES
    (DST / "NAVIGATOR_PRIORITY_MODEL.json").write_text(
        json.dumps(p, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    d = json.loads((SRC / "NAVIGATOR_DELIVERY_STATE.json").read_text(encoding="utf-8"))
    d["snapshot_at"] = SNAP
    d["top_priorities"] = PRIORITIES
    d["one_next_action"] = ("Steward acceptance review of the completed Navigator L1/L2/L3 "
                            "deployment, starting from 00_HOME.md.")
    (DST / "NAVIGATOR_DELIVERY_STATE.json").write_text(
        json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    b = json.loads((SRC / "NAVIGATOR_BENEFIT_REALISATION.json").read_text(encoding="utf-8"))
    b["snapshot_at"] = SNAP
    for o in NEW_OUTCOMES:
        if o not in b["technical_outcomes_observed"]:
            b["technical_outcomes_observed"].append(o)
    b["material_steward_benefits_realised"] = []
    (DST / "NAVIGATOR_BENEFIT_REALISATION.json").write_text(
        json.dumps(b, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("data projections refreshed")


if __name__ == "__main__":
    main()
