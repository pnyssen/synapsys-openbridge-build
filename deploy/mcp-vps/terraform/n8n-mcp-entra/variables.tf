variable "domain_name" {
  description = "Base domain for the MCP servers, e.g. srv1536619.hstgr.cloud. Used to build the connector app's OAuth redirect URI: https://n8n-mcp.<domain_name>/auth/callback (FastMCP AzureProvider's default redirect_path, see mcp-servers/_azure_auth.py)."
  type        = string
}
