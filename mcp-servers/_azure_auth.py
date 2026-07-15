"""
Shared Entra ID (Azure AD) OAuth wiring for network-exposed MCP servers.

Uses FastMCP's own built-in `AzureProvider` (fastmcp.server.auth.providers.azure)
— a maintained OAuth-Proxy implementation, not a hand-rolled facade. Entra ID
has no Dynamic Client Registration, which is what MCP clients like Cowork's
connector UI expect; AzureProvider is FastMCP's official bridge for exactly
that gap, so there is no reason to reimplement it here.

Combined with the existing static-bearer-token verifier via FastMCP's
`MultiAuth`, so both auth styles work on the same endpoint at once:
  - OAuth (Entra sign-in via AzureProvider) for connector UIs that require it
  - a fixed shared bearer token (`_bearer_auth.StaticBearerTokenVerifier`)
    for this repo's own direct HTTP clients

If the Entra env vars are not set, callers fall back to bearer-only — the
prior, still-supported behaviour — rather than forcing every deployment to
configure Entra before it can start.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def _entra_env() -> dict[str, str] | None:
    """Read the five Entra-specific env vars. Returns None if none are set
    (Entra disabled — bearer-only mode). Raises if some but not all are set
    (fail closed rather than silently half-configuring OAuth)."""
    names = [
        "ENTRA_TENANT_ID",
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "MCP_API_AUDIENCE",
        "MCP_PUBLIC_URL",
    ]
    values = {n: os.environ.get(n, "") for n in names}
    present = {n: v for n, v in values.items() if v}
    if not present:
        return None
    missing = [n for n in names if not values[n]]
    if missing:
        sys.stderr.write(
            "ERROR: partial Entra OAuth configuration — "
            f"{', '.join(sorted(present))} set but missing {', '.join(missing)}. "
            "Set all five env vars to enable Entra OAuth, or none to stay bearer-only.\n"
        )
        sys.exit(1)
    return values


def build_combined_auth(mcp_auth_token: str) -> Any:
    """Return the `auth=` value for `FastMCP(...)` / `mcp.auth = ...`.

    Bearer-only (a bare TokenVerifier) if Entra env vars are absent; a
    `MultiAuth(server=AzureProvider(...), verifiers=[bearer])` combining both
    if they're present. Either way the static bearer token keeps working.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from _bearer_auth import StaticBearerTokenVerifier  # noqa: E402

    bearer_verifier = StaticBearerTokenVerifier(mcp_auth_token)

    entra = _entra_env()
    if entra is None:
        return bearer_verifier

    from fastmcp.server.auth.auth import MultiAuth
    from fastmcp.server.auth.providers.azure import AzureProvider

    scope = os.environ.get("MCP_OAUTH_SCOPE", "mcp.access")

    azure_provider = AzureProvider(
        client_id=entra["OAUTH_CLIENT_ID"],
        client_secret=entra["OAUTH_CLIENT_SECRET"],
        tenant_id=entra["ENTRA_TENANT_ID"],
        required_scopes=[scope],
        identifier_uri=entra["MCP_API_AUDIENCE"],
        base_url=entra["MCP_PUBLIC_URL"],
    )

    # AzureProvider assumes one app plays both roles (OAuth client AND
    # resource), so it only ever validates tokens against
    # [connector_client_id, identifier_uri]. This deployment splits those
    # roles across two app registrations (a "-connector" client app + a
    # "-api" resource app), and Entra issues access tokens whose `aud` claim
    # is the resource app's bare client ID (observed directly in
    # AADSTS-free 401s: "audience mismatch (got '<api-app-guid>', expected
    # [...])") rather than its api://... Application ID URI. Add that bare
    # GUID as an accepted audience so tokens Entra actually issues verify.
    bare_api_app_id = entra["MCP_API_AUDIENCE"].removeprefix("api://")
    verifier = azure_provider._token_validator
    if bare_api_app_id not in verifier.audience:
        verifier.audience = [*verifier.audience, bare_api_app_id]

    return MultiAuth(server=azure_provider, verifiers=[bearer_verifier])
