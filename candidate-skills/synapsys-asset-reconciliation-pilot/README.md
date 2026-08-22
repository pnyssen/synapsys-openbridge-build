# synapsys-asset-reconciliation-pilot

The bounded "smallest live move" both this session's own capability
discovery report and the follow-on `SYNAPSYS_OBSIDIAN_MMM3CCC_ECOSYSTEM_
REPOSITORY_UPGRADE_SUITE_v0.1.md` independently converged on: a read-only
reconciliation engine, piloted against the real `x_parent_asset_id` /
`x_retired_to_successor_id` discrepancy found live in Working Memory.

## What's here

- `reconciliation_engine.py` — offline, zero-network, zero-subprocess. Given
  an already-fetched Odoo extraction and already-read Obsidian canvas text,
  it: summarises relationship-field population (`extract_relationship_population`),
  parses the specific factual claims this contract cares about out of raw
  canvas text (`parse_obsidian_asset_claim`), classifies the comparison as
  `MATCHED`/`STALE_PROJECTION`/`UNKNOWN` (`reconcile_relationship_field`,
  never silently repairs, never returns `MATCHED` on an unparseable claim),
  detects self-loops/cycles/duplicate-identities/orphan-references with
  plain DFS (no `networkx` needed — confirmed unavailable in this
  environment by the earlier discovery audit), and generates a
  deterministic JSON Canvas with governed IDs (`AST-<id>` / `REL-AST-<id>-
  PARENT-AST-<id>`, never an ad hoc `obj_01`).
- `tests/test_reconciliation_engine.py` — 17 tests, including the exact
  8-condition synthetic fixture this session's discovery report constructed
  but could not run against anything (no candidate existed yet): 2 valid
  parents, 1 orphan, 1 self-loop, 1 cycle, 1 duplicate identity, 1 stale
  Obsidian count, 0 successor relationships. Isolation enforced by an
  AST-import-scan test, same pattern as every other candidate skill in
  this repo.
- `run_pilot.py` — replays this session's actual live data (the real
  120-record `search_odoo` extraction and the real canvas text read from
  `Obsidian/ASSETS_SUITE/ASSETS_SUITE_CANVAS_v0.1.canvas`) through the
  engine. Run twice back-to-back to prove determinism (second-run-identical
  is one of the discovery report's named acceptance tests).
- `pilot_output/asset_parent_canvas_2026-07-24.json` — the generated
  canvas from that real run (120 nodes, 37 edges), written to a local
  output folder, **not** to the live Obsidian vault — this lane has no
  write authorization there (see the separately-filed CR request from
  earlier this session), so the "generate one canvas" step is proven
  against a local file, not deployed live.

## Real result, this session

`x_parent_asset_id` reconciliation: **STALE_PROJECTION** — the live
source has 120 records (37 with a parent set), the Obsidian canvas claims
115 records (0 with either field set). Record-count drift alone is enough
to classify this `STALE_PROJECTION` before population is even compared —
matches this session's own manual finding exactly, now produced by code
instead of by eye. Integrity checks (self-loop/cycle/duplicate/orphan) on
the real 120-record extraction all came back clean — the live data itself
has no structural defects, only the Obsidian projection is stale.

## What this is not

Not a general entity/relationship framework — one relationship shape only
(a self-referential `many2one` field), matching the exact proof case named
in this session's discovery audit. Not connected to any live write path —
no Odoo, N8N, or Obsidian mutation occurs anywhere in this code. Not an
adopted Reconciliation Contract in the Working-Memory-registered sense the
upgrade suite describes — that requires D001/D002 registration this lane
doesn't have authority to perform.

## Status

CANDIDATE_CODE, not yet authorized for live/production wiring. Building
and running this against real (already-fetched) data was within this
lane's standing capability contract ("candidate code + test suite for
scoped capability gaps"); connecting it to a live write path or the
Navigator membrane described in the upgrade suite requires the D007/D001
review named in that document's own Gate 5.
