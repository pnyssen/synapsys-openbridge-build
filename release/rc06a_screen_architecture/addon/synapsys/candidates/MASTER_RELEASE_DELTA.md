# Master Architecture: exact release delta (UNRELEASED CANDIDATE)
Source-only. Nothing below has been applied to any database, and nothing here has run inside Odoo.
Prepared files (all under addon/synapsys/): arch_master.py, arch_master_views.py, arch_master_drill.py, arch_master_ctx.py, master_render.py, controllers/arch_master.py,
data/arch_master_definition.json, data/arch_master_roles.json, static/src/master/{master_nav.js,master.js,master.xml}, candidates/synapsys_master_menu_candidate.xml.
Python files are imported by the controller; controllers/__init__.py already imports it in source. A module upgrade loads the new Python and data files.

## Manifest delta (exact): candidates/MASTER_MANIFEST_DELTA.patch
1. `data` += `candidates/synapsys_master_menu_candidate.xml` (one ir.actions.client, tag synapsys_master_architecture, and one menuitem under menu_config).
2. `web.assets_backend` += `synapsys/static/src/master/master_nav.js`, `master.js`, `master.xml` (navigation module first: the component imports it).
3. No version bump is required; no schema change, no ACL change, no data write, no new model, no new group.

## What an upgrade does and does not expose
- With only the Python and JSON files (manifest unchanged), the two routes exist but no menu and no client action points at them.
- With the delta applied, the menu "Master" appears under the same parent as Lenses for users who can see that parent. Page content is always the caller's own rights.
- Removing the menu record is enough to make the page unreachable. Rollback: upgrade back to the previous manifest.

## Release gates (all outstanding)
D007 scope-specific release (this addon only), RUN_LOCK, prestate, tested backup and restore, named roles for negative tests, canary, rollback, readback. Steward ruling on the menu's semantic home (HOLD H03). D009 independent challenge of the frozen commit. Real-role tests (Steward, Collaborator; Client has no group), direct URL/API negatives and 390/768/1024/1440 viewport tests inside V20.

## Verified here, not in Odoo
The client component runs under real OWL 3 in Chromium with the web-client services stubbed; the controller runs against a stubbed `odoo` package and a fake environment; native URLs `/odoo/action-<id>[/<res_id>]` are built from integer ids but the URL scheme is SOURCE_UNVERIFIED in V20.
