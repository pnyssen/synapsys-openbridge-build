"""Mutation controls for the SB-02 source correction. Copies the tree to a temp dir, applies ONE mutation, runs the focused tests,
expects a failure (killed). A surviving mutant means a missing test. Offline; no Odoo; no network."""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = [  # (name, file, old, new)
 ("ancestors ignored", "lens_contract.py", "    for a in (ancestors or ()):\n        if a in ov:\n            return normalise(ov[a])\n", ""),
 ("ancestor beats exact override", "lens_contract.py", "    if eid in ov:\n        return normalise(ov[eid])\n    for a in", "    for a in (ancestors or ()):\n        if a in ov:\n            return normalise(ov[a])\n    if eid in ov:\n        return normalise(ov[eid])\n    for a in"),
 ("farthest ancestor wins", "lens_contract.py", "for a in (ancestors or ()):", "for a in reversed(tuple(ancestors or ())):"),
 ("inherited labelled as local", "lens_contract.py", "'yes' if local else 'inherited' if inherited else 'no'", "'yes' if (local or inherited) else 'no'"),
 ("membership filter removed", "scaffold_wire.py", "for r in recs if _entitled(r, uid)", "for r in recs"),
 ("wrong role still queries", "scaffold_wire.py", "if groups else set()}", "}"),
 ("steward match dropped", "scaffold_wire.py", "if _rid(getattr(rec, 'steward_user_id', None)) == uid:\n        return True\n", ""),
 ("access error not failing closed", "scaffold_wire.py", "if _is_access_error(exc) or exc.__class__.__name__ == 'MissingError':\n            return set()\n        raise", "raise"),
 ("all errors swallowed", "scaffold_wire.py", "        if _is_access_error(exc) or exc.__class__.__name__ == 'MissingError':\n            return set()\n        raise", "        return set()"),
 ("sudo used", "scaffold_wire.py", "recs = env['synapsys.context'].search(", "recs = env.sudo()['synapsys.context'].search("),
 ("binding always BOUND", "scaffold_wire.py", "'status': 'BOUND' if (ctx and mth) else 'UNBOUND/HOLD'", "'status': 'BOUND'"),
 ("context alone makes it ready", "scaffold_wire.py", "'status': 'BOUND' if (ctx and mth) else 'UNBOUND/HOLD'", "'status': 'BOUND' if (ctx or mth) else 'UNBOUND/HOLD'"),
 ("pin ignores source", "scaffold_wire.py", "'sha256': canonical_hash(values, flds)", "'sha256': b['pinned_sha256']"),
 ("native binding removed", "scaffold_wire.py", "{'model': 'synapsys.service', 'code_field': 'code', 'code': 'SB-02'", "{'model': 'synapsys.service', 'code_field': 'code', 'code': 'SB-99'"),
 ("missing model crashes", "scaffold_wire.py", "            except KeyError:\n                notes.append('%s: model not present in this database' % ref)\n                continue\n", ""),
 ("D009 service-root cross-Context unflagged", "arch_graph.py", "or (root_context not in (None, False) and any(c != root_context for c in contexts))", "or False"),
 ("D009 flag never set", "arch_graph.py", 'e["cross_context"] = True\n    return', 'pass\n    return'),
 ("D009 old label restored", "arch_slice.py", '"NO_DIRECT_SERVICE_CONTEXT" if not sc', '"UNLINKED_CONTEXT" if not sc'),
]
killed = survived = 0
for name, rel, old, new in M:
    with tempfile.TemporaryDirectory() as t:
        dst = os.path.join(t, "r"); shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "review", ".pytest_cache"))
        p = os.path.join(dst, "addon", "synapsys", rel); s = open(p, encoding="utf-8").read()
        if s.count(old) < 1:
            print("MUTANT-SETUP-ERROR", name); sys.exit(2)
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_architecture_first_reuse.py", "tests/test_d009_arch_projection.py"], cwd=dst, capture_output=True, text=True)
        if r.returncode != 0:
            killed += 1; print("KILLED  ", name)
        else:
            survived += 1; print("SURVIVED", name)
print("killed=%d survived=%d total=%d" % (killed, survived, len(M)))
sys.exit(1 if survived else 0)
