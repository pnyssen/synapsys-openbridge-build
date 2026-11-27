"""Renders the real route output (menu_enable) of ONE addon tree for the matrix cases. Run from that tree's tests directory:
   cd <tree>/release/rc06a_screen_architecture/tests && python3 <this file> OUT.json
Fixture registry and declarations come from that tree's own tests (fakes); nothing touches Odoo or the network."""
import json, os, sys
sys.path.insert(0, os.getcwd())
import fakes_core as F0
from fakes import sw
from test_batch5 import E5, BOUND

CASES = (("service", "SCR.SERVICE.NOUN"), ("measures", "SCR.MESH_MEASURES.MENU"), ("noun_ruled", "SCR.PROJECT.NOUN"))
out = {}
for name, sid in CASES:
    b = [x for x in BOUND if x["screen_id"] == sid][0]
    for d in ("enable", "enhance", "enrich"):
        r = sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], b["screen_id"], d)
        out["%s|%s" % (name, d)] = {"action": b["action_id"], "screen": sid, "result": r.get("result"), "reason": r.get("reason"), "html": r.get("html", "")}
json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True)
print("rendered", len(out), "cases from", os.getcwd())
