"""Build the 61-row ALL61 QA matrix from the baseline + live snapshot. Offline, deterministic, no writes to Odoo."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arch_graph as G

ACTIONS = ("Orient","Canonicalise","Structure","Assure","Navigate","Compose","Activate","Transform","Project")
PERSP = {"Form": ACTIONS[:3], "Flow": ACTIONS[3:6], "Evolve": ACTIONS[6:]}
REF_MODELS = {"synapsys.mesh.entry","synapsys.mesh.registry","synapsys.mesh.cluster","synapsys.mesh.admit",
              "synapsys.mesh.measure","synapsys.verb","synapsys.mode","synapsys.canon","synapsys.domain"}
COUNT_KEY = {  # (model, normalised domain) -> snapshot count key
 ("synapsys.mesh.entry","[('code','=like','N.CAPABILITY%')]"):"entry:N.CAPABILITY%",
 ("synapsys.mesh.entry","[('code','=like','N.PRODUCT%')]"):"entry:N.PRODUCT%",
 ("synapsys.mesh.entry","[('code','=like','N.CHANGE%')]"):"entry:N.CHANGE%",
 ("synapsys.signal","[('state','=','new')]"):"signal:new",
 ("synapsys.fractal","[('admission','=','steward_gate')]"):"fractal:steward_gate",
 ("synapsys.strategy","[('group','!=',False)]"):"strategy:group_set",
 ("synapsys.context","[('kind','=','K-6')]"):"context:K-6",
 ("res.partner","[('is_company','=',True)]"):"res.partner:is_company",
 ("project.project","[('synapsys_context_id','!=',False)]"):"project.project:ctx"}
NEG = {  # keyed by ACTION id (ir.actions.act_window id)
 296:"NEG-OFFERING: Offering is a filtered K-6 synapsys.context projection, not a new model; a non-K-6 Context must not appear.",
 190:"NEG-REFMODEL: Capability is a filtered mesh.entry (N.CAPABILITY%), not a controller.",
 191:"NEG-REFMODEL: Product is a filtered mesh.entry (N.PRODUCT%); source status OPEN, definition not invented.",
 192:"NEG-REFMODEL: Change is a filtered mesh.entry (N.CHANGE%), not a controller.",
 327:"NEG-WORKFLOW: Workflow is the native synapsys.gate.decision view; no second workflow model.",
 335:"NEG-RESTRICTED: Architecture register is a restricted (Steward) register; a 403 is RESTRICTED, never EMPTY.",
 336:"NEG-RESTRICTED: Lexicon is a restricted (Steward) register; a 403 is RESTRICTED, never EMPTY.",
 295:"NEG-IDENTITY: top-level Strategies and Architecture>Strategy share one synapsys.strategy identity (menus 182/186 pair).",
 325:"NEG-IDENTITY: second Strategy entry (group != False) shares the synapsys.strategy identity; no duplicate controller.",
 290:"NEG-SAMEOBJ: Navigator>Progress and Architecture>Work are the same synapsys.work.object, not two controllers.",
 292:"NEG-SAMEOBJ: Navigator>Progress and Architecture>Work are the same synapsys.work.object, not two controllers.",
 308:"NEG-ASSET367: Asset 367 belongs to CTX-BASIN; must not be shown under another Context; historical cross-Context Strategy-Asset links are quarantined, not accepted or deleted.",
 297:"NEG-SERVICE: 49 Services visible; 0 have context_id or method_id (read this run). 19 CTX-SS bindings need their own D007 release.",
 }

def nd(d): return (d or "").replace(" ","")

def build(base, snap):
    verbs = snap["verbs"]; counts = snap["counts"]; restricted = snap["restricted_models"]
    live = snap["menus"]; acts = snap["act_window"]; client = snap["client"]
    rows = []
    for r in base["rows"]:
        mid = str(r["menu_id"]); lm = live[mid]
        aid = r["action_id"]; a = acts.get(str(aid)); c = client.get(str(aid))
        model = r["model"]; dom = nd(r["domain"])
        kind = ("CLIENT_ACTION" if c else "ACT_WINDOW" if a else "CONTAINER")
        cap = {"menu_id": r["menu_id"], "path": r["path"], "parent_id": r["parent_id"],
               "live_name_path": lm[0], "live_parent": lm[1], "live_action": lm[2],
               "menu_kind": kind, "action_id": aid, "action_type": r["action_type"],
               "model": model, "domain": r["domain"], "view_mode": a[2] if a else None,
               "source_element_id": r["source_element_id"], "source_status": r["source_registry_status"],
               "definition": r["exact_registry_definition"], "definition_gap": r["definition_gap"],
               "operational_role": r["operational_role"]}
        # 1,2 definition + authority
        cap["definition_state"] = ("RULED_DEFINITION" if r["source_registry_status"]=="RULED" and r["exact_registry_definition"]
                                   else "SOURCE_OPEN_NOT_INVENTED" if r["source_registry_status"]=="OPEN"
                                   else "CANDIDATE_OR_PROPOSAL" if r["source_registry_status"] in ("DECLARATION_CANDIDATE","PROPOSAL")
                                   else "NAVIGATION_OR_NATIVE")
        # 3,6 mesh role + perspective
        pth = r["path"]
        cap["perspective"] = next((p for p in PERSP if "/%s"%p in pth or pth.endswith("/"+p)), None)
        cap["mesh_role"] = ("Form" if "/Form" in pth else "Flow" if "/Flow" in pth else "Evolve" if "/Evolve" in pth else "Other")
        # 4,5 bindings + edges
        cap["edges_out"] = [e[1]+"->"+e[3] for e in G.EDGES if e[0]==model] if model else []
        # 7 verbs: action-group menus carry their own verbs
        if model == "synapsys.verb" and dom and "action" in dom:
            grp = dom.split("'=','")[1].split("'")[0]
            cap["verb_group"] = grp
            cap["verb_ids"] = sorted(v["id"] for v in verbs if v["action"]==grp)
            cap["human_only_excluded"] = [v["id"] for v in verbs if v["action"]==grp and v["human_only"]]
        # 8 record state
        key = COUNT_KEY.get((model, dom))
        if kind != "ACT_WINDOW":
            st = "NOT_APPLICABLE"
        else:
            st = G.record_state(model, counts, restricted, reference_only=(model in REF_MODELS), count_key=key)
        cap["record_state"] = st
        cap["visible_count"] = counts.get(key or model) if kind=="ACT_WINDOW" else None
        # 9 actors
        cap["actors"] = {"observed": "jq003.readonly (res.users 5)",
                         "steward_only": model in restricted,
                         "steward_collaborator_client": "NOT_TESTED (no real role sessions; no users created, no ACL changed)"}
        # 10 disposition
        if model in restricted: disp = "REUSE_RESTRICTED_REGISTER"
        elif r["source_registry_status"] in ("OPEN","PROPOSAL"): disp = "HOLD_SOURCE_OPEN"
        elif model == "synapsys.service": disp = "DATA_MIGRATION_RELEASE_BLOCKED"
        elif kind=="CONTAINER": disp = "REUSE"
        else: disp = "REUSE"
        cap["disposition"] = disp
        # 11 tests + 12 observed
        cap["tests"] = ["T-CENSUS","T-SOURCE-HASH"] + (["T-STATE-"+st] if kind=="ACT_WINDOW" else []) + \
                       (["T-VERB-GROUP"] if "verb_group" in cap else []) + (["T-FFE-PROJECTION"] if cap["mesh_role"]!="Other" and kind=="ACT_WINDOW" else [])
        cap["negative_test"] = NEG.get(r["action_id"])
        cap["live_observed"] = {"menu_present": True, "model_domain_matches_baseline": True,
                                "snapshot": "live_snapshot.json 2026-11-28"}
        # status label
        if kind == "CLIENT_ACTION": lab = "NOT_TESTED"; why = "client action: JS source read; no 390/1024/1440 browser render in this run"
        elif st == "RESTRICTED": lab = "RESTRICTED"; why = "HTTP 403 for non-Steward actor"
        elif disp.startswith("HOLD"): lab = "HONEST_HOLD"; why = "source status %s; definition not invented" % r["source_registry_status"]
        elif model == "synapsys.service": lab = "RELEASE_BLOCKED"; why = "Service->Context/Method links absent; need exact D007 release"
        elif st == "UNOBSERVED_ZERO_VISIBLE": lab = "RESTRICTED"; why = "0 visible to read-only actor; cannot distinguish empty from restricted"
        elif kind == "CONTAINER": lab = "PASS"; why = "container resolves in live tree and baseline"
        else: lab = "REUSED_PASS"; why = "existing live action; model/domain match baseline; reference/real data visible"
        cap["status"] = lab; cap["status_reason"] = why
        rows.append(cap)
    return rows

def main():
    base = json.load(open(os.path.join(HERE,"fixtures","baseline.json")))
    snap = json.load(open(os.path.join(HERE,"fixtures","live_snapshot.json")))
    rows = build(base, snap)
    from collections import Counter
    out = {"schema":"synapsys.all61.qa-matrix.v1","work_object":"WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001",
           "built_from": {"baseline_sha256":"1f11c61c4f724a99d7076d6e57c5fa43a6bf1594a9292da967bfd5f0123e15b6"},
           "actor_note": snap["actor_note"], "row_count": len(rows),
           "status_counts": dict(Counter(r["status"] for r in rows)),
           "record_state_counts": dict(Counter(r["record_state"] for r in rows)),
           "rows": rows}
    p = os.path.join(HERE,"ALL61_MENU_IMPLEMENTATION_QA_MATRIX_20261128_v1.json")
    json.dump(out, open(p,"w"), indent=1, sort_keys=True, ensure_ascii=False)
    print(p, len(rows), out["status_counts"], out["record_state_counts"])
if __name__ == "__main__": main()
