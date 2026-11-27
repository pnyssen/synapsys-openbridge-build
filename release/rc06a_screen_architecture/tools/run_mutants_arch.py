"""Mutation controls for the FFE projection and the read-only slice. One fault per run in a COPY; some suite must fail (KILLED).
Run: python3 -I tools/run_mutants_arch.py   (exit 1 on any survivor / pattern that no longer applies)."""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AG = ("review/all61/arch_graph.py", "addon/synapsys/arch_graph.py")          # kept byte-identical in every mutant
SL = "addon/synapsys/arch_slice.py"
SUITES = (("review/all61", "test_all61.py"), ("review/all61", "test_ffe_projection.py"), ("review/all61", "test_ffe_regressions.py"), ("tests", "test_arch_slice.py"))
M = [
 (AG, 'if tm != model or _restricted(actor, fm):\n            continue', 'if tm != model:\n            continue'),
 (AG, 'and _readable(graph, actor, fm, sid):\n                out.append', 'and True:\n                out.append'),
 (AG, 'for e in _incoming(graph, actor, model, rid, perspective):          # one governed hop in; does not recurse', 'for e in []:'),
 (AG, '    if model == "synapsys.context":\n        for m in _members', '    if False:\n        for m in _members'),
 (AG, 'if not _readable(graph, actor, model, rid):\n        return {"state": "DENIED_REDACTED"', 'if not _visible(actor, model, rid):\n        return {"state": "DENIED_REDACTED"'),
 (AG, 'return model in actor.get("restricted_models", ())', 'return False'),
 (AG, 'e["cross_context"] = True', 'pass'),
 (AG, 'if sig[p] == sig[q] and out[p].get("edges"):', 'if False:'),
 (AG, '"finding": "EMPTY_WHERE_SOURCE_BACKED" if not got else "MISSING_SOURCE_BACKED_EDGE"', '"finding": "X"'),
 (AG, 'if rec is None or e[4] not in _targets(rec, e[2]):', 'if False:'),
 (AG, 'if not _readable(graph, actor, n[0], n[1]):', 'if False:'),
 (AG, 'st = "SOURCE_MODEL_RESTRICTED"', 'st = "NONE_VISIBLE_TO_ACTOR"'),
 (AG, 'uniq.setdefault((tuple(e["from"]), e["field"], tuple(e["to"])), e)', 'uniq.setdefault(id(e), e)'),
 (AG, 'e["direction"] = "out" if e["from"] == [model, rid] else "in" if e["to"] == [model, rid] else "via"', 'e["direction"] = "out"'),
 ((SL,), 'out["stopped_at"] = "Context"; out["reason"] = ctx["state"]', 'out["stopped_at"] = None; out["reason"] = None'),
 ((SL,), 'if sc == cid else "UNLINKED_CONTEXT" if not sc else "WRONG_CONTEXT"', 'if True else "UNLINKED_CONTEXT" if not sc else "WRONG_CONTEXT"'),
 ((SL,), '"services": {"state": "FIELD_NOT_PRESENT", "ids": []}', '"services": {"state": "NONE_VISIBLE_TO_ACTOR", "ids": []}'),
 ((SL,), 'except access_error:\n            actor["restricted_models"].add(model); notes["restricted"].append(model); continue\n        if len(rows)', 'except access_error:\n            continue\n        if len(rows)'),
 ((SL,), 'ctx["ids"] = [i for i in ctx["ids"] if i == context_id]', 'pass'),
 ((SL,), 'notes["truncated"].append(model)', 'pass'),
 ((SL,), '"role_tests": "NOT_TESTED"', '"role_tests": "PASS"'),
 ((SL,), '"writes": 0', '"writes": 1'),
]
EQUIV = {1: "redundant second guard: _readable() already refuses a restricted source model inside _incoming"}
def stage():
    d = tempfile.mkdtemp()
    for sub in ("review/all61", "addon/synapsys", "tests", "tools"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return d
def ok(d): return all(subprocess.run([sys.executable, "-I", t], cwd=os.path.join(d, w), capture_output=True, text=True).returncode == 0 for w, t in SUITES)
def main():
    d0 = stage(); assert ok(d0), "baseline must pass"; shutil.rmtree(d0)
    surv, na = [], []
    for n, (files, old, new) in enumerate(M, 1):
        d = stage(); files = (files,) if isinstance(files, str) else files; hit = False
        for f in files:
            p = os.path.join(d, f); s = open(p).read()
            if old in s: open(p, "w").write(s.replace(old, new, 1)); hit = True
        if not hit: na.append(n); print("M%02d NOT_APPLICABLE %s" % (n, old[:50].replace("\n", " "))); shutil.rmtree(d); continue
        killed = not ok(d); print("M%02d %s %s" % (n, "KILLED  " if killed else "SURVIVED", old[:60].replace("\n", " "))); shutil.rmtree(d)
        if not killed: (print('     EQUIV (documented): ' + EQUIV[n]) if n in EQUIV else surv.append(n))
    print("mutants=%d survivors=%s not_applicable=%s" % (len(M), surv, na)); sys.exit(1 if surv or na else 0)
main()
