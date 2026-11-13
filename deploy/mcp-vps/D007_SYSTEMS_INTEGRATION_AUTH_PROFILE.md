# D007 Systems Integration MCP webhook authentication profile
Status: IMPLEMENTATION_CANDIDATE_IN_GITHUB_ONLY — not an installed profile.
Decision: `MESH_QUEUE/DECISIONS/STEWARD_APPROVAL_D007_SYSTEMS_INTEGRATION_MCP_AUTH_PROFILE_20261114_V1.md`
Context: CTX-SS; parent Work Object `WO-NAVIGATOR-AUTONOMOUS-GOAL-PORTFOLIO-CONTROL-001`; canonical pointer revision 146.
Owner: D007 MCP host administrator under exact protected release. This GitHub change is not that release.

## Naming and scope
Proposed name (unverified until host readback): **`systems_integration`**.
Call as `trigger_webhook(path="...", payload={...}, auth_profile="systems_integration")` after host deployment/provisioning.
Never treat a proposed name as live. The server must confirm its actual name and effective paths.

Required initial exact-path allowlist:
- `d007-svc-identity-probe-v2` (n8n workflow `h5BVAVr1ozSiD7Wi`, inactive at preflight).
- `d007-cbc-c1c4-cr-register-v1` (n8n workflow `lmbJ7qJSwC9NbIQv`, inactive at preflight).

The current MCP implementation checks **exact strings**. It does not interpret `d007-*` as a wildcard. Do not configure a broad prefix or automatically admit newly created paths. For every later D007 webhook path, verify the exact workflow/path, owning Work Object, service, Context, authority and safe effect; append it explicitly to the path list under D007 release control. Inactive workflows stay inactive. Never activate the CBC registrar merely to prove authentication.

## No-secret host configuration
The currently deployed MCP already supports multiple named `N8N_WEBHOOK_AUTH_*` profiles. The code change needed in this release is Docker environment pass-through and documentation/tests; the Python profile resolver need not be widened.
Set these keys **on the authorised host only** in `deploy/mcp-vps/.env`. Never store header name/value in GitHub, chat or a Working Memory receipt.

```dotenv
# Retain all existing profile names such as w15_dispatch.
N8N_WEBHOOK_AUTH_PROFILES=w15_dispatch,systems_integration
N8N_WEBHOOK_AUTH_SYSTEMS_INTEGRATION_HEADER=<HOST_SECRET_HEADER_NAME>
N8N_WEBHOOK_AUTH_SYSTEMS_INTEGRATION_VALUE=<HOST_SECRET_HEADER_VALUE>
N8N_WEBHOOK_AUTH_SYSTEMS_INTEGRATION_PATHS=d007-svc-identity-probe-v2,d007-cbc-c1c4-cr-register-v1
```

Use the n8n Header Auth credential approved for the actual endpoints. The probe v2 currently binds the existing H1-CGPT-N8N-Inbound-Auth reference `9gaq6IiZhQLiEJV7`. The registrar has `headerAuth` set, but a bound credential reference was not independently verified; D007 must verify it before positive invocation. **Never create or display a secret to satisfy this instruction.** If header credentials differ across endpoints, do not force them into a single profile; use separately named, exactly scoped profiles and record the variance.

## Operational release process
1. Verify the exact D001 approval and a classified scope-matched D007 CR/release. Reuse existing records where they actually cover this profile scope. CR1311/Release125 cover W11 mediation, **not** this profile. Do not infer a Major release authority from standing internal task routing.
2. Record host process image, current Git commit, n8n MCP service identity, non-secret old `N8N_WEBHOOK_AUTH_PROFILES` and `*_PATHS` values, code/compose hash and rollback image/compose; verify no stale deployment or parallel writer.
3. With a compatible authenticated D007 host executor, deploy the reviewed commit and set the two host-held header variables. Preserve existing W15 profile; the server should remain fail-closed when any required profile value is missing. Do not change workflow enablement or n8n API credentials.
4. Restart **only** the n8n MCP container under the approved D007 release; verify readiness and ensure existing W15 calls still work.
5. In a fresh connected session, invoke a **known forbidden path** with `auth_profile="systems_integration"`. Expected response: `AUTH_PATH_NOT_ALLOWED` before HTTP; `AUTH_PROFILE_UNKNOWN` means it is not enabled or wrong profile name. Run a second negative with a wrong profile name and confirm `AUTH_PROFILE_UNKNOWN`. The absence of a workflow run is additional, not sole, evidence.
6. Inspect host non-secret effective `*_PATHS` and `*_PROFILES` entries and compare exactly to the approved names; verify that an unlisted D007 path, unrelated W15, D009 and API administration route are refused before HTTP.
7. Positive admission must be run only after the target workflow is legitimately active and its own downstream validation is authorised. A successful authenticated webhook call proves transport, not actor approval, worker lineage or release authority.
8. File and independently read back a receipt stating exact **actual** profile name, effective paths, host version/hash, D007 release ID, test identifiers/results, authentication caller and rollback readiness. Retain the host credential value entirely server-side. Obtain D009 assurance if required.

## Explicit security boundaries
- Profile authorises **invocation only**, not `create_workflow`, `update_workflow`, `activate_workflow`, `deactivate_workflow`, direct Odoo writes, CR approval or D007 worker acceptance.
- The N8N MCP API tool surface may still offer workflow management for separately authorised principals; this profile must never be treated as granting those capabilities.
- Do not silently set this profile as a default for unlisted paths. Supply `auth_profile="systems_integration"` explicitly.
- Keep the existing W15 `w15_dispatch` profile and all G1/G2/G3 protected controls intact. The W15 task178 operator-trace defect and W11 Gate5 body-role approval weakness are separate unrepaired defects.
- Task178 is `consumed` but not returned/implemented; it is not an authentic worker acceptance.
- Odoo CR1311/release125 remain scoped to separate W11 hardening and must not be reused as an MCP auth-profile release.

## Rollback
Restore the saved version of the n8n MCP container/compose and the old host environment entries for only `systems_integration`, preserving `w15_dispatch`; restart the n8n MCP service, verify old profile behaviour and no D007 new-path access, record before/after. An unqualified whole-environment rollback may disrupt other live integrations and is not authorised.

## Evidence / completion
No positive host activation or deployment has been performed by this source change. Acceptance requires host-issued, independently verified receipt and actual profile name. Main Navigator revision146 and PPV remain unchanged.
