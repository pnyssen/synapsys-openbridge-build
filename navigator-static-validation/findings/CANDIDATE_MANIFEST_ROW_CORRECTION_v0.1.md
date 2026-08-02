# Candidate Manifest Row Correction v0.1 — isolated, not applied

Target file (not written to by this lane):
`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/FILE_MANIFEST_SHA256_v0.3.csv`

## Stale row

```
CURRENT_DELIVERY.md,4235,ea01bab35cfcaddd82130b7067224d771ba13235ac90cc0977167a9a8fc5b0a3
```

## Evidence the row is stale

- Manifest file `sp_list` `lastModified`: `2026-08-01T22:40:27Z`.
- `CURRENT_DELIVERY.md` `sp_list` `lastModified`: `2026-08-02T00:59:33Z` — **2 hours 19 minutes after** the manifest.
- `CURRENT_DELIVERY.md` `sp_list` current size: `3,029` bytes, not the `4,235` bytes the manifest records.

Both facts came from `sp_list` calls made this session, not from an
earlier turn's memory or from a pasted claim.

## What this candidate correction does NOT do

It does not supply a replacement SHA-256. `sp_read`'s returned text is
not guaranteed byte-identical to the SharePoint source (demonstrated
elsewhere this session via trailing-newline/CRLF drift on round-trips
through `sp_write`), so a hash self-computed from a fetched copy would
be an unverified value dressed up as an authoritative one — exactly
the failure mode this Work Object's filing discipline exists to
prevent.

## What whoever holds write access to this file should do

1. Read the current `CURRENT_DELIVERY.md` directly from its own write
   path (not through a re-fetch-and-hash round trip like this one).
2. Recompute its SHA-256 from that direct read.
3. Replace the one stale row in `FILE_MANIFEST_SHA256_v0.3.csv` (or
   file a `v0.4`) with the corrected `bytes`/`sha256` pair.
4. Re-run this Work Object's own manifest-parity check (or this
   package's `checks.manifest_parity`) against the regenerated file to
   confirm no other row has drifted in the same way.

## Authority

This note is analysis only. No write was made to
`Obsidian/10_WORKSPACES/NAVIGATOR_MVP_v0.2/` or any other live path.
Filed as a candidate correction under this lane's own write scope
(`05_AI_RETURNS_HASHED/`), not the live workspace.
