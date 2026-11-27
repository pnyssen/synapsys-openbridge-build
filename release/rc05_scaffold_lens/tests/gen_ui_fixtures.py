"""Generates the HTML/JSON a correctly installed RC05e would return, from the same code the offline tests use. Used only to test ui_verify_console.js."""
import importlib.util, json, os, sys, types
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, HERE)
LENSES = os.environ.get("LENSESPY", os.path.join(ROOT, "patched", "lenses.py")); VIEW = os.environ.get("VIEW_SRC", os.path.join(ROOT, "src", "scaffold_view.py"))
import test_scaffold_view_ui as tu            # reuses the stub odoo modules and the crumb-accurate lens_render stub
import test_scaffold_wire as tw
ctl = tu.L; tu.L.setUpClass()
m = tu.load("lenses_ctl2", LENSES); sv = tu.load("scaffold_view", VIEW); import scaffold_wire as sw
def lens(level): 
    ctl.Req.env = tu.L().env(True); return m.SynapsysLenses().lenses_data(level=level)
fx = {"lens1": lens(1), "lens2": lens(2), "lens3": lens(3)}
for d in ("enable", "enhance", "enrich"):
    out = sw.scaffold_context(tw.Env([tw.STEW]), d, "1"); fx["view_" + d] = sv.render(out, d)
fx["ctx_bad"] = sw.scaffold_context(tw.Env([tw.STEW]), "deep", "1"); fx["ctx_ok"] = sw.scaffold_context(tw.Env([tw.STEW]), "enrich", "1")
print(json.dumps(fx))
