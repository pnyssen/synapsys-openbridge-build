"""Diagnostic middleware for the network-exposed MCP OAuth endpoints.

The MCP SDK's token/authorize handlers return a detailed OAuth error body
(error + error_description) in the HTTP response sent to the CLIENT on
failure, but never log that detail server-side — a failed exchange shows up
in `docker compose logs` as a bare "POST /token HTTP/1.1 401 Unauthorized"
uvicorn access line with no reason. This middleware logs only a validated
OAuth error category (the RFC 6749 / RFC 7591 `error` code, checked against
a fixed allow-list). Response error descriptions and authentication material
are never logged.

Request and response bodies may contain secrets: only a validated error
category is eligible for logging, never raw content or credentials.
"""
from __future__ import annotations

import logging
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("oauth_debug")

_LOGGED_PATHS = {"/authorize", "/consent", "/token", "/register"}
_MAX_INSPECTED_BODY_BYTES = 8192

# RFC 6749 §4.1.2.1/§5.2, RFC 6750 §3.1 and RFC 7591 §3.2.2 error codes —
# the only response content eligible for logging.
_ALLOWED_ERROR_CODES = frozenset({
    "invalid_client", "invalid_request", "invalid_grant", "unauthorized_client",
    "unsupported_grant_type", "unsupported_response_type", "invalid_scope",
    "access_denied", "server_error", "temporarily_unavailable",
    "invalid_token", "insufficient_scope",
    "invalid_redirect_uri", "invalid_client_metadata",
})


def _safe_error_code(body: bytes) -> str:
    """Return only a strict OAuth error code; never log response descriptions."""
    try:
        data = json.loads(body[:_MAX_INSPECTED_BODY_BYTES].decode("utf-8"))
        code = data.get("error") if isinstance(data, dict) else None
    except (ValueError, UnicodeDecodeError, TypeError):
        return "unclassified"
    return code if isinstance(code, str) and code in _ALLOWED_ERROR_CODES else "unclassified"


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
            _safe_error_code(body),
        )

        # Same bytes, so the original raw headers (including Content-Length
        # and any repeated header such as Set-Cookie) still apply verbatim.
        rebuilt = Response(content=body, status_code=response.status_code)
        rebuilt.raw_headers = list(response.raw_headers)
        return rebuilt
