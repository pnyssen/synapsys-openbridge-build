# synapsys-wm-filing-compliance

Codifies, as reusable code, the naming-convention discipline this lane has
applied by hand, repeatedly, across this session: reading a real `sp_write`
rejection, working out what the enforced pattern actually is, and manually
converting a proposed filename to match it while preserving continuity via
`supersedes:`/`aliases:`.

## What's here

- `wm_filing_compliance.py` — pure functions, no network/`sp_write`/`sp_read`
  calls of any kind:
  - `validate_filename()` / `validate_front_matter()` — check a proposed
    filename or front-matter field set against the pattern this lane's
    `sp_write` calls have actually enforced this session
    (`YYYYMMDD--lane--artifact-type--slug--vMAJOR-MINOR.ext`, and nine
    required front-matter fields).
  - `slug_from_legacy_name()` / `extract_legacy_version()` /
    `build_compliant_filename()` — convert a legacy-convention filename
    (e.g. `M3C_DOCUMENT_INDEX_..._v0.195.md`) into a compliant one that
    preserves the exact version number and keeps literal recognisable
    tokens in the slug — not just a semantic `aliases:` entry — so a plain
    filename substring search still has a real chance of matching.
- `tests/test_wm_filing_compliance.py` — 13/13 passing, grounded in real
  filenames this session actually filed (accepted and rejected) plus the
  real M3C_DOCUMENT_INDEX case this tool was built to solve.

## What this is not

Not a `sp_write` wrapper and does not call it. Not a guess at the server's
actual validation source — this module's rules were derived empirically
from real rejection error text this session, and should be re-derived from
a fresh rejection if the server's behaviour ever appears to differ from
what's coded here, not patched from assumption.

## Status

CANDIDATE. Built as a general-purpose WM-filing utility, not as part of the
Navigator/Odoo four-round wave the SynapSys Wave Accelerator has separately
gated — see the alignment receipt filed this session
(`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/20260812--claude-code--alignment-receipt--wave-accelerator-consumption--v1-0.md`)
for that hold's actual scope.
