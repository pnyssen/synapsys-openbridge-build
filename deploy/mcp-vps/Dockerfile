# Shared image for both odoo-mcp and n8n-mcp — same runtime dependencies,
# different script selected via the `command:` override in docker-compose.yml.
# Slim base has no PEP 668 "externally-managed-environment" marker (unlike
# the Ubuntu 24.04 host this runs on), so plain pip install works inside the
# build without needing a venv here — the venv problem this port hit on the
# host doesn't apply inside the container.
FROM python:3.12-slim

WORKDIR /app

COPY mcp-servers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-servers/odoo_mcp.py mcp-servers/n8n_mcp.py mcp-servers/_bearer_auth.py ./

# Actual command (which script, which transport) is set per-service in
# docker-compose.yml — this default just documents intent for a bare
# `docker run` against this image.
CMD ["python3", "odoo_mcp.py"]
