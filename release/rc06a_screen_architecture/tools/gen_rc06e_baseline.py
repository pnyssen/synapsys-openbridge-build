"""Writes tests/golden/rc06e_baseline.json: for every screen and depth, the sha256 of the RC06e visible text and of the RC06e markup (style block removed),
from the RC06e commit 970528c itself, plus copies of the three RC06e Context view goldens. Run once from the repo root:
  python3 release/rc06a_screen_architecture/tools/gen_rc06e_baseline.py
Visible text = the page with its style block and tags removed and whitespace collapsed. Two normalisations, both for RC06f's own stated changes: the S13 original
status note is removed from the baseline text (RC06f replaces it with the placeholder note), and the 'Source table fingerprint' line is removed (the batch 3 source
table changes, so its fingerprint does)."""
import hashlib, html, importlib, json, os, re, subprocess, sys, tempfile
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
COMMIT = "970528c"
BASE = "release/rc06a_screen_architecture/addon/synapsys"
TESTS = os.path.join(REPO, "release/rc06a_screen_architecture/tests")
tmp = tempfile.mkdtemp()
files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", COMMIT, BASE], cwd=REPO, text=True).split()
for f in files:
    rel = f[len(BASE) + 1:]
    if rel.endswith((".py", ".json")) and not rel.startswith(("tests/", "controllers/", "migrations/", "models/", "static/")):
        os.makedirs(os.path.dirname(os.path.join(tmp, rel)) or tmp, exist_ok=True)
        open(os.path.join(tmp, rel), "wb").write(subprocess.check_output(["git", "show", "%s:%s" % (COMMIT, f)], cwd=REPO))
sys.path.insert(0, tmp); sys.path.insert(1, TESTS)
os.environ.setdefault("SYN_REG_FIXTURE", os.path.join(REPO, "release/rc05_scaffold_lens/fixtures/mesh_registry_v0_3.json"))
sd = importlib.import_module("screen_decl"); sw = importlib.import_module("scaffold_wire"); sv = importlib.import_module("scaffold_view")
assert os.path.dirname(sd.__file__) == tmp
import pages_all
S13_NOTE = "proposal, Steward decision 3 unruled"


def visible(h):
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", h, flags=re.S)))).strip()
    t = re.sub(r"Source table fingerprint [0-9a-f]{12}", "", t)
    t = t.replace(" (%s)" % S13_NOTE, "").replace(" %s" % S13_NOTE, "")
    return re.sub(r"\s+", " ", t).strip()


def markup(h):
    return re.sub(r"<style>.*?</style>", "", h, flags=re.S)


pages = pages_all.all_pages(sd, sw, sv)
out = {sid: {d: {"text_sha": hashlib.sha256(visible(h).encode()).hexdigest(), "markup_sha": hashlib.sha256(markup(h).encode()).hexdigest()} for d, h in ds.items()} for sid, ds in pages.items()}
json.dump({"commit": COMMIT, "screens": out}, open(os.path.join(TESTS, "golden", "rc06e_baseline.json"), "w"), indent=1, sort_keys=True)
for d in ("enable", "enhance", "enrich"):
    open(os.path.join(TESTS, "golden", "rc06e_context_noun_view_%s.html" % d), "w", encoding="utf-8").write(pages["SCR.CONTEXT.NOUN"][d])
print("baseline written from", COMMIT, len(out), "screens")
