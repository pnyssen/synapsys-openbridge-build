"""Claim-verification regression tests for PR #35 (commit aa492da).

PR #35 claimed to fix production "Connection closed" *and* timeout failures
in get_execution(include_data=true) by catching TimeoutError in _request(),
and added get_execution_summary(). An adversarial claim-verification pass
(skill: synapsys-claim-verification, 2026-10-09) ran each claimed failure
mode and its siblings against a local fake N8N server. Five defects were
reproduced on BOTH n8n_mcp.py and n8n_mcp_readonly.py; none was covered by
the existing tests (which exercise only the TimeoutError path).

Each test asserts the CORRECT behaviour and is marked xfail(strict=True):
- today it fails, documenting the known defect without breaking CI;
- when a fix lands it XPASSes, which strict mode turns into a failure,
  forcing whoever fixes it to delete the marker -- the test then guards
  against regression permanently.

No live N8N is touched: a throwaway HTTP server on 127.0.0.1 stands in.
"""

from __future__ import annotations

import http.server
import json
import socket
import struct
import sys
import threading

import pytest

MODULES = ["n8n_mcp_readonly", "n8n_mcp"]

_OK_BODY = json.dumps({
    "id": "1", "status": "success",
    "data": {"resultData": {"runData": {
        "A": [{"executionStatus": "success", "executionTime": 5, "startTime": 1}]}}},
}).encode()


class _FakeN8N(http.server.BaseHTTPRequestHandler):
    mode = "ok"
    seen: list[str] = []

    def log_message(self, *a):  # keep test output clean
        pass

    def _send(self, body: bytes, length: int | None = None):
        self.send_response(200)
        self.send_header("Content-Length", str(len(body) if length is None else length))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).seen.append(self.path)
        mode = type(self).mode
        if mode == "reset_mid_body":
            # Promise a large body, send a fragment, then RST the connection.
            self._send(_OK_BODY[:20], length=100_000)
            self.wfile.flush()
            self.connection.setsockopt(
                socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            self.connection.close()
        elif mode == "truncated_json":
            self._send(_OK_BODY[:30])
        elif mode == "mixed_starttime":
            self._send(json.dumps({"data": {"resultData": {"runData": {
                "A": [{"startTime": 5}],
                "B": [{"startTime": "2026-01-01T00:00:00Z"}],
            }}}}).encode())
        else:
            self._send(_OK_BODY)


@pytest.fixture
def fake_n8n():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeN8N)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    _FakeN8N.mode, _FakeN8N.seen = "ok", []
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture(params=MODULES)
def module(request, fake_n8n, monkeypatch):
    monkeypatch.setenv("N8N_URL", f"http://127.0.0.1:{fake_n8n.server_address[1]}")
    monkeypatch.setenv("N8N_API_TOKEN", "dummy-for-test-only")
    sys.modules.pop(request.param, None)
    mod = __import__(request.param)
    return mod


def _summary(mod):
    fn = mod.get_execution_summary
    return getattr(fn, "fn", fn)  # unwrap a FastMCP tool if wrapped


def test_baseline_summary_works(module):
    """Control: the happy path is unaffected (not xfail)."""
    result = _summary(module)("1")
    assert result["nodeCount"] == 1
    assert _FakeN8N.seen == ["/api/v1/executions/1?includeData=true"]


@pytest.mark.xfail(strict=True, reason="F1 (High): PR #35 claimed to fix 'Connection closed' "
                   "failures but only catches TimeoutError; a reset during resp.read() escapes "
                   "as an unhandled ConnectionResetError.")
def test_f1_connection_reset_mid_body_is_clean_runtime_error(module):
    _FakeN8N.mode = "reset_mid_body"
    with pytest.raises(RuntimeError):
        _summary(module)("1")


@pytest.mark.xfail(strict=True, reason="F2 (Medium): a truncated JSON body escapes as an "
                   "unhandled JSONDecodeError instead of a bounded RuntimeError.")
def test_f2_truncated_json_is_clean_runtime_error(module):
    _FakeN8N.mode = "truncated_json"
    with pytest.raises(RuntimeError):
        _summary(module)("1")


@pytest.mark.xfail(strict=True, reason="F3 (Low-Med): execution id is interpolated into the URL "
                   "path unescaped -- query injection and '../' traversal reach the server as sent.")
@pytest.mark.parametrize("bad_id", ["1?includeData=false&x=", "../credentials"])
def test_f3_execution_id_cannot_alter_request_path(module, bad_id):
    try:
        _summary(module)(bad_id)
    except (RuntimeError, ValueError):
        return  # rejecting the id outright is also acceptable
    sent = _FakeN8N.seen[-1]
    assert sent.count("?") == 1, f"id altered the query string: {sent}"
    assert "/../" not in sent, f"id traversed the path: {sent}"


@pytest.mark.xfail(strict=True, reason="F4 (Low): timeout is unbounded; timeout=-1 raises an "
                   "unhandled ValueError from the socket layer.")
def test_f4_invalid_timeout_is_clean_error(module):
    with pytest.raises(RuntimeError):
        _summary(module)("1", timeout=-1)


@pytest.mark.xfail(strict=True, reason="F5 (Low): mixed int/str startTime values make the node "
                   "sort raise an unhandled TypeError.")
def test_f5_mixed_starttime_types_do_not_crash(module):
    _FakeN8N.mode = "mixed_starttime"
    result = _summary(module)("1")
    assert result["nodeCount"] == 2
