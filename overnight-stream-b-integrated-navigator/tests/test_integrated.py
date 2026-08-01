"""
Overnight Stream B test suite: schema, link/route validity, determinism,
accessibility, white-background, source-tag, control-route, no-competing-
Home, and manifest-integrity — run after build_overnight_candidate.py,
viewer/n8n_viewer_scvs.py and architecture/build_architecture_v1_3.py have
all produced their current output (same precondition pattern Lane B's own
test suite uses).
"""
import copy
import csv
import hashlib
import json
import pathlib
import re
import sys
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from adapters.accepted_canvas_raw_capture import parsed as parsed_accepted_canvases  # noqa: E402
from adapters.existing_canvas_adapter import adapt_accepted_canvas  # noqa: E402
from scvs.scvs_compiler import GraphCompileError, canonical_dumps, compile_canvas_scvs, load_schema_v02, structural_only  # noqa: E402
from scvs.stream_a_adapter import StreamANotReturnedError, adapt_stream_a_payload  # noqa: E402

GENERATED = ROOT / "generated"
CANVAS_SUITE_DIR = GENERATED / "candidate_canvases"
PROFILES_DIR = GENERATED / "candidate_profiles"
VIEWER_HTML = GENERATED / "N8N_VIEWER_CANDIDATE.html"
ARCHITECTURE_HTML = GENERATED / "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"
MANIFEST_PATH = ROOT / "CANDIDATE_MANIFEST_SHA256.csv"
V1_3_RETURN_ROUTE = (
    "05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
    "WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/OVERNIGHT_STREAM_B_OUTPUT_v0.1/"
    "SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.3_CANDIDATE.html"
)

HREF_RE = re.compile(r'(?:href|src)="([^"]*)"')
# Known, disclosed exception: the three iframe components carried unchanged from
# v1.2 are vault-relative by original design (see README "Known constraint").
VAULT_RELATIVE_ALLOWED_PREFIXES = ("COMPONENTS/",)


def _minimal_valid_graph():
    return {
        "view_id": "test_view",
        "title": "Test View",
        "snapshot": "2026-08-01T16:48:19Z",
        "source": "unit_test_fixture",
        "evidence": "LABELLED_FIXTURE",
        "reality": "test",
        "ppv": "Potential",
        "authority": "test_authority",
        "return_route": V1_3_RETURN_ROUTE,
        "objects": [
            {"id": "a", "label": "A", "kind": "test_kind", "lifecycle_state": "active", "authority": "auth_a"},
            {"id": "b", "label": "B", "kind": "test_kind", "lifecycle_state": "candidate", "authority": "auth_b",
             "evidence": "SUFFICIENT", "ppv": "Probable", "owner_lane": "[D001]", "source_tag": "WM"},
        ],
        "relationships": [{"id": "e1", "from": "a", "to": "b", "verb": "flows_to"}],
    }


class SchemaTests(unittest.TestCase):
    def test_v02_schema_loads(self):
        schema = load_schema_v02()
        self.assertEqual(schema["$id"], "synapsys://overnight-stream-b/graph-adapter-contract-v0.2")

    def test_minimal_graph_compiles(self):
        compile_canvas_scvs(_minimal_valid_graph())

    def test_every_adapted_canvas_suite_graph_conforms(self):
        accepted = parsed_accepted_canvases()
        for filename, raw in accepted.items():
            with self.subTest(file=filename):
                graph = adapt_accepted_canvas(filename, raw, V1_3_RETURN_ROUTE, "2026-08-01T16:48:19Z")
                compile_canvas_scvs(graph)  # raises on any schema/link violation

    def test_optional_v02_fields_do_not_break_v01_shaped_graphs(self):
        # a v0.1-shaped graph (no evidence/ppv/owner_lane/source_tag on objects) must still compile
        graph = _minimal_valid_graph()
        del graph["objects"][1]["evidence"]
        del graph["objects"][1]["ppv"]
        del graph["objects"][1]["owner_lane"]
        del graph["objects"][1]["source_tag"]
        compile_canvas_scvs(graph)


class LinkAndRouteTests(unittest.TestCase):
    def test_arrow_notation_return_route_fails_closed(self):
        graph = _minimal_valid_graph()
        graph["return_route"] = "Obsidian/00_HOME.md -> somewhere/else.md"
        with self.assertRaises(GraphCompileError):
            compile_canvas_scvs(graph)

    def test_every_generated_canvas_return_route_is_the_v13_candidate_path(self):
        for path in sorted(CANVAS_SUITE_DIR.glob("*.canvas")) + sorted(PROFILES_DIR.glob("*.canvas")):
            with self.subTest(file=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["metadata"]["return_route"], V1_3_RETURN_ROUTE)
                self.assertNotIn("->", data["metadata"]["return_route"])

    def test_every_generated_canvas_edge_resolves_to_a_real_node(self):
        for path in sorted(CANVAS_SUITE_DIR.glob("*.canvas")) + sorted(PROFILES_DIR.glob("*.canvas")):
            with self.subTest(file=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                node_ids = {n["id"] for n in data["nodes"]}
                for edge in data["edges"]:
                    self.assertIn(edge["fromNode"], node_ids)
                    self.assertIn(edge["toNode"], node_ids)

    def test_viewer_html_links_have_no_arrow_notation_or_mac_absolute_paths(self):
        html = VIEWER_HTML.read_text(encoding="utf-8")
        for href in HREF_RE.findall(html):
            with self.subTest(href=href):
                self.assertNotIn("->", href)
                self.assertFalse(href.startswith("/Users/"), "absolute local Mac path found")
                self.assertFalse(href.startswith("file://"), "absolute local file path found")

    def test_architecture_v13_links_have_no_arrow_notation_or_mac_absolute_paths(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        hrefs = HREF_RE.findall(html)
        self.assertGreater(len(hrefs), 0)
        for href in hrefs:
            with self.subTest(href=href):
                self.assertNotIn("->", href)
                self.assertFalse(href.startswith("/Users/"))
                self.assertFalse(href.startswith("file://"))
                is_fragment = href.startswith("#")
                is_stable_url = href.startswith("https://")
                is_disclosed_vault_relative = href.startswith(VAULT_RELATIVE_ALLOWED_PREFIXES)
                self.assertTrue(
                    is_fragment or is_stable_url or is_disclosed_vault_relative,
                    f"href {href!r} is neither a fragment, a stable https URL, nor a disclosed vault-relative path",
                )

    def test_architecture_v13_return_link_points_at_v12(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        self.assertIn("SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html", html)

    def test_architecture_v13_does_not_self_declare_implemented_or_current(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        self.assertNotIn('class="state implemented">Architecture v1.3', html)
        self.assertIn("CANDIDATE", html)
        self.assertIn("NOT the current Navigator control surface", html)


class DeterminismTests(unittest.TestCase):
    def test_same_graph_compiles_byte_identical_twice(self):
        graph = _minimal_valid_graph()
        a = compile_canvas_scvs(copy.deepcopy(graph))
        b = compile_canvas_scvs(copy.deepcopy(graph))
        self.assertEqual(canonical_dumps(structural_only(a)), canonical_dumps(structural_only(b)))

    def test_every_adapted_canvas_suite_graph_is_deterministic(self):
        accepted = parsed_accepted_canvases()
        for filename, raw in accepted.items():
            with self.subTest(file=filename):
                graph = adapt_accepted_canvas(filename, raw, V1_3_RETURN_ROUTE, "2026-08-01T16:48:19Z")
                a = compile_canvas_scvs(copy.deepcopy(graph))
                b = compile_canvas_scvs(copy.deepcopy(graph))
                self.assertEqual(canonical_dumps(structural_only(a)), canonical_dumps(structural_only(b)))

    def test_rebuild_from_unchanged_inputs_matches_files_on_disk(self):
        # Re-adapt + re-compile canvas 01 right now and compare against the
        # already-written file — proves the actual build script's output
        # (not just the function in isolation) is reproducible.
        accepted = parsed_accepted_canvases()
        filename = "01_ENTERPRISE_INTEGRATED.canvas"
        graph = adapt_accepted_canvas(filename, accepted[filename], V1_3_RETURN_ROUTE, "2026-08-01T16:48:19Z")
        rebuilt = compile_canvas_scvs(graph)
        on_disk = json.loads((CANVAS_SUITE_DIR / "01_ENTERPRISE_INTEGRATED_CANDIDATE.canvas").read_text(encoding="utf-8"))
        self.assertEqual(canonical_dumps(structural_only(rebuilt)), canonical_dumps(structural_only(on_disk)))


class WhiteBackgroundTests(unittest.TestCase):
    def test_viewer_html_has_no_dark_mode_media_query(self):
        html = VIEWER_HTML.read_text(encoding="utf-8")
        self.assertNotIn("prefers-color-scheme", html)
        self.assertIn("background:#ffffff", html)

    def test_architecture_v13_has_no_dark_mode_media_query(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        self.assertNotIn("prefers-color-scheme", html)
        self.assertIn("background:#fff", html)


class AccessibilityTests(unittest.TestCase):
    def test_architecture_v13_has_lang_and_skip_link(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)
        self.assertIn('class="skip" href="#main"', html)

    def test_viewer_html_has_lang_attribute(self):
        html = VIEWER_HTML.read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)

    def test_architecture_v13_tabs_carry_aria_roles(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8")
        self.assertIn('role="tablist"', html)
        self.assertIn('role="tabpanel"', html)
        self.assertIn('aria-selected', html)


class NoCompetingHomeTests(unittest.TestCase):
    def test_no_generated_file_is_named_00_home(self):
        for path in GENERATED.rglob("*"):
            if path.is_file():
                self.assertNotIn("00_HOME", path.name.upper())

    def test_architecture_v13_does_not_declare_itself_a_new_home_or_dashboard(self):
        html = ARCHITECTURE_HTML.read_text(encoding="utf-8").lower()
        # It may reference "home"/"dashboard" only in the context of returning
        # to or describing the EXISTING ones, never claiming to BE one.
        self.assertNotIn("new home", html)
        self.assertNotIn("new dashboard", html)
        self.assertNotIn("this is the current home", html)

    def test_only_one_architecture_shell_file_is_generated(self):
        shells = list(GENERATED.glob("SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_*"))
        self.assertEqual(len(shells), 1, f"expected exactly one architecture shell, found {shells}")


class StreamAAdapterTests(unittest.TestCase):
    def test_adapter_refuses_when_no_payload(self):
        with self.assertRaises(StreamANotReturnedError):
            adapt_stream_a_payload(None)

    def test_adapter_maps_a_well_formed_payload_without_fabrication(self):
        payload = {
            "nodes_or_objects": [{"id": "x1", "label": "X", "lifecycle_state": "active", "authority": "a"}],
            "edges_or_relationships": [{"id": "e1", "from": "x1", "to": "x1", "verb": "self"}],
            "return_route": V1_3_RETURN_ROUTE,
        }
        graph = adapt_stream_a_payload(payload)
        compile_canvas_scvs(graph)  # must be a fully valid, compilable graph


class ManifestIntegrityTests(unittest.TestCase):
    def test_manifest_exists(self):
        self.assertTrue(MANIFEST_PATH.exists())

    def test_every_manifest_row_matches_file_on_disk(self):
        with open(MANIFEST_PATH, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreater(len(rows), 0)
        for row in rows:
            full_path = ROOT / row["path"]
            with self.subTest(file=row["path"]):
                self.assertTrue(full_path.exists())
                content = full_path.read_bytes()
                self.assertEqual(len(content), int(row["bytes"]))
                self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])


if __name__ == "__main__":
    unittest.main()
