"""Tests for the matrix engine: reducer correctness (including rejection
of out-of-order events -- no silent repair), prioritisation ordering, mesh
gating, pattern-registry MECE shape, renderer purity, receipt
recomputability, and the static no-Odoo/no-N8N-import boundary.
"""

import ast
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matrix_engine as me  # noqa: E402


def test_pattern_registry_is_mece_nine_cells_three_planes():
    assert len(me.PATTERN_REGISTRY) == 9
    planes = [p["plane"] for p in me.PATTERN_REGISTRY.values()]
    assert sorted(set(planes)) == sorted(me.PLANES)
    for plane in me.PLANES:
        assert planes.count(plane) == 3
    verbs = [p["verb"] for p in me.PATTERN_REGISTRY.values()]
    assert len(verbs) == len(set(verbs)), "verb names must be mutually exclusive"


def test_new_state_starts_every_cell_idle_at_signal():
    state = me.new_state()
    assert state["rev"] == 0
    assert state["events"] == []
    assert state["rejected"] == []
    assert set(state["cells"]) == set(me.PATTERN_REGISTRY)
    for cell in state["cells"].values():
        assert cell["stage"] == "signal"
        assert cell["stage_since_rev"] == 0


def test_reduce_accepts_valid_sequential_transition():
    state = me.new_state()
    event = {"cell_id": "G1", "to_stage": "attributes", "payload": {"direction": "north"}}
    new = me.reduce(state, event)
    assert new is not state, "reduce must not mutate its input in place"
    assert new["cells"]["G1"]["stage"] == "attributes"
    assert new["cells"]["G1"]["attributes"] == {"direction": "north"}
    assert new["rev"] == 1
    assert new["events"] == [event]
    assert new["rejected"] == []
    # original untouched
    assert state["cells"]["G1"]["stage"] == "signal"
    assert state["rev"] == 0


def test_reduce_rejects_out_of_order_jump():
    state = me.new_state()
    bad_event = {"cell_id": "G1", "to_stage": "observation", "payload": {}}
    new = me.reduce(state, bad_event)
    assert new["cells"]["G1"]["stage"] == "signal", "invalid event must not be silently repaired into a valid one"
    assert new["rev"] == 0
    assert len(new["rejected"]) == 1
    assert new["rejected"][0]["reason"] == "not-a-valid-sequential-transition"


def test_reduce_rejects_unknown_cell_id():
    state = me.new_state()
    new = me.reduce(state, {"cell_id": "Z9", "to_stage": "attributes", "payload": {}})
    assert new["rejected"][0]["reason"] == "not-a-valid-sequential-transition"
    assert new["rev"] == 0


def test_reduce_feedback_wraps_to_signal_and_clears_the_cycle():
    state = me.new_state()
    for stage, payload in [
        ("attributes", {"a": 1}),
        ("expression", {"e": 1}),
        ("observation", {"o": 1}),
        ("learning", {"l": 1}),
        ("asset_conversion", {"ac": 1}),
        ("feedback", {"f": 1}),
    ]:
        state = me.reduce(state, {"cell_id": "G1", "to_stage": stage, "payload": payload})
    assert state["cells"]["G1"]["stage"] == "feedback"
    assert state["rejected"] == []

    next_cycle = me.reduce(state, {"cell_id": "G1", "to_stage": "signal", "payload": {"s": "cycle-2"}})
    cell = next_cycle["cells"]["G1"]
    assert cell["stage"] == "signal"
    assert cell["signal"] == {"s": "cycle-2"}
    assert cell["attributes"] is None
    assert cell["expression"] is None
    assert cell["observation"] is None
    assert cell["learning"] is None
    assert cell["asset_conversion"] is None


def test_prioritise_orders_govern_before_deliver_before_realise():
    state = me.new_state()
    ranked = me.prioritise(state)
    plane_sequence = [r["plane"] for r in ranked]
    first_deliver = plane_sequence.index("deliver")
    first_realise = plane_sequence.index("realise")
    last_govern = max(i for i, p in enumerate(plane_sequence) if p == "govern")
    assert last_govern < first_deliver < first_realise


def test_prioritise_favours_longer_idle_cells_within_a_plane():
    state = me.new_state()
    # advance G2 once so G1/G3 are "more idle" relative to it at rev=1
    state = me.reduce(state, {"cell_id": "G2", "to_stage": "attributes", "payload": {}})
    ranked = me.prioritise(state)
    govern_ranked = [r["cell_id"] for r in ranked if r["plane"] == "govern"]
    assert govern_ranked[0] in ("G1", "G3"), "cells still idle since rev 0 must outrank the one just advanced"
    assert govern_ranked[-1] == "G2"


def test_validate_mesh_fails_on_incomplete_triad():
    state = me.new_state()
    result = me.validate_mesh(state, "G1")
    assert result["passed"] is False
    assert result["checks"]["canonical"] is True
    assert result["checks"]["intelligence"] is False
    assert result["checks"]["fpv"] is False


def test_validate_mesh_passes_once_signal_attributes_expression_complete():
    state = me.new_state()
    state = me.reduce(state, {"cell_id": "G1", "to_stage": "attributes", "payload": {"a": 1}})
    state = me.reduce(state, {"cell_id": "G1", "to_stage": "expression", "payload": {"e": 1}})
    result = me.validate_mesh(state, "G1")
    assert result["passed"] is True
    assert all(result["checks"].values())


def test_validate_mesh_unknown_cell_fails_cleanly():
    state = me.new_state()
    result = me.validate_mesh(state, "Z9")
    assert result["passed"] is False
    assert result["checks"] == {}


def test_render_is_pure_and_deterministic():
    state = me.new_state()
    html_a = me.render(state)
    html_b = me.render(copy.deepcopy(state))
    assert html_a == html_b
    assert html_a.count("<tr>") == 9 + 1  # 9 body rows + 1 header row


def test_render_emits_no_script_tag():
    state = me.new_state()
    html = me.render(state)
    assert "<script" not in html.lower(), "HTML is presentation only -- no behaviour may be emitted"


def test_write_receipt_hash_is_independently_recomputable():
    state = me.new_state()
    state = me.reduce(state, {"cell_id": "G1", "to_stage": "attributes", "payload": {"a": 1}})
    receipt = me.write_receipt(state)
    recomputed = me.write_receipt(copy.deepcopy(state))
    assert receipt["state_sha256"] == recomputed["state_sha256"]
    assert receipt["revision"] == 1
    assert receipt["event_count"] == 1
    assert receipt["rejected_count"] == 0
    assert receipt["odoo_mutations"] == 0
    assert receipt["n8n_mutations"] == 0


def test_write_receipt_hash_changes_when_state_changes():
    state = me.new_state()
    r0 = me.write_receipt(state)
    state = me.reduce(state, {"cell_id": "G1", "to_stage": "attributes", "payload": {"a": 1}})
    r1 = me.write_receipt(state)
    assert r0["state_sha256"] != r1["state_sha256"]


def test_no_odoo_or_n8n_imports_anywhere_in_the_module():
    source = (Path(__file__).resolve().parents[1] / "matrix_engine.py").read_text()
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0].lower())
    banned = {"odoo", "n8n", "xmlrpc", "requests", "httpx", "socket", "subprocess"}
    assert imported.isdisjoint(banned), imported & banned


def test_no_odoo_or_n8n_mentioned_outside_the_module_docstring_boundary_comment():
    """The words 'odoo'/'n8n' may appear only in the module docstring and
    the receipt's own field names (odoo_mutations/n8n_mutations, always 0)
    -- never as a call, client, or credential reference."""
    source = (Path(__file__).resolve().parents[1] / "matrix_engine.py").read_text()
    lines = source.splitlines()
    in_docstring = False
    offending = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"""'):
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        lowered = line.lower()
        if ("odoo" in lowered or "n8n" in lowered) and "mutations" not in lowered:
            offending.append((i + 1, line))
    assert offending == [], offending
