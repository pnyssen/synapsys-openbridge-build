# ADDENDUM 2 to the RC05 returns: portal cost alignment, Option A (26 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: DECISION RECORDED FROM CHAT WORDS; not a CHG, not D007, not D009. Installed code unchanged by this addendum.

## Words received (Steward, chat, 26 Nov 2026)
New internal users can trigger a roughly $100 a month charge, which the Steward does not want. Collaborators are portal users: they see a website portal, give feedback on their Context, and the Steward applies it under the Steward's own user. Claude Code was told to align its approach so no extra cost arises. Then, when offered Option A or B: "a".

## Correction recorded
RC05 mapped "Collaborator" to group synapsys.group_synapsys_user, which implies Odoo's internal-user group and would be a billable user. Collaborators in this ecosystem are portal users (synapsys_portal_scaffold: partner x_context_ids plus the Context's x_portal_group_id, route /my/synapsys, permission by P1._permitted). The dev-only Collaborator login previously requested is WITHDRAWN. No user was created by Claude Code at any time.

## Decision: Option A
Portal Collaborators keep using their Context pages at /my/synapsys. The new route /synapsys/scaffold/context and the Lenses/architecture views stay Steward-only in practice: a portal user is refused (NO_RECOGNISED_ROLE) and cannot read synapsys.mesh.registry (needs synapsys_mesh.group_mesh_read, an internal group). No ACL, group, user or schema change. Option B (a narrowly scoped registry read for portal members behind P1._permitted) is NOT authorised and NOT built; it would be a rights decision needing its own explicit ruling and tests.
The earlier Collaborator-to-Enrich depth ruling applies only to internal users already in group_synapsys_user (none created for this work); it has no effect on portal users under Option A.

## Cost-free test route
Steward-only call of /synapsys/scaffold/context from the Steward's own logged-in browser (DevTools console), including a bad-depth call. No new user. A portal denial test would need a portal user (understood to be free; not confirmed for this plan): optional, Steward's choice.

## ONE NEXT
Steward runs the two console calls and returns the raw JSON; Claude Code compares it with the offline expectations (result OK, depth_effective enrich, 7 H.CTX roles, both peers NO_OPERATING_SOURCE; and REFUSED UNKNOWN_DEPTH). Then the SSH key is removed in hPanel.
