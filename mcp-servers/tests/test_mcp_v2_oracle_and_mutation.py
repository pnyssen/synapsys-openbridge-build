"""
Oracle-bearing validation tests for SYNAPSYS MCP UPGRADE — CONSOLIDATED
REQUIREMENTS v2 / ACCEPTANCE CRITERIA v1 (D007 bounded validation tranche,
rev533, job a36c4a92d077151a).

Per Acceptance Criteria v1's own governing rule (R1: "Every test row
carries an EXPECTED OUTCOME. Coverage without an oracle is not evidence."),
every test below asserts an exact expected value from the labelled corpus
(L-01..L-12), not merely that a function ran or returned *a* type. Where a
row cites a live fixture (L-06 ir.filters id 47, L-10 act_window ids
1583/1584/1040, L-01's current register population), the fixture data used
here was independently read live via the read-only Odoo connector this
session, on 2026-08-25, immediately before writing these tests — recorded
per-test below, not merely asserted from the readiness document's word.

No live Odoo/N8N credential or write access is used by any test in this
file — every test mocks odoo_mcp._exec / the safety core's own read_fn/
count_fn/search_fn closures, per this validation tranche's own boundary
("run only the minimum harmless real Odoo/SharePoint/n8n replay needed").
The live calls this producer DID make (read-only, to confirm fixture
identity) are documented in the required return, not repeated as "live
replay" here — they are ordinary read verification, not the bounded
harmless mutating replay the acceptance gate separately requires and which
remains blocked by this lane's standing read-only Odoo/N8N connector gap
(see the required return's blockers section).

SCOPE NOTE: L-03, L-04, L-05 and L-11 exercise SharePoint MCP v2 controls
(WM artefact-instruction guard, target-metadata preview, context
derivation). The SharePoint MCP source lives in the sibling repository
`pnyssen/synapsys-openbridge` (mcp/sharepoint/sharepoint_mcp.py), not in
this repository's mcp-servers/ tree — this file covers only the Odoo/N8N
gap delta implemented in this repo (`_write_safety.py` / `odoo_mcp.py` /
`n8n_mcp.py`). L-03/L-04/L-05/L-11 are reported as an explicit gap in the
required return, not silently skipped without record.
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
def fresh_safety_state(monkeypatch):
    """Each test gets a fresh write-set store and retry tracker — mirrors a
    fresh process, and stops retry-escalation state leaking test-to-test."""
    monkeypatch.setattr(odoo_mcp, "_WRITE_SET_STORE", ws.WriteSetStore())
    monkeypatch.setattr(odoo_mcp, "_RETRY_TRACKER", ws.RetryTracker())


class FakeOdoo:
    """Backs odoo_mcp._exec. Same shape as test_odoo_mcp_write_safety.py's
    fixture, extended with a `next_create_id` counter and act_window search
    support for L-10."""

    def __init__(self, records: dict[int, dict]):
        self.records = {int(k): dict(v) for k, v in records.items()}
        self.calls: list[tuple[str, str, list, dict]] = []
        self.search_results: dict[str, list] = {}  # keyed by "model|domain_json" for act_window reuse

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
        if method == "search_read":
            domain, = args[:1]
            key = f"{model}|{domain!r}"
            return self.search_results.get(key, [])
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
        return {"method": method, "args": args, "kwargs": kwargs}


def _isError(resp):
    return resp["result"].get("isError") is True


def _call(name, arguments, id_=1):
    return odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": id_, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })


# ===========================================================================
# L-01 — blast-radius accuracy: actual scope (53) wins over caller intent (15)
# ===========================================================================
#
# Reproduces the exact historical shape (Benefit register incident: consent
# surfaced 15, actual affected 53) as a disposable non-business fixture, per
# the readiness assessment's own instruction — the live x_ss_benefit_register
# population is now 1 record (independently confirmed via count_odoo this
# session, 2026-08-25), so the 53-record shape cannot and must not be
# replayed against live business data.

def test_L01_blast_radius_actual_count_wins_over_intended(monkeypatch):
    fake = FakeOdoo({i: {"x_benefit_status": "planned"} for i in range(1, 54)})  # 53 records
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    resp = _call("prepare_write_odoo", {
        "model": "x_ss_benefit_register",
        "domain": [["x_benefit_status", "!=", "superseded"]],
        "values": {"x_benefit_status": "superseded"},
        "intended_count": 15,
    })
    assert not _isError(resp)
    import json
    preview = json.loads(resp["result"]["content"][0]["text"])

    # EXPECTED (exact, not type-only): actual count is 53, not 15.
    assert preview["actual_affected_count"] == 53
    assert preview["intended_count"] == 15
    assert len(preview["enumerated_ids"]) == 53
    assert preview["requires_enumerated_ids"] is True
    assert fake.calls == [c for c in fake.calls if c[1] != "write"]  # no mutation occurred


# ===========================================================================
# L-02 — secret-shaped payload refused; field path returned; value never echoed
# ===========================================================================

def test_L02_jwt_shaped_value_refused_field_path_only():
    # Synthetic fixture, not a real credential — deliberately JWT-shaped so
    # ws.scan_for_secrets' JWT pattern actually has something to match.
    dummy_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummySigContent"  # gitleaks:allow
    offending = ws.scan_for_secrets({"x_token": dummy_jwt})
    assert offending == {"field": "x_token", "pattern": "JWT"}
    # value never present anywhere in the returned structure
    assert dummy_jwt not in repr(offending)


def test_L02_env_reference_refused(monkeypatch):
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("create_odoo", {
        "model": "x_service_catalogue",
        "values": {"x_config": "$env.ODOO_JSONRPC_KEY"},
    })
    assert _isError(resp)
    body = resp["result"]["content"][0]["text"]
    assert "SECRET_MATERIAL_REFUSED" in body
    assert "ENV_REFERENCE" in body
    assert "$env.ODOO_JSONRPC_KEY" not in body  # value never echoed
    assert fake.calls == []  # refused before any _exec call


def test_L02_connection_string_with_credentials_refused():
    offending = ws.scan_for_secrets({"x_dsn": "postgres://svc_user:s3cr3t@db.internal:5432/prod"})
    assert offending == {"field": "x_dsn", "pattern": "CONNECTION_STRING_WITH_CREDENTIALS"}


def test_L02_ordinary_field_not_falsely_flagged():
    """R1 companion: the guard must not over-trigger on ordinary CR text."""
    assert ws.scan_for_secrets({"x_reference": "CHG-2026-665", "name": "Programme Delivery"}) is None


# ===========================================================================
# L-06 — already-correct end state returns NO_CHANGE_REQUIRED, no prompt
# ===========================================================================
#
# Fixture: ir.filters id 47, live-read this session (2026-08-25) via
# read_odoo(model="ir.filters", ids=[47], fields=["name","is_default",
# "model_id"]) -> {"id":47,"name":"Probable / Verified Contexts",
# "is_default":false,"model_id":"x_ss_context_master"}. Exactly matches the
# acceptance corpus's stated fixture.

def test_L06_no_change_required_short_circuits_before_any_mutating_call(monkeypatch):
    fake = FakeOdoo({47: {"name": "Probable / Verified Contexts", "is_default": False}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    resp = _call("write_odoo", {
        "model": "ir.filters", "ids": 47,
        "values": {"name": "Probable / Verified Contexts", "is_default": False},
    })
    assert not _isError(resp)
    import json
    result = json.loads(resp["result"]["content"][0]["text"])
    assert result == "NO_CHANGE_REQUIRED"
    # No write call was ever issued.
    assert not any(c[1] == "write" for c in fake.calls)


def test_L06_prepare_alone_reports_no_change_required(monkeypatch):
    fake = FakeOdoo({47: {"name": "Probable / Verified Contexts", "is_default": False}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("prepare_write_odoo", {
        "model": "ir.filters", "ids": 47,
        "values": {"name": "Probable / Verified Contexts", "is_default": False},
    })
    import json
    preview = json.loads(resp["result"]["content"][0]["text"])
    assert preview["no_change_required"] is True


# ===========================================================================
# L-07 — identical refused retry increments and escalates; never re-proposed
# ===========================================================================

def test_L07_identical_retry_escalates_second_time(monkeypatch):
    fake = FakeOdoo({i: {"name": f"r{i}"} for i in range(1, 13)})  # 12 records -> bulk refusal
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    args = {"model": "x_service_catalogue", "ids": list(range(1, 13)), "values": {"name": "renamed"}}

    resp1 = _call("write_odoo", args, id_=1)
    body1 = resp1["result"]["content"][0]["text"]
    assert "TWO_PHASE_CONFIRMATION_REQUIRED" in body1
    assert "_ESCALATED" not in body1
    assert '"retry_count": 1' in body1

    resp2 = _call("write_odoo", args, id_=2)  # identical proposal, re-submitted unchanged
    body2 = resp2["result"]["content"][0]["text"]
    assert "TWO_PHASE_CONFIRMATION_REQUIRED_ESCALATED" in body2
    assert '"retry_count": 2' in body2
    assert "refused 2 times" in body2

    # neither attempt mutated anything
    assert not any(c[1] == "write" for c in fake.calls)


def test_L07_different_proposal_does_not_escalate(monkeypatch):
    fake = FakeOdoo({i: {"name": f"r{i}"} for i in range(1, 13)})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp1 = _call("write_odoo", {
        "model": "x_service_catalogue", "ids": list(range(1, 13)), "values": {"name": "renamed_a"},
    }, id_=1)
    resp2 = _call("write_odoo", {
        "model": "x_service_catalogue", "ids": list(range(1, 13)), "values": {"name": "renamed_b"},
    }, id_=2)
    assert "_ESCALATED" not in resp1["result"]["content"][0]["text"]
    assert "_ESCALATED" not in resp2["result"]["content"][0]["text"]


# ===========================================================================
# L-08 — n8n workflow id and WM filename classify IDENTIFIER, not SECRET;
# same-shaped opaque value with no declared context stays UNKNOWN (never
# globally whitelisted); JWT/$env remain refused regardless of context.
# ===========================================================================
#
# Fixture: n8n workflow id NMkMpCy608AfkkBE (SynapSys Universal Gate Event
# Wake Receiver, confirmed active earlier this session). WM filename grammar
# per this repo's own naming convention (CLAUDE.md).

def test_L08_n8n_workflow_id_classified_identifier_in_workflow_id_context():
    assert ws.classify_identifier("NMkMpCy608AfkkBE", ws.IDENTIFIER_CONTEXT_WORKFLOW_ID) == ws.CLASS_IDENTIFIER


def test_L08_wm_filename_classified_identifier_in_wm_path_context():
    filename = "20260825--chatgpt-hub--state-control--navigator-state-control--v19-151"
    assert ws.classify_identifier(filename, ws.IDENTIFIER_CONTEXT_WM_PATH) == ws.CLASS_IDENTIFIER


def test_L08_same_shaped_value_without_declared_context_is_unknown_not_whitelisted():
    """The exact v2 correction: a bare 16-character string is never globally
    whitelisted as safe just because its shape matches a known grammar."""
    assert ws.classify_identifier("NMkMpCy608AfkkBE", None) == ws.CLASS_UNKNOWN
    assert ws.classify_identifier("NMkMpCy608AfkkBE", "credential_field") == ws.CLASS_UNKNOWN


def test_L08_jwt_overrides_identifier_grammar_even_in_workflow_id_context():
    # A JWT does not happen to be 16 chars, but this proves the precedence
    # rule: secret signatures always win over any declared context.
    dummy_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJYIn0.sig"  # gitleaks:allow — synthetic, not a real credential
    assert ws.classify_identifier(dummy_jwt, ws.IDENTIFIER_CONTEXT_WORKFLOW_ID) == ws.CLASS_SECRET


# ===========================================================================
# L-09 — ir.filters/ir.ui.view/ir.ui.menu (and, per requirements A8,
# ir.actions.act_window) mutation classified OBSERVABILITY; default-state
# change requires a distinct confirmation.
# ===========================================================================

def test_L09_ir_filters_default_change_classified_observability_and_blocked(monkeypatch):
    # Same live-verified id47 fixture as L-06, but proposing an actual
    # default-state change this time.
    fake = FakeOdoo({47: {"name": "Probable / Verified Contexts", "is_default": False}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("prepare_write_odoo", {
        "model": "ir.filters", "ids": 47, "values": {"is_default": True},
    })
    import json
    preview = json.loads(resp["result"]["content"][0]["text"])
    assert preview["observability"] == {
        "model": "ir.filters", "fields": ["is_default"], "default_change": True,
    }
    assert preview["requires_observability_default_confirmation"] is True

    resp2 = _call("write_odoo", {"model": "ir.filters", "ids": 47, "values": {"is_default": True}})
    assert _isError(resp2)
    assert "TWO_PHASE_CONFIRMATION_REQUIRED" in resp2["result"]["content"][0]["text"]


def test_L09_extension_ir_actions_act_window_write_classified_observability(monkeypatch):
    """Requirements v2 §A8 explicitly extends the observability class to
    ir.actions.act_window ('and equivalent action/projection objects'),
    which the readiness assessment flagged as a gap in PR39. Labelled
    extension of the L-09 corpus row, not itself one of the twelve rows."""
    fake = FakeOdoo({1583: {"view_mode": "list,form", "name": "Old"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("prepare_write_odoo", {
        "model": "ir.actions.act_window", "ids": 1583, "values": {"view_mode": "list,form,kanban"},
    })
    import json
    preview = json.loads(resp["result"]["content"][0]["text"])
    assert preview["observability"]["model"] == "ir.actions.act_window"
    assert "view_mode" in preview["observability"]["fields"]


# ===========================================================================
# L-10 — duplicate ir.actions.act_window capability check surfaces the
# actually-existing ids and refuses parallel capability creation.
# ===========================================================================
#
# Fixture: ids 1583 (PLAN · Portfolio Delivery), 1584 (PLAN · Programme),
# 1040 (Context Tasks) — all live-read this session on project.task with
# view_mode == "gantt,list,kanban,form,calendar,pivot,graph,activity"
# exactly. This is the same shape the acceptance corpus names, and matches
# the exact bug the corpus calls out: "the lane ran this reuse test,
# reported 'no equivalent exists', and was wrong" — this test proves the
# wrapper runs the check itself rather than trusting the caller.

_L10_VIEW_MODE = "gantt,list,kanban,form,calendar,pivot,graph,activity"


def test_L10_duplicate_action_window_refused_with_exact_existing_ids(monkeypatch):
    fake = FakeOdoo({})
    fake.search_results[
        f"ir.actions.act_window|{[['res_model', '=', 'project.task'], ['view_mode', '=', _L10_VIEW_MODE]]!r}"
    ] = [
        {"id": 1583, "name": "PLAN · Portfolio Delivery"},
        {"id": 1584, "name": "PLAN · Programme"},
        {"id": 1040, "name": "Context Tasks"},
    ]
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    resp = _call("create_odoo", {
        "model": "ir.actions.act_window",
        "values": {"name": "New Duplicate Plan View", "res_model": "project.task", "view_mode": _L10_VIEW_MODE},
        "consent_ack": ["CONFIGURATION_RUNTIME_MUTATION"],
    })
    assert _isError(resp)
    body = resp["result"]["content"][0]["text"]
    assert "REUSABLE_CAPABILITY_EXISTS" in body
    assert "1583" in body and "1584" in body and "1040" in body
    assert not any(c[1] == "create" for c in fake.calls)


def test_L10_novel_view_mode_not_blocked_by_reuse_check(monkeypatch):
    fake = FakeOdoo({})  # no search_results configured -> reuse check returns []
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("create_odoo", {
        "model": "ir.actions.act_window",
        "values": {"name": "Genuinely New View", "res_model": "x_service_catalogue", "view_mode": "list,form"},
        "consent_ack": ["CONFIGURATION_RUNTIME_MUTATION"],
    })
    assert not _isError(resp)
    assert any(c[1] == "create" for c in fake.calls)


# ===========================================================================
# L-12 — bulk field write returns per-record prestate automatically, before
# any mutating call.
# ===========================================================================

def test_L12_bulk_write_prestate_captured_per_record_before_execute(monkeypatch):
    fake = FakeOdoo({1: {"name": "a"}, 2: {"name": "b"}, 3: {"name": "c"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
    resp = _call("prepare_write_odoo", {
        "model": "x_service_catalogue", "ids": [1, 2, 3], "values": {"name": "renamed"},
    })
    import json
    preview = json.loads(resp["result"]["content"][0]["text"])
    assert preview["prestate"] == {"1": {"name": "a"}, "2": {"name": "b"}, "3": {"name": "c"}}
    # prestate was captured via read, not write — no mutation occurred yet
    assert not any(c[1] == "write" for c in fake.calls)


# ===========================================================================
# M1-M5 semantic mutation gate. Each mutant reproduces the exact defect
# named in Acceptance Criteria v1; the corresponding oracle test above must
# distinguish correct behaviour from the mutant's (i.e. the oracle "kills"
# the mutant by asserting the value the mutant would get wrong).
# ===========================================================================

def test_M1_reuse_check_always_clear_mutant_is_killed_by_L10(monkeypatch):
    """Mutant: check_action_window_reuse always returns [] regardless of
    input (the exact 2026-08-25 defect: 'ran the check, reported clear, was
    wrong'). L-10's oracle expects a refusal naming the existing ids —
    under the mutant it would instead succeed, so the oracle kills it."""
    fake = FakeOdoo({})
    fake.search_results[
        f"ir.actions.act_window|{[['res_model', '=', 'project.task'], ['view_mode', '=', _L10_VIEW_MODE]]!r}"
    ] = [{"id": 1583, "name": "PLAN · Portfolio Delivery"}]
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    # Correct implementation: refuses (this IS the L-10 oracle).
    correct_resp = _call("create_odoo", {
        "model": "ir.actions.act_window",
        "values": {"name": "Dup", "res_model": "project.task", "view_mode": _L10_VIEW_MODE},
        "consent_ack": ["CONFIGURATION_RUNTIME_MUTATION"],
    }, id_=1)
    assert _isError(correct_resp)

    # Mutant: reuse-check always reports clear.
    monkeypatch.setattr(ws, "check_action_window_reuse", lambda **kwargs: [])
    mutant_resp = _call("create_odoo", {
        "model": "ir.actions.act_window",
        "values": {"name": "Dup", "res_model": "project.task", "view_mode": _L10_VIEW_MODE},
        "consent_ack": ["CONFIGURATION_RUNTIME_MUTATION"],
    }, id_=2)
    assert not _isError(mutant_resp)  # mutant wrongly allows the duplicate — oracle would have caught this


def test_M2_bulk_ceiling_10000_mutant_is_killed_by_bulk_oracle(monkeypatch):
    """Mutant: BULK_ID_CEILING raised to 10000, defeating the >10 blast-
    radius check entirely."""
    fake = FakeOdoo({i: {"name": f"r{i}"} for i in range(1, 54)})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    original_ceiling = ws.BULK_ID_CEILING
    try:
        # Correct: 53 records over a small register requires two-phase.
        resp_correct = _call("prepare_write_odoo", {
            "model": "x_ss_benefit_register",
            "domain": [["x_benefit_status", "!=", "superseded"]],
            "values": {"x_benefit_status": "superseded"},
        }, id_=1)
        import json
        assert json.loads(resp_correct["result"]["content"][0]["text"])["requires_enumerated_ids"] is True

        # Mutant: ceiling raised so far the same 53-record write is no
        # longer flagged as bulk by id-count (percentage still applies here
        # since register_total==53, so also monkeypatch percentage ceiling).
        ws.BULK_ID_CEILING = 10000
        monkeypatch.setattr(ws, "BULK_PERCENTAGE_CEILING", 100.0)
        odoo_mcp._WRITE_SET_STORE = ws.WriteSetStore()
        resp_mutant = _call("prepare_write_odoo", {
            "model": "x_ss_benefit_register",
            "domain": [["x_benefit_status", "!=", "superseded"]],
            "values": {"x_benefit_status": "superseded"},
        }, id_=2)
        preview_mutant = json.loads(resp_mutant["result"]["content"][0]["text"])
        assert preview_mutant["requires_enumerated_ids"] is False  # mutant wrongly allows bulk auto-execute
    finally:
        ws.BULK_ID_CEILING = original_ceiling


def test_M3_secret_scan_disclosure_branch_dropped_mutant_is_killed_by_L02(monkeypatch):
    """Mutant: the secret-refusal branch is dropped entirely (scan_for_secrets
    is a no-op)."""
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    # Correct: refused.
    correct_resp = _call("create_odoo", {
        "model": "x_service_catalogue", "values": {"x_config": "$env.ODOO_JSONRPC_KEY"},
    }, id_=1)
    assert _isError(correct_resp)

    # Mutant: disclosure/refusal branch dropped.
    monkeypatch.setattr(ws, "scan_for_secrets", lambda payload, path_prefix="": None)
    mutant_resp = _call("create_odoo", {
        "model": "x_service_catalogue", "values": {"x_config": "$env.ODOO_JSONRPC_KEY"},
    }, id_=2)
    assert not _isError(mutant_resp)  # mutant wrongly persists the secret reference


def test_M4_accept_any_consent_class_mutant_is_killed(monkeypatch):
    """Mutant: the consent_ack gate accepts ANY non-empty list, not
    specifically CONFIGURATION_RUNTIME_MUTATION."""
    fake = FakeOdoo({})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    # Correct: wrong consent class string still refuses.
    correct_resp = _call("create_odoo", {
        "model": "ir.cron", "values": {"name": "x"}, "consent_ack": ["SOME_OTHER_CLASS"],
    }, id_=1)
    assert _isError(correct_resp)

    # Mutant: gate weakened to "any non-empty ack".
    import odoo_mcp as _om
    original = _om.tool_create_odoo

    def mutant_create_odoo(args):
        model = args["model"]
        if _om._is_runtime_config_model(model) and not (args.get("consent_ack") or []):
            raise ws.WriteSafetyRefusal("CONFIGURATION_RUNTIME_MUTATION_CONFIRMATION_REQUIRED", "mutant gate")
        return _om._exec(model, "create", [args["values"]])

    monkeypatch.setattr(_om, "tool_create_odoo", mutant_create_odoo)
    _om.TOOL_HANDLERS["create_odoo"] = mutant_create_odoo
    try:
        mutant_resp = _call("create_odoo", {
            "model": "ir.cron", "values": {"name": "x"}, "consent_ack": ["SOME_OTHER_CLASS"],
        }, id_=2)
        assert not _isError(mutant_resp)  # mutant wrongly accepts an unrelated consent class
    finally:
        _om.TOOL_HANDLERS["create_odoo"] = original


def test_M5_skip_prestate_capture_mutant_is_killed_by_L12(monkeypatch):
    """Mutant: prepare_write_set never calls read_fn, leaving prestate empty."""
    fake = FakeOdoo({1: {"name": "a"}, 2: {"name": "b"}})
    monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)

    # Correct: prestate captured exactly.
    resp_correct = _call("prepare_write_odoo", {
        "model": "x_service_catalogue", "ids": [1, 2], "values": {"name": "renamed"},
    }, id_=1)
    import json
    assert json.loads(resp_correct["result"]["content"][0]["text"])["prestate"] == {
        "1": {"name": "a"}, "2": {"name": "b"},
    }

    # Mutant: prestate capture skipped. TOOL_HANDLERS holds a direct
    # reference to the function object, not a by-name lookup, so the
    # dispatch table entry itself must be replaced (same pattern as M4).
    def mutant_prepare_write_odoo(args):
        return ws.prepare_write_set(
            model=args["model"], operation="write",
            resolve_ids=lambda: odoo_mcp._resolve_ids_for_prepare(args),
            read_fn=lambda model, ids, fields: [],  # prestate read skipped
            count_fn=odoo_mcp._ws_count_fn,
            proposed=args["values"], intended_count=args.get("intended_count"),
            store=odoo_mcp._WRITE_SET_STORE,
        )

    original_handler = odoo_mcp.TOOL_HANDLERS["prepare_write_odoo"]
    odoo_mcp.TOOL_HANDLERS["prepare_write_odoo"] = mutant_prepare_write_odoo
    try:
        resp_mutant = _call("prepare_write_odoo", {
            "model": "x_service_catalogue", "ids": [1, 2], "values": {"name": "renamed"},
        }, id_=2)
    finally:
        odoo_mcp.TOOL_HANDLERS["prepare_write_odoo"] = original_handler
    preview_mutant = json.loads(resp_mutant["result"]["content"][0]["text"])
    assert preview_mutant["prestate"] == {}  # mutant wrongly loses prestate — oracle would catch this


# ===========================================================================
# Strictly-safer mutant MUST SURVIVE — per Acceptance Criteria v1: "any
# mutant that makes the wrapper STRICTER must SURVIVE — a suite that
# rejects a safer implementation is measuring the wrong thing."
# ===========================================================================

def test_stricter_mutant_lower_bulk_ceiling_survives_all_L_oracles(monkeypatch):
    """A stricter bulk ceiling (5 instead of 10) makes the wrapper MORE
    cautious, never less safe. None of the L-01..L-12 oracle tests above
    depend on the exact value 10 (L-01/L-07 use bulk sets far past either
    ceiling; L-06/L-09/L-10/L-12 use single-digit non-bulk sets well under
    5 too) — so this mutant must not break any of them, proving the suite
    isn't just testing for one specific implementation constant."""
    original_ceiling = ws.BULK_ID_CEILING
    try:
        ws.BULK_ID_CEILING = 5  # stricter

        fake = FakeOdoo({47: {"name": "Probable / Verified Contexts", "is_default": False}})
        monkeypatch.setattr(odoo_mcp, "_exec", fake.exec)
        odoo_mcp._WRITE_SET_STORE = ws.WriteSetStore()
        # L-06 still holds under the stricter mutant.
        resp = _call("write_odoo", {
            "model": "ir.filters", "ids": 47,
            "values": {"name": "Probable / Verified Contexts", "is_default": False},
        })
        import json
        assert json.loads(resp["result"]["content"][0]["text"]) == "NO_CHANGE_REQUIRED"
    finally:
        ws.BULK_ID_CEILING = original_ceiling
