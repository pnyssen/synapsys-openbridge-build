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

# Stale pre-execution D007 language markers: any of these appearing in an
# emitted current projection fails the build (RC12 guard).
STALE_MARKERS = [
    "READY_FOR_D007_RELEASE", "prepared but not released",
    "not released for mutation", "Obtain explicit",
    "No Odoo mutation has occurred", "receives explicit release",
    "Explicit release is now required", "registration gap remains",
]

ONE_NEXT_ACTION = ("Run the read-only independent D009 replay of the executed D007 "
                   "correction and the deployed Navigator from filed inputs; then Steward "
                   "cold-start acceptance from 00_HOME.md. No further register mutation is "
                   "authorised (the D007 packet is CONSUMED_EXECUTED_ONCE).")

STREAM_C = {
    "status": "D007_CORRECTION_EXECUTED_RECEIPTED",
    "progress": 100,
    "reality": ("The bounded D007 Work Object / Project / Service / Method packet was "
                "executed once under quoted Steward release: fields x_project_id, "
                "x_service_catalogue_id, x_method_id created on x_ss_work_object_register "
                "and authoritative record id 2 created with native links to Project 101, "
                "Service SC-01 and Method D002-PTF. Independently read back; historical "
                "pilot id 1 untouched; receipt filed in FIVE_PRIORITY_COMPLETE_DEPLOYMENT."),
    "next_action": ("None in Stream C. Final read-only D009 acceptance replay covers the "
                    "record; no further register mutation is authorised."),
}

STREAM_E_NEXT = ("Perform the final read-only D009 acceptance replay from filed inputs — "
                 "the bounded Odoo correction is executed and receipted, and the Navigator "
                 "deployment is link-tested; retain bridge Pattern qualification on HOLD.")


def apply_stream_c(stream):
    stream.update(STREAM_C)


def coherence_check(paths):
    bad = []
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for m in STALE_MARKERS:
            if m in text:
                bad.append((p.name, m))
    if bad:
        raise SystemExit(f"STALE PROJECTION MARKERS FOUND: {bad}")

PRIORITIES = [
    {"rank": 1, "id": "P1-NAV-ACCEPTANCE",
     "title": "Accept the completed Navigator L1/L2/L3 integration",
     "summary": ("All nine Elements, nine verbs and 243 Level-3 positions are integrated, "
                 "registry-validated, tested and deployed. Steward acceptance is the one open step."),
     "criticality": "CRITICAL", "status": "IMPLEMENTED_PENDING_STEWARD_ACCEPTANCE",
     "anchor": "l1l2l3-routes",
     "contribution": "Closes Priority 1 of the Work Object and unlocks Process/Offering delivery."},
    {"rank": 2, "id": "P2-ODOO-IDENTITY",
     "title": "Bounded Odoo Work Object / Service / Method correction — EXECUTED",
     "summary": ("The filed D007 packet was released and executed once under quoted Steward "
                 "authority: authoritative Work Object identity created (x_ss_work_object_register "
                 "id 2) with native Project 101, Service SC-01 and Method D002-PTF links; "
                 "receipted and independently read back."),
     "criticality": "HIGH", "status": "EXECUTED_RECEIPTED", "anchor": "stream-c",
     "contribution": "Operational-register identity condition closed."},
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
    "Authoritative Odoo Work Object identity created with native Project/Service/Method links "
    "(D007 packet executed once under quoted Steward release, receipted, independently read back)",
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
    if "one_next_action" in p:
        p["one_next_action"] = ONE_NEXT_ACTION
    (DST / "NAVIGATOR_PRIORITY_MODEL.json").write_text(
        json.dumps(p, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    d = json.loads((SRC / "NAVIGATOR_DELIVERY_STATE.json").read_text(encoding="utf-8"))
    d["snapshot_at"] = SNAP
    d["top_priorities"] = PRIORITIES
    for ss in d.get("source_systems", []):
        if ss["system"] == "Odoo":
            ss["mode"] = ("read-only snapshot; authoritative Work Object identity registered "
                          "(x_ss_work_object_register id 2, D007 packet executed and receipted)")
    wo = d.get("work_object", {})
    wo["authority"] = ("Steward authority for the projection/link correction was exercised. "
                       "The bounded D007 Odoo packet has been RELEASED AND EXECUTED ONCE "
                       "(receipted; CONSUMED_EXECUTED_ONCE; no re-execution authorised). "
                       "Stream A run-04 remains closed and must not be replayed.")
    for st in d.get("parallel_streams", []):
        if st.get("id") == "STREAM-C":
            apply_stream_c(st)
        if st.get("id") == "STREAM-E":
            st["next_action"] = STREAM_E_NEXT
    d["held_items"] = [h for h in d.get("held_items", [])
                       if "explicit release" not in h] + [
        "Any further Odoo schema or record mutation — the filed D007 packet is "
        "CONSUMED_EXECUTED_ONCE and must not be re-executed"]
    wo["reality"] = ("Stream A complete and independently assured. Navigator L1/L2/L3 deployed and "
                     "tested. Authoritative Odoo Work Object identity and native Project/Service/"
                     "Method links created via the released D007 packet (record id 2, receipted, "
                     "independently read back). Bridge remains ineligible for Pattern qualification.")
    sl = d.get("strategy_lock", {})
    sl["critical_path"] = ("D007 correction executed and receipted. Remaining path: Steward cold-start "
                           "acceptance of the deployed Navigator; Stream A stays closed, no rerun.")
    d["one_next_action"] = ONE_NEXT_ACTION
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

    s = json.loads((SRC / "NAVIGATOR_PARALLEL_STREAMS.json").read_text(encoding="utf-8"))
    s["snapshot_at"] = SNAP
    if "one_next_action" in s:
        s["one_next_action"] = ONE_NEXT_ACTION
    for st in s["streams"]:
        if st["id"] == "STREAM-E":
            st["next_action"] = STREAM_E_NEXT
        if st["id"] == "STREAM-C":
            apply_stream_c(st)
    (DST / "NAVIGATOR_PARALLEL_STREAMS.json").write_text(
        json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    coherence_check([DST / n for n in [
        "NAVIGATOR_PRIORITY_MODEL.json", "NAVIGATOR_DELIVERY_STATE.json",
        "NAVIGATOR_BENEFIT_REALISATION.json", "NAVIGATOR_PARALLEL_STREAMS.json"]])
    print("data projections refreshed and coherence-checked")


if __name__ == "__main__":
    main()
