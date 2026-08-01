"""
unittest (stdlib only — no pytest dependency in this environment) covering:
  - schema validation (valid graphs pass, invalid ones are rejected)
  - link integrity (every edge resolves to a real node id, fails closed otherwise)
  - node/edge counts match the compiled canvas for every profile
  - determinism (same input -> byte-identical structural output, twice)
  - fail-closed on unknown relationship endpoints and missing authority metadata
  - every generated .canvas file is valid JSON with the required nodes/edges keys
"""
import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.canvas_compiler import (  # noqa: E402
    GraphCompileError,
    canonical_dumps,
    compile_canvas,
    load_schema,
    structural_only,
    validate_graph,
)
from compiler.view_profiles import available_profiles, load_profile_graph  # noqa: E402

GENERATED_DIR = ROOT / "generated"


def minimal_valid_graph() -> dict:
    return {
        "view_id": "test_view",
        "title": "Test View",
        "snapshot": "2026-08-02T00:00:00Z",
        "source": "unit_test_fixture",
        "evidence": "LABELLED_FIXTURE",
        "reality": "test",
        "ppv": "Potential",
        "authority": "test_authority",
        "return_route": "Obsidian/00_HOME.md",
        "objects": [
            {"id": "a", "label": "A", "kind": "test_kind", "lifecycle_state": "active", "authority": "auth_a"},
            {"id": "b", "label": "B", "kind": "test_kind", "lifecycle_state": "candidate", "authority": "auth_b", "group": "g1"},
        ],
        "relationships": [
            {"id": "e1", "from": "a", "to": "b", "verb": "flows_to"},
        ],
    }


class SchemaValidationTests(unittest.TestCase):
    def test_valid_graph_passes(self):
        validate_graph(minimal_valid_graph())  # should not raise

    def test_missing_required_top_level_field_fails_closed(self):
        graph = minimal_valid_graph()
        del graph["evidence"]
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)

    def test_missing_object_authority_fails_closed(self):
        graph = minimal_valid_graph()
        del graph["objects"][0]["authority"]
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)

    def test_empty_object_authority_fails_closed(self):
        graph = minimal_valid_graph()
        graph["objects"][0]["authority"] = "   "
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)

    def test_invalid_lifecycle_state_fails_closed(self):
        graph = minimal_valid_graph()
        graph["objects"][0]["lifecycle_state"] = "not_a_real_state"
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)

    def test_duplicate_object_id_fails_closed(self):
        graph = minimal_valid_graph()
        graph["objects"].append({"id": "a", "label": "A2", "kind": "k", "lifecycle_state": "active", "authority": "x"})
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)


class LinkIntegrityTests(unittest.TestCase):
    def test_unknown_relationship_from_fails_closed(self):
        graph = minimal_valid_graph()
        graph["relationships"][0]["from"] = "does_not_exist"
        with self.assertRaises(GraphCompileError) as ctx:
            validate_graph(graph)
        self.assertIn("UNKNOWN_RELATIONSHIP_ENDPOINT", str(ctx.exception))

    def test_unknown_relationship_to_fails_closed(self):
        graph = minimal_valid_graph()
        graph["relationships"][0]["to"] = "does_not_exist"
        with self.assertRaises(GraphCompileError) as ctx:
            validate_graph(graph)
        self.assertIn("UNKNOWN_RELATIONSHIP_ENDPOINT", str(ctx.exception))

    def test_missing_verb_fails_closed(self):
        graph = minimal_valid_graph()
        graph["relationships"][0]["verb"] = ""
        with self.assertRaises(GraphCompileError):
            validate_graph(graph)

    def test_compiled_edges_all_resolve_to_compiled_nodes(self):
        canvas = compile_canvas(minimal_valid_graph())
        node_ids = {n["id"] for n in canvas["nodes"]}
        for edge in canvas["edges"]:
            self.assertIn(edge["fromNode"], node_ids)
            self.assertIn(edge["toNode"], node_ids)


class CountTests(unittest.TestCase):
    def test_node_count_is_objects_plus_two_fixed_panels(self):
        graph = minimal_valid_graph()
        canvas = compile_canvas(graph)
        # +2: the source/evidence/authority metadata panel and the Home-return node
        self.assertEqual(len(canvas["nodes"]), len(graph["objects"]) + 2)

    def test_edge_count_is_relationships_plus_one_return_edge(self):
        graph = minimal_valid_graph()
        canvas = compile_canvas(graph)
        self.assertEqual(len(canvas["edges"]), len(graph["relationships"]) + 1)

    def test_every_profile_node_and_edge_count_matches_its_source_graph(self):
        for profile_id in available_profiles():
            graph = load_profile_graph(profile_id)
            canvas = compile_canvas(graph)
            with self.subTest(profile=profile_id):
                self.assertEqual(len(canvas["nodes"]), len(graph["objects"]) + 2)
                self.assertEqual(len(canvas["edges"]), len(graph["relationships"]) + 1)


class DeterminismTests(unittest.TestCase):
    def test_identical_input_produces_identical_structural_output(self):
        graph = minimal_valid_graph()
        first = compile_canvas(copy.deepcopy(graph))
        second = compile_canvas(copy.deepcopy(graph))
        self.assertEqual(canonical_dumps(structural_only(first)), canonical_dumps(structural_only(second)))

    def test_object_input_order_does_not_affect_output(self):
        graph_a = minimal_valid_graph()
        graph_b = copy.deepcopy(graph_a)
        graph_b["objects"] = list(reversed(graph_b["objects"]))
        canvas_a = compile_canvas(graph_a)
        canvas_b = compile_canvas(graph_b)
        self.assertEqual(canonical_dumps(structural_only(canvas_a)), canonical_dumps(structural_only(canvas_b)))

    def test_snapshot_only_change_does_not_affect_structural_output(self):
        graph_a = minimal_valid_graph()
        graph_b = copy.deepcopy(graph_a)
        graph_b["snapshot"] = "2099-01-01T00:00:00Z"
        canvas_a = compile_canvas(graph_a)
        canvas_b = compile_canvas(graph_b)
        self.assertEqual(canonical_dumps(structural_only(canvas_a)), canonical_dumps(structural_only(canvas_b)))

    def test_every_profile_is_deterministic_across_two_compiles(self):
        for profile_id in available_profiles():
            graph = load_profile_graph(profile_id)
            first = compile_canvas(copy.deepcopy(graph))
            second = compile_canvas(copy.deepcopy(graph))
            with self.subTest(profile=profile_id):
                self.assertEqual(
                    canonical_dumps(structural_only(first)),
                    canonical_dumps(structural_only(second)),
                )


class SchemaFileTests(unittest.TestCase):
    def test_schema_loads_and_is_valid_json_schema(self):
        schema = load_schema()
        self.assertEqual(schema["$id"], "synapsys://lane-b/graph-adapter-contract-v0.1")
        self.assertIn("objects", schema["required"])
        self.assertIn("relationships", schema["required"])

    def test_every_fixture_file_conforms_to_the_declared_schema(self):
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                validate_graph(graph)  # raises on any violation


class GeneratedCanvasFileTests(unittest.TestCase):
    """Guards the two REQUIRED deliverables and every demo canvas already
    written to generated/ by generate_canvases.py — run that script first.
    """

    def test_required_deliverables_exist_and_are_valid_json_canvas(self):
        for fname in ("N8N_OVERVIEW.canvas", "D007_WORKFLOW_TOPOLOGY.canvas"):
            path = GENERATED_DIR / fname
            with self.subTest(file=fname):
                self.assertTrue(path.exists(), f"missing required deliverable {path}")
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("nodes", data)
                self.assertIn("edges", data)
                self.assertIn("metadata", data)
                node_ids = {n["id"] for n in data["nodes"]}
                for edge in data["edges"]:
                    self.assertIn(edge["fromNode"], node_ids)
                    self.assertIn(edge["toNode"], node_ids)

    def test_all_generated_canvas_files_share_one_grammar(self):
        canvas_files = sorted(GENERATED_DIR.glob("*.canvas"))
        self.assertGreaterEqual(len(canvas_files), 11, "expected all 11 view profiles to have generated a .canvas file")
        for path in canvas_files:
            with self.subTest(file=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(set(data.keys()), {"nodes", "edges", "metadata"})
                self.assertEqual(
                    data["metadata"]["grammar"],
                    "synapsys-obsidian-canvas-v0.2 (nodes/edges per JSON Canvas + metadata panel node + Home return node/edge)",
                )
                node_ids = [n["id"] for n in data["nodes"]]
                self.assertEqual(len(node_ids), len(set(node_ids)), "duplicate node id in generated canvas")


if __name__ == "__main__":
    unittest.main()
