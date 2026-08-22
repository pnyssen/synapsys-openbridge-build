output "entra_tenant_id" {
  description = "-> .env ENTRA_TENANT_ID (shared with odoo-mcp's existing value; should already match)"
  value       = data.azuread_client_config.current.tenant_id
}

output "n8n_oauth_client_id" {
  description = "-> .env N8N_OAUTH_CLIENT_ID"
  value       = azuread_application_registration.connector.client_id
}

output "n8n_oauth_client_secret" {
  description = "-> .env N8N_OAUTH_CLIENT_SECRET"
  value       = azuread_application_password.connector.value
  sensitive   = true
}

output "n8n_mcp_api_audience" {
  description = "-> .env N8N_MCP_API_AUDIENCE"
  value       = azuread_application_identifier_uri.api.identifier_uri
}
