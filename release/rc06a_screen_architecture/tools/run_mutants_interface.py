"""Mutation controls for the Master interface (arch_master_views.py, master_render.py). One fault per run in a COPY; the named suite must fail (KILLED).
Logic/markup faults run the offline views suite; CSS/layout faults run the real-browser suite (skipped, and reported as NOT_RUN, if no browser launches).
Run: python3 -I tools/run_mutants_interface.py   (exit 1 on any survivor or stale pattern)."""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
VW, RD = "addon/synapsys/arch_master_views.py", "addon/synapsys/master_render.py"
NAV = "addon/synapsys/static/src/master/master_nav.js"
M = [  # (suite, file, name, old, new)
 ("views", RD, "escaping removed", '    return _e("" if x is None else str(x), quote=True)', '    return "" if x is None else str(x)'),
 ("views", VW, "requested actor widens data view", '"data_view": "ACTUAL_ACCOUNT" if requested == own else "DEFINITION_ONLY_NOT_TESTED"', '"data_view": "ACTUAL_ACCOUNT"'),
 ("views", VW, "collaborator shown as tested for everyone", '"collaborator": {"state": "ACTUAL_ACCOUNT" if own == "collaborator" else "GROUP_IN_SOURCE_NOT_TESTED"}', '"collaborator": {"state": "ACTUAL_ACCOUNT"}'),
 ("views", VW, "realisation promoted from nothing", '"state": "UNOBSERVED" if not real["total"] else "SOURCE_VALUES_SHOWN_NOT_VERIFIED"', '"state": "SOURCE_VALUES_SHOWN_NOT_VERIFIED"'),
 ("views", VW, "AI promotion claimed", '"ai_promotion": False', '"ai_promotion": True'),
 ("views", VW, "membrane case accepted", '"ruling": "UNRULED_NOT_ACCEPTED"', '"ruling": "ACCEPTED"'),
 ("views", VW, "membrane lists same-Context edges", 'if cs not in (None, False) and ct not in (None, False) and cs != ct:', 'if cs not in (None, False) and ct not in (None, False):'),
 ("views", VW, "unset many2one shown as value False", 'or (v is False and field not in BOOLEAN_FIELDS)', 'or False'),
 ("views", VW, "boolean False treated as unset", 'BOOLEAN_FIELDS = frozenset({"baseline_observed", "qualifies", "rights_confirmed"})', 'BOOLEAN_FIELDS = frozenset()'),
 ("views", VW, "evidence detail leaks at enable", '            if depth != "enable":\n                for k in ("id", "ids"', '            if True:\n                for k in ("id", "ids"'),
 ("views", VW, "value detail leaks at enable", '    detail = depth != "enable"', '    detail = True'),
 ("views", VW, "verb names leak at enable", '"eligible_names": [verbs[i]["name"] for i in el["verb_ids"]] if depth != "enable" else []', '"eligible_names": [verbs[i]["name"] for i in el["verb_ids"]]'),
 ("views", VW, "unruled kind shown", '"kind": r.get("kind") if ruled else None', '"kind": r.get("kind")'),
 ("views", VW, "stage shown for unruled kind", '"stage": G.CUT_B.get(r.get("kind")) if ruled else None,\n                     "eligible": el', '"stage": G.CUT_B.get(r.get("kind")),\n                     "eligible": el'),
 ("views", VW, "execution authorised", '"human_only_ids": sorted(i for i, v in verbs.items() if v["human_only"]), "execution_authorised": False', '"human_only_ids": sorted(i for i, v in verbs.items() if v["human_only"]), "execution_authorised": True'),
 ("views", VW, "unknown section defaulted", '    if section not in SECTIONS:\n        raise ValueError(section)', '    if section not in SECTIONS:\n        section = "overview"'),
 ("views", VW, "unknown actor defaulted", '    if requested not in ACTORS:\n        raise ValueError(requested)', '    if requested not in ACTORS:\n        requested = "steward"'),
 ("views", VW, "ungrouped strategies guessed into Build", 'by_group[g] if g in by_group else ungrouped', 'by_group[g] if g in by_group else by_group["build"]'),
 ("views", VW, "single perspective section shows all", '(G.PERSPECTIVES if section == "overview" else (perspective,))', '(G.PERSPECTIVES)'),
 ("views", VW, "holds truncated", '"holds": [{"id": h[0], "title": h[1], "state": h[2], "text": h[3]} for h in HOLDS]', '"holds": [{"id": h[0], "title": h[1], "state": h[2], "text": h[3]} for h in HOLDS[:9]]'),
 ("views", RD, "candidate banner removed", 'Candidate · not installed · read-only', 'Ready'),
 ("views", RD, "every perspective shown pressed", 'pbar = "".join(btn(p, pressed=(p == persp), persp=p)', 'pbar = "".join(btn(p, pressed=True, persp=p)'),
 ("views", RD, "table region not keyboard reachable", 'class="sm-scroll" tabindex="0" role="region"', 'class="sm-scroll" role="region"'),
 ("views", NAV, "invalid section accepted", 'if (!SECTIONS.includes(ds.section)) { return null; }', ''),
 ("views", NAV, "no-op press reloads", 'return JSON.stringify(s) === JSON.stringify(state) ? null : s;', 'return s;'),
 ("views", NAV, "state mutated in place", 'const s = Object.assign({}, state);', 'const s = state;'),
 ("browser", RD, "tables do not scroll", '.syn-master .sm-scroll{overflow-x:auto;', '.syn-master .sm-scroll{overflow-x:visible;'),
 ("browser", RD, "phone nav does not scroll", 'padding-bottom:4px;-webkit-overflow-scrolling:touch}', 'padding-bottom:4px;-webkit-overflow-scrolling:touch;flex-wrap:nowrap;overflow-x:visible}'),
 ("browser", RD, "touch target shrunk", 'min-height:44px;padding:6px 12px}', 'min-height:20px;padding:0 4px}'),
 ("browser", RD, "focus outline removed", 'outline:3px solid #f5a623;outline-offset:2px}', 'outline:none}'),
 ("browser", RD, "wide grid forces columns", '@media (min-width:1025px){.syn-master .sm-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}', '@media (min-width:1025px){.syn-master .sm-grid{grid-template-columns:repeat(3,minmax(520px,1fr))}}'),
 ("browser", RD, "min-width reset removed", '.syn-master *{box-sizing:border-box;min-width:0}', '.syn-master *{box-sizing:border-box}'),
]
EQUIV = {32: "redundant guard: overflow-wrap:anywhere on cards, lists and notes already lets grid items shrink below their longest word; min-width:0 is defence in depth"}
def stage():
    d = tempfile.mkdtemp()
    for sub in ("addon/synapsys", "tests", "tools", "review/all61"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return d
def run(d, suite):
    f = "test_arch_master_views.py" if suite == "views" else "test_master_browser.py"
    r = subprocess.run([sys.executable, "-I", f], cwd=os.path.join(d, "tests"), capture_output=True, text=True)
    skipped = suite == "browser" and "skipped" in (r.stderr or "")
    return r.returncode == 0, skipped
def main():
    d0 = stage()
    for suite in ("views", "browser"):
        ok, sk = run(d0, suite); assert ok, "baseline %s must pass" % suite
        if sk: print("NOTE: no browser in this environment; browser mutants are NOT_RUN")
    shutil.rmtree(d0)
    surv, na, notrun = [], [], []
    for n, (suite, f, name, old, new) in enumerate(M, 1):
        d = stage(); p = os.path.join(d, f); s = open(p, encoding="utf-8").read()
        if old not in s: na.append(n); print("I%02d NOT_APPLICABLE %s" % (n, name)); shutil.rmtree(d); continue
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
        try: ok, sk = run(d, suite)
        finally: shutil.rmtree(d)
        if sk and ok: notrun.append(n); print("I%02d NOT_RUN  %s (%s)" % (n, name, suite)); continue
        print("I%02d %s %s (%s)" % (n, "KILLED  " if not ok else "SURVIVED", name, suite))
        if ok: (print("     EQUIV (documented): " + EQUIV[n]) if n in EQUIV else surv.append(n))
    print("mutants=%d survivors=%s not_applicable=%s not_run=%s" % (len(M), surv, na, notrun)); sys.exit(1 if surv or na else 0)
main()
