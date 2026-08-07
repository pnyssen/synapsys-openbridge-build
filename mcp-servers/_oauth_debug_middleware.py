"""Diagnostic middleware for the network-exposed MCP OAuth endpoints.

The MCP SDK's token/authorize handlers return a detailed OAuth error body
(error + error_description) in the HTTP response sent to the CLIENT on
failure, but never log that detail server-side — a failed exchange shows up
in `docker compose logs` as a bare "POST /token HTTP/1.1 401 Unauthorized"
uvicorn access line with no reason. This middleware logs the response body
for the OAuth routes on any non-2xx response, so the actual failure reason
is visible in server logs without needing to reproduce the client's request.

Only response bodies are logged, never request bodies — request bodies to
these routes can carry client_assertion JWTs, PKCE verifiers, or
client_secret values; response error bodies from this SDK do not.
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("oauth_debug")

_LOGGED_PATHS = {"/authorize", "/consent", "/token", "/register"}
_MAX_LOGGED_BODY_BYTES = 2000


class OAuthErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.url.path not in _LOGGED_PATHS or response.status_code < 400:
            return response

        body = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body += chunk

        logger.warning(
            "OAuth error: %s %s -> %s %s",
            request.method,
            request.url.path,
            response.status_code,
            body[:_MAX_LOGGED_BODY_BYTES].decode("utf-8", errors="replace"),
        )

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
