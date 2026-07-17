"""
Shared static bearer-token auth for network-exposed MCP servers.

Deliberately simple: one shared secret (`MCP_AUTH_TOKEN`) checked with a
constant-time comparison. This is the "fast option" auth tier — adequate for
a single trusted client (this repo's own sessions) reaching a private
endpoint, not a substitute for real per-client OAuth if multiple distinct
consumers ever need to be told apart or individually revoked. That's a
follow-on decision, not solved here.

Used by both odoo_mcp.py (raw Starlette wrapper) and n8n_mcp.py (FastMCP's
TokenVerifier protocol) so the two servers share one auth story instead of
each inventing its own.
"""
from __future__ import annotations

import hmac
import os


class StaticBearerTokenVerifier:
    """Implements mcp.server.auth.provider.TokenVerifier's Protocol.

    verify_token() is the only method FastMCP's auth middleware calls. It
    must be async per the Protocol definition, even though this check itself
    has no I/O.
    """

    def __init__(self, expected_token: str):
        if not expected_token:
            raise ValueError("StaticBearerTokenVerifier requires a non-empty token")
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
