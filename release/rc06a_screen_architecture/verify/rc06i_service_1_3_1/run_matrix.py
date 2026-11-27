"""Runs the real-browser layout matrix for RC06g (88eb331), RC06h (e5322c9) and the working tree (RC06i): renders each tree's real route output, puts it in the
MOCK SHELL built from that tree's own enable_panel.xml, measures it in Chromium at 390x844 and 1024x854 for all three depths, and evaluates the checks.
   python3 run_matrix.py OUT_DIR [--no-old]      (needs git objects for the old commits, node + playwright + chromium)"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip()
REL = "release/rc06a_screen_architecture"
VERSIONS = (("rc06g", "88eb331"), ("rc06h", "e5322c9"), ("rc06i", None))
sys.path.insert(0, HERE)
import build_shell


def tree(commit, tmp):
    if commit is None:
        return os.path.join(REPO, REL)
    subprocess.check_call("git archive %s %s release/rc05_scaffold_lens | tar -x -C %s" % (commit, REL, tmp), shell=True, cwd=REPO)
    return os.path.join(tmp, REL)


def checks(case, m):
    """Pass/fail per check for one measured case. depth/screen come from the file name 'screen_depth'."""
    name, depth = case.split("_")[-1], None
    screen, depth = case.rsplit("_", 1)
    svc = screen == "service"
    t = m["tops"]
    order_keys = ["answer", "apertures", "value", "records", "native"] if svc else ["answer", "records", "native"]
    seq = [t[k] for k in order_keys]
    r = {}
    r["dom_order"] = all(v is not None for v in seq) and all(a < b for a, b in zip(seq, seq[1:]))
    r["no_horizontal_scroll"] = m["docScrollW"] <= m["vw"]
    r["no_truncated_cell"] = len(m["truncated"]) == 0
    r["source_visible"] = m["sourceRows"] == m["sourceVisible"] if depth == "enrich" and m["sourceRows"] else (None if depth == "enrich" else True)
    r["targets_44"] = m["controlCount"] > 0 and len(m["smallTargets"]) == 0
    r["one_accessible_control"] = m["controlCount"] == 1 and m["controlGroupLabelled"] and m["controlAllPressedAttr"] and m["pressed"] == [depth] and (m["controlInAnswerBand"] if svc else True)
    r["keyboard_focus_visible"] = bool(m["keyboard"]["reached"] and m["keyboard"]["outline"] and m["keyboard"]["outline"]["style"] != "none" and float(m["keyboard"]["outline"]["width"].replace("px", "") or 0) > 0)
    r["no_nested_scroll"] = m["scrollContainers"] == 0
    r["content_reachable"] = m["unreachablePx"] <= 1
    r["list_not_squeezed"] = m["nativeHeight"] is not None and m["nativeHeight"] >= 0.7 * (m["vh"] - 46)
    r["records_adjacent_to_native"] = m["gapRecordsToNative"] is not None and m["gapRecordsToNative"] <= 8
    if svc:
        r["apertures_ffe"] = m["apertures"] == ["form", "flow", "evolve"]
        r["value_band"] = m["valueBand"]
        sizes = {k.replace("px", "") for k in m["fonts"]}
        r["font_14_12_10"] = bool(sizes) and sizes <= {"14", "12", "10"} and sizes == {"14", "12", "10"}
    if depth == "enable" and m["vw"] == 390:
        r["enable_head_fits_viewport"] = m["recordsBottom"] is not None and m["recordsBottom"] <= m["vh"]
    return {k: v for k, v in r.items() if v is not None}


def run(outdir, old=True):
    os.makedirs(outdir, exist_ok=True)
    allres = {}
    for ver, commit in VERSIONS:
        if commit and not old:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            root = tree(commit, tmp)
            pages = os.path.join(tmp, "pages_%s.json" % ver)
            subprocess.check_call([sys.executable, os.path.join(HERE, "render_pages.py"), pages], cwd=os.path.join(root, "tests"), stdout=subprocess.DEVNULL)
            d = os.path.join(outdir, "shell_" + ver); os.makedirs(d, exist_ok=True)
            xml = open(os.path.join(root, "addon/synapsys/static/src/enable_panel.xml")).read()
            data = json.load(open(pages))
            for k, v in data.items():
                open(os.path.join(d, k.replace("|", "_") + ".html"), "w").write(build_shell.shell(xml, v["html"] if v["result"] == "OK" else ""))
            shots = os.path.join(outdir, "screenshots_" + ver); os.makedirs(shots, exist_ok=True)
            mj = os.path.join(outdir, "metrics_%s.json" % ver)
            subprocess.check_call(["node", os.path.join(HERE, "probe_layout.js"), d, mj, shots], cwd=HERE)
            res = json.load(open(mj))
            allres[ver] = {"commit": commit or "working tree", "not_rendered": sorted(k for k, v in data.items() if v["result"] != "OK"),
                           "cases": [{"case": x["file"], "w": x["w"], "checks": checks(x["file"], x["m"])} for x in res], "raw": res}
    json.dump(allres, open(os.path.join(outdir, "matrix.json"), "w"), indent=1)
    return allres


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    res = run(out, "--no-old" not in sys.argv)
    for ver, v in res.items():
        fails = {}
        for c in v["cases"]:
            for k, ok in c["checks"].items():
                if ok is False:
                    fails.setdefault(k, 0); fails[k] += 1
        print(ver, v["commit"], "not rendered:", v["not_rendered"], "failing checks (count of cases):", fails)
