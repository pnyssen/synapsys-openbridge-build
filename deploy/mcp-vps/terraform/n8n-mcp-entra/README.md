# n8n-mcp Entra app registration (Terraform)

Creates the missing `n8n-mcp-api` / `n8n-mcp-connector` Entra ID app pair —
`odoo-mcp` already has its equivalent, `n8n-mcp` didn't (see
`../../SECRETS_INDEX.md`). Replaces the older imperative
`setup_n8n_mcp_entra.sh` script with a reviewable Terraform plan.

**Who runs this**: a human with `az login`/Terraform access to the SynapSys
Entra tenant. No lane in this ecosystem holds Azure credentials — this
module was authored and reviewed here but never applied by this repo's own
tooling. `terraform init`/`validate` could not be run in the environment
that authored this module either (its own network policy blocks
`registry.terraform.io`) — run `terraform validate` yourself as a first
step before `plan`/`apply`, on top of reading the plan output carefully.

## Prerequisites

- Terraform >= 1.5
- `az login` as (or `ARM_*` / `az` credentials for) an Application
  Administrator in the SynapSys Entra tenant — the `azuread` provider
  authenticates via the Azure CLI's cached login by default.

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars   # edit domain_name if needed
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

Then fill the four outputs into `deploy/mcp-vps/.env`:

```bash
terraform output entra_tenant_id
terraform output n8n_oauth_client_id
terraform output -raw n8n_oauth_client_secret   # sensitive — shown once, copy to the password manager too
terraform output n8n_mcp_api_audience
```

Record the two new credentials in the password manager per
`../../SECRETS_INDEX.md`'s naming convention (`SynapSys - Entra -
n8n-mcp-api (App ID + secret)` / `... n8n-mcp-connector ...`), then restart
n8n-mcp to pick up the new env vars:

```bash
cd ../..
docker compose -f docker-compose.yml up -d --no-deps n8n-mcp
```

Verify: `https://n8n-mcp.<domain>/.well-known/oauth-protected-resource`
should now advertise Entra OAuth alongside the existing bearer path.

## State file — read this before running `apply`

`terraform.tfstate` stores `azuread_application_password.connector`'s value
— the connector app's client secret — **in plaintext**. Marking the output
`sensitive` (done in `outputs.tf`) only suppresses it from console/log
output; it does not encrypt state at rest. For anything beyond a one-off
local run:

- Use a remote backend with encryption at rest (Terraform Cloud, an Azure
  Storage backend with encryption, S3 with SSE, etc.) rather than a local
  `terraform.tfstate` file.
- If you do run this locally, treat the resulting `terraform.tfstate` file
  itself as a secret: it's `.gitignore`d here already, but also don't copy
  it anywhere the LastPass-first discipline in `SECRETS_INDEX.md` wouldn't
  already cover.
- `.terraform.lock.hcl` is safe to commit (no secrets, just provider
  version pins) and is intentionally not ignored.

## Rotating the secret later

`azuread_application_password` supports `rotate_when_changed` (see the
resource's own docs) for scheduled rotation via Terraform instead of the
one-off value created on first `apply`. Not wired up here — this module
creates the initial pair; ongoing rotation policy is a separate decision.

## Scope note

This module manages the **new** `n8n-mcp` app pair only. `odoo-mcp`'s
existing `odoo-mcp-api`/`odoo-mcp-connector` apps were created manually
(no Terraform state exists for them) and are **not** touched, imported, or
managed by this module — running `terraform plan` here will never propose
changes to them.
