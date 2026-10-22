"""
Real HTTP/Streamable-HTTP boundary tests for odoo_mcp.py and n8n_mcp.py.

test_transport.py's HTTP-wiring tests only inspect in-process FastMCP
objects (auth type, registered tool names via list_tools() called directly
on the app) — it says so explicitly in its own comments, and defers "full
request/response cycle testing" to a live streamable-HTTP handshake. This
file closes that gap: each server is started as a real subprocess, bound to
an ephemeral localhost port, and driven over the wire with the actual
`mcp` 2.2.0 client (mcp.client.streamable_http + mcp.ClientSession) rather
than a hand-built approximation of the protocol.

All credentials/URLs are synthetic and localhost/unreachable-only — no test
here calls a tool that would make an outbound Odoo or N8N request; only
protocol-level operations (initialize, tools/list, and raw auth-boundary
probes) are exercised.
"""
from __future__ import annotations

import asyncio
import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

MCP_SERVERS_DIR = Path(__file__).resolve().parent.parent

AUTH_TOKEN = "synthetic-test-token-do-not-use-in-production"
WRONG_TOKEN = "synthetic-wrong-token-do-not-use-in-production"

STARTUP_TIMEOUT_S = 15.0
POLL_INTERVAL_S = 0.2
SHUTDOWN_TIMEOUT_S = 10.0

SERVER_SPECS = {
    "odoo": {
        "script": "odoo_mcp.py",
        # Synthetic, unreachable — no test in this file invokes a tool body,
        # only protocol-level operations, so these values are never dialed.
        "extra_env": {
            "ODOO_URL": "http://127.0.0.1:1",
            "ODOO_DB": "synthetic-db",
            "ODOO_LOGIN": "synthetic-user@example.invalid",
            "ODOO_API_KEY": "synthetic-odoo-api-key",
        },
        "expected_server_name": "synapsys-odoo",
        "expected_tools": {
            "search_odoo", "read_odoo", "count_odoo", "create_odoo", "write_odoo",
            "prepare_write_odoo", "execute_write_odoo", "unlink_odoo",
            "prepare_unlink_odoo", "execute_unlink_odoo", "execute_odoo",
            "search_multi", "create_fields_batch", "create_acls_batch",
        },
    },
    "n8n": {
        "script": "n8n_mcp.py",
        "extra_env": {
            "N8N_URL": "http://127.0.0.1:1",
            "N8N_API_TOKEN": "synthetic-n8n-token",
        },
        "expected_server_name": "synapsys-n8n",
        "expected_tools": {
            "ping_n8n", "list_workflows", "get_workflow", "update_workflow",
            "activate_workflow", "deactivate_workflow", "list_executions",
            "get_execution", "get_execution_summary", "list_credentials",
            "trigger_webhook", "create_workflow", "bind_workflow_credentials_by_id",
        },
    },
}


def _free_port() -> int:
    """Bind to port 0 and read back the OS-assigned ephemeral port, so
    parallel/repeated test runs never collide on a fixed port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerHandle:
    def __init__(self, proc: subprocess.Popen, base_url: str):
        self.proc = proc
        self.base_url = base_url
        self.forced_kill = False


def _wait_until_healthy(proc: subprocess.Popen, base_url: str) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(
                f"server process exited early (code {proc.returncode}):\n{out}"
            )
        try:
            r = httpx.get(base_url + "/health", timeout=1.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError as e:
            last_err = e
        time.sleep(POLL_INTERVAL_S)
    proc.kill()
    raise RuntimeError(f"server never became healthy within {STARTUP_TIMEOUT_S}s (last error: {last_err})")


@contextlib.contextmanager
def _run_server(script: str, extra_env: dict) -> Iterator[ServerHandle]:
    port = _free_port()
    env = os.environ.copy()
    env.update({
        "MCP_TRANSPORT": "http",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": str(port),
        "MCP_ALLOWED_HOSTS": "127.0.0.1",
        "MCP_AUTH_TOKEN": AUTH_TOKEN,
    })
    env.update(extra_env)
    proc = subprocess.Popen(
        [sys.executable, script],
        cwd=str(MCP_SERVERS_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    handle = ServerHandle(proc, f"http://127.0.0.1:{port}")
    try:
        _wait_until_healthy(proc, handle.base_url)
        yield handle
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.communicate(timeout=SHUTDOWN_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                handle.forced_kill = True
                proc.kill()
                proc.communicate(timeout=SHUTDOWN_TIMEOUT_S)
        else:
            proc.communicate()


@pytest.fixture(params=sorted(SERVER_SPECS))
def server(request) -> Iterator[tuple[str, ServerHandle]]:
    key = request.param
    spec = SERVER_SPECS[key]
    with _run_server(spec["script"], spec["extra_env"]) as handle:
        yield key, handle


async def _initialize_and_list_tools(base_url: str, token: str):
    client = create_mcp_http_client(headers={"Authorization": f"Bearer {token}"})
    async with streamable_http_client(base_url + "/mcp", http_client=client) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            tools_result = await session.list_tools()
            return init_result, tools_result


def _raw_post(base_url: str, extra_headers: dict) -> httpx.Response:
    return httpx.post(
        base_url + "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            **extra_headers,
        },
        timeout=5,
    )


# ---------------------------------------------------------------------------
# A. server starts using its actual HTTP/Streamable HTTP path
# ---------------------------------------------------------------------------

def test_server_starts_on_real_http_path(server):
    _key, handle = server
    r = httpx.get(handle.base_url + "/health", timeout=2)
    assert r.status_code == 200
    assert r.text == "ok"


# ---------------------------------------------------------------------------
# B. authenticated MCP client can complete protocol initialization
# ---------------------------------------------------------------------------

def test_authenticated_client_completes_protocol_initialization(server):
    key, handle = server
    spec = SERVER_SPECS[key]
    init_result, _ = asyncio.run(_initialize_and_list_tools(handle.base_url, AUTH_TOKEN))
    assert init_result.server_info.name == spec["expected_server_name"]


# ---------------------------------------------------------------------------
# C. authenticated client can perform tools/list and receive the expected
#    tool catalogue
# ---------------------------------------------------------------------------

def test_authenticated_client_receives_expected_tool_catalogue(server):
    key, handle = server
    spec = SERVER_SPECS[key]
    _, tools_result = asyncio.run(_initialize_and_list_tools(handle.base_url, AUTH_TOKEN))
    names = {t.name for t in tools_result.tools}
    assert names == spec["expected_tools"]


# ---------------------------------------------------------------------------
# D. request without required bearer authentication fails closed
# ---------------------------------------------------------------------------

def test_missing_bearer_token_fails_closed(server):
    _key, handle = server
    r = _raw_post(handle.base_url, {})
    assert r.status_code in (401, 403)


def test_wrong_bearer_token_fails_closed(server):
    _key, handle = server
    r = _raw_post(handle.base_url, {"Authorization": f"Bearer {WRONG_TOKEN}"})
    assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# E. synthetic bearer token is not echoed in response/error material
# ---------------------------------------------------------------------------

def test_bearer_token_never_echoed_in_refusal_response(server):
    """Neither the real secret nor a wrongly-presented token should ever
    appear verbatim in a 401/403 body or its headers — a naive error
    handler could echo the Authorization header back for debugging and
    leak it."""
    _key, handle = server
    responses = [
        _raw_post(handle.base_url, {}),
        _raw_post(handle.base_url, {"Authorization": f"Bearer {WRONG_TOKEN}"}),
    ]
    for r in responses:
        assert AUTH_TOKEN not in r.text
        assert WRONG_TOKEN not in r.text
        header_blob = "".join(f"{k}:{v}" for k, v in r.headers.items())
        assert AUTH_TOKEN not in header_blob
        assert WRONG_TOKEN not in header_blob


# ---------------------------------------------------------------------------
# F. server terminates cleanly after test
#
# Standalone (not the shared `server` fixture) so the SIGTERM-driven
# shutdown outcome can be asserted directly, rather than relying on timing
# inside a parametrized fixture's teardown.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(SERVER_SPECS))
def test_server_terminates_cleanly_after_test(key):
    spec = SERVER_SPECS[key]
    with _run_server(spec["script"], spec["extra_env"]) as handle:
        pass
    assert handle.proc.poll() is not None, f"{key} process did not exit after terminate()"
    assert not handle.forced_kill, f"{key} process required SIGKILL, did not shut down cleanly on SIGTERM"
