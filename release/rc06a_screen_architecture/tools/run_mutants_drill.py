"""Mutation controls for the RC03 drill-down, context builder, record evidence, navigation module and client component.
One fault per run in a COPY of the tree; the named suite must fail (KILLED). 'drill' = offline drill suite; 'views' = offline views suite (includes the Node navigation tests); 'owl' = real controller + real OWL component suite.
Run: python3 -I tools/run_mutants_drill.py   (exit 1 on any survivor or stale pattern)."""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REL = os.path.abspath(os.path.join(ROOT, ".."))
DR, CX, RD = "addon/synapsys/arch_master_drill.py", "addon/synapsys/arch_master_ctx.py", "addon/synapsys/master_render.py"
NAV, MJS, VW = "addon/synapsys/static/src/master/master_nav.js", "addon/synapsys/static/src/master/master.js", "addon/synapsys/arch_master_views.py"
M = [  # (suite, file, name, old, new)
 ("drill", DR, "trailing newline accepted in a path", "_PATH.fullmatch(path)", "_PATH.match(path)"),
 ("drill", DR, "link ignores menu visibility", 'if vis is None or m["menu_id"] not in vis or m["kind"] == "CONTAINER" or aid is None:', 'if m["kind"] == "CONTAINER" or aid is None:'),
 ("drill", DR, "containers get a link", 'or m["menu_id"] not in vis or m["kind"] == "CONTAINER" or aid is None:', 'or m["menu_id"] not in vis or aid is None:'),
 ("drill", DR, "record link ignores the real read right", 'or rm is None or m["model"] not in rm:', 'or False:'),
 ("drill", DR, "record link ignores row readability", 'if not isinstance(rid, int) or isinstance(rid, bool) or not G._readable(graph, actor, m["model"], rid):\n        return None', 'if not isinstance(rid, int) or isinstance(rid, bool):\n        return None'),
 ("drill", DR, "unread effective action called a match", '"state": "SOURCE_UNVERIFIED", "reason": "effective action configuration was not read"', '"state": "MATCHES_DEFINITION", "reason": "effective action configuration was not read"'),
 ("drill", DR, "domain drift not compared", 'if (got.get("domain") or "").replace(" ", "") != (m.get("domain") or "").replace(" ", ""):', 'if False:'),
 ("drill", DR, "model drift not compared", 'if m.get("model") and got.get("res_model") != m["model"]:', 'if False:'),
 ("drill", DR, "cardinality drift not compared", 'if CARD.get(f.get("type")) != edge["cardinality"]:', 'if False:'),
 ("drill", DR, "missing field called a match", 'return {"state": "FIELD_NOT_PRESENT", "reason": "the installed model does not declare this field"}', 'return {"state": "MATCHES_DEFINITION", "reason": "the installed model does not declare this field"}'),
 ("drill", DR, "unreadable field metadata called a match", '"reason": "field metadata for this model could not be read under your rights"}', '"reason": "x"} if False else {"state": "MATCHES_DEFINITION"}'),
 ("drill", DR, "hidden record answer leaks the id", 'return dict(NOT_AVAILABLE, level="rec", writes=0)\n        out.update(r)', 'return dict(NOT_AVAILABLE, level="rec", writes=0, id=parts[2])\n        out.update(r)'),
 ("drill", DR, "record evidence skips readability", 'or not G._readable(graph, actor, model, rid):\n        return dict(NOT_AVAILABLE)', 'or False:\n        return dict(NOT_AVAILABLE)'),
 ("drill", DR, "related records not rights-checked", 'if G._readable(graph, actor, tm, t) and G._edge_supported(graph, actor, fm, field, rid, t):', 'if G._edge_supported(graph, actor, fm, field, rid, t):'),
 ("drill", DR, "fractal evidence not rights-checked", 'for fid in A._readable_ids(graph, actor, "synapsys.fractal"):', 'for fid in graph["records"].get("synapsys.fractal", {}):'),
 ("drill", DR, "PPV movement claimed", '"ppv_movement": False', '"ppv_movement": True'),
 ("drill", DR, "AI promotion claimed", '"ai_promotion": False}', '"ai_promotion": True}'),
 ("drill", DR, "Realisation shown without evidence", '"state": "UNOBSERVED_BY_THIS_INTERFACE" if not fr else "SOURCE_VALUES_SHOWN_NOT_VERIFIED"', '"state": "SOURCE_VALUES_SHOWN_NOT_VERIFIED"'),
 ("drill", DR, "qualification rule weakened", '(rec.get("qualified_benefit_count") or 0) < 3', '(rec.get("qualified_benefit_count") or 0) < 2'),
 ("drill", DR, "long text not shortened", "TEXT_CAP = 400", "TEXT_CAP = 100000"),
 ("drill", DR, "data cap removed", "DATA_CAP = 50", "DATA_CAP = 5000"),
 ("drill", DR, "pairs shown at Enable depth", '"pairs": shown if depth != "enable" else []', '"pairs": shown'),
 ("drill", DR, "unsafe embedded markup accepted", 'return html if isinstance(html, str) and not _UNSAFE.search(html) else None', 'return html if isinstance(html, str) else None'),
 ("drill", DR, "provider reason passed through unchecked", 're.fullmatch(r"[A-Z_]{3,40}", r["reason"])', 'True'),
 ("drill", DR, "lens overrides ignored", 'LC.parse_overrides(ov or "")', '{}'),
 ("drill", DR, "lens style repeated", 'return head + html[first + len(LC.STYLE):].replace(LC.STYLE, "")', 'return html'),
 ("drill", DR, "menu ancestors not given to the lens", 'ancestors=anc,', 'ancestors=[],'),
 ("drill", DR, "a screen can be drilled as a group", 'if m["kind"] != "CONTAINER":\n            return dict(NOT_AVAILABLE, level="grp", writes=0)', 'if False:\n            return dict(NOT_AVAILABLE, level="grp", writes=0)'),
 ("drill", DR, "a container can be drilled as a screen", '    if m["kind"] == "CONTAINER":\n        return dict(NOT_AVAILABLE, level=parts[0], writes=0)', '    if False:\n        return dict(NOT_AVAILABLE, level=parts[0], writes=0)'),
 ("drill", DR, "unknown field answers instead of refusing", 'if edge is None or not m.get("model"):', 'if False:'),
 ("drill", DR, "asset record screen not embedded", 'if model == "synapsys.asset" and ctx.get("record_screen_html"):', 'if False:'),
 ("drill", CX, "failed menu probe becomes permissive", "    return _safe(probe, access_error)\n\n\ndef readable_models", "    return _safe(probe, access_error) or set(ids)\n\n\ndef readable_models"),
 ("drill", CX, "failed model probe becomes permissive", "        return {m for m in models if sw._can_read(env, m)}\n    return _safe(probe, access_error)", "        return {m for m in models if sw._can_read(env, m)}\n    return _safe(probe, access_error) or set(models)"),
 ("drill", CX, "unreadable action recorded as empty config", 'out.setdefault(aid, "UNREADABLE")', 'out.setdefault(aid, {})'),
 ("drill", CX, "any error is propagated", "    except Exception:                      # noqa: BLE001 - an unreadable probe is \"not read\", not a crash and not a leak\n        return None", "    except ZeroDivisionError:\n        return None"),
 ("drill", CX, "screen provider error leaks", '        except Exception:                  # noqa: BLE001\n            return {"result": "REFUSED", "reason": "NOT_AVAILABLE"}', '        except ZeroDivisionError:\n            return {"result": "REFUSED", "reason": "NOT_AVAILABLE"}'),
 ("drill", RD, "override anchors not made operable", 'return html.replace(\'<a class="tg" data-ovel=\', \'<a class="tg" role="button" tabindex="0" href="#" data-ovel=\')', 'return html'),
 ("drill", RD, "unverified effective state hidden", 'read under your rights; SOURCE_UNVERIFIED when not read', 'read under your rights'),
 ("views", VW, "role definitions entitle Client", '    ent["client"] = None', '    ent["client"] = 61'),
 ("views", NAV, "any drill path accepted", 'if (!DRILL_RE.test(ds.drill)) { return null; }', ''),
 ("views", NAV, "drill press does not land on the drill section", 's.drill = ds.drill; s.section = "drill"; moved = true;', 's.drill = ds.drill; moved = true;'),
 ("views", NAV, "override reset ignored", 'if (ds.ovmode === "") { m.delete(ds.ovel); } else { m.set(ds.ovel, ds.ovmode); }', 'm.set(ds.ovel, ds.ovmode || "enable");'),
 ("views", NAV, "unsafe override id accepted", 'if (!OV_ID_RE.test(ds.ovel) || (ds.ovmode !== "" && !DEPTHS.includes(ds.ovmode))) { return null; }', 'if (ds.ovmode !== "" && !DEPTHS.includes(ds.ovmode)) { return null; }'),
 ("owl", MJS, "focus never moves", "await focusContentWhenPatched(root);", ""),
 ("owl", MJS, "drill and overrides not sent", "drill: n.drill, ov: n.ov,", "drill: 'app', ov: '',"),
 ("owl", MJS, "server errors swallowed", 'this.state.error = (r && (r.error || r.state)) || "NOT_LOADED";', 'this.state.error = "";'),
 ("owl", MJS, "invalid presses still request", "        if (!next) {\n            return;\n        }\n        ev.preventDefault();", "        if (!next) { next = this.state.nav; }\n        ev.preventDefault();"),
]
EQUIV = {3: "redundant guard: containers carry no action id, so the aid-is-None guard already refuses a link (asserted by test_containers_carry_no_action_so_they_can_never_be_linked)"}
def stage():
    d = tempfile.mkdtemp(); base = os.path.join(d, "rc06a_screen_architecture")
    for sub in ("addon/synapsys", "tests", "tools", "review/all61", "review/wave1"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(base, sub), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(os.path.join(REL, "rc05_scaffold_lens"), os.path.join(d, "rc05_scaffold_lens"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return d, base
def run(base, suite):
    f = {"drill": "test_arch_master_drill.py", "views": "test_arch_master_views.py", "owl": "test_master_owl.py"}[suite]
    r = subprocess.run([sys.executable, "-I", f], cwd=os.path.join(base, "tests"), capture_output=True, text=True)
    return r.returncode == 0, ("skipped" in (r.stderr or "") and "OK (skipped" in (r.stderr or ""))
def main():
    d0, b0 = stage()
    for suite in ("drill", "views", "owl"):
        ok, sk = run(b0, suite); assert ok, "baseline %s must pass" % suite
        if sk: print("NOTE: %s suite skipped here; its mutants are NOT_RUN" % suite)
    shutil.rmtree(d0)
    surv, na, notrun = [], [], []
    for n, (suite, f, name, old, new) in enumerate(M, 1):
        d, base = stage(); p = os.path.join(base, f); s = open(p, encoding="utf-8").read()
        if old not in s: na.append(n); print("D%02d NOT_APPLICABLE %s" % (n, name)); shutil.rmtree(d); continue
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
        try: ok, sk = run(base, suite)
        finally: shutil.rmtree(d)
        if ok and sk: notrun.append(n); print("D%02d NOT_RUN  %s (%s)" % (n, name, suite)); continue
        print("D%02d %s %s (%s)" % (n, "KILLED  " if not ok else "SURVIVED", name, suite))
        if ok: (print("     EQUIV (documented): " + EQUIV[n]) if n in EQUIV else surv.append(n))
    print("mutants=%d survivors=%s not_applicable=%s not_run=%s" % (len(M), surv, na, notrun)); sys.exit(1 if surv or na else 0)
main()
