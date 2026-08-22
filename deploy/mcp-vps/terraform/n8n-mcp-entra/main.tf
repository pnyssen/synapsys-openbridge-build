# Creates the n8n-mcp Entra ID app pair that odoo-mcp already has
# (odoo-mcp-api / odoo-mcp-connector) but n8n-mcp was missing — logged in
# ../../SECRETS_INDEX.md as "Not yet created". Replaces the imperative
# setup_n8n_mcp_entra.sh script that used to live in this directory: same
# end result (a resource app exposing an mcp.access scope, a confidential
# client app consented to call it), but as a reviewable plan/diff instead
# of a one-shot `az` CLI script that's unsafe to re-run.
#
# Mirrors exactly what mcp-servers/_azure_auth.py expects at runtime: a
# resource ("-api") app whose Application ID URI becomes MCP_API_AUDIENCE,
# and a confidential client ("-connector") app that requests its scope —
# see that file's own comment block for why the split exists (Entra issues
# tokens whose `aud` is the resource app's bare client ID, not its
# api://... URI).

# ---- Resource ("-api") app -------------------------------------------------

resource "azuread_application_registration" "api" {
  display_name     = "n8n-mcp-api"
  sign_in_audience = "AzureADMyOrg"
}

resource "azuread_application_identifier_uri" "api" {
  application_id = azuread_application_registration.api.id
  identifier_uri = "api://${azuread_application_registration.api.client_id}"
}

resource "random_uuid" "mcp_access_scope" {}

resource "azuread_application_permission_scope" "mcp_access" {
  application_id = azuread_application_registration.api.id
  scope_id       = random_uuid.mcp_access_scope.id
  value          = "mcp.access"
  type           = "User"

  admin_consent_description  = "Allows the app to call the n8n-mcp server on behalf of the signed-in user."
  admin_consent_display_name = "Access n8n-mcp"
  user_consent_description   = "Allow this app to call the n8n-mcp server."
  user_consent_display_name  = "Access n8n-mcp"
}

resource "azuread_service_principal" "api" {
  client_id = azuread_application_registration.api.client_id

  # Must exist after the scope is defined, or a consumer reading this SP's
  # own oauth2_permission_scope_ids map (not used here, but by convention)
  # would see it before the scope is attached.
  depends_on = [azuread_application_permission_scope.mcp_access]
}

# ---- Client ("-connector") app ---------------------------------------------

resource "azuread_application_registration" "connector" {
  display_name     = "n8n-mcp-connector"
  sign_in_audience = "AzureADMyOrg"
}

resource "azuread_application_redirect_uris" "connector_web" {
  application_id = azuread_application_registration.connector.id
  type           = "Web"
  redirect_uris  = ["https://n8n-mcp.${var.domain_name}/auth/callback"]
}

resource "azuread_application_password" "connector" {
  application_id = azuread_application_registration.connector.id
  display_name   = "n8n-mcp-connector-secret"
}

resource "azuread_application_api_access" "connector_to_api" {
  application_id = azuread_application_registration.connector.id
  api_client_id  = azuread_application_registration.api.client_id
  scope_ids      = [azuread_application_permission_scope.mcp_access.scope_id]
}

resource "azuread_service_principal" "connector" {
  client_id = azuread_application_registration.connector.client_id
}

# Admin consent for the connector -> api delegated scope, equivalent to
# `az ad app permission admin-consent` in the script this module replaces.
resource "azuread_service_principal_delegated_permission_grant" "connector_consent" {
  service_principal_object_id          = azuread_service_principal.connector.object_id
  resource_service_principal_object_id = azuread_service_principal.api.object_id
  claim_values                         = [azuread_application_permission_scope.mcp_access.value]
}
