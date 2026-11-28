"""Generate the ONE versioned Master Architecture definition file (addon/synapsys/data/arch_master_definition.json).
Deterministic: same inputs, same bytes. Sources, all in the repository: review/all61 baseline + live snapshot (via build_matrix) and the
byte-pinned Navigator integration contract (typed relationships). Declarations stay FILES; no Odoo mirror. Invents nothing: a menu whose
source element is OPEN or a candidate keeps that status and its definition_gap.
Run: python3 tools/gen_arch_master_definition.py [--check]   (--check exits 1 if the committed file differs)"""
import hashlib, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
A61 = os.path.join(ROOT, "review", "all61")
OUT = os.path.join(ROOT, "addon", "synapsys", "data", "arch_master_definition.json")
sys.path.insert(0, A61)
import build_matrix as M, arch_graph as G

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def build():
    base = json.load(open(os.path.join(A61, "fixtures", "baseline.json")))
    snap = json.load(open(os.path.join(A61, "fixtures", "live_snapshot.json")))
    contract_p = os.path.join(A61, "navigator_integration_contract.json")
    contract = json.load(open(contract_p))
    rows = M.build(base, snap)
    persp = {(e[0], e[1]): e[4] for e in G.EDGES}
    menus = []
    for r in sorted(rows, key=lambda x: x["menu_id"]):
        cm = contract["menus"][str(r["menu_id"])]
        edges = [{"field": e["field"], "target_model": e["target_model"], "cardinality": e["cardinality"], "direction": e["direction"],
                  "perspective": persp.get((r["model"], e["field"]))} for e in cm["relationships"]]
        menus.append({"menu_id": r["menu_id"], "path": r["path"], "parent_id": r["parent_id"], "kind": r["menu_kind"], "action_ref": r["live_action"],
                      "client_tag": None, "model": r["model"], "domain": r["domain"], "view_mode": r["view_mode"], "mesh_role": r["mesh_role"],
                      "perspective_home": r["perspective"], "source_element_id": r["source_element_id"], "source_status": r["source_status"],
                      "definition_state": r["definition_state"], "definition": r["definition"], "definition_gap": r["definition_gap"],
                      "operational_role": r["operational_role"], "edges": edges, "matrix_status": r["status"], "status_reason": r["status_reason"],
                      "negative_test": r.get("negative_test"), "steward_only": bool((r.get("actors") or {}).get("steward_only"))})
    verbs = [{k: v[k] for k in ("id", "name", "action", "plane", "human_only", "grammar_status")} for v in snap["verbs"]]
    actions = {}
    for v in verbs: actions.setdefault(v["action"], []).append(v["id"])
    from_tags = {331: "synapsys_home", 332: "synapsys_architecture_map", 358: "synapsys_lenses"}
    for m in menus:
        if m["kind"] == "CLIENT_ACTION": m["client_tag"] = from_tags.get(int(m["action_ref"].split(",")[1]))
    return {"schema": "synapsys.arch.master.definition.v1", "status": "SOURCE_READY_NOT_INSTALLED",
            "authority": "versioned FILE; no competing Odoo mirror until ruled (Steward answer 27 Nov 2026)",
            "source_pins": {"contract_sha256": sha(contract_p), "baseline_sha256": sha(os.path.join(A61, "fixtures", "baseline.json")),
                            "live_snapshot_sha256": sha(os.path.join(A61, "fixtures", "live_snapshot.json"))},
            "counts": {"menus": len(menus), "actions": sum(1 for m in menus if m["kind"] != "CONTAINER"),
                       "containers": sum(1 for m in menus if m["kind"] == "CONTAINER"), "verbs": len(verbs)},
            "cut_b": G.CUT_B, "action_groups": {k: list(v) for k, v in G.ACTION_GROUPS.items()},
            "verbs": verbs, "action_verbs": actions, "modes": snap["modes"], "menus": menus,
            "typed_edges": [{"from_model": e[0], "field": e[1], "type": e[2], "to_model": e[3], "perspective": e[4], "evidence": e[5]} for e in G.EDGES],
            "forbidden_pairs": sorted(list(p) for p in G.FORBIDDEN_PAIRS)}

def render(d): return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

if __name__ == "__main__":
    text = render(build())
    if "--check" in sys.argv:
        sys.exit(0 if os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text else 1)
    open(OUT, "w", encoding="utf-8").write(text); print(OUT, len(text.encode()), hashlib.sha256(text.encode()).hexdigest())
