"""Writes tests/golden/rc06h_tree_manifest.json: path -> sha256 of every file of the RC06h addon tree (commit e5322c9), so a later build can prove by file hash
what it changed, added or left alone. Run once from the repo root: python3 release/rc06a_screen_architecture/tools/gen_rc06h_tree_manifest.py"""
import hashlib, json, os, subprocess
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
COMMIT, BASE = "e5322c9", "release/rc06a_screen_architecture/addon/synapsys"
files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", COMMIT, BASE], cwd=REPO, text=True).split()
m = {f[len(BASE) + 1:]: hashlib.sha256(subprocess.check_output(["git", "show", "%s:%s" % (COMMIT, f)], cwd=REPO)).hexdigest() for f in files}
assert len(m) == 69
json.dump({"commit": COMMIT, "tree_hash": "5671fcafea9009845ee97b1fc511c335846a7bc38723ef302355457509ac5433", "files": m}, open(os.path.join(REPO, "release/rc06a_screen_architecture/tests/golden/rc06h_tree_manifest.json"), "w"), indent=1, sort_keys=True)
print("manifest of", len(m), "files from", COMMIT)
