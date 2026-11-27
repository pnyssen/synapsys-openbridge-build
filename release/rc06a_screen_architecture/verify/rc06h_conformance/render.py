import sys, json, os
sys.path.insert(0, os.getcwd())
import fakes_core as F0
from fakes import sw
from test_batch5 import E5, BOUND
out={}
for b in BOUND:
    if b["screen_id"] in ("SCR.SERVICE.NOUN","SCR.MESH_MEASURES.MENU"):
        for d in ("enable","enhance","enrich"):
            r=sw.menu_enable(E5([F0.STEW]), b["action_id"], b["menu_id"], b["screen_id"], d)
            out["%s|%s"%(b["screen_id"],d)]={"action":b["action_id"],"res":r["result"],"html":r.get("html","")}
json.dump(out,open("/tmp/cf/pages.json","w"))
for k,v in out.items(): print(k,v["action"],v["res"],len(v["html"]))
