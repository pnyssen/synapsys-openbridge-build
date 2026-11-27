"""Enumerates every screen's rendered page at all three depths through the wire entry points, with the offline fakes. Used by the RC06f
baseline generator (run against the RC06e modules from git) and by test_batch6 (run against the working tree). Offline only."""
import fakes_core as F0

DEPTHS = ("enable", "enhance", "enrich")


def all_pages(sd, sw, sv, decls=None):
    """{screen id: {depth: html}} for every declaration. Record screens use in-memory fixtures (a Context at K-12, an Asset in a K-12 Context)."""
    decls = decls or sd.load_declarations()[0]
    out = {}
    for sid, d in decls.items():
        out[sid] = {}
        for depth in DEPTHS:
            t = d["screen_type"]
            if t == "noun":
                o = sw.scaffold_context(F0.Env([F0.STEW]), depth, "1") if sid == "SCR.CONTEXT.NOUN" else sw.scaffold_noun(F0.Env([F0.STEW]), sid, depth, "1")
            elif t == "menu":
                o = sw.scaffold_menu(F0.Env([F0.STEW]), sid, depth)
            else:
                rows = {"synapsys.context": [F0.Row(5, name="CTX-FIXTURE", kind="K-12")],
                        "synapsys.asset": [F0.Row(3, name="Asset fixture", context_id=F0.Row(9, name="C"), context_kind="K-12")]}
                o = sw.screen_record(F0.Env([F0.STEW], records=rows), sid, 5 if sid == "SCR.CONTEXT.RECORD" else 3, depth)
            assert o.get("result") == "OK", (sid, depth, o)
            out[sid][depth] = sv.render(o, depth)
    return out
