"""Shared KDA routing (source-only candidate). One router for every change type.

Implements A2 v3 Part F verbatim as data: floors F0-F5 (highest wins, floors are minimums),
seats S0-S7 (cumulative), then SEPARATES five statuses that must never be conflated:
  applicability | seat_release | actor_permission | executor_admission | implementation_assurance
A restricted connector can change only the actor_permission/route of ONE effect. It can never narrow
applicability or become a reason to ask for credentials. No I/O, no writes, no Odoo imports.
"""
import hashlib, json

SEATS_ALL = ["D000", "D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008", "D009", "D010", "D011"]
GPC = {"F0": 3, "F1": 4, "F2": 6, "F3": 8, "F4": 12}
STATUSES = ("applicability", "seat_release", "actor_permission", "executor_admission", "implementation_assurance")
NOT_ADMITTED = ("INACTIVE_SHADOW", "FORGED", "STALE", "MISMATCH")


def floor_for(e):
    """F0..F5. Returns (floor_id, gpc, reasons). Highest wins; F5 only raises to GPC-6, never grants."""
    fl, why = [], []
    if not e.get("mutates"):
        return "F0", GPC["F0"], ["no system mutation"]
    if e.get("protected", True):
        fl.append(("F1", 4)); why.append("protected change")
    f2 = [k for k in ("data_migration", "production_data", "rights_change", "approval_mechanism_change",
                      "personal_or_financial_data", "client_data", "rights_holder_changed") if e.get(k)]
    if f2:
        fl.append(("F2", 6)); why.append("F2:" + ",".join(f2))
    if e.get("interfaces", 0) >= 2 or e.get("go_live_clients"):
        fl.append(("F3", 8)); why.append("F3 interfaces/go-live")
    if e.get("whole_mesh") or e.get("approval_service_adoption") or e.get("canon_renumbering") or e.get("platform_cutover"):
        fl.append(("F4", 12)); why.append("F4 whole-mesh")
    if e.get("context_kind") == "K-12" and e.get("cross_context"):
        fl.append(("F5", 6)); why.append("F5 advisory raise")
    top = max(fl, key=lambda x: x[1])
    return top[0], top[1], why


def seats_for(e, floor_gpc):
    """S0..S7 cumulative. Returns (seats, stakeholder_reps, excluded_with_reasons)."""
    s = {"D000", "D001", "D002"}
    reps = []
    if e.get("mutates") and e.get("protected", True):
        s.add("D007")
    if e.get("builder_may_be_decider") or floor_gpc >= 6:
        s.add("D009")  # different provider from builder; may not assure its own mechanism
    if e.get("regulation_applies") or e.get("personal_or_financial_data"):
        s.add("D011")
    if e.get("client_data") or e.get("client_rights_or_assets"):
        s.add("D006"); reps.append("client representative")
    dom = {"crm_sales_web": "D003", "offerings_services_chains": "D004", "collaborators_partners_portals": "D005", "users_ai_orientation": "D010"}
    for k, d in dom.items():
        if e.get(k):
            s.add(d)
    if e.get("transport_changes"):
        s.add("D008")
    if e.get("collaborator_context_k8"):
        reps.append("collaborator representative")
    if floor_gpc >= 12:
        s = set(SEATS_ALL)
    seats = sorted(s)
    excluded = {d: "no trigger in this effect" for d in SEATS_ALL if d not in s}
    return seats, reps, excluded


# ---- target-aware executor routes (resolve by target model AND environment) -------------
def resolve_route(env, model, restricted_connector=None):
    """Select an existing authorised route for the actual target. Never repoints V19->V20,
    never creates a second Hostinger/Odoo.sh environment, never widens an allowlist."""
    if env == "odoo_v20" and model.startswith("x_ss_"):
        return {"route": "V20_MCP_GATED_WRITE", "needs_executor_admission": False, "credentials": "connector-held"}
    if env == "odoo_v20" and model.startswith("synapsys."):
        return {"route": "HOSTINGER_ODOO_SHELL_FAST_PATH", "needs_executor_admission": True,
                "credentials": "stay at destination; never typed or relayed", "precedent": "Wave1 nine-record load (capability discovery only)"}
    if env == "odoo_v19":
        return {"route": "V19_ROUTE_UNCHANGED", "needs_executor_admission": True, "credentials": "route-owned", "note": "never repointed to V20"}
    if env == "n8n":
        return {"route": "N8N_VERIFIED_WORKFLOW_ROUTE", "needs_executor_admission": True, "credentials": "route-owned"}
    if env == "github":
        return {"route": "GIT_OWN_RELEASE", "needs_executor_admission": False, "credentials": "git-held", "note": "default-branch merge needs CR"}
    if env == "sharepoint":
        return {"route": "WM_CREATE_ONLY", "needs_executor_admission": False, "credentials": "connector-held"}
    return {"route": "NO_ROUTE_FOUND", "needs_executor_admission": True, "credentials": None}


def verify_release(rel, effect_scope_hash, work_object, context, now_iso):
    """Fail closed. A chat claim alone is recorded but is NOT a verified seat return."""
    if not rel:
        return "UNVERIFIED"
    if rel.get("kind") == "kda_shadow" or rel.get("source") == "n8n_shadow":
        return "INACTIVE_SHADOW"
    if rel.get("seat") != "D007" or not rel.get("receipt_sha256") or len(rel.get("receipt_sha256", "")) != 64:
        return "FORGED"
    if rel.get("scope_hash") != effect_scope_hash:
        return "MISMATCH"
    if rel.get("work_object") != work_object or rel.get("context") != context:
        return "MISMATCH"
    if rel.get("expires") and rel["expires"] < now_iso:
        return "STALE"
    return "VERIFIED"


def decide(effect, rel=None, executor=None, connector=None, now_iso="2026-11-28T00:00:00Z", d009=None):
    """Return the five independent statuses and a disposition. Only the failing effect is held."""
    fl, gpc, why = floor_for(effect)
    seats, reps, excl = seats_for(effect, gpc)
    route = resolve_route(effect["env"], effect["model"])
    st = {k: "UNVERIFIED" for k in STATUSES}
    st["applicability"] = "APPLIES" if effect.get("mutates") or effect.get("decision") else "APPLIES_F0_NO_NEW_APPROVAL"
    if fl == "F0":
        return {"floor": fl, "gpc": gpc, "seats": seats, "statuses": {**st, "seat_release": "NOT_REQUIRED", "actor_permission": "NOT_REQUIRED",
                "executor_admission": "NOT_REQUIRED", "implementation_assurance": "NOT_REQUIRED"}, "route": route, "disposition": "PROCEED_F0"}
    sh = effect.get("scope_hash")
    st["seat_release"] = verify_release(rel, sh, effect.get("work_object"), effect.get("context"), now_iso)
    # connector limit changes the ROUTE for this one effect; it does not touch applicability
    if connector and effect["model"] not in connector.get("write_scope", ()) and not any(effect["model"].startswith(p.rstrip("*")) for p in connector.get("write_scope", ()) if p.endswith("*")):
        st["actor_permission"] = "CONNECTOR_CANNOT_WRITE_USE_ROUTE_" + route["route"]
    else:
        st["actor_permission"] = "CONNECTOR_CAN_WRITE" if connector else "UNVERIFIED"
    ex_ok = bool(executor and executor.get("admitted") and executor.get("current_release_id") == (rel or {}).get("receipt_sha256")
                 and executor.get("backup_restore_evidence") and executor.get("run_lock") and executor.get("dry_run_ok") and executor.get("rollback_ready"))
    st["executor_admission"] = "VERIFIED" if (not route["needs_executor_admission"]) or ex_ok else "EXECUTOR_ROUTE_UNVERIFIED"
    if d009 and d009.get("provider") == effect.get("builder_provider"):
        st["implementation_assurance"] = "SAME_PROVIDER_SELF_ASSURANCE_REJECTED"
    else:
        st["implementation_assurance"] = "VERIFIED" if d009 and d009.get("receipt_sha256") else "PENDING_INDEPENDENT"
    ok = st["seat_release"] == "VERIFIED" and st["executor_admission"] == "VERIFIED"
    return {"floor": fl, "gpc": gpc, "seats_required": len(seats), "seats": seats, "stakeholder_reps": reps, "excluded": excl,
            "statuses": st, "route": route, "applies_to_this_effect_only": True,
            "needs_steward": False,  # only a genuinely NEW authority/consent/investment decision escalates
            "disposition": "APPLY_ADMITTED" if ok else "HOLD_APPLY_ONLY", "blockers": [k for k, v in st.items() if v not in ("VERIFIED", "NOT_REQUIRED", "APPLIES", "PENDING_INDEPENDENT") and not v.startswith("CONNECTOR_CANNOT")]}


def digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
