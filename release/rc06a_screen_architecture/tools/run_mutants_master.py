"""Mutation controls for arch_master.py (the Master builder). One fault per run in a COPY; test_arch_master.py must fail (KILLED).
Run: python3 -I tools/run_mutants_master.py  (exit 1 on any survivor / pattern that no longer applies)."""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AM = "addon/synapsys/arch_master.py"
M = [
 ("unreadable rows counted", 'return sorted(i for i in graph["records"].get(model, {}) if G._readable(graph, actor, model, i))', 'return sorted(i for i in graph["records"].get(model, {}))'),
 ("target readability ignored", 'if G._readable(graph, actor, to_model, t) and G._edge_supported(graph, actor, from_model, field, sid, t):', 'if G._edge_supported(graph, actor, from_model, field, sid, t):'),
 ("computed relation needs no Work", 'and G._edge_supported(graph, actor, from_model, field, sid, t):', 'and True:'),
 ("restricted model not reported", 'if from_model in actor["restricted_models"] or to_model in actor["restricted_models"]:\n        return "RESTRICTED"', 'if False:\n        return "RESTRICTED"'),
 ("absent field not reported", 'if field in notes["field_absent"].get(from_model, ()):\n        return "FIELD_NOT_PRESENT"', 'if False:\n        return "FIELD_NOT_PRESENT"'),
 ("absent model not reported", 'if from_model in notes["model_absent"] or to_model in notes["model_absent"]:\n        return "MODEL_NOT_INSTALLED"', 'if False:\n        return "MODEL_NOT_INSTALLED"'),
 ("always CONNECTED", '    if n:\n        return "CONNECTED"', '    if True:\n        return "CONNECTED"'),
 ("zero visible called connected-defined", 'return "DEFINED_NO_READABLE_INSTANCE" if _readable_ids(graph, actor, from_model) else "NONE_VISIBLE_TO_ACTOR"', 'return "DEFINED_NO_READABLE_INSTANCE"'),
 ("perspective filter ignored (caption only)", 'if te is None:\n                continue', 'if te is None:\n                te = {"type": "many2one"}'),
 ("ruling ignored for eligibility", '{"kind": rec.get("kind"), "kind_ruling": rec.get("kind_ruling")}, verbs, defn["modes"])', '{"kind": rec.get("kind"), "kind_ruling": True}, verbs, defn["modes"])'),
 ("execution authorised", '"execution_authorised": False,', '"execution_authorised": True,'),
 ("depth confers stage", '**G.display_depth_is_not_stage(depth, c)', '"stage": depth.title()'),
 ("container treated as record model", 'if m["kind"] == "CONTAINER":', 'if False:'),
 ("restricted menu model not reported", 'if model in actor["restricted_models"]:\n        return {"state": "RESTRICTED"}', 'if False:\n        return {"state": "RESTRICTED"}'),
 ("caption-only audit disabled", 'if sig[p] == sig[q] and outs[p]["edge_totals"]["typed_edges"]:', 'if False:'),
 ("verb count not audited", 'if o["verbs"]["governed_verbs"] != 27', 'if False and o["verbs"]["governed_verbs"] != 27'),
 ("leaked count not audited", 'if e["instance_edges"] != truth:', 'if False:'),
 ("truncation not reported", 'notes["truncated"].append(model)', 'pass'),
 ("access error swallowed as zero rows", 'except access_error:\n            actor["restricted_models"].add(model); notes["restricted"].append(model); continue\n        if len(rows)', 'except access_error:\n            continue\n        if len(rows)'),
 ("context filter ignored", 'if context_id is not None and cid != context_id:\n            continue', 'if False:\n            continue'),
 ("depth not validated", 'if depth not in DEPTHS:\n        raise ValueError(depth)', 'pass'),
 ("perspective not validated", 'if perspective not in G.PERSPECTIVES:\n        raise ValueError(perspective)', 'pass'),
 ("definition missing guessed", 'if defn is None:\n        return {"state": "DEFINITION_NOT_LOADED", "writes": 0}', 'if False:\n        pass'),
 ("writes claimed", '"read_only": True, "writes": 0,', '"read_only": True, "writes": 1,'),
]
EQUIV = {16: "redundant guard: governed_verbs, the per-action sum and the action count are three views of the same 27 verbs; the other two still raise VERB_COUNT_DRIFT"}
def stage():
    d = tempfile.mkdtemp()
    for sub in ("addon/synapsys", "tests", "tools", "review/all61"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return d
def ok(d): return subprocess.run([sys.executable, "-I", "test_arch_master.py"], cwd=os.path.join(d, "tests"), capture_output=True, text=True).returncode == 0
def main():
    d0 = stage(); assert ok(d0), "baseline must pass"; shutil.rmtree(d0)
    surv, na = [], []
    for n, (name, old, new) in enumerate(M, 1):
        d = stage(); p = os.path.join(d, AM); s = open(p).read()
        if old not in s: na.append(n); print("X%02d NOT_APPLICABLE %s" % (n, name)); shutil.rmtree(d); continue
        open(p, "w").write(s.replace(old, new, 1))
        try: killed = not ok(d)
        finally: shutil.rmtree(d)
        print("X%02d %s %s" % (n, "KILLED  " if killed else "SURVIVED", name))
        if not killed:
            if n in EQUIV: print('     EQUIV (documented): ' + EQUIV[n])
            else: surv.append(n)
    print("mutants=%d survivors=%s not_applicable=%s" % (len(M), surv, na)); sys.exit(1 if surv or na else 0)
main()
