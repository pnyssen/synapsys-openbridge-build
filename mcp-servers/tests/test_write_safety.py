"""
Tests for mcp-servers/_write_safety.py — the common prepare/execute
write-set safety core (RELEASE_D007_SYNAPSYS_MCP_FFE_MUTATION_SAFETY_
ENFORCEMENT_V1, group A/B).

No live Odoo/N8N credentials or network access required — the module has
no direct connector dependency; every read/count/mutate closure here is a
plain in-memory fake driven by explicit fixture data, matching this
release's "HOLD any test requiring an unavailable live connector" boundary.

Each test is named after the acceptance-matrix canary it exercises where
one applies (P0-A .. P0-F).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

MCP_SERVERS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_SERVERS_DIR))

import _write_safety as ws  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture backend: an in-memory fake "Odoo" — resolve_ids/read_fn/count_fn/
# mutate_fn implementations closing over a plain dict-of-records store.
# ---------------------------------------------------------------------------

class FakeBackend:
    def __init__(self, model: str, records: dict[int, dict]):
        self.model = model
        self.records = {int(k): dict(v) for k, v in records.items()}
        self.mutations: list[tuple[str, list[int], dict]] = []

    def resolve_all_ids(self) -> list[int]:
        return list(self.records.keys())

    def read_fn(self, model: str, ids: list[int], fields: list[str]) -> list[dict]:
        rows = []
        for i in ids:
            rec = self.records.get(i, {})
            row = {f: rec.get(f) for f in fields if f != "id"}
            row["id"] = i  # 'id' always reflects the real record id, never a stored field
            rows.append(row)
        return rows

    def count_fn(self, model: str) -> int:
        return len(self.records)

    def mutate_fn(self, model: str, operation: str, ids: list[int], proposed: dict):
        self.mutations.append((operation, list(ids), dict(proposed)))
        if operation == "write":
            for i in ids:
                self.records.setdefault(i, {}).update(proposed)
            return True
        if operation == "unlink":
            for i in ids:
                self.records.pop(i, None)
            return True
        raise ValueError(operation)


def make_store() -> ws.WriteSetStore:
    return ws.WriteSetStore()


# ---------------------------------------------------------------------------
# P0-A BLAST_RADIUS_CANARY — actual resolved count/ids are authoritative,
# never a caller-supplied intended_count. Reproduces the root-cause shape
# of the Benefit-register incident (15 believed vs 53 actual) at small
# scale, non-mutating.
# ---------------------------------------------------------------------------

def test_p0a_actual_count_is_authoritative_over_intended_count():
    backend = FakeBackend("x_ss_benefit_register", {i: {"x_benefit_status": "planned"} for i in range(1, 6)})
    store = make_store()

    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"x_benefit_status": "superseded"}, intended_count=1, store=store,
    )

    assert preview["actual_affected_count"] == 5
    assert preview["enumerated_ids"] == [1, 2, 3, 4, 5]
    assert preview["intended_count"] == 1  # carried through informationally, not trusted
    # no mutation occurred during prepare
    assert backend.mutations == []
    assert all(r["x_benefit_status"] == "planned" for r in backend.records.values())


def test_p0a_execute_only_mutates_the_resolved_actual_set():
    backend = FakeBackend("x_ss_benefit_register", {i: {"x_benefit_status": "planned"} for i in range(1, 6)})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"x_benefit_status": "superseded"}, store=store,
    )
    result = ws.execute_write_set(
        write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
        read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
    )
    assert result["actual_affected_count"] == 5
    assert all(r["x_benefit_status"] == "superseded" for r in backend.records.values())


# ---------------------------------------------------------------------------
# P0-B BULK_CEILING — >10 ids, or <=10 but >20% of register, requires
# explicit enumerated ids identical to the prepared set (i.e. prepare
# flags requires_enumerated_ids=True; the *wrapping* single-call tools use
# this flag to refuse convenience auto-execution — tested at the odoo_mcp
# layer in test_transport.py).
# ---------------------------------------------------------------------------

def test_p0b_bulk_over_ten_requires_enumerated_ids():
    backend = FakeBackend("x_service_catalogue", {i: {"name": f"r{i}"} for i in range(1, 12)})  # 11 records
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "renamed"}, store=store,
    )
    assert preview["actual_affected_count"] == 11
    assert preview["requires_enumerated_ids"] is True


def test_p0b_small_but_over_twenty_percent_of_register_requires_enumerated_ids():
    # 3 of 10 = 30% > 20% ceiling, even though 3 <= BULK_ID_CEILING (10)
    all_records = {i: {"name": f"r{i}"} for i in range(1, 11)}
    backend = FakeBackend("x_service_catalogue", all_records)

    class SubsetBackend(FakeBackend):
        def resolve_subset(self):
            return [1, 2, 3]

    backend.resolve_subset = lambda: [1, 2, 3]
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_subset, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "renamed"}, store=store,
    )
    assert preview["actual_affected_count"] == 3
    assert preview["affected_percentage"] == 30.0
    assert preview["requires_enumerated_ids"] is True


def test_p0b_execute_refuses_when_supplied_ids_dont_exactly_match_prepared_set():
    backend = FakeBackend("x_service_catalogue", {i: {"name": f"r{i}"} for i in range(1, 4)})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "renamed"}, store=store,
    )
    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id=preview["write_set_id"], enumerated_ids=[1, 2],  # missing id 3
            read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        )
    assert ei.value.invariant == "SET_MISMATCH"
    assert ei.value.actual["removed"] == [3]
    # no mutation occurred
    assert backend.mutations == []


# ---------------------------------------------------------------------------
# P0-C PROTECTED_STATE — mixed ordinary+protected Benefit-state transitions
# refuse ordinary execution and require a distinct confirmation.
# ---------------------------------------------------------------------------

def test_p0c_protected_benefit_state_transition_blocks_ordinary_execute():
    backend = FakeBackend("x_ss_benefit_register", {
        1: {"x_benefit_status": "planned"},
        2: {"x_benefit_status": "verified"},  # protected
    })
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"x_benefit_status": "superseded"}, store=store,
    )
    assert preview["requires_protected_state_confirmation"] is True
    assert preview["protected_transitions"] == [
        {"id": 2, "field": "x_benefit_status", "prior": "verified", "proposed": "superseded"}
    ]
    assert ws.CONSENT_PROTECTED_STATE_TRANSITION in preview["consent_classes"]

    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
            read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        )
    assert ei.value.invariant == "PROTECTED_STATE_CONFIRMATION_REQUIRED"
    assert backend.mutations == []


def test_p0c_protected_state_executes_once_explicitly_confirmed():
    backend = FakeBackend("x_ss_benefit_register", {2: {"x_benefit_status": "measured"}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"x_benefit_status": "superseded"}, store=store,
    )
    result = ws.execute_write_set(
        write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
        read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        protected_state_confirmed=True,
    )
    assert backend.records[2]["x_benefit_status"] == "superseded"
    assert result["result"] is True


# ---------------------------------------------------------------------------
# P0-D PRESTATE_AND_DRIFT — a target mutated after prepare causes execute
# to refuse rather than silently overwrite a value the caller never saw.
# ---------------------------------------------------------------------------

def test_p0d_execute_refuses_on_prestate_drift():
    backend = FakeBackend("x_service_catalogue", {1: {"name": "original"}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "renamed"}, store=store,
    )
    # Someone/something else mutates the record between prepare and execute.
    backend.records[1]["name"] = "changed_by_someone_else"

    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
            read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        )
    assert ei.value.invariant == "PRESTATE_DRIFT"
    assert ei.value.actual["drifted"][0]["id"] == 1
    assert backend.records[1]["name"] == "changed_by_someone_else"  # untouched


# ---------------------------------------------------------------------------
# P0-E SEQUENTIAL_SET — a write set is consumed exactly once; any further
# execute attempt (including retrying the exact same write_set_id, or a
# superset/different set) refuses rather than silently extending the old
# approved scope.
# ---------------------------------------------------------------------------

def test_p0e_write_set_cannot_be_executed_twice():
    backend = FakeBackend("x_service_catalogue", {1: {"name": "a"}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "b"}, store=store,
    )
    ws.execute_write_set(
        write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
        read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
    )
    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
            read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        )
    assert ei.value.invariant in ("UNKNOWN_WRITE_SET", "WRITE_SET_ALREADY_CONSUMED")
    assert len(backend.mutations) == 1  # second attempt did not mutate again


def test_p0e_unknown_write_set_id_refuses():
    store = make_store()
    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id="never-prepared", enumerated_ids=[1],
            read_fn=lambda *a: [], mutate_fn=lambda *a: None, store=store,
        )
    assert ei.value.invariant == "UNKNOWN_WRITE_SET"


# ---------------------------------------------------------------------------
# P0-F OBSERVABILITY — a default-visibility change on ir.filters/ir.ui.view/
# ir.ui.menu is classified separately and requires its own confirmation.
# ---------------------------------------------------------------------------

def test_p0f_observability_default_change_classified_and_blocked():
    backend = FakeBackend("ir.filters", {1: {"is_default": False}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"is_default": True}, store=store,
    )
    assert preview["observability"] == {"model": "ir.filters", "fields": ["is_default"], "default_change": True}
    assert preview["requires_observability_default_confirmation"] is True
    assert ws.CONSENT_OBSERVABILITY_MUTATION in preview["consent_classes"]

    with pytest.raises(ws.WriteSafetyRefusal) as ei:
        ws.execute_write_set(
            write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
            read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
        )
    assert ei.value.invariant == "OBSERVABILITY_DEFAULT_CONFIRMATION_REQUIRED"


def test_p0f_observability_non_default_field_change_does_not_require_default_confirmation():
    backend = FakeBackend("ir.filters", {1: {"name": "old"}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"name": "new"}, store=store,
    )
    assert preview["observability"]["default_change"] is False
    assert preview["requires_observability_default_confirmation"] is False
    # executes fine without the extra confirmation
    result = ws.execute_write_set(
        write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
        read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
    )
    assert backend.records[1]["name"] == "new"
    assert result["result"] is True


def test_unrelated_model_is_not_classified_as_observability():
    backend = FakeBackend("x_service_catalogue", {1: {"is_default": False}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="write",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={"is_default": True}, store=store,
    )
    assert preview["observability"] is None
    assert ws.CONSENT_OBSERVABILITY_MUTATION not in preview["consent_classes"]


# ---------------------------------------------------------------------------
# Unlink (destructive) path — resolves/prestates/executes the same way,
# always carries DESTRUCTIVE_MUTATION, and readback is skipped (nothing
# left to read).
# ---------------------------------------------------------------------------

def test_unlink_carries_destructive_consent_class_and_executes():
    backend = FakeBackend("x_service_catalogue", {1: {}, 2: {}})
    store = make_store()
    preview = ws.prepare_write_set(
        model=backend.model, operation="unlink",
        resolve_ids=backend.resolve_all_ids, read_fn=backend.read_fn, count_fn=backend.count_fn,
        proposed={}, store=store,
    )
    assert preview["consent_classes"] == [ws.CONSENT_DESTRUCTIVE_MUTATION]
    result = ws.execute_write_set(
        write_set_id=preview["write_set_id"], enumerated_ids=preview["enumerated_ids"],
        read_fn=backend.read_fn, mutate_fn=backend.mutate_fn, store=store,
    )
    assert result["after"] is None
    assert backend.records == {}


# ---------------------------------------------------------------------------
# Digest — changes if any input to it changes; stable given identical
# inputs (this is a receipt, not itself the enforcement — enforcement is
# the explicit id/prestate comparisons above, verified separately).
# ---------------------------------------------------------------------------

def test_digest_changes_with_proposed_values():
    kwargs = dict(model="m", operation="write", ids=[1], prestate={1: {"f": "a"}},
                  consent_classes=["DATA_MUTATION"], prepared_at=1000.0)
    d1 = ws.compute_digest(proposed={"f": "b"}, **kwargs)
    d2 = ws.compute_digest(proposed={"f": "c"}, **kwargs)
    assert d1 != d2


def test_digest_stable_for_identical_inputs():
    kwargs = dict(model="m", operation="write", ids=[1], prestate={1: {"f": "a"}},
                  proposed={"f": "b"}, consent_classes=["DATA_MUTATION"], prepared_at=1000.0)
    assert ws.compute_digest(**kwargs) == ws.compute_digest(**kwargs)


# ---------------------------------------------------------------------------
# Trace/consent envelope (group B primitive, shared by n8n_mcp.py)
# ---------------------------------------------------------------------------

def test_trace_envelope_emits_success_event_and_returns_fn_result():
    events = []
    result = ws.with_trace_envelope(
        tool="t", consent_classes=["DATA_MUTATION"], target="x:1",
        trace_sink=events.append, fn=lambda: 42,
    )
    assert result == 42
    assert len(events) == 1
    assert events[0]["result"] == "success"
    assert events[0]["refusal_reason"] is None
    assert events[0]["tool"] == "t"
    assert events[0]["consent_classes"] == ["DATA_MUTATION"]


def test_trace_envelope_emits_error_event_and_reraises():
    events = []
    with pytest.raises(RuntimeError):
        ws.with_trace_envelope(
            tool="t", consent_classes=["DATA_MUTATION"], target="x:1",
            trace_sink=events.append, fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
    assert len(events) == 1
    assert events[0]["result"] == "error"
    assert "boom" in events[0]["refusal_reason"]
