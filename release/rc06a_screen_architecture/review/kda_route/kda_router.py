"""Shared KDA routing v2 (source-only candidate). Fixes P0-1/P0-2/P1-4 of NAV_RETURN_DEFECTS (dac82614...).

Authority never comes from caller-supplied fields. A release exists only if a destination-bound,
PINNED Verifier retrieves the authoritative receipt bytes and every binding checks out. With no pinned
verifier, VERIFIED is unreachable and apply is HOLD. A2 v3 Part F floors/seats are unchanged data.
No I/O of its own, no writes, no Odoo imports.
"""
import hashlib, json
from datetime import datetime, timezone

SEATS_ALL = ["D000", "D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008", "D009", "D010", "D011"]
GPC = {"F0": 3, "F1": 4, "F2": 6, "F3": 8, "F4": 12}
STATUSES = ("applicability", "seat_release", "actor_permission", "executor_admission",
            "pre_effect_assurance", "post_effect_verification")
PINNED_VERIFIER_IDS = frozenset()  # D007 pins destination-bound verifier ids here under release; empty = nothing admissible
EFFECT_CLASSES = ("read_only", "filing", "protected_change")
BOOL_FLAGS = ("data_migration", "production_data", "rights_change", "approval_mechanism_change", "personal_or_financial_data",
              "client_data", "client_rights_or_assets", "rights_holder_changed", "go_live_clients", "whole_mesh",
              "approval_service_adoption", "canon_renumbering", "platform_cutover", "cross_context", "regulation_applies",
              "builder_may_be_decider", "transport_changes", "collaborator_context_k8", "crm_sales_web", "offerings_services_chains",
              "collaborators_partners_portals", "users_ai_orientation", "reads_sensitive", "exports_data")
MUTATING_FLAGS = ("data_migration", "production_data", "rights_change", "approval_mechanism_change", "rights_holder_changed",
                  "go_live_clients", "whole_mesh", "approval_service_adoption", "canon_renumbering", "platform_cutover")
SENSITIVE_READ = ("reads_sensitive", "exports_data", "personal_or_financial_data", "client_data", "client_rights_or_assets")


class ClassificationHold(Exception):
    pass


class Verifier:
    """Interface of a DESTINATION-BOUND verifier. The router never implements one: D007 supplies it.
    Each method must read an authoritative source with the verifier's own credentials."""
    def identity(self): raise NotImplementedError
    def fetch_receipt(self, receipt_id): raise NotImplementedError   # -> {"bytes": b, "issuer": "D007", "status": "RELEASED"} or None
    def scope_bytes(self, scope_ref): raise NotImplementedError      # frozen scope bytes
    def now_utc(self): raise NotImplementedError
    def is_consumed(self, receipt_id): raise NotImplementedError
    def current_pins(self): raise NotImplementedError                # commit/tree/state hashes as they are NOW
    def actor_permission(self, env, model, fields): raise NotImplementedError  # -> {"actor": id, "can_write": bool}
    def executor_state(self, receipt_id): raise NotImplementedError  # -> admitted/route/actor/backup/run_lock/dry_run/rollback
    def d009_challenge(self, receipt_id): raise NotImplementedError  # -> {"provider","verdict","bytes","sha256"} or None
    def receipt_state(self, receipt_id):                              # -> ("AVAILABLE"|"RESERVED"|"CONSUMED", holder_run_id|None)
        return ("CONSUMED", None) if self.is_consumed(receipt_id) else ("AVAILABLE", None)
    def reserve(self, receipt_id, run_id): raise NotImplementedError          # revocable hold, before any write
    def finalize_consume(self, receipt_id, run_id): raise NotImplementedError  # irreversible; ONLY after the DB commit; idempotent for the same run_id
    def release_reservation(self, receipt_id, run_id): raise NotImplementedError  # revocable; only for the holder


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


def scope_digest(scope):
    return hashlib.sha256(canon(scope)).hexdigest()


def _isbool(v):
    return type(v) is bool


def validate_effect(e):
    """Strict schema. Missing, malformed or contradictory classification raises ClassificationHold (fail closed)."""
    if not isinstance(e, dict):
        raise ClassificationHold("EFFECT_NOT_A_DICT")
    for k in ("env", "model", "effect_class"):
        if not isinstance(e.get(k), str) or not e[k]:
            raise ClassificationHold("MISSING_OR_MALFORMED:" + k)
    if e["effect_class"] not in EFFECT_CLASSES:
        raise ClassificationHold("UNKNOWN_EFFECT_CLASS")
    for k in BOOL_FLAGS:
        if k in e and not _isbool(e[k]):
            raise ClassificationHold("MALFORMED_FLAG:" + k)
    if "interfaces" in e and (type(e["interfaces"]) is not int or e["interfaces"] < 0):
        raise ClassificationHold("MALFORMED_INTERFACES")
    mut = e.get("mutates")
    if not _isbool(mut):
        raise ClassificationHold("MUTATES_NOT_EXPLICIT_BOOL")
    cls = e["effect_class"]
    if cls == "read_only" and (mut or any(e.get(k) for k in MUTATING_FLAGS)):
        raise ClassificationHold("CONTRADICTORY_READ_ONLY_WITH_MUTATION")
    if cls == "protected_change" and not mut:
        raise ClassificationHold("CONTRADICTORY_PROTECTED_CHANGE_WITHOUT_MUTATION")
    if cls == "filing" and (any(e.get(k) for k in MUTATING_FLAGS) or any(e.get(k) for k in SENSITIVE_READ)):
        raise ClassificationHold("CONTRADICTORY_FILING_WITH_PROTECTED_FLAGS")
    if e.get("context_kind") not in (None, "K-1", "K-3", "K-4", "K-6", "K-8", "K-12"):
        raise ClassificationHold("UNKNOWN_CONTEXT_KIND")
    return e


def floor_for(e):
    """F0..F5 per A2 v3 F1 table. Highest wins; floors never caps. Sensitive reads/exports are F2."""
    validate_effect(e)
    cls = e["effect_class"]
    if cls in ("read_only", "filing"):
        if any(e.get(k) for k in SENSITIVE_READ):
            return "F2", GPC["F2"], ["F2:sensitive/personal/financial/client data read or export"]
        return "F0", GPC["F0"], ["no system mutation"]
    fl, why = [("F1", 4)], ["protected change"]
    f2 = [k for k in ("data_migration", "production_data", "rights_change", "approval_mechanism_change", "personal_or_financial_data",
                      "client_data", "rights_holder_changed", "reads_sensitive", "exports_data") if e.get(k)]
    if f2:
        fl.append(("F2", 6)); why.append("F2:" + ",".join(f2))
    if e.get("interfaces", 0) >= 2 or e.get("go_live_clients"):
        fl.append(("F3", 8)); why.append("F3 interfaces/go-live")
    if any(e.get(k) for k in ("whole_mesh", "approval_service_adoption", "canon_renumbering", "platform_cutover")):
        fl.append(("F4", 12)); why.append("F4 whole-mesh")
    if e.get("context_kind") == "K-12" and e.get("cross_context"):
        fl.append(("F5", 6)); why.append("F5 advisory raise")
    top = max(fl, key=lambda x: x[1])
    return top[0], top[1], why


def seats_for(e, floor_gpc):
    s = {"D000", "D001", "D002"}
    reps = []
    if e["effect_class"] == "protected_change":
        s.add("D007")
    if e.get("builder_may_be_decider") or floor_gpc >= 6:
        s.add("D009")
    if e.get("regulation_applies") or e.get("personal_or_financial_data"):
        s.add("D011")
    if e.get("client_data") or e.get("client_rights_or_assets"):
        s.add("D006"); reps.append("client representative")
    for k, d in {"crm_sales_web": "D003", "offerings_services_chains": "D004", "collaborators_partners_portals": "D005", "users_ai_orientation": "D010"}.items():
        if e.get(k):
            s.add(d)
    if e.get("transport_changes"):
        s.add("D008")
    if e.get("collaborator_context_k8"):
        reps.append("collaborator representative")
    if floor_gpc >= 12:
        s = set(SEATS_ALL)
    seats = sorted(s)
    return seats, reps, {d: "no trigger in this effect" for d in SEATS_ALL if d not in s}


def resolve_route(env, model, restricted_connector=None):
    if env == "odoo_v20" and model.startswith("x_ss_"):
        return {"route": "V20_MCP_GATED_WRITE", "needs_executor_admission": True, "needs_chg": True, "credentials": "connector-held"}
    if env == "odoo_v20" and model.startswith("synapsys."):
        return {"route": "HOSTINGER_ODOO_SHELL_FAST_PATH", "needs_executor_admission": True, "credentials": "stay at destination; never typed or relayed",
                "precedent": "Wave1 nine-record load (capability discovery only)"}
    if env == "odoo_v19":
        return {"route": "V19_ROUTE_UNCHANGED", "needs_executor_admission": True, "credentials": "route-owned", "note": "never repointed to V20"}
    if env == "n8n":
        return {"route": "N8N_VERIFIED_WORKFLOW_ROUTE", "needs_executor_admission": True, "credentials": "route-owned"}
    if env == "github":
        return {"route": "GIT_OWN_RELEASE", "needs_executor_admission": True, "credentials": "git-held", "note": "default-branch merge needs CR"}
    if env == "sharepoint":
        return {"route": "WM_CREATE_ONLY", "needs_executor_admission": True, "credentials": "connector-held"}
    return {"route": "NO_ROUTE_FOUND", "needs_executor_admission": True, "credentials": None}


def _parse_ts(s):
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def trusted(verifier):
    return isinstance(verifier, Verifier) and verifier.identity() in PINNED_VERIFIER_IDS


def verify_release(ref, effect, verifier, run_id=None):
    """VERIFIED only via a pinned destination-bound verifier reading the authoritative receipt. Returns (status, receipt_body|None)."""
    if not trusted(verifier):
        return "NO_TRUSTED_VERIFIER", None
    if not isinstance(ref, dict) or not isinstance(ref.get("receipt_id"), str) or not ref["receipt_id"]:
        return "UNVERIFIED", None
    got = verifier.fetch_receipt(ref["receipt_id"])
    if not got:
        return "RECEIPT_NOT_FOUND_AUTHORITATIVELY", None
    b = got.get("bytes")
    if not isinstance(b, (bytes, bytearray)) or hashlib.sha256(b).hexdigest() != ref.get("sha256"):
        return "RECEIPT_HASH_MISMATCH", None
    if got.get("issuer") != "D007" or got.get("status") != "RELEASED":
        return "ISSUER_OR_STATUS_INVALID", None
    try:
        body = json.loads(b)
    except Exception:
        return "RECEIPT_MALFORMED", None
    if body.get("receipt_id") != ref["receipt_id"] or body.get("seat") != "D007":
        return "FORGED", None
    scope = effect.get("scope")
    if not isinstance(scope, dict):
        return "SCOPE_MISSING", None
    mine = scope_digest(scope)
    frozen = verifier.scope_bytes(body.get("scope_ref"))
    if not isinstance(frozen, (bytes, bytearray)) or hashlib.sha256(frozen).hexdigest() != mine or body.get("scope_digest") != mine:
        return "SCOPE_DIGEST_MISMATCH", None
    for k_body, k_eff in (("work_object", "work_object"), ("context", "context"), ("env", "env"), ("model", "model")):
        if body.get(k_body) != effect.get(k_eff):
            return "BINDING_MISMATCH:" + k_body, None
    if body.get("fields") != effect.get("fields") or body.get("target_ids") != effect.get("target_ids"):
        return "BINDING_MISMATCH:target", None
    now = verifier.now_utc()
    nb, ex = _parse_ts(body.get("not_before", "")), _parse_ts(body.get("expires", ""))
    if now is None or getattr(now, "tzinfo", None) is None or ex is None or nb is None or not (nb <= now <= ex):
        return "EXPIRED_OR_NOT_YET_VALID_OR_MALFORMED", None
    state = verifier.receipt_state(ref["receipt_id"])
    if not (isinstance(state, tuple) and len(state) == 2) or state[0] not in ("AVAILABLE", "RESERVED"):
        return "REPLAYED", None            # CONSUMED or anything unrecognised fails closed
    if state[0] == "RESERVED" and (run_id is None or state[1] != run_id):
        return "REPLAYED", None            # held by another run (or by none we know)
    if effect.get("pins") != verifier.current_pins():
        return "PINS_DRIFTED", None
    return "VERIFIED", body


GATES = ("seat_release", "actor_permission", "executor_admission", "pre_effect_assurance")


def _allowed(connector, model):
    if not isinstance(connector, dict):
        return False
    return any(model == p or (p.endswith("*") and model.startswith(p[:-1])) for p in connector.get("write_scope", ()))


def _gate(effect, rel, connector, verifier, route, seats, st, run_id):
    st["seat_release"], body = verify_release(rel, effect, verifier, run_id)
    rid = body["receipt_id"] if body else None
    ok_v = trusted(verifier) and body is not None
    if route["route"] == "V20_MCP_GATED_WRITE" and not _allowed(connector, effect["model"]):
        st["actor_permission"] = "MODEL_NOT_IN_CONNECTOR_ALLOWLIST"
    elif ok_v:
        ap = verifier.actor_permission(effect["env"], effect["model"], effect.get("fields"))
        good = isinstance(ap, dict) and ap.get("can_write") is True and bool(ap.get("actor")) and ap.get("actor") == body.get("actor_id")
        st["actor_permission"] = "VERIFIED" if good else "ACTOR_CANNOT_WRITE_OR_NOT_THE_RELEASED_ACTOR"
    elif connector is not None and not _allowed(connector, effect["model"]):
        st["actor_permission"] = "CONNECTOR_CANNOT_WRITE_USE_ROUTE_" + route["route"]
    ex = verifier.executor_state(rid) if ok_v else None
    ex_ok = bool(isinstance(ex, dict) and ex.get("admitted") is True and ex.get("route") == route["route"] and ex.get("actor") == body.get("actor_id")
                 and ex.get("current_release_id") == rid and ex.get("backup_restore_verified") is True and ex.get("run_lock_held") is True
                 and ex.get("dry_run_ok") is True and ex.get("rollback_ready") is True and (not route.get("needs_chg") or bool(body.get("chg"))))
    st["executor_admission"] = "VERIFIED" if ex_ok else "EXECUTOR_ROUTE_UNVERIFIED"
    if "D009" not in seats:
        st["pre_effect_assurance"] = "NOT_REQUIRED"
    elif ok_v:
        ch = verifier.d009_challenge(rid)
        bp = effect.get("builder_provider")
        if not bp:
            st["pre_effect_assurance"] = "BUILDER_PROVIDER_UNKNOWN"
        elif isinstance(ch, dict) and ch.get("provider") == bp:
            st["pre_effect_assurance"] = "SAME_PROVIDER_SELF_ASSURANCE_REJECTED"
        else:
            good = (isinstance(ch, dict) and ch.get("verdict") == "PASS" and ch.get("provider")
                    and isinstance(ch.get("bytes"), (bytes, bytearray)) and hashlib.sha256(ch["bytes"]).hexdigest() == ch.get("sha256"))
            st["pre_effect_assurance"] = "VERIFIED" if good else "INDEPENDENT_CHALLENGE_MISSING_OR_NOT_PASS"



def decide(effect, rel=None, executor=None, connector=None, now_iso=None, d009=None, verifier=None, run_id=None):
    """Six independent statuses. `executor`, `d009`, `now_iso` (legacy params) are NEVER trusted; only the verifier is."""
    try:
        validate_effect(effect)
        fl, gpc, why = floor_for(effect)
    except ClassificationHold as h:
        return {"floor": None, "statuses": {k: "UNVERIFIED" for k in STATUSES}, "disposition": "HOLD_UNCLASSIFIED", "blockers": [str(h)], "needs_steward": False}
    seats, reps, excl = seats_for(effect, gpc)
    route = resolve_route(effect["env"], effect["model"])
    st = {k: "UNVERIFIED" for k in STATUSES}
    st["applicability"] = "APPLIES" if effect["effect_class"] == "protected_change" else "APPLIES_F0_NO_NEW_APPROVAL" if fl == "F0" else "APPLIES"
    if fl == "F0":
        for k in STATUSES[1:]:
            st[k] = "NOT_REQUIRED"
        return {"floor": fl, "gpc": gpc, "seats": seats, "statuses": st, "route": route, "disposition": "PROCEED_F0", "blockers": [], "needs_steward": False}
    if effect["effect_class"] != "protected_change":  # F2 sensitive read/export: seats required, no effect to apply
        return {"floor": fl, "gpc": gpc, "seats": seats, "seats_required": len(seats), "statuses": {**st, "seat_release": "REQUIRED_BEFORE_ACCESS"},
                "route": route, "disposition": "HOLD_SENSITIVE_ACCESS_NEEDS_SEATS", "blockers": ["seat_release"], "needs_steward": False}
    try:
        _gate(effect, rel, connector, verifier, route, seats, st, run_id)
    except Exception as ex_:   # a verifier that errors is a verifier that did not verify
        for g in GATES:
            if st[g] == "VERIFIED":
                st[g] = "VERIFIER_ERROR"
        st["seat_release"] = "VERIFIER_ERROR:" + type(ex_).__name__
    st["post_effect_verification"] = "PENDING_AFTER_EFFECT"
    gates = GATES
    ok = all(st[g] in ("VERIFIED", "NOT_REQUIRED") for g in gates)
    return {"floor": fl, "gpc": gpc, "seats_required": len(seats), "seats": seats, "stakeholder_reps": reps, "excluded": excl, "statuses": st,
            "route": route, "applies_to_this_effect_only": True, "needs_steward": False,
            "disposition": "APPLY_ADMITTED" if ok else "HOLD_APPLY_ONLY",
            "blockers": [g for g in gates if st[g] not in ("VERIFIED", "NOT_REQUIRED") and not st[g].startswith("CONNECTOR_CANNOT")] if not ok else []}


def activation_status(lane, receipt, verifier):
    """R7: a lane inherits the KDA rule only with an authoritative activation receipt showing a CHANGED routing decision. Copied text is not activation."""
    if not trusted(verifier) or not isinstance(receipt, dict):
        return "TEXT_ONLY_NOT_ACTIVATED"
    got = verifier.fetch_receipt(receipt.get("receipt_id", ""))
    if not got or not isinstance(got.get("bytes"), (bytes, bytearray)) or hashlib.sha256(got["bytes"]).hexdigest() != receipt.get("sha256"):
        return "TEXT_ONLY_NOT_ACTIVATED"
    try:
        b = json.loads(got["bytes"])
    except Exception:
        return "TEXT_ONLY_NOT_ACTIVATED"
    return "ACTIVATED" if b.get("lane") == lane and b.get("routing_decision_changed") is True and b.get("native_control") is True else "TEXT_ONLY_NOT_ACTIVATED"


def digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
