"""Generates addon/synapsys/data/screen_bindings_batch5.json from the Navigator's N1 spec
(NAV_N1_RC06_BATCH5_LIVE_MENU_DECLARATION_BINDING_20261127_v1.json, sha256 9e316030d709896390c99cf845848d17c2d87e678a08344d0c6da54b43d695ee).
Rows are copied field by field from N1, never retyped; a field is kept only if the binding route or a test needs it. Build aid, not part of the addon.
usage: python3 gen_batch5_bindings.py N1.json > out.json"""
import hashlib, json, sys

raw = open(sys.argv[1], "rb").read()
assert hashlib.sha256(raw).hexdigest() == "9e316030d709896390c99cf845848d17c2d87e678a08344d0c6da54b43d695ee", "not the N1 spec"
n1 = json.loads(raw.decode("utf-8"))
rows = n1["rows"]
assert len(rows) == 51 and len({r["menu_id"] for r in rows}) == 51
NONE_NOS = [17, 18, 34, 35, 36, 37, 38, 42]
out = []
for r in rows:
    bound = r["bind_decision"] == "BIND_ENABLE_OVERLAY_PRESERVE_NATIVE_ACTION"
    assert bound == (r["declaration_screen_id"] is not None), r["screen_no"]
    assert (r["bind_decision"] == "NONE_KEEP_EXISTING_NATIVE") == (r["screen_no"] in NONE_NOS), r["screen_no"]
    out.append({
        "screen_no": r["screen_no"], "menu_id": r["menu_id"], "menu_name": r["menu_name"], "parent_id": r["parent_id"], "current_menu_path": r["current_menu_path"],
        "action_type": r["action_type"], "action_id": r["action_id"], "action_xmlid": r["action_xmlid"], "action_name": r["action_name"],
        "native": {"model": r["model"], "view_type": r["view_type"], "action_view_refs": r["action_view_refs"], "action_context": r["action_context"],
                   "action_domain": r["action_domain"], "client_tag": r["client_tag"]},
        "bind_decision": r["bind_decision"], "screen_id": r["declaration_screen_id"], "declaration_type": r["declaration_type"],
        "none_reason": r["none_reason"], "record_form_variant": r["record_form_variant"],
        "menu_groups": {"root": r["acl_current"]["root_menu_groups"], "leaf": r["acl_current"]["leaf_menu_groups"]},
        "navigator_placement_default": r["navigator_placement_default"], "binding_status": r["source_status"]})
doc = {"schema": "synapsys.screen.bindings/1",
       "origin": "Generated from NAV_N1_RC06_BATCH5_LIVE_MENU_DECLARATION_BINDING_20261127_v1.json (sha256 9e316030d709896390c99cf845848d17c2d87e678a08344d0c6da54b43d695ee), the Navigator's read-only spec, with menu_id and action_xmlid as anchors (N1 implementation_contract). The ids are those read from dev V20 on 27 Nov; on a database where they differ the binding refuses (fail closed).",
       "status": "SOURCE CANDIDATE, NON_AUTHORISING. Binding status as N1 states it: CANDIDATE_NOT_ADOPTED. Not installed.",
       "rows": out}
print(json.dumps(doc, indent=1, ensure_ascii=False))
