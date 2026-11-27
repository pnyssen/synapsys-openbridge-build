"""Generates the HTML/JSON a correctly installed RC06a would return, from the same code the offline tests use, and a set of WRONG
installs (the RC05e golden pages, a reordered frame, a five-column table). Used only to test verify/ui_verify_console_rc06a_v1.js
offline. Nothing here touches Odoo or dev. Output: JSON on stdout.  usage: python3 gen_ui_fixtures_rc06a.py"""
import importlib.util, json, os, re, sys, types
import fakes as F

LENSES = os.path.join(F.ADDON, "controllers", "lenses.py")
LV = {
    1: '<style>x</style><div class="lv"><div class="cr">Level 1 of 3 · Architecture, Lenses, Enable</div><h1>Lenses</h1><div class="gr"><a class="cd"><h3>The lens pattern</h3><div class="sb">Enable, Enhance, Enrich: the repeatable structure</div></a></div><p class="nt">Registry</p></div>',
    2: '<style>x</style><div class="lv"><div class="cr">Level 2 of 3 · Architecture, Lenses · <a data-lv="1" data-g="">Lenses</a> / The lens pattern, Enhance</div><h1>The lens pattern</h1><p class="nt">Click one</p></div>',
    3: '<style>x</style><div class="lv"><div class="cr">Level 3 of 3 · Architecture, Lenses · <a data-lv="1" data-g="">Lenses</a> / <a data-lv="2" data-g="pattern">The lens pattern</a> / Enrich</div><h1>Enable</h1><div class="cd bx">Enable and Enrich as words</div></div>'}


def lens_controller():
    odoo = types.ModuleType("odoo"); h = types.ModuleType("odoo.http")
    class Controller: pass
    class Req: env = None
    h.Controller = Controller; h.route = lambda *a, **k: (lambda f: f); h.request = Req; odoo.http = h
    addons = types.ModuleType("odoo.addons"); syn = types.ModuleType("odoo.addons.synapsys")
    lr = types.ModuleType("odoo.addons.synapsys.lens_render"); lc = types.ModuleType("odoo.addons.synapsys.lens_contract")
    lr.STAGES = {"Form": ("a",)}; lr.render = lambda level, g, s, live, verbs: LV[level]; lr.lenses_for = lambda g, s: []
    lc.parse_overrides = lambda ov: {}; lc.render_element = lambda *a: ""; lc.from_lens = lambda l: {}
    syn.lens_render = lr; syn.lens_contract = lc; odoo.addons = addons; addons.synapsys = syn
    for k, v in {"odoo": odoo, "odoo.http": h, "odoo.addons": addons, "odoo.addons.synapsys": syn,
                 "odoo.addons.synapsys.lens_render": lr, "odoo.addons.synapsys.lens_contract": lc}.items():
        sys.modules[k] = v
    spec = importlib.util.spec_from_file_location("lenses_ctl", LENSES); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m, Req


class Rs:
    def search_count(s, d): return 1
    def search(s, d, order=None):
        class X:
            def mapped(s2, f): return ["v"]
        return X()


class U:
    def has_group(s, x): return x == "synapsys.group_synapsys_steward"


class E(dict):
    user = U()


def lens(level):
    m, Req = lens_controller(); e = E(); e["synapsys.mesh.entry"] = Rs(); e["synapsys.verb"] = Rs(); Req.env = e
    return m.SynapsysLenses().lenses_data(level=level)


def good():
    fx = {"lens1": lens(1), "lens2": lens(2), "lens3": lens(3)}
    for d in F.sl.DEPTHS:
        fx["view_" + d] = F.sv.render(F.sw.scaffold_context(F.Env([F.STEW]), d, "1"), d)
    fx["ctx_bad"] = F.sw.scaffold_context(F.Env([F.STEW]), "deep", "1")
    fx["ctx_ok"] = F.sw.scaffold_context(F.Env([F.STEW]), "enrich", "1")
    return fx


def wrong():
    g = good(); out = {}
    old = {d: open(os.path.join(F.HERE, "golden", "rc05e_installed_view_%s.html" % d), encoding="utf-8").read() for d in F.sl.DEPTHS}
    out["rc05e_installed_pages"] = dict(g, **{"view_" + d: old[d] for d in F.sl.DEPTHS})
    swap = lambda h: re.sub(r'(<p class="an" data-slot="answer">.*?</p>)(<p class="tl" data-slot="trust">.*?</p>)', r"\2\1", h, flags=re.S)
    out["frame_reordered"] = dict(g, view_enhance=swap(g["view_enhance"]))
    out["five_column_table"] = dict(g, view_enrich=g["view_enrich"].replace("<th>Open question</th>", "<th>Open question</th><th>Extra</th>"))
    out["frame_reworded_at_enrich"] = dict(g, view_enrich=g["view_enrich"].replace("verbs not yet bound", "no verbs"))
    out["open_question_repeated"] = dict(g, view_enrich=g["view_enrich"].replace("<p class=\"nt\">", "<p>Which domain is Context's home (D001 governance of boundary and rights, D002 which rules kind, or D006/D008)?</p><p class=\"nt\">"))
    ctx = dict(g["ctx_ok"]); ctx.pop("declaration_sha", None)
    out["no_declaration_fingerprint"] = dict(g, ctx_ok=ctx)
    return {"good": g, **out}


if __name__ == "__main__":
    print(json.dumps(wrong()))
