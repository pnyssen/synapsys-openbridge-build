"""D6 table for RC06b batch 1, computed from the declarations and registry 0.3.5 (same code path as the screens). Markdown on stdout."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
import fakes as F
sd, sr, sw, sl = F.sd, F.sr, F.sw, F.sl
decls, meta = sd.load_declarations()
ev, idx, _ = sw.collect_evidence(F.Env([F.STEW]))
print("| Noun | Registry status | Chips kept | Chips dropped | Open questions | made_of (registry relationship) | Sections that read \"None recorded\" or say nothing is declared |")
print("|---|---|---|---|---|---|---|")
for sid, d in decls.items():
    if sid in ("SCR.CONTEXT.NOUN", "SCR.CONTEXT.RECORD", "SCR.ASSET.RECORD"):
        continue
    o = sd.project(d, F.REG, "enrich", {"groups": {"steward"}, "context_ids": set()}, ev, idx, "1", sw.DEFAULT_ROLE_MAX_DEPTH)
    o.update({"registry_state": "candidate", "registry_sha": F.SHA})
    h = sr.render_screen(o)
    row = o["enrich"]["rows"][0]
    nothing = []
    if not d["made_of"]:
        nothing.append("Made of: no roles declared")
    if not d["peers"]:
        nothing.append("Linked peers: none declared")
    if not row["open"]:
        nothing.append("Open questions: none recorded")
    if not row["chips"]:
        nothing.append("Source: None recorded")
    dropped = len(d["claims"][0]["sources"]) - o["frame"]["trust"]["source_count"]
    mo = (d["made_of"] or {}).get("relationship") or "none"
    print("| %s | %s | %d of %d | %d | %d | %s | %s |" % (d["noun"][2:].title(), o["frame"]["trust"]["status"], o["frame"]["trust"]["source_count"], len(d["claims"][0]["sources"]), dropped, len(row["open"]), mo, "; ".join(nothing) or "none"))
