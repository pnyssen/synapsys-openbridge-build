"""Generate the EXACT manifest delta for releasing the Master Architecture interface (a RELEASE CANDIDATE; nothing here is applied).
Output: addon/synapsys/candidates/MASTER_MANIFEST_DELTA.patch (unified diff of __manifest__.py, additive lines only).
Edits: (1) data += the candidate menu/action XML, (2) web.assets_backend += the three client files (navigation module first, because the component imports it).
Deterministic. Run: python3 tools/gen_master_manifest_delta.py [--check]"""
import difflib, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MAN = os.path.join(ROOT, "addon", "synapsys", "__manifest__.py")
OUT = os.path.join(ROOT, "addon", "synapsys", "candidates", "MASTER_MANIFEST_DELTA.patch")
REL = "release/rc06a_screen_architecture/addon/synapsys/__manifest__.py"
DATA_OLD = "        'views/synapsys_enable_peers.xml',\n    ],"
DATA_NEW = "        'views/synapsys_enable_peers.xml',\n        'candidates/synapsys_master_menu_candidate.xml',\n    ],"
ASSET_NEW = "'synapsys/static/src/enable_panel.xml', 'synapsys/static/src/master/master_nav.js', 'synapsys/static/src/master/master.js', 'synapsys/static/src/master/master.xml']"

def patched(text):
    assert text.count(DATA_OLD) == 1, "data anchor"
    assert text.count("'synapsys/static/src/enable_panel.xml']") == 1, "assets anchor"
    return text.replace(DATA_OLD, DATA_NEW).replace("'synapsys/static/src/enable_panel.xml']", ASSET_NEW)

def build():
    old = open(MAN, encoding="utf-8").read()
    return "".join(difflib.unified_diff(old.splitlines(True), patched(old).splitlines(True), "a/" + REL, "b/" + REL, n=2))

if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv:
        sys.exit(0 if os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text else 1)
    open(OUT, "w", encoding="utf-8").write(text); print(OUT, len(text.encode()))
