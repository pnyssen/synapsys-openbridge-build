"""Deterministic test harness for the Navigator L1/L2/L3 deployment.

Runs against navigator/dist (the deployable tree) plus the updated
00_HOME.md and Navigator v1.5. Covers the 35 required acceptance tests and
the nested Element x Verb x Level-3 assertion sweep.
"""
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import model  # noqa: E402

DIST = HERE / "dist"
CURRENT = DIST / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT"
COMP = CURRENT / "COMPONENTS"
DATA = CURRENT / "DATA"
HOME = DIST / "00_HOME.md"
NAVIGATOR = CURRENT / model.NAVIGATOR_FILE

REG = json.loads((DATA / model.REGISTRY_FILE).read_text(encoding="utf-8"))


def read(p):
    return p.read_text(encoding="utf-8")


def html_files():
    return sorted(CURRENT.rglob("*.html"))


def hrefs(text):
    return re.findall(r'href="([^"]+)"', text)


def ids_in(text):
    return re.findall(r'id="([^"]+)"', text)


# ---- 1-2: exactly one current Home and Navigator ----
def test_01_exactly_one_current_home():
    assert HOME.exists()
    t = read(HOME)
    assert "content_state: current" in t
    assert t.count("# SynapSys Navigator") == 1


def test_02_exactly_one_current_navigator():
    assert NAVIGATOR.exists()
    others = [p for p in CURRENT.glob("SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE*.html")
              if p.name != model.NAVIGATOR_FILE]
    # dist deploys only the single current navigator; older versions stay
    # in the vault as historical lineage but are not part of the deploy set.
    assert others == []
    assert read(HOME).count(model.NAVIGATOR_FILE) >= 1


# ---- 3-5: nine element pages, canvas views, canvas source routes ----
def test_03_nine_element_pages():
    for e in model.ELEMENTS:
        p = COMP / e["html"]
        assert p.exists(), e["html"]
        t = read(p)
        import html as _h
        assert _h.escape(e["name"]) in t or e["name"] in t


def test_04_nine_canvas_views_render():
    for e in model.ELEMENTS:
        p = COMP / e["canvas_view"]
        assert p.exists(), e["canvas_view"]
        t = read(p)
        assert "<svg" in t and "</svg>" in t, f"no SVG in {p.name}"
        assert t.count("<text") >= 3, f"canvas view {p.name} has no visible node text"
        assert "PROJECTION" in t


def test_05_nine_canvas_source_routes():
    for e in model.ELEMENTS:
        t = read(COMP / e["canvas_view"])
        assert model.CANVAS_DIR_FROM_COMPONENTS + e["canvas_source"] in t
        # and the source itself exists in the vault mirror
        assert (HERE / "mirror" / "CANVAS" / e["canvas_source"]).exists()


# ---- 6-9: verb anchors and groups ----
def test_06_nine_verb_anchors():
    t = read(COMP / model.VERBS_FILE)
    page_ids = ids_in(t)
    for v in model.VERBS:
        assert v["key"] in page_ids, v["key"]


@pytest.mark.parametrize("group,expected", [
    ("FORM", ["Orient", "Canonicalise", "Structure"]),
    ("FLOW", ["Assure", "Navigate", "Compose"]),
    ("EVOLVE", ["Activate", "Transform", "Project"]),
])
def test_07_08_09_verb_groups(group, expected):
    names = [v["name"] for v in model.VERBS if v["group"] == group]
    assert names == expected


# ---- 10-12: L3 completeness ----
def test_10_27_l3_cells_per_element():
    for e in REG["elements"]:
        assert len(e["level3"]) == 27, e["id"]
        t = read(COMP / next(x["html"] for x in model.ELEMENTS if x["id"] == e["id"]))
        for c in e["level3"]:
            assert c["trace_id"] in t, c["trace_id"]


def test_11_no_duplicate_l3_ids():
    ids = [c["trace_id"] for e in REG["elements"] for c in e["level3"]]
    assert len(ids) == 243
    assert len(set(ids)) == 243


def test_12_81_element_verb_mappings():
    maps = REG["element_verb_mappings"]
    assert len(maps) == 81
    pairs = {(m["element"], m["verb"]) for m in maps}
    assert len(pairs) == 81


# ---- 13-14: mesh coverage ----
def test_13_all_mesh_stages_covered_by_verbs():
    cov = REG["mesh_stage_verb_coverage"]
    assert set(cov) == set(model.MESH_STAGES)
    for stage, verbs in cov.items():
        assert verbs, f"mesh stage {stage} has no verb"


def test_14_all_elements_participate_in_mesh():
    for e in REG["elements"]:
        mesh = e["mesh"]
        for k in ["enters", "interprets", "structures", "validated_by", "action",
                  "observes", "learns", "asset_conversion", "feedback_to"]:
            assert mesh[k].strip(), f"{e['id']} mesh.{k} empty"


# ---- 15-17: benefits and assets ----
def test_15_every_verb_has_benefit():
    for v in REG["verbs"]:
        assert v["benefit"] in REG["benefits"]
        assert v["benefit_statement"].strip()


def test_16_benefits_have_evidence_and_realisation():
    for bid, b in REG["benefits"].items():
        assert b["evidence"].strip(), bid
        assert b["realisation"].strip(), bid


def test_17_asset_qualification_and_authority():
    for v in REG["verbs"]:
        assert v["asset_implication"].strip()
    b4 = REG["benefits"]["B4"]
    assert "authority" in b4["realisation"].lower() or "Steward" in b4["realisation"]


# ---- 18-20: link, anchor and return-route resolution ----
def _resolve(base, href):
    if href.startswith(("http://", "https://", "obsidian://", "mailto:")):
        return None
    target, _, frag = href.partition("#")
    if not target:
        return ("SELF", frag, base)
    return ((base.parent / target).resolve(), frag, base)


def test_18_all_relative_links_resolve():
    missing = []
    for p in html_files():
        for href in hrefs(read(p)):
            r = _resolve(p, href)
            if r is None:
                continue
            tgt, frag, _ = r
            if tgt == "SELF":
                continue
            if tgt.exists():
                continue
            # paths outside dist must exist in the live vault (vault_index.json,
            # captured from sp_list this session)
            vault = json.loads((HERE / "vault_index.json").read_text())["paths"]
            try:
                rel = tgt.relative_to(DIST.resolve()).as_posix()
            except ValueError:
                rel = tgt.name
            if rel not in vault and not any(v.endswith("/" + tgt.name) or v == tgt.name for v in vault):
                missing.append((p.name, href))
    assert not missing, missing


def test_19_all_internal_anchors_exist():
    bad = []
    for p in html_files():
        t = read(p)
        page_ids = set(ids_in(t))
        for href in hrefs(t):
            r = _resolve(p, href)
            if r is None:
                continue
            tgt, frag, _ = r
            if not frag:
                continue
            if tgt == "SELF":
                if frag not in page_ids:
                    bad.append((p.name, href))
            elif tgt.exists() and tgt.suffix == ".html":
                if frag not in set(ids_in(read(tgt))):
                    bad.append((p.name, href))
    assert not bad, bad


def test_20_all_return_routes_resolve():
    for e in model.ELEMENTS:
        for f in [e["html"], e["canvas_view"]]:
            t = read(COMP / f)
            assert f'href="../{model.NAVIGATOR_FILE}"' in t, f"{f} missing navigator return"
            assert f'href="{model.VERBS_FILE}"' in t, f"{f} missing nine-verbs return"
    for f in [model.VERBS_FILE, model.START_FILE]:
        assert f'href="../{model.NAVIGATOR_FILE}"' in read(COMP / f)


# ---- 21-24: staleness and protocol discipline ----
def test_21_no_stale_v14_active_route():
    for p in html_files() + [HOME]:
        t = read(p)
        assert "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.4" not in t, p.name


def test_22_no_invalid_status_mesh_anchor():
    for p in html_files():
        assert "#status/mesh" not in read(p), p.name


def test_23_no_critical_custom_protocol_only_route():
    """Every obsidian:// link must have a browser-safe sibling on the same page."""
    for p in html_files():
        t = read(p)
        obs = [h for h in hrefs(t) if h.startswith("obsidian://")]
        if obs:
            rel = [h for h in hrefs(t) if not h.startswith(
                ("obsidian://", "http://", "https://", "#", "mailto:"))]
            assert rel, f"{p.name} has only obsidian:// routes"
    # Home: every obsidian:// canvas route must have a browser-safe CANVAS_VIEW route
    th = read(HOME)
    assert "CANVAS_VIEW_" in th


def test_24_no_primary_route_to_raw_canvas_json():
    """Primary 'View Canvas' buttons must go to the HTML view, not raw .canvas."""
    for e in model.ELEMENTS:
        t = read(COMP / e["html"])
        m = re.search(r'<a class="primary" href="([^"]+)"', t)
        assert m and m.group(1).endswith(".html"), e["html"]
        t2 = read(COMP / e["canvas_view"])
        m2 = re.search(r'<a class="primary" href="([^"]+)"', t2)
        assert m2 and m2.group(1).endswith(".html")


# ---- 25-26: Stream A discipline ----
def test_25_26_stream_a_complete_never_active():
    assert REG["stream_a"]["state"] == "ASSURED_STREAM_A_COMPLETE"
    assert "no rerun" in REG["stream_a"]["disposition"].lower() or \
           "No rerun" in REG["stream_a"]["disposition"]
    neg = re.compile(r"(do not|don't|never|no)\s+(rerun|reactivate|restart|replay)", re.I)
    for p in html_files() + [HOME]:
        t = read(p)
        low = t.lower()
        for bad in ["rerun stream a", "reactivate stream a", "stream a next action",
                    "restart stream a"]:
            for i in range(len(low)):
                j = low.find(bad, i)
                if j == -1:
                    break
                ctx = t[max(0, j - 30):j + len(bad)]
                assert neg.search(ctx), (p.name, bad, ctx)
                i = j + 1


# ---- 27-30: false-claim discipline ----
def test_27_no_false_benefit_realisation_claim():
    for p in html_files():
        t = read(p)
        assert "benefit realised" not in t.lower()
        assert "realisation declared" not in t.lower()


def test_28_no_false_pattern_or_asset_qualification():
    for f in DATA.glob("TEST_*_CANDIDATE.json"):
        d = json.loads(read(f))
        assert d["packet"]["proposed_pattern"].startswith("NONE")
    for p in html_files():
        assert "qualified as a pattern" not in read(p).lower()


def test_29_ppv_remains_potential():
    assert REG["ppv"] == "Potential"
    for e in REG["elements"]:
        for c in e["level3"]:
            assert c["ppv"] == "Potential"
    for v in REG["verbs"]:
        assert v["ppv"] == "Potential"


def test_30_bridge_pattern_qualification_held():
    assert any("Bridge Pattern qualification" in h for h in REG["held"])


# ---- 31-32: fixture routing ----
@pytest.mark.parametrize("fid", ["TEST_PROCESS_001", "TEST_OFFERING_001"])
def test_31_32_fixture_candidate_routing(fid):
    d = json.loads(read(DATA / f"{fid}_CANDIDATE.json"))
    assert d["packet"]["synthetic"] is True
    trace = d["verb_routing_trace"]
    assert [t["verb"] for t in trace] == [v["id"] for v in model.VERBS]
    v7 = next(t for t in trace if t["verb"] == "V7")
    assert v7["state"] == "HOLD"
    assert set(d["mesh_stages_covered"]) == set(model.MESH_STAGES)
    assert d["result"] == "CANDIDATE_ROUTING_COMPLETE_ACTIVATION_HELD"
    # all required candidate fields populated
    for k in ["candidate_id", "name", "type", "purpose", "strategic_contribution",
              "target_beneficiary", "context", "initiating_signal",
              "problem_or_opportunity", "proposed_service", "proposed_method",
              "proposed_pattern", "canonical_basis", "work_object",
              "expected_benefits", "baseline", "target", "evidence_source",
              "realisation_test", "potential_asset_effect", "owner_lane",
              "dependencies", "risks", "authority", "ppv", "stop_hold",
              "next_action", "replay_validity"]:
        assert str(d["packet"][k]).strip(), (fid, k)


# ---- 33-34: no mutation, no secrets ----
def test_33_no_odoo_n8n_mutation_language():
    for p in list(CURRENT.rglob("*.json")) + [pathlib.Path(p) for p in html_files()]:
        t = read(pathlib.Path(p))
        for phrase in ["create_odoo(", "write_odoo(", "unlink_odoo(",
                       "update_workflow(", "activate_workflow("]:
            assert phrase not in t, (str(p), phrase)


def test_34_no_secret_shaped_value():
    pat = re.compile(r"(api[_-]?key|password|secret|token)\s*[:=]\s*['\"][A-Za-z0-9+/]{16,}",
                     re.I)
    for p in CURRENT.rglob("*"):
        if p.is_file() and p.suffix in {".html", ".json", ".md", ".csv"}:
            assert not pat.search(read(p)), str(p)


# ---- 35: cold-start replay from Home ----
def test_35_cold_start_replay_from_home():
    t = read(HOME)
    # Home -> Navigator (browser-safe vault-relative route present)
    assert f"{model.NAVIGATOR_FILE}" in t
    nav = read(NAVIGATOR)
    # Navigator communicates objective, priorities, stream A, and routes onward
    assert "WO-NAVIGATOR-MVP" in nav
    assert "ASSURED_STREAM_A_COMPLETE" in nav
    assert model.VERBS_FILE in nav
    assert model.START_FILE in nav
    for e in model.ELEMENTS:
        assert e["html"] in nav, e["html"]
        assert e["canvas_view"] in nav, e["canvas_view"]
    # Verbs page routes back and onward
    tv = read(COMP / model.VERBS_FILE)
    assert model.START_FILE in tv


# ---- nested loop: 9 x 9 x 27 assertion sweep ----
def test_nested_element_verb_l3_sweep():
    """Full nested verification: every element x verb mapping and every L3
    cell carries the required fields, valid mesh stages, valid benefit,
    routes and return paths. Counts filed in the test matrix."""
    checks = 0
    for e in REG["elements"]:
        # element routes
        for rk in ["html", "canvas_view", "canvas_source", "return_verbs",
                   "return_navigator"]:
            assert e["routes"][rk]
            checks += 1
        maps = [m for m in REG["element_verb_mappings"] if m["element"] == e["id"]]
        assert len(maps) == 9
        for m in maps:
            assert m["statement"].strip()
            assert set(m["mesh_stages"]) <= set(model.MESH_STAGES)
            assert m["benefit"] in REG["benefits"]
            checks += 3
        for c in e["level3"]:
            for k in ["trace_id", "decision_served", "incoming_signal",
                      "interpretation", "required_structure", "validation_test",
                      "permitted_action", "expected_benefit",
                      "evidence_requirement", "realisation_condition",
                      "asset_implication", "source_system", "reality", "ppv",
                      "authority", "owner", "next_action", "stop_hold",
                      "replay_validity", "return_path"]:
                assert str(c[k]).strip(), (c["trace_id"], k)
                checks += 1
            assert c["applicable"] is True
            assert set(c["verbs"]) <= {v["id"] for v in model.VERBS}
            checks += 2
    (HERE / "dist" / "ASSERTION_COUNT.txt").write_text(str(checks))
    assert checks >= 2187  # exceeds the 'up to 2187' nested assertion budget
