"""Build NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY.json from model.py.

The registry is a current navigation and validation projection - not a
competing operational register. It is the validation source the test
harness runs against.
"""
import json
import pathlib

import model

HERE = pathlib.Path(__file__).parent


def build():
    elements = []
    for e in model.ELEMENTS:
        elements.append({
            "id": e["id"], "key": e["key"], "name": e["name"],
            "state": "current",
            "role": e["role"],
            "routes": {
                "html": f"COMPONENTS/{e['html']}",
                "canvas_view": f"COMPONENTS/{e['canvas_view']}",
                "canvas_source": (model.CANVAS_DIR_FROM_COMPONENTS
                                  + e["canvas_source"]),
                "canvas_source_obsidian": (model.OBSIDIAN_CANVAS_PREFIX
                                           + e["canvas_source"].replace(" ", "%20")),
                "return_verbs": f"COMPONENTS/{model.VERBS_FILE}",
                "return_navigator": model.NAVIGATOR_FILE,
            },
            "mesh": {
                "enters": e["signal_in"], "interprets": e["interprets"],
                "structures": e["structures"], "validated_by": e["validated_by"],
                "action": e["action"], "observes": e["observes"],
                "learns": e["learns"], "asset_conversion": e["asset_conversion"],
                "feedback_to": e["feedback_to"],
            },
            "purpose": e["purpose"], "strategy": e["strategy"], "assets": e["assets"],
            "evidence_requirement": ("Every state shown on this Element's surfaces carries "
                                     "source, snapshot and freshness; claims bind to filed receipts."),
            "authority": model.AUTHORITY,
            "ppv": model.PPV,
            "freshness": model.SNAPSHOT,
            "source": "navigator/model.py (single-source model), deployed via Working Memory",
            "acceptance_status": "CANDIDATE_FOR_STEWARD_ACCEPTANCE",
            "l3_common": model.l3_common(e),
            "l3_axis_statements": model.l3_axis_statements(e),
            "level3": model.l3_cells_min(e),
        })

    verbs = []
    for v in model.VERBS:
        verbs.append({
            "id": v["id"], "key": v["key"], "name": v["name"], "group": v["group"],
            "controlling_question": v["question"], "purpose": v["purpose"],
            "inputs": v["inputs"], "outputs": v["outputs"],
            "elements_primary": v["elements_primary"],
            "mesh_stages": v["mesh"],
            "benefit": v["benefit"],
            "benefit_statement": model.BENEFITS[v["benefit"]]["meaning"],
            "evidence_requirement": v["evidence"],
            "asset_implication": v["asset_implication"],
            "authority": model.AUTHORITY,
            "ppv": model.PPV,
            "owner": model.OWNER_LANE,
            "next_action": "Select the primary Element surface for this verb and continue the Mesh route.",
            "stop_hold": ("HOLD: Activate performs no runtime activation in this cycle; "
                          "all operational mutation held."),
            "replay_validity": model.REPLAY,
            "return_path": f"COMPONENTS/{model.VERBS_FILE}#{v['key']} -> {model.NAVIGATOR_FILE}",
            "anchor": v["key"],
        })

    mesh_coverage = {stage: [v["id"] for v in model.VERBS if stage in v["mesh"]]
                     for stage in model.MESH_STAGES}

    registry = {
        "registry": "NAVIGATOR_L1_L2_L3_ROUTE_REGISTRY",
        "version": "v0.1",
        "work_object": model.WORK_OBJECT,
        "snapshot": model.SNAPSHOT,
        "state": "current",
        "nature": ("Current navigation and validation projection only. Not an operational "
                   "register; confers no authority; PPV Potential throughout."),
        "home": {"path": "00_HOME.md", "state": "current"},
        "navigator": {"path": model.NAVIGATOR_FILE, "state": "current"},
        "nine_verbs_route": {"path": f"COMPONENTS/{model.VERBS_FILE}", "state": "current"},
        "process_offering_start": {"path": f"COMPONENTS/{model.START_FILE}", "state": "current"},
        "verb_groups": {"FORM": ["V1", "V2", "V3"], "FLOW": ["V4", "V5", "V6"],
                        "EVOLVE": ["V7", "V8", "V9"]},
        "mesh_stages": model.MESH_STAGES,
        "mesh_stage_verb_coverage": mesh_coverage,
        "benefits": model.BENEFITS,
        "l3_defaults": model.L3_DEFAULTS,
        "l3_axis_c_content": model.axis_c_content(),
        "l3_resolution_rule": ("Full cell = l3_defaults + element.l3_common + axis statements "
                               "from element.l3_axis_statements + l3_axis_c_content[axis_c] "
                               "+ the cell's own fields (cell fields win). Derived fields: "
                               "decision_served = 'How the <axis_a> of <element name> is expressed "
                               "in its <axis_b> mode, read through <axis_c lens>.'; "
                               "verbs = verb_groups for the axis_b group (Form->FORM, Flow->FLOW, "
                               "Evolve->EVOLVE)."),
        "element_verb_mapping_rule": ("Full mapping = {element, verb, relationship} + statement "
                                      "'<verb name> at <element name>: <verb purpose> Applied here, "
                                      "it acts on <element role>.' with mesh_stages/benefit/evidence "
                                      "taken from the verb entry."),
        "elements": elements,
        "verbs": verbs,
        "element_verb_mappings": model.ev_mappings_min(),
        "stream_a": {"state": "ASSURED_STREAM_A_COMPLETE",
                     "disposition": "Completed evidence only. No rerun, no reactivation, no active next action."},
        "held": ["Odoo mutation", "N8N mutation or activation", "credential access",
                 "runtime deployment", "production automation", "Stream A replay",
                 "Service/Method/Pattern/Canonical/Asset promotion",
                 "Benefit-realisation declaration", "PPV movement",
                 "Bridge Pattern qualification"],
        "authority": model.AUTHORITY,
        "ppv": model.PPV,
        "replay_validity": model.REPLAY,
        "acceptance_status": "CANDIDATE_FOR_STEWARD_ACCEPTANCE",
    }
    return registry


if __name__ == "__main__":
    reg = build()
    out = HERE / "dist" / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" / "DATA" / model.REGISTRY_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    n_l3 = sum(len(e["level3"]) for e in reg["elements"])
    print(f"registry written: {out}")
    print(f"elements={len(reg['elements'])} verbs={len(reg['verbs'])} "
          f"l3_cells={n_l3} ev_maps={len(reg['element_verb_mappings'])}")
