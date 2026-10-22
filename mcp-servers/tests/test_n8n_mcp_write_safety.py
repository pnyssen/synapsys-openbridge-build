"""
Tests for n8n_mcp.py's group-B wiring: the trace/consent envelope around
mutating tools, and — critically — that update_workflow's existing
snapshot/validate/rollback behaviour (CHG-2026-271) and PR35's
get_execution_summary are unchanged by that wrapping (no regression).

No live N8N credentials/network — every test mocks n8n_mcp._request, the
one function that actually talks to N8N (same pattern as test_transport.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

MCP_SERVERS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_SERVERS_DIR))


@pytest.fixture
def n8n_module(monkeypatch):
    monkeypatch.setenv("N8N_URL", "https://example.invalid")
    monkeypatch.setenv("N8N_API_TOKEN", "dummy-for-import-only")
    sys.modules.pop("n8n_mcp", None)
    import n8n_mcp
    return n8n_mcp


def _workflow(name="wf", nodes=None, connections=None, **extra):
    return {
        "id": "1", "name": name,
        "nodes": nodes if nodes is not None else [{"name": "Start", "parameters": {}}],
        "connections": connections if connections is not None else {},
        "settings": {},
        **extra,
    }


# ---------------------------------------------------------------------------
# update_workflow — trace envelope wraps it without changing its existing
# snapshot/validate/rollback control flow.
# ---------------------------------------------------------------------------

def test_update_workflow_success_path_unchanged_and_traced(n8n_module, monkeypatch):
    wf = _workflow()
    calls = []

    def fake_request(method, path, body=None, timeout=30):
        calls.append((method, path))
        if method == "GET":
            return wf
        if method == "PUT":
            return {"id": "1", "name": wf["name"]}
        raise AssertionError(method)

    monkeypatch.setattr(n8n_module, "_request", fake_request)
    traced = []
    monkeypatch.setattr(n8n_module, "_trace_sink", traced.append)

    result = n8n_module.update_workflow("1", _workflow())
    assert result["id"] == "1"
    assert calls[0] == ("GET", "/api/v1/workflows/1")  # snapshot
    assert calls[1][0] == "PUT"  # the write itself

    assert len(traced) == 1
    assert traced[0]["tool"] == "update_workflow"
    assert traced[0]["result"] == "success"
    assert traced[0]["consent_classes"] == ["CONFIGURATION_RUNTIME_MUTATION"]


def test_update_workflow_partial_payload_still_rejected_before_any_request(n8n_module, monkeypatch):
    """CHG-2026-271 contract: rejects partial payloads. Must still reject
    with no _request call at all, exactly as before this release's wrapping."""
    calls = []
    monkeypatch.setattr(n8n_module, "_request", lambda *a, **k: calls.append(a) or {})
    with pytest.raises(ValueError, match="Full payload required"):
        n8n_module.update_workflow("1", {"name": "x"})  # missing nodes/connections
    assert calls == []


def test_update_workflow_integrity_failure_still_rolls_back_and_raises(n8n_module, monkeypatch):
    """Post-write node-loss integrity check + rollback (the original Issue-4
    defect this file fixes) must still fire exactly as before."""
    snapshot = _workflow(nodes=[{"name": "A", "parameters": {}}, {"name": "B", "parameters": {}}])
    corrupted_post = _workflow(nodes=[{"name": "A", "parameters": {}}])  # B silently lost

    calls = []

    def fake_request(method, path, body=None, timeout=30):
        calls.append(method)
        if method == "GET":
            # First GET = snapshot, second GET = post-write validation
            return snapshot if calls.count("GET") == 1 else corrupted_post
        if method == "PUT":
            return {}
        raise AssertionError(method)

    monkeypatch.setattr(n8n_module, "_request", fake_request)
    traced = []
    monkeypatch.setattr(n8n_module, "_trace_sink", traced.append)

    with pytest.raises(n8n_module.MutationError, match="Post-write integrity failure"):
        n8n_module.update_workflow("1", _workflow(nodes=[{"name": "A", "parameters": {}}, {"name": "B", "parameters": {}}]))

    # GET snapshot, PUT write, GET validate, PUT rollback
    assert calls == ["GET", "PUT", "GET", "PUT"]
    # the envelope still traces this as an error, carrying the failure reason
    assert traced[0]["result"] == "error"
    assert "integrity" in traced[0]["refusal_reason"].lower()


# ---------------------------------------------------------------------------
# activate_workflow / deactivate_workflow / trigger_webhook — traced,
# behaviour otherwise unchanged.
# ---------------------------------------------------------------------------

def test_activate_workflow_traced_and_unchanged(n8n_module, monkeypatch):
    monkeypatch.setattr(n8n_module, "_request", lambda method, path, body=None, timeout=30: {"active": True})
    traced = []
    monkeypatch.setattr(n8n_module, "_trace_sink", traced.append)
    result = n8n_module.activate_workflow("42")
    assert result == {"active": True}
    assert traced[0]["tool"] == "activate_workflow"
    assert traced[0]["target"] == "workflow:42"


def test_trigger_webhook_traced_and_strips_leading_slash(n8n_module, monkeypatch):
    seen = {}

    def fake_request(method, path, body=None, timeout=30):
        seen["path"] = path
        return {"ok": True}

    monkeypatch.setattr(n8n_module, "_request", fake_request)
    traced = []
    monkeypatch.setattr(n8n_module, "_trace_sink", traced.append)
    result = n8n_module.trigger_webhook("/my/path", {"a": 1})
    assert result == {"ok": True}
    assert seen["path"] == "/webhook/my/path"
    assert traced[0]["consent_classes"] == ["DATA_MUTATION"]


# ---------------------------------------------------------------------------
# PR35 regression — get_execution_summary does not go through the trace
# envelope (it's a read, not a mutation) and its exact summarisation
# behaviour is untouched.
# ---------------------------------------------------------------------------

def test_pr35_get_execution_summary_unchanged(n8n_module, monkeypatch):
    raw = {
        "id": "999", "status": "success", "finished": True, "workflowId": "1",
        "startedAt": "2026-08-25T00:00:00Z", "stoppedAt": "2026-08-25T00:00:05Z",
        "data": {
            "resultData": {
                "lastNodeExecuted": "End",
                "runData": {
                    "Start": [{"executionStatus": "success", "executionTime": 12, "startTime": 1}],
                    "End": [{"executionStatus": "success", "executionTime": 5, "startTime": 2}],
                },
                "error": None,
            }
        },
    }
    traced = []
    monkeypatch.setattr(n8n_module, "_trace_sink", traced.append)
    monkeypatch.setattr(n8n_module, "_request", lambda method, path, **kwargs: raw)

    summary = n8n_module.get_execution_summary("999")
    assert summary["id"] == "999"
    assert summary["nodeCount"] == 2
    assert [n["node"] for n in summary["nodes"]] == ["Start", "End"]
    assert summary["error"] is None
    # read-only tool: no mutation trace emitted by this release's changes
    assert traced == []


def test_pr35_get_execution_summary_error_extraction_unchanged(n8n_module, monkeypatch):
    raw = {
        "id": "1000", "status": "error", "finished": False, "workflowId": "1",
        "startedAt": None, "stoppedAt": None,
        "data": {
            "resultData": {
                "lastNodeExecuted": "Bad Node",
                "runData": {},
                "error": {
                    "node": {"name": "Bad Node", "type": "n8n-nodes-base.odoo"},
                    "errorResponse": {"name": "OdooFault"},
                    "message": "boom",
                },
            }
        },
    }
    monkeypatch.setattr(n8n_module, "_request", lambda method, path, **kwargs: raw)
    summary = n8n_module.get_execution_summary("1000")
    # The original four fields keep their exact values; later releases may
    # only add fields (name/description/httpCode), never change these.
    original = {k: summary["error"][k] for k in ("node", "nodeType", "errorName", "message")}
    assert original == {
        "node": "Bad Node", "nodeType": "n8n-nodes-base.odoo",
        "errorName": "OdooFault", "message": "boom",
    }

# ---------------------------------------------------------------------------
# CHG-2027-088 — trigger_webhook server-held auth profiles.
# (Kept in this CI-listed file so mcp-tests.yml runs them without a workflow edit.)
# ---------------------------------------------------------------------------
SECRET = "s3cr3t-header-value-should-never-leak"


@pytest.fixture
def n8n_auth_module(monkeypatch):
    monkeypatch.setenv("N8N_URL", "https://example.invalid")
    monkeypatch.setenv("N8N_API_TOKEN", "dummy-for-import-only")
    monkeypatch.setenv("N8N_WEBHOOK_AUTH_PROFILES", "w15_dispatch")
    monkeypatch.setenv("N8N_WEBHOOK_AUTH_W15_DISPATCH_HEADER", "X-Test-Auth")
    monkeypatch.setenv("N8N_WEBHOOK_AUTH_W15_DISPATCH_VALUE", SECRET)
    monkeypatch.setenv("N8N_WEBHOOK_AUTH_W15_DISPATCH_PATHS", "dispatch-submit, dispatch-route,/dispatch-complete")
    sys.modules.pop("n8n_mcp", None)
    import n8n_mcp
    return n8n_mcp


def _capture(n8n_auth_module, monkeypatch):
    seen = {}

    def fake_request(method, path, body=None, timeout=30, extra_headers=None):
        seen.update(method=method, path=path, body=body, extra_headers=extra_headers)
        return {"status": "validated"}

    monkeypatch.setattr(n8n_auth_module, "_request", fake_request)
    traced = []
    monkeypatch.setattr(n8n_auth_module, "_trace_sink", traced.append)
    return seen, traced


def test_no_profile_is_unchanged(n8n_auth_module, monkeypatch):
    seen, traced = _capture(n8n_auth_module, monkeypatch)
    assert n8n_auth_module.trigger_webhook("dispatch-submit", {"a": 1}) == {"status": "validated"}
    assert seen["path"] == "/webhook/dispatch-submit"
    assert seen["extra_headers"] is None
    assert traced[0]["target"] == "webhook:dispatch-submit"


def test_profile_injects_header_for_allowlisted_path(n8n_auth_module, monkeypatch):
    seen, traced = _capture(n8n_auth_module, monkeypatch)
    result = n8n_auth_module.trigger_webhook("/dispatch-complete", {"a": 1}, auth_profile="W15_Dispatch")
    assert result == {"status": "validated"}
    assert seen["path"] == "/webhook/dispatch-complete"
    assert seen["extra_headers"] == {"X-Test-Auth": SECRET}
    assert traced[0]["target"] == "webhook:dispatch-complete|auth_profile:w15_dispatch"


def test_profile_refuses_unlisted_path_without_http_call(n8n_auth_module, monkeypatch):
    seen, _ = _capture(n8n_auth_module, monkeypatch)
    with pytest.raises(n8n_auth_module.WebhookAuthError, match="AUTH_PATH_NOT_ALLOWED"):
        n8n_auth_module.trigger_webhook("some-other-hook", {}, auth_profile="w15_dispatch")
    assert seen == {}


def test_unknown_profile_refused(n8n_auth_module, monkeypatch):
    seen, _ = _capture(n8n_auth_module, monkeypatch)
    with pytest.raises(n8n_auth_module.WebhookAuthError, match="AUTH_PROFILE_UNKNOWN"):
        n8n_auth_module.trigger_webhook("dispatch-submit", {}, auth_profile="nope")
    assert seen == {}


def test_incomplete_profile_refused(n8n_auth_module, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_AUTH_W15_DISPATCH_VALUE", "")
    seen, _ = _capture(n8n_auth_module, monkeypatch)
    with pytest.raises(n8n_auth_module.WebhookAuthError, match="AUTH_PROFILE_INCOMPLETE"):
        n8n_auth_module.trigger_webhook("dispatch-submit", {}, auth_profile="w15_dispatch")
    assert seen == {}


def test_secret_never_in_trace_or_errors(n8n_auth_module, monkeypatch):
    seen, traced = _capture(n8n_auth_module, monkeypatch)
    n8n_auth_module.trigger_webhook("dispatch-submit", {}, auth_profile="w15_dispatch")
    assert SECRET not in repr(traced)
    with pytest.raises(n8n_auth_module.WebhookAuthError) as ei:
        n8n_auth_module.trigger_webhook("x", {}, auth_profile="w15_dispatch")
    assert SECRET not in str(ei.value)


def test_request_adds_extra_headers(n8n_auth_module, monkeypatch):
    captured = {}

    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    def fake_urlopen(req, timeout=30):
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        return FakeResp()

    monkeypatch.setattr(n8n_auth_module.urllib.request, "urlopen", fake_urlopen)
    assert n8n_auth_module._request("POST", "/webhook/x", {}, extra_headers={"X-Test-Auth": "v"}) == {"ok": True}
    assert captured["headers"]["x-test-auth"] == "v"
