# Service Catalogue adoption loader (RC07, source-only candidate)

V19 `x_service_catalogue` (49 rows, extract `V19_SERVICE_CATALOGUE_EXTRACT_20261127.json` (not committed; filed in Working Memory), sha256 87bdc258f65dc57175cbed5f6fdeebce6658a3868e495dd2dec7b107aa58f887) to V20 `synapsys.service` via the 15-slot map.
Nothing here is installed, run on dev, or run on V19. It lives outside `addon/synapsys`, so the addon tree on dev is unchanged and the loader never runs on module upgrade.

## Proposed dev fast path (a separate Steward word and D007 release; not part of this build)
1. Backup the dev database (and note the backup id). 2. Copy `loader/service_catalogue_load.py` and the extract to the box. 3. `odoo-bin shell -d <db> --no-http`, then `L.run(env, extract=...)`:
a DRY-RUN that prints the diff and writes nothing. 4. Review the diff and the report with the Steward (held names, unresolved relations, lifecycle counts). 5. Only then `L.run(env, extract=..., apply=True)`, `env.cr.commit()`.
6. Read back: the Service screen and the Master view counts. 7. Rollback if needed: `L.rollback(env, apply=True)`, `env.cr.commit()` removes only the rows and the Standard this loader created (marked by external ids in module `__synapsys_v19_load__`); a backup restore is the fallback.
A second apply changes 0 rows. A Steward ruling on a held name goes in as `name_rulings={"3": "...", "14": "..."}`.
