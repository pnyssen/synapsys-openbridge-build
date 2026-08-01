"""
Builds the 8 explicitly-labelled fixture graphs for view profiles this
candidate pass has NO live or Stream-A-sourced data for: enterprise, psa,
three_by_three_by_three, nine_verbs, mesh, signal_to_asset,
service_pattern_method_canonical, work_object_queue.

Every one of these sets evidence="LABELLED_FIXTURE" and a source string that
says plainly this is placeholder structure proving the compiler handles the
profile, NOT a reproduction of the real content of the corresponding existing
Obsidian canvas (01/02/03/04/05/06/09/14_*.canvas) — this lane read those
files' NAMES via sp_list but did not treat their content as licence to
restate SynapSys canon it did not itself verify. Per the dispatch: "Stream A
object/relationship JSON when returned; before then, use a declared adapter
contract and labelled fixtures only."
"""
import json
import pathlib

SNAPSHOT = "2026-08-02T02:15:00Z"
OUT = pathlib.Path(__file__).resolve().parent / "fixtures"
RETURN_ROUTE = "Obsidian/00_HOME.md -> NAVIGATOR_MVP_v0.2/NAVIGATOR_MVP_PRIMARY_HOME_CANDIDATE_v0.2.md"

FIXTURE_NOTE = (
    "LABELLED FIXTURE — placeholder structure demonstrating this compiler handles the "
    "{profile} view profile through the same code path as the live views. Not a reproduction "
    "of any existing canvas's real content; awaits Stream A's governed object/relationship JSON."
)


def fixture(view_id: str, title: str, objects: list, relationships: list) -> dict:
    return {
        "view_id": view_id,
        "title": title,
        "snapshot": SNAPSHOT,
        "source": f"declared_adapter_contract_fixture (schema/graph_schema.json) — {FIXTURE_NOTE.format(profile=view_id)}",
        "evidence": "LABELLED_FIXTURE",
        "reality": "FIXTURE — not implemented/live; structural demonstration only",
        "ppv": "Potential — fixture data, not a governed record",
        "authority": "No production authority claimed; fixture author is this candidate compiler pass",
        "return_route": RETURN_ROUTE,
        "objects": objects,
        "relationships": relationships,
    }


DATA = {}

DATA["enterprise"] = fixture(
    "enterprise",
    "Enterprise Integrated — labelled fixture",
    [
        {"id": "ent_constitution", "label": "Constitution", "kind": "canon_layer", "lifecycle_state": "active", "authority": "steward_ratified", "group": "1_canon"},
        {"id": "ent_eom", "label": "Operating Model (EOM)", "kind": "canon_layer", "lifecycle_state": "active", "authority": "steward_ratified", "group": "1_canon"},
        {"id": "ent_sea", "label": "Enterprise Architecture (SEA)", "kind": "canon_layer", "lifecycle_state": "active", "authority": "steward_ratified", "group": "1_canon"},
        {"id": "ent_domains", "label": "Domains D000-D010", "kind": "domain_layer", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "2_domains"},
        {"id": "ent_runtime", "label": "Runtime (Odoo/N8N/Working Memory)", "kind": "runtime_layer", "lifecycle_state": "active", "authority": "d007_operational", "group": "3_runtime"},
    ],
    [
        {"id": "e1", "from": "ent_constitution", "to": "ent_eom", "verb": "governs"},
        {"id": "e2", "from": "ent_eom", "to": "ent_sea", "verb": "governs"},
        {"id": "e3", "from": "ent_sea", "to": "ent_domains", "verb": "structures"},
        {"id": "e4", "from": "ent_domains", "to": "ent_runtime", "verb": "operates_through"},
    ],
)

DATA["psa"] = fixture(
    "psa",
    "Purpose / Strategy / Assets — labelled fixture",
    [
        {"id": "psa_purpose", "label": "Purpose", "kind": "psa_layer", "lifecycle_state": "active", "authority": "steward_ratified", "group": "1_purpose"},
        {"id": "psa_strategy", "label": "Strategy", "kind": "psa_layer", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "2_strategy"},
        {"id": "psa_assets", "label": "Assets", "kind": "psa_layer", "lifecycle_state": "active", "authority": "d007_operational", "group": "3_assets"},
    ],
    [
        {"id": "e1", "from": "psa_purpose", "to": "psa_strategy", "verb": "informs"},
        {"id": "e2", "from": "psa_strategy", "to": "psa_assets", "verb": "compounds_into"},
    ],
)

DATA["three_by_three_by_three"] = fixture(
    "three_by_three_by_three",
    "3x3x3 (FFE/SBR) — labelled fixture",
    [
        {"id": "f_form", "label": "Form", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "1_ffe"},
        {"id": "f_flow", "label": "Flow", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "1_ffe"},
        {"id": "f_evolve", "label": "Evolve", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "1_ffe"},
        {"id": "s_strategic", "label": "Strategic", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "2_sbr"},
        {"id": "s_business", "label": "Business", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "2_sbr"},
        {"id": "s_relational", "label": "Relational", "kind": "3x3x3_axis", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": "2_sbr"},
    ],
    [
        {"id": "e1", "from": "f_form", "to": "s_strategic", "verb": "cross_maps"},
        {"id": "e2", "from": "f_flow", "to": "s_business", "verb": "cross_maps"},
        {"id": "e3", "from": "f_evolve", "to": "s_relational", "verb": "cross_maps"},
    ],
)

NINE_VERBS = ["Sense", "Route", "Verify", "Decide", "Execute", "Record", "Learn", "Escalate", "Return"]
DATA["nine_verbs"] = fixture(
    "nine_verbs",
    "Nine-Verb Operating Model — labelled fixture",
    [
        {"id": f"verb_{i+1}_{v.lower()}", "label": v, "kind": "operating_verb", "lifecycle_state": "active", "authority": "steward_directed_working_definition", "group": f"{(i // 3) + 1}_triad"}
        for i, v in enumerate(NINE_VERBS)
    ],
    [
        {"id": f"e{i+1}", "from": f"verb_{i+1}_{NINE_VERBS[i].lower()}", "to": f"verb_{i+2}_{NINE_VERBS[i+1].lower()}", "verb": "sequences_to"}
        for i in range(len(NINE_VERBS) - 1)
    ],
)

DATA["mesh"] = fixture(
    "mesh",
    "Mesh Lifecycle Gates — labelled fixture",
    [
        {"id": "mesh_signal", "label": "Signal", "kind": "mesh_gate", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "1_lifecycle"},
        {"id": "mesh_qualify", "label": "Qualify", "kind": "mesh_gate", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "1_lifecycle"},
        {"id": "mesh_bind", "label": "Bind", "kind": "mesh_gate", "lifecycle_state": "held", "authority": "steward_directed_working_definition", "group": "1_lifecycle"},
        {"id": "mesh_realise", "label": "Realise", "kind": "mesh_gate", "lifecycle_state": "held", "authority": "d001_decision_gate", "group": "2_realisation"},
    ],
    [
        {"id": "e1", "from": "mesh_signal", "to": "mesh_qualify", "verb": "gates_to"},
        {"id": "e2", "from": "mesh_qualify", "to": "mesh_bind", "verb": "gates_to"},
        {"id": "e3", "from": "mesh_bind", "to": "mesh_realise", "verb": "gates_to"},
    ],
)

DATA["signal_to_asset"] = fixture(
    "signal_to_asset",
    "Signal-to-Asset Relationship — labelled fixture",
    [
        {"id": "s2a_signal", "label": "Signal", "kind": "s2a_stage", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "1_capture"},
        {"id": "s2a_event", "label": "Benefit Event", "kind": "s2a_stage", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "2_event"},
        {"id": "s2a_asset", "label": "Asset (X/Y/Z)", "kind": "s2a_stage", "lifecycle_state": "held", "authority": "steward_directed_working_definition", "group": "3_asset"},
    ],
    [
        {"id": "e1", "from": "s2a_signal", "to": "s2a_event", "verb": "captured_as"},
        {"id": "e2", "from": "s2a_event", "to": "s2a_asset", "verb": "compounds_into"},
    ],
)

DATA["service_pattern_method_canonical"] = fixture(
    "service_pattern_method_canonical",
    "Service / Pattern / Method / Canonical — labelled fixture",
    [
        {"id": "spmc_service", "label": "Service", "kind": "spmc_layer", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "1_service"},
        {"id": "spmc_pattern", "label": "Pattern", "kind": "spmc_layer", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "2_pattern"},
        {"id": "spmc_method", "label": "Method", "kind": "spmc_layer", "lifecycle_state": "candidate", "authority": "steward_directed_working_definition", "group": "3_method"},
        {"id": "spmc_canonical", "label": "Canonical", "kind": "spmc_layer", "lifecycle_state": "active", "authority": "steward_ratified", "group": "4_canonical"},
    ],
    [
        {"id": "e1", "from": "spmc_service", "to": "spmc_pattern", "verb": "instantiates"},
        {"id": "e2", "from": "spmc_pattern", "to": "spmc_method", "verb": "operationalised_by"},
        {"id": "e3", "from": "spmc_method", "to": "spmc_canonical", "verb": "candidate_for_promotion_to"},
    ],
)

DATA["work_object_queue"] = fixture(
    "work_object_queue",
    "Current Work Object Queue — labelled fixture",
    [
        {"id": "wo_b", "label": "WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001 (this wave)", "kind": "work_object", "lifecycle_state": "active", "authority": "wave_controller_v0.2", "group": "1_active"},
        {"id": "wo_a", "label": "Stream A — Codex runtime/integration graph", "kind": "work_object_lane", "lifecycle_state": "candidate", "authority": "wave_controller_v0.2", "group": "2_lanes"},
        {"id": "wo_c", "label": "Stream C — Claude CoWork/Fable visual system", "kind": "work_object_lane", "lifecycle_state": "candidate", "authority": "wave_controller_v0.2", "group": "2_lanes"},
        {"id": "wo_d009", "label": "D009 integrated assurance", "kind": "work_object_lane", "lifecycle_state": "held", "authority": "wave_controller_v0.2", "group": "3_held"},
    ],
    [
        {"id": "e1", "from": "wo_b", "to": "wo_a", "verb": "runs_alongside"},
        {"id": "e2", "from": "wo_b", "to": "wo_c", "verb": "runs_alongside"},
        {"id": "e3", "from": "wo_a", "to": "wo_d009", "verb": "feeds"},
        {"id": "e4", "from": "wo_c", "to": "wo_d009", "verb": "feeds"},
    ],
)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in DATA.items():
        path = OUT / f"{name}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {path} ({len(data['objects'])} objects, {len(data['relationships'])} relationships)")
