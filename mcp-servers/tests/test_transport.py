"""
Tests for the dual-transport (stdio / HTTP) port of odoo_mcp.py and
n8n_mcp.py. No live Odoo/N8N credentials or network access required — the
Odoo/N8N calls themselves are mocked; what's under test is the JSON-RPC
dispatch logic and the HTTP transport wiring (auth, routing), which is
exactly the part this port actually changed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

MCP_SERVERS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_SERVERS_DIR))

# odoo_mcp.py reads its Odoo env vars at call time, not import time — safe
# to import without setting them, as long as tests don't exercise real
# Odoo-calling tool handlers (search_odoo etc.) without mocking _exec.
import odoo_mcp  # noqa: E402


# ---------------------------------------------------------------------------
# odoo_mcp.py — build_response() pure-logic tests (stdio and HTTP both call
# this same function; testing it once covers both transports' dispatch path)
# ---------------------------------------------------------------------------

def test_initialize_returns_server_info():
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "synapsys-odoo"


def test_tools_list_returns_all_ten_tools():
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in resp["result"]["tools"]}
    assert names == set(odoo_mcp.TOOL_HANDLERS.keys())


def test_notifications_initialized_returns_none():
    """Notifications have no id and expect no response body at all —
    build_response() must return None so callers (stdio's handle(), the
    HTTP endpoint) can each apply their own no-response behaviour."""
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert resp is None


def test_unknown_method_returns_json_rpc_error():
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "id": 5, "method": "nonexistent/method"})
    assert resp["error"]["code"] == -32601


def test_unknown_method_with_no_id_returns_none():
    """Per JSON-RPC 2.0, a request with no id is itself a notification —
    still no response even on an error path."""
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "method": "nonexistent/method"})
    assert resp is None


def test_ping_returns_empty_result():
    resp = odoo_mcp.build_response({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert resp["result"] == {}


def test_tools_call_unknown_tool_is_iserror_not_exception():
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "not_a_real_tool", "arguments": {}},
    })
    assert resp["result"]["isError"] is True
    assert "Unknown tool" in resp["result"]["content"][0]["text"]


def test_tools_call_search_odoo_success_path(monkeypatch):
    """Mocks _exec (the one function that actually talks to Odoo) so this
    test exercises real dispatch through count_odoo without any live
    credentials or network access."""
    monkeypatch.setattr(odoo_mcp, "_exec", lambda *a, **k: 34)
    resp = odoo_mcp.build_response({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "count_odoo", "arguments": {"model": "x_service_catalogue"}},
    })
    assert resp["result"].get("isError") is not True
    assert "34" in resp["result"]["content"][0]["text"]


def test_tools_call_wraps_xmlrpc_fault_as_error_content():
    import xmlrpc.client

    def raise_fault(*a, **k):
        raise xmlrpc.client.Fault(1, "Access Denied")

    with patch.object(odoo_mcp, "_exec", raise_fault):
        resp = odoo_mcp.build_response({
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "count_odoo", "arguments": {"model": "res.users"}},
        })
    assert resp["result"]["isError"] is True
    assert "Odoo error" in resp["result"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# odoo_mcp.py — HTTP transport wiring (auth + tool registration)
#
# build_fastmcp_app() builds a real fastmcp.FastMCP app (replacing the old
# hand-rolled Starlette /mcp endpoint tested above via TestClient). Full
# request/response cycle testing now belongs to a live streamable-HTTP
# handshake (as already verified manually against the deployed VPS — see
# 05_AI_RETURNS_HASHED/..._mcp-hosting-deployment-session-closure_v0.1.md);
# these unit tests cover what's actually under this repo's control: that
# every tool got registered and that auth wiring picks bearer-only vs
# combined (bearer + Entra) correctly, both via _azure_auth.py.
# ---------------------------------------------------------------------------

import asyncio


@pytest.fixture
def fastmcp_app(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "test-secret-token")
    return odoo_mcp.build_fastmcp_app()


def test_fastmcp_app_registers_all_ten_tools(fastmcp_app):
    tools = asyncio.run(fastmcp_app.list_tools())
    names = {t.name for t in tools}
    assert names == set(odoo_mcp.TOOL_HANDLERS.keys())


def test_fastmcp_app_bearer_only_when_no_entra_vars(fastmcp_app):
    import _bearer_auth

    assert isinstance(fastmcp_app.auth, _bearer_auth.StaticBearerTokenVerifier)


def test_fastmcp_app_uses_multiauth_when_entra_configured(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "test-secret-token")
    monkeypatch.setenv("ENTRA_TENANT_ID", "test-tenant")
    monkeypatch.setenv("OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("OAUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("MCP_API_AUDIENCE", "api://test-api-app")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://odoo-mcp.example.com")

    from fastmcp.server.auth.auth import MultiAuth

    app = odoo_mcp.build_fastmcp_app()
    assert isinstance(app.auth, MultiAuth)


def test_fastmcp_app_refuses_to_build_without_auth_token(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        odoo_mcp.build_fastmcp_app()


def test_odoo_configure_http_kwargs_requires_allowed_hosts(monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    with pytest.raises(SystemExit):
        odoo_mcp._configure_http_kwargs()


def test_odoo_configure_http_kwargs_respects_host_port_env(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "odoo-mcp.example.com")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9200")
    kwargs = odoo_mcp._configure_http_kwargs()
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9200
    assert kwargs["allowed_hosts"] == ["odoo-mcp.example.com"]


def test_odoo_configure_http_kwargs_rejects_bad_http_transport(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "odoo-mcp.example.com")
    monkeypatch.setenv("MCP_HTTP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(SystemExit):
        odoo_mcp._configure_http_kwargs()


def test_stdio_transport_is_default(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    with patch.object(odoo_mcp, "main_stdio") as mock_stdio, \
         patch.object(odoo_mcp, "main_http") as mock_http:
        odoo_mcp.main()
    mock_stdio.assert_called_once()
    mock_http.assert_not_called()


def test_unsupported_transport_exits(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(SystemExit):
        odoo_mcp.main()


# ---------------------------------------------------------------------------
# _bearer_auth.py — standalone verifier logic
# ---------------------------------------------------------------------------

import _bearer_auth  # noqa: E402


def test_static_verifier_rejects_wrong_token():
    v = _bearer_auth.StaticBearerTokenVerifier("correct-token")
    assert v.verify_sync("wrong-token") is False


def test_static_verifier_accepts_correct_token():
    v = _bearer_auth.StaticBearerTokenVerifier("correct-token")
    assert v.verify_sync("correct-token") is True


def test_static_verifier_rejects_empty_presented_token():
    v = _bearer_auth.StaticBearerTokenVerifier("correct-token")
    assert v.verify_sync("") is False


def test_verifier_construction_requires_nonempty_expected_token():
    with pytest.raises(ValueError):
        _bearer_auth.StaticBearerTokenVerifier("")


def test_load_required_token_exits_when_unset(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        _bearer_auth.load_required_token()


def test_load_required_token_returns_value_when_set(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "abc123")
    assert _bearer_auth.load_required_token() == "abc123"


def test_verify_token_async_path_matches_sync():
    """No pytest-asyncio dependency for one test — run the coroutine
    directly instead."""
    import asyncio

    v = _bearer_auth.StaticBearerTokenVerifier("correct-token")
    ok = asyncio.run(v.verify_token("correct-token"))
    bad = asyncio.run(v.verify_token("nope"))
    assert ok is not None and ok.token == "correct-token"
    assert bad is None


# ---------------------------------------------------------------------------
# n8n_mcp.py — transport config helper (import requires dummy env vars,
# since the module exits at import time if N8N_URL/N8N_API_TOKEN are unset)
# ---------------------------------------------------------------------------

@pytest.fixture
def n8n_module(monkeypatch):
    monkeypatch.setenv("N8N_URL", "https://example.invalid")
    monkeypatch.setenv("N8N_API_TOKEN", "dummy-for-import-only")
    # Fresh import each time so per-test env changes (MCP_AUTH_TOKEN etc.)
    # are actually picked up rather than reusing a cached module instance.
    sys.modules.pop("n8n_mcp", None)
    import n8n_mcp
    return n8n_mcp


def test_n8n_module_imports_with_stdio_defaults(n8n_module):
    # Standalone `fastmcp` package has no shared `.settings` object the way
    # the bare SDK's FastMCP does — importing cleanly with no auth
    # configured is itself the meaningful stdio-mode assertion here.
    assert n8n_module.mcp.auth is None


def test_n8n_configure_http_kwargs_sets_auth(n8n_module, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "n8n-secret")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "n8n.example.com")
    kwargs = n8n_module._configure_http_kwargs()
    assert kwargs["transport"] == "http"
    assert n8n_module.mcp.auth is not None


def test_n8n_configure_http_kwargs_requires_auth_token(n8n_module, monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "n8n.example.com")
    with pytest.raises(SystemExit):
        n8n_module._configure_http_kwargs()


def test_n8n_configure_http_kwargs_requires_allowed_hosts(n8n_module, monkeypatch):
    """No default/guessed allow-list — a network-exposed, credential-bearing
    server must refuse to start rather than silently pick a value."""
    monkeypatch.setenv("MCP_AUTH_TOKEN", "n8n-secret")
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    with pytest.raises(SystemExit):
        n8n_module._configure_http_kwargs()


def test_n8n_configure_http_kwargs_respects_host_port_env(n8n_module, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "n8n-secret")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "n8n.example.com")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9100")
    kwargs = n8n_module._configure_http_kwargs()
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9100
    assert kwargs["allowed_hosts"] == ["n8n.example.com"]


def test_n8n_configure_http_kwargs_rejects_bad_http_transport(n8n_module, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "n8n-secret")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "n8n.example.com")
    monkeypatch.setenv("MCP_HTTP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(SystemExit):
        n8n_module._configure_http_kwargs()


def test_n8n_configure_http_kwargs_parses_multiple_allowed_hosts(n8n_module, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "n8n-secret")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "n8n.example.com, secondary.example.com")
    kwargs = n8n_module._configure_http_kwargs()
    assert kwargs["allowed_hosts"] == ["n8n.example.com", "secondary.example.com"]


# ---------------------------------------------------------------------------
# _azure_auth.py — shared Entra OAuth wiring, used by both servers
# ---------------------------------------------------------------------------

import _azure_auth  # noqa: E402

ENTRA_VARS = {
    "ENTRA_TENANT_ID": "test-tenant",
    "OAUTH_CLIENT_ID": "test-client-id",
    "OAUTH_CLIENT_SECRET": "test-client-secret",
    "MCP_API_AUDIENCE": "api://test-api-app",
    "MCP_PUBLIC_URL": "https://mcp.example.com",
}


def test_azure_auth_bearer_only_when_no_entra_vars(monkeypatch):
    for name in ENTRA_VARS:
        monkeypatch.delenv(name, raising=False)
    import _bearer_auth

    auth = _azure_auth.build_combined_auth("shared-token")
    assert isinstance(auth, _bearer_auth.StaticBearerTokenVerifier)


def test_azure_auth_multiauth_when_fully_configured(monkeypatch):
    for name, value in ENTRA_VARS.items():
        monkeypatch.setenv(name, value)
    from fastmcp.server.auth.auth import MultiAuth
    from fastmcp.server.auth.providers.azure import AzureProvider

    auth = _azure_auth.build_combined_auth("shared-token")
    assert isinstance(auth, MultiAuth)
    assert isinstance(auth.server, AzureProvider)
    assert len(auth.verifiers) == 1


def test_azure_auth_fails_closed_on_partial_config(monkeypatch):
    for name in ENTRA_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ENTRA_TENANT_ID", "test-tenant")
    monkeypatch.setenv("OAUTH_CLIENT_ID", "test-client-id")
    # OAUTH_CLIENT_SECRET / MCP_API_AUDIENCE / MCP_PUBLIC_URL deliberately unset
    with pytest.raises(SystemExit):
        _azure_auth.build_combined_auth("shared-token")


def test_azure_auth_identifier_uri_matches_api_app_not_connector(monkeypatch):
    """The connector app's client_id must NOT silently become the scope
    prefix — required_scopes are validated against MCP_API_AUDIENCE (the
    separate API app's Application ID URI), matching this deployment's
    two-app registration pattern (API app + connector app), not
    AzureProvider's single-app default (api://{client_id})."""
    for name, value in ENTRA_VARS.items():
        monkeypatch.setenv(name, value)

    auth = _azure_auth.build_combined_auth("shared-token")
    assert auth.server.identifier_uri == ENTRA_VARS["MCP_API_AUDIENCE"]
    assert auth.server.identifier_uri != f"api://{ENTRA_VARS['OAUTH_CLIENT_ID']}"


# ---------------------------------------------------------------------------
# n8n_mcp.py / n8n_mcp_readonly.py — _request() transport-failure handling,
# id validation, and get_execution_summary() (fix for
# get_execution(include_data=true) failing unhandled on large, long-running
# executions -- see 05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-
# VISUAL-COMPLETION-001/CONTROLLER_CYCLES/20260823--claude-code--return--
# common-gate-runtime-slo-recovery--v0-1.md for the production evidence)
# ---------------------------------------------------------------------------

import inspect  # noqa: E402
import json as _json  # noqa: E402
import socket  # noqa: E402
import struct  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

N8N_MODULES = ["n8n_readonly_module", "n8n_module"]


@pytest.fixture
def n8n_readonly_module(monkeypatch):
    monkeypatch.setenv("N8N_URL", "https://example.invalid")
    monkeypatch.setenv("N8N_API_TOKEN", "dummy-for-import-only")
    sys.modules.pop("n8n_mcp_readonly", None)
    import n8n_mcp_readonly
    return n8n_mcp_readonly


def test_n8n_servers_share_identical_helpers(n8n_readonly_module, n8n_module):
    """The two servers carry duplicated transport/summary helpers (each file
    must stay deployable on its own). Fail loudly if the copies drift."""
    for name in ("_path_id", "_read_body", "_decode_json", "_clip",
                 "_summarise_error", "_summarise_execution", "get_execution_summary"):
        a = getattr(n8n_readonly_module, name)
        b = getattr(n8n_module, name)
        a, b = getattr(a, "fn", a), getattr(b, "fn", b)  # unwrap FastMCP tools
        assert inspect.getsource(a) == inspect.getsource(b), f"{name} drifted"
    for const in ("_READ_CHUNK", "_SUMMARY_MAX_TIMEOUT", "_SUMMARY_TEXT_LIMIT"):
        assert getattr(n8n_readonly_module, const) == getattr(n8n_module, const)
    assert n8n_readonly_module._ID_RE.pattern == n8n_module._ID_RE.pattern


# --- real-socket transport failures ----------------------------------------

def _serve_once(behaviour):
    """One-shot local HTTP server: accept a connection, swallow the request,
    then hand the raw socket to `behaviour`. Returns the base URL."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        try:
            conn.recv(65536)
            behaviour(conn)
        except OSError:
            pass
        finally:
            conn.close()
            srv.close()

    threading.Thread(target=run, daemon=True).start()
    return f"http://127.0.0.1:{srv.getsockname()[1]}"


def _stall_mid_body(conn):
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{")
    time.sleep(3)


def _close_mid_body(conn):
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\n{\"a\":")


def _reset_mid_body(conn):
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\n{\"a\":")
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))


def _html_body(conn):
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 22\r\n\r\n<html>Bad Gateway</html>"[:61])


def _slow_drip(conn):
    # Each byte arrives well inside the per-read timeout, so only a TOTAL
    # deadline can stop this.
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 200\r\n\r\n")
    for _ in range(200):
        conn.send(b" ")
        time.sleep(0.2)


@pytest.mark.parametrize("module_name", N8N_MODULES)
@pytest.mark.parametrize("behaviour, expected", [
    (_stall_mid_body, "no data for 1s"),
    (_close_mid_body, "connection dropped mid-response (IncompleteRead"),
    (_reset_mid_body, "connection dropped mid-response"),
    (_html_body, "not valid UTF-8 JSON"),
])
def test_request_transport_failures_raise_runtime_error(module_name, behaviour, expected, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "N8N_URL", _serve_once(behaviour))
    with pytest.raises(RuntimeError) as exc_info:
        module._request("GET", "/api/v1/executions/1", timeout=1)
    assert expected in str(exc_info.value)


@pytest.mark.parametrize("module_name", N8N_MODULES)
def test_request_deadline_caps_total_time_on_slow_drip(module_name, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "N8N_URL", _serve_once(_slow_drip))
    t0 = time.monotonic()
    with pytest.raises(RuntimeError) as exc_info:
        module._request("GET", "/api/v1/executions/1", timeout=1.5, deadline=1.5)
    elapsed = time.monotonic() - t0
    assert "1.5s total deadline" in str(exc_info.value)
    assert elapsed < 2.5, f"deadline overran: {elapsed:.2f}s"


def test_request_mutation_failure_warns_change_may_have_applied(n8n_module, monkeypatch):
    monkeypatch.setattr(n8n_module, "N8N_URL", _serve_once(_close_mid_body))
    with pytest.raises(RuntimeError) as exc_info:
        n8n_module._request("POST", "/api/v1/workflows/abc/activate", timeout=1)
    assert "MAY have been applied" in str(exc_info.value)


def test_request_get_failure_has_no_mutation_warning(n8n_module, monkeypatch):
    monkeypatch.setattr(n8n_module, "N8N_URL", _serve_once(_close_mid_body))
    with pytest.raises(RuntimeError) as exc_info:
        n8n_module._request("GET", "/api/v1/workflows/abc", timeout=1)
    assert "MAY have been applied" not in str(exc_info.value)


# --- id validation ----------------------------------------------------------

def _forbid_request(*a, **k):
    raise AssertionError("_request must not be called for an invalid argument")


@pytest.mark.parametrize("module_name", N8N_MODULES)
@pytest.mark.parametrize("bad_id", ["../credentials", "..", "1?includeData=false", "1#", "1/2", "", "a" * 65, "1 2"])
def test_path_tools_reject_unsafe_ids(module_name, bad_id, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "_request", _forbid_request)
    for call in (lambda: module.get_workflow(bad_id),
                 lambda: module.get_execution(bad_id),
                 lambda: module.get_execution_summary(bad_id)):
        with pytest.raises(ValueError):
            call()


def test_mutation_tools_reject_unsafe_ids(n8n_module, monkeypatch):
    monkeypatch.setattr(n8n_module, "_request", _forbid_request)
    for call in (lambda: n8n_module.activate_workflow("../x"),
                 lambda: n8n_module.deactivate_workflow("../x"),
                 lambda: n8n_module.update_workflow("../x", {"nodes": [], "connections": {}})):
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize("module_name", N8N_MODULES)
def test_path_tools_accept_real_n8n_ids(module_name, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    seen = []
    monkeypatch.setattr(module, "_request", lambda method, path, *a, **k: seen.append(path) or {})
    module.get_workflow("KpjCoiFNrjTNbbat")
    module.get_execution(12345, include_data=True)
    assert seen == ["/api/v1/workflows/KpjCoiFNrjTNbbat", "/api/v1/executions/12345?includeData=true"]


# --- get_execution_summary --------------------------------------------------

@pytest.mark.parametrize("module_name", N8N_MODULES)
@pytest.mark.parametrize("bad_timeout", [0, -1, 301, True, "60", None])
def test_get_execution_summary_rejects_out_of_range_timeout(module_name, bad_timeout, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "_request", _forbid_request)
    with pytest.raises(ValueError):
        module.get_execution_summary("9999", timeout=bad_timeout)


@pytest.mark.parametrize("module_name", N8N_MODULES)
def test_get_execution_summary_passes_timeout_as_total_deadline(module_name, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    calls = []
    monkeypatch.setattr(module, "_request", lambda *a, **k: calls.append(k) or {})
    module.get_execution_summary("9999")
    module.get_execution_summary("9999", timeout=120)
    assert calls == [{"timeout": 50, "deadline": 50}, {"timeout": 120, "deadline": 120}]


def _large_execution_payload():
    """Execution response in N8N's shape (data.resultData.runData keyed by
    node name, each a list of run dicts with executionStatus/executionTime/
    startTime), carrying large per-node payloads the summary must drop."""
    huge_blob = "x" * 500_000  # stand-in for a large record/file payload
    return {
        "id": "9999",
        "status": "success",
        "finished": True,
        "mode": "trigger",
        "workflowId": "WF123",
        "startedAt": "2026-08-23T06:00:51.040Z",
        "stoppedAt": "2026-08-23T06:46:18.606Z",
        "data": {
            "resultData": {
                "lastNodeExecuted": "Write Controller Receipt SCHEDULE",
                "runData": {
                    "Read Pattern Register SCHEDULE": [{
                        "executionStatus": "success",
                        "executionTime": 900,
                        "startTime": 2000,
                        "data": {"main": [[{"json": {"blob": huge_blob}}]]},
                    }],
                    "Read Method Registry SCHEDULE": [{
                        "executionStatus": "success",
                        "executionTime": 1794,
                        "startTime": 1000,
                        "data": {"main": [[{"json": {"blob": huge_blob}}]]},
                    }],
                },
            }
        },
    }


def _large_execution_error_payload():
    """Failed execution, with the error serialised the way N8N's
    NodeApiError.toJSON() does: name/message/description/httpCode/node plus
    stack and context, the last two of which must never be returned."""
    d = _large_execution_payload()
    d["status"] = "error"
    d["finished"] = False
    node_error = {
        "name": "NodeApiError",
        "message": "Forbidden - perhaps check your credentials?",
        "description": "You are not allowed to access 'Pattern Register' records. " + "y" * 5000,
        "httpCode": "403",
        "node": {"name": "Read Pattern Register SCHEDULE", "type": "n8n-nodes-base.odoo"},
        "stack": "NodeApiError: Forbidden\n    at secret/internal/path.js:1:1",
        "context": {"requestOptions": {"marker": "SENTINEL-NOT-RETURNED"}},
    }
    d["data"]["resultData"]["error"] = node_error
    run = d["data"]["resultData"]["runData"]["Read Pattern Register SCHEDULE"][0]
    del run["executionStatus"]  # older N8N: only the run-level error marks failure
    run["error"] = node_error
    return d


@pytest.mark.parametrize("module_name", N8N_MODULES)
def test_get_execution_summary_omits_large_payload_and_extracts_timings(module_name, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "_request", lambda *a, **k: _large_execution_payload())

    result = module.get_execution_summary("9999")

    assert result["id"] == "9999"
    assert result["status"] == "success"
    assert result["mode"] == "trigger"
    assert result["nodeCount"] == 2
    # Sorted by startTime -- Method Registry (1000) before Pattern Register (2000)
    assert [n["node"] for n in result["nodes"]] == [
        "Read Method Registry SCHEDULE",
        "Read Pattern Register SCHEDULE",
    ]
    assert result["nodes"][1]["executionTimeMs"] == 900
    assert result["nodes"][1]["error"] is None
    assert result["error"] is None

    serialised = _json.dumps(result)
    assert "x" * 1000 not in serialised
    assert len(serialised) < 5_000


@pytest.mark.parametrize("module_name", N8N_MODULES)
def test_get_execution_summary_extracts_error_detail(module_name, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "_request", lambda *a, **k: _large_execution_error_payload())

    result = module.get_execution_summary("9999")

    assert result["status"] == "error"
    err = result["error"]
    assert err["node"] == "Read Pattern Register SCHEDULE"
    assert err["nodeType"] == "n8n-nodes-base.odoo"
    assert err["name"] == "NodeApiError"
    assert err["httpCode"] == "403"
    assert "Forbidden" in err["message"]
    assert "Pattern Register" in err["description"]
    assert len(err["description"]) < module._SUMMARY_TEXT_LIMIT + 100  # clipped

    failed = next(n for n in result["nodes"] if n["node"] == "Read Pattern Register SCHEDULE")
    assert failed["status"] == "error"  # derived: no executionStatus on older N8N
    assert failed["error"]["name"] == "NodeApiError"

    serialised = _json.dumps(result)
    assert "SENTINEL-NOT-RETURNED" not in serialised
    assert "secret/internal/path" not in serialised


@pytest.mark.parametrize("module_name", N8N_MODULES)
@pytest.mark.parametrize("raw", [[], "oops", {"data": "not-a-dict"}, {"data": {"resultData": {"runData": []}}}])
def test_get_execution_summary_tolerates_malformed_responses(module_name, raw, request, monkeypatch):
    module = request.getfixturevalue(module_name)
    monkeypatch.setattr(module, "_request", lambda *a, **k: raw)
    result = module.get_execution_summary("9999")
    assert result["id"] == "9999"


def test_azure_auth_accepts_bare_api_app_guid_as_audience(monkeypatch):
    """Entra issues access tokens with `aud` set to the resource (API) app's
    bare client ID GUID, not its api://... Application ID URI — observed
    directly in production 401s ("audience mismatch (got '<bare-guid>',
    expected [...])"). AzureProvider's default audience list only contains
    the connector's client_id and the api://... URI, so real tokens were
    being rejected. The bare GUID must be added as an accepted audience."""
    for name, value in ENTRA_VARS.items():
        monkeypatch.setenv(name, value)

    auth = _azure_auth.build_combined_auth("shared-token")
    bare_guid = ENTRA_VARS["MCP_API_AUDIENCE"].removeprefix("api://")
    verifier = auth.server._token_validator
    assert bare_guid in verifier.audience
    assert ENTRA_VARS["MCP_API_AUDIENCE"] in verifier.audience
    assert ENTRA_VARS["OAUTH_CLIENT_ID"] in verifier.audience


def test_rejected_mutation_ids_are_still_traced(n8n_module, monkeypatch):
    """Id validation runs inside the D007 trace envelope, so a refused id
    still emits its one trace event rather than bypassing the trace."""
    events = []
    monkeypatch.setattr(n8n_module, "_trace_sink", events.append)
    monkeypatch.setattr(n8n_module, "_request", _forbid_request)
    for call in (lambda: n8n_module.activate_workflow("../x"),
                 lambda: n8n_module.deactivate_workflow("../x"),
                 lambda: n8n_module.update_workflow("../x", {"nodes": [], "connections": {}})):
        with pytest.raises(ValueError):
            call()
    assert [e["result"] for e in events] == ["error"] * 3
    assert all("invalid N8N workflow id" in e["refusal_reason"] for e in events)
