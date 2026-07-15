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
