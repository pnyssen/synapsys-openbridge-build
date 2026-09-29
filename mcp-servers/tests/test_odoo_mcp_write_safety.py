"""
Tests for odoo_mcp.py's group-A wiring: wrapped create/write/unlink tools,
the explicit prepare_/execute_ two-phase tools, and the constrained
execute_odoo passthrough. No live Odoo credentials/network — every test
mocks odoo_mcp._exec, the single function that actually talks to Odoo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

MCP_SERVERS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_SERVERS_DIR))

import odoo_mcp  # noqa: E402
import _write_safety as ws  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_write_set_store(monkeypatch):
    """Each test gets its own write-set store so prepare/execute across
    tests never interfere (mirrors a fresh process for each canary)."""
    monkeypatch.setattr(odoo_mcp, "_WRITE_SET_STORE", ws.WriteSetStore())


class FakeOdoo:
    """Backs odoo_mcp._exec for read/search_count/write/unlink/create,
    driven by a plain dict-of-records store."""

    def __init__(self, records: dict[int, dict]):
        self.records = {int(k): dict(v) for k, v in records.items()}
        self.calls: list[tuple[str, str, list, dict]] = []

    def exec(self, model, method, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        self.calls.append((model, method, args, kwargs))
        if method == "read":
            ids, = args[:1]
            fields = kwargs.get("fields", [])
            rows = []
            for i in ids:
                rec = self.records.get(i, {})
                row = {f: rec.get(f) for f in fields if f != "id"}
                row["id"] = i
                rows.append(row)
            return rows
        if method == "search_count":
            return len(self.records)
        if method == "search":
            return list(self.records.keys())
        if method == "write":
            ids, values = args
            for i in ids:
                self.records.setdefault(i, {}).update(values)
            return True
        if method == "unlink":
            ids, = args
            for i in ids:
                self.records.pop(i, None)
            return True
        if method == "create":
            new_id = max(self.records.keys(), default=0) + 1
            self.records[new_id] = dict(args[0])
            return new_id
        # Generic passthrough for any other execute_odoo-style method under
        # test (e.g. a runtime-config action) — real Odoo would run the
        # actual server action; the test only needs to observe that _exec
        # was reached with the right args once consent is granted.
        return {"method": method, "args": args, "kwargs": kwargs}


def _isError(resp):
    return resp["result"].get("isError") is True


# ---------------------------------------------------------------------------
# write_odoo — small/safe write executes in one call; bulk/protected refuses
# with TWO_PHASE_CONFIRMATION_REQUIRED via the JSON-RPC dispatch layer.
# ---------------------------------------------------------------------------

def test_write_odoo_small_safe_write_executes_in_one_call(monkeypatch):
    # A large-enough register (20 records) so touching 1 record (5%) stays
    # under the 20% affected-percentage ceiling — the everyday "small,
    # unprotected write" case this convenience path is meant to serve.
    fake = FakeOdoo({i: {"name": f"r{i}"} for i in range(1, 21)})
    fake.records[1]["name"] = "old"
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "write_odoo", "arguments": {"model": "x_service_catalogue", "ids": 1, "values": {"name": "new"}}},
    })
    assert not _isError(resp)
    assert fake.records[1]["name"] == "new"


def test_write_odoo_bulk_refuses_and_does_not_mutate(monkeypatch):
    fake = FakeOdoo({i: {"name": f"r{i}"} for i in range(1, 13)})  # 12 records
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "write_odoo", "arguments": {
            "model": "x_service_catalogue", "ids": list(range(1, 13)), "values": {"name": "renamed"},
        }},
    })
    assert _isError(resp)
    body = resp["result"]["content"][0]["text"]
    assert "TWO_PHASE_CONFIRMATION_REQUIRED" in body
    assert all(v["name"] == f"r{i}" for i, v in fake.records.items())  # untouched


def test_write_odoo_protected_benefit_state_refuses(monkeypatch):
    fake = FakeOdoo({1: {"x_benefit_status": "verified"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "write_odoo", "arguments": {
            "model": "x_ss_benefit_register", "ids": 1, "values": {"x_benefit_status": "superseded"},
        }},
    })
    assert _isError(resp)
    assert "TWO_PHASE_CONFIRMATION_REQUIRED" in resp["result"]["content"][0]["text"]
    assert fake.records[1]["x_benefit_status"] == "verified"  # untouched


# ---------------------------------------------------------------------------
# prepare_write_odoo / execute_write_odoo — explicit two-phase path, with
# the protected-state confirmation flag actually unblocking execution.
# ---------------------------------------------------------------------------

def test_two_phase_path_executes_protected_write_when_confirmed(monkeypatch):
    fake = FakeOdoo({1: {"x_benefit_status": "measured"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    prep = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "prepare_write_odoo", "arguments": {
            "model": "x_ss_benefit_register", "ids": [1], "values": {"x_benefit_status": "superseded"},
        }},
    })
    assert not _isError(prep)
    import json
    preview = json.loads(prep["result"]["content"][0]["text"])
    assert preview["requires_protected_state_confirmation"] is True

    exe = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "execute_write_odoo", "arguments": {
            "write_set_id": preview["write_set_id"], "enumerated_ids": preview["enumerated_ids"],
            "protected_state_confirmed": True,
        }},
    })
    assert not _isError(exe)
    assert fake.records[1]["x_benefit_status"] == "superseded"


# ---------------------------------------------------------------------------
# unlink_odoo — same wrap pattern; bulk refuses.
# ---------------------------------------------------------------------------

def test_unlink_odoo_bulk_refuses(monkeypatch):
    fake = FakeOdoo({i: {} for i in range(1, 13)})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "unlink_odoo", "arguments": {"model": "x_service_catalogue", "ids": list(range(1, 13))}},
    })
    assert _isError(resp)
    assert len(fake.records) == 12  # untouched


def test_unlink_odoo_small_executes(monkeypatch):
    # 20-record register; unlinking 2 (10%) stays under both the id-count
    # (<=10) and percentage (<=20%) ceilings — the everyday small-unlink case.
    fake = FakeOdoo({i: {} for i in range(1, 21)})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "unlink_odoo", "arguments": {"model": "x_service_catalogue", "ids": [1, 2]}},
    })
    assert not _isError(resp)
    assert 1 not in fake.records and 2 not in fake.records
    assert len(fake.records) == 18


# ---------------------------------------------------------------------------
# execute_odoo — write/create/unlink always refused; other non-read methods
# require consent_ack; read-safe methods pass straight through unchanged.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method", ["write", "create", "unlink"])
def test_execute_odoo_refuses_raw_mutation_methods(monkeypatch, method):
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "execute_odoo", "arguments": {"model": "x_service_catalogue", "method": method, "args": []}},
    })
    assert _isError(resp)
    assert "RAW_MUTATION_METHOD_REFUSED" in resp["result"]["content"][0]["text"]
    assert fake.calls == []  # _exec never invoked


def test_execute_odoo_non_read_safe_method_requires_consent_ack(monkeypatch):
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "execute_odoo", "arguments": {
            "model": "base.automation", "method": "action_run", "args": [],
        }},
    })
    assert _isError(resp)
    assert "CONFIGURATION_RUNTIME_MUTATION_CONFIRMATION_REQUIRED" in resp["result"]["content"][0]["text"]
    assert fake.calls == []

    resp2 = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "execute_odoo", "arguments": {
            "model": "base.automation", "method": "action_run", "args": [],
            "consent_ack": ["CONFIGURATION_RUNTIME_MUTATION"],
        }},
    })
    assert not _isError(resp2)
    assert fake.calls == [("base.automation", "action_run", [], {})]


def test_execute_odoo_read_safe_method_passes_through_unchanged(monkeypatch):
    fake = FakeOdoo({1: {"name": "x"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "execute_odoo", "arguments": {
            "model": "x_service_catalogue", "method": "search_count", "args": [[]],
        }},
    })
    assert not _isError(resp)
    assert fake.calls == [("x_service_catalogue", "search_count", [[]], {})]


# ---------------------------------------------------------------------------
# create_odoo — runtime/config models require consent_ack; ordinary models
# unaffected (regression check against the pre-existing single-record path).
# ---------------------------------------------------------------------------

def test_create_odoo_runtime_config_model_requires_consent_ack(monkeypatch):
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "create_odoo", "arguments": {"model": "ir.cron", "values": {"name": "x"}}},
    })
    assert _isError(resp)
    assert "CONFIGURATION_RUNTIME_MUTATION_CONFIRMATION_REQUIRED" in resp["result"]["content"][0]["text"]


def test_create_odoo_ordinary_model_unaffected(monkeypatch):
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "create_odoo", "arguments": {"model": "x_service_catalogue", "values": {"name": "x"}}},
    })
    assert not _isError(resp)


# ---------------------------------------------------------------------------
# tools/list includes the four new tools alongside the original ten.
# ---------------------------------------------------------------------------

def test_tools_list_includes_new_write_safety_tools():
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in resp["result"]["tools"]}
    for expected in ("prepare_write_odoo", "execute_write_odoo", "prepare_unlink_odoo", "execute_unlink_odoo"):
        assert expected in names
    assert names == set(odoo_mcp.TOOL_HANDLERS.keys())
