"""Mutation controls for the Navigator-contract reconciler blind-spot fixes (view_mode, client_tag, cardinality).
One fault per run in a COPY; test_navigator_contract.py must fail (KILLED). Run: python3 -I run_mutants_reconciler.py (exit 1 on survivor / stale pattern)."""
import os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
F = "navigator_contract.py"
M = [
 ("view_mode compare removed", "elif _modes(L.get('view_mode')) != _modes(cvm):", "elif False:"),
 ("view_mode order ignored", "return [x.strip() for x in str(v).split(',') if x.strip()] if v else []", "return sorted(x.strip() for x in str(v).split(',') if x.strip()) if v else []"),
 ("view_mode unread passes silently", "holds.append({'code': 'VIEW_MODE_NOT_READ'", "pass; _x = ({'code': 'VIEW_MODE_NOT_READ'"),
 ("client_tag drift removed", "elif lt != pin:", "elif False:"),
 ("client_tag unread passes silently", "holds.append({'code': 'CLIENT_TAG_NOT_READ'", "pass; _x = ({'code': 'CLIENT_TAG_NOT_READ'"),
 ("client_tag unpinned accepted", "holds.append({'code': 'CLIENT_TAG_UNPINNED'", "pass; _x = ({'code': 'CLIENT_TAG_UNPINNED'"),
 ("pin 332 and 358 swapped", "332: 'synapsys_architecture_map', 358: 'synapsys_lenses'", "332: 'synapsys_lenses', 358: 'synapsys_architecture_map'"),
 ("pin invented for unknown action", "pin = PINNED_CLIENT_TAGS.get(c['identity']['action_id'])", "pin = PINNED_CLIENT_TAGS.get(c['identity']['action_id'], lt_default := 'x')"),
 ("cardinality compare removed", "elif CARDINALITY_OF_TYPE.get(f['type']) != e.get('cardinality'):", "elif False:"),
 ("one2many treated as one", "'one2many': 'many'", "'one2many': 'one'"),
 ("field type unread passes silently", "holds.append({'code': 'FIELD_TYPE_NOT_READ'", "pass; _x = ({'code': 'FIELD_TYPE_NOT_READ'"),
 ("client_tag check skipped for client actions", "if L is not None and c['identity']['kind'] == 'CLIENT_ACTION':", "if False:"),
]
def run(d):
    return subprocess.run([sys.executable, "-I", "test_navigator_contract.py"], cwd=d, capture_output=True, text=True).returncode == 0
def stage():
    d = tempfile.mkdtemp()
    for f in os.listdir(HERE):
        p = os.path.join(HERE, f)
        if os.path.isfile(p): shutil.copy(p, d)
    shutil.copytree(os.path.join(HERE, "fixtures"), os.path.join(d, "fixtures"))
    return d
def main():
    d0 = stage(); assert run(d0), "baseline must pass"; shutil.rmtree(d0)
    surv, na = [], []
    for n, (name, old, new) in enumerate(M, 1):
        d = stage(); p = os.path.join(d, F); s = open(p).read()
        if old not in s: na.append(n); print("R%02d NOT_APPLICABLE %s" % (n, name)); shutil.rmtree(d); continue
        open(p, "w").write(s.replace(old, new, 1))
        try: killed = not run(d)
        finally: shutil.rmtree(d)
        print("R%02d %s %s" % (n, "KILLED  " if killed else "SURVIVED", name))
        if not killed: surv.append(n)
    print("mutants=%d survivors=%s not_applicable=%s" % (len(M), surv, na)); sys.exit(1 if surv or na else 0)
main()
