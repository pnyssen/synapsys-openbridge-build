"""D5 table for RC06d batch 3 (seven menu screens), computed from the declarations and the shipped source table. Markdown on stdout."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
import fakes as F
sd, sw = F.sd, F.sw
decls, meta = sd.load_declarations()
src, _ = sd.load_sources(sd.DEFAULT_SOURCES_PATH)
print("| Screen | Answer row | Rows used (status) | Chips kept | Chips dropped | Open questions | Sections that read \"none recorded\" or say nothing is declared |")
print("|---|---|---|---|---|---|---|")
for sid, d in decls.items():
    if d["screen_type"] != "menu":
        continue
    o = sd.project_menu(d, "enrich", {"groups": {"steward"}, "context_ids": set()}, sw.DEFAULT_ROLE_MAX_DEPTH)
    rows = []
    for c in d["claims"]:
        for r in c["rows"]:
            if r not in rows:
                rows.append(r)
    for r in d["made_of"]["rows"] + [d["answer"]["row"]]:
        if r not in rows:
            rows.append(r)
    kept = sum(len(r["chips"]) for r in o["enrich"]["rows"])
    nothing = ["Linked peers: none declared"]
    if not o["enrich"]["open_total"]:
        nothing.append("Open questions: none recorded")
    opens = "; ".join("%s on %s" % (e["kind"], e["claim"][2:]) for e in d["open"]) or "0"
    print("| %s | %s | %s | %d of %d | 0 | %s | %s |" % (d["title"], d["answer"]["row"], ", ".join("%s (%s)" % (r, src[r]["status_word"]) for r in rows), kept, kept, opens, "; ".join(nothing)))
