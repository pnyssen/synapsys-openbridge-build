"""Writes the RC06a Context noun-screen output (view HTML and route JSON, three depths) from the RC06a commit e423bb1 itself, so a later
build can prove Context output is byte-identical. Run once, from the repo root:  python3 release/rc06a_screen_architecture/tools/gen_rc06a_context_golden.py"""
import importlib, json, os, subprocess, sys, tempfile
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
COMMIT = "e423bb1"
BASE = "release/rc06a_screen_architecture/addon/synapsys"
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "data"))
for f in ("scaffold_lens.py", "scaffold_wire.py", "scaffold_view.py", "screen_decl.py", "screen_render.py", "data/screen_declarations.json"):
    open(os.path.join(tmp, f), "wb").write(subprocess.check_output(["git", "show", "%s:%s/%s" % (COMMIT, BASE, f)], cwd=REPO))
sys.path.insert(0, tmp)
sys.path.insert(1, os.path.join(REPO, "release/rc06a_screen_architecture/tests"))
sd = importlib.import_module("screen_decl"); sw = importlib.import_module("scaffold_wire"); sv = importlib.import_module("scaffold_view")
assert os.path.dirname(sd.__file__) == tmp
import fakes_core as F  # noqa: E402  (fake env only; does not load the addon)
out = os.path.join(REPO, "release/rc06a_screen_architecture/tests/golden")
for d in ("enable", "enhance", "enrich"):
    o = sw.scaffold_context(F.Env([F.STEW]), d, "1")
    open(os.path.join(out, "rc06a_context_noun_view_%s.html" % d), "w", encoding="utf-8").write(sv.render(o, d))
    open(os.path.join(out, "rc06a_context_noun_route_%s.json" % d), "w", encoding="utf-8").write(json.dumps(o, sort_keys=True, indent=1))
print("golden written from", COMMIT)
