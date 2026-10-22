"""
Shared static bearer-token auth for network-exposed MCP servers.

Deliberately simple: one shared secret (`MCP_AUTH_TOKEN`) checked with a
constant-time comparison. This is the "fast option" auth tier — adequate for
a single trusted client (this repo's own sessions) reaching a private
endpoint, not a substitute for real per-client OAuth if multiple distinct
consumers ever need to be told apart or individually revoked. That's a
follow-on decision, not solved here.

Used by both odoo_mcp.py and n8n_mcp.py (as the bearer-only `auth=` value,
or nested inside `MultiAuth(verifiers=[...])` when Entra is also configured)
so the two servers share one auth story instead of each inventing its own.
"""
from __future__ import annotations

import hmac
import os

from fastmcp.server.auth.auth import TokenVerifier as _FastMCPTokenVerifier


class StaticBearerTokenVerifier(_FastMCPTokenVerifier):
    """A real fastmcp AuthProvider (via fastmcp's own TokenVerifier base),
    not just the bare mcp.server.auth.provider.TokenVerifier Protocol.

    fastmcp 4.x's create_streamable_http_app() calls `auth.get_middleware()`
    on whatever is assigned to `app.auth` — a plain Protocol implementer
    (only `verify_token()`, no `get_middleware()`/`get_routes()`) raises
    AttributeError the first time an HTTP app is actually built. Inheriting
    from fastmcp's TokenVerifier (an AuthProvider subclass) picks up its
    default get_middleware()/get_routes() implementations — exactly the
    "check a bearer header, no OAuth routes" behaviour this class already
    wants — while keeping the same constructor and verify_token() contract,
    so nested use inside MultiAuth(verifiers=[...]) is unaffected. Caught by
    mcp-servers/tests/test_http_boundary.py, which starts a real HTTP app
    instead of only inspecting the auth object in-process.

    verify_token() is the only method fastmcp's auth middleware actually
    calls at request time. It must be async per the base class's contract,
    even though this check itself has no I/O.
    """

    def __init__(self, expected_token: str):
        if not expected_token:
            raise ValueError("StaticBearerTokenVerifier requires a non-empty token")
        super().__init__()
        self._expected = expected_token

    async def verify_token(self, token: str):
        from mcp.server.auth.provider import AccessToken

        if not token or not hmac.compare_digest(token, self._expected):
            return None
        return AccessToken(
            token=token,
            client_id="synapsys-static-client",
            scopes=["mcp"],
        )

    def verify_sync(self, token: str) -> bool:
        """Non-async helper for the plain-Starlette (odoo_mcp.py) path,
        which doesn't go through FastMCP's auth middleware."""
        return bool(token) and hmac.compare_digest(token, self._expected)


def load_required_token(env_var: str = "MCP_AUTH_TOKEN") -> str:
    """Read the auth token from the environment, refusing to start without
    one — an HTTP-exposed server with live Odoo/N8N write access must never
    run unauthenticated by accident."""
    token = os.environ.get(env_var, "")
    if not token:
        raise SystemExit(
            f"ERROR: {env_var} must be set to run in HTTP transport mode — "
            "refusing to start an unauthenticated, network-reachable server "
            "with live write access."
        )
    return token
