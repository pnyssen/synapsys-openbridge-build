# Manual Handoff Packet v0.1

**This packet has not been sent to anyone.** It is a copy-ready
reference for the Hub/Steward to use manually. This lane has no
mechanism to deliver it.

## Important: do not duplicate — a real one already exists

A real, already-filed execution dispatch for this exact pilot already
exists in Working Memory:

- File: `CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`
- SHA-256: `cc8fe34620bc51a634639fc5a34ced35ba543c8174ef4ec5ea1074b1930e2b0b`
- Location: `05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`

That file, not a fresh one authored by this lane, is the payload that
should be pasted into the Codex thread. Producing a second, independently
worded dispatch here would risk drifting from the one the real N8N
workflow's fixed contract was actually built and statically tested
against (`D007_WM_TO_CODEX_TRANSPORT_STATIC_TEST_REPORT_v0.1.md`). This
packet restates its destination/timing/payload/return/filing/boundary
fields for completeness of this readiness return only — it is a
pointer, not a replacement.

## Destination

Existing authorised Codex Stream A execution thread — the same thread
that produced the earlier reported verdict
`TRANSPORT_CANDIDATE_COMPLETE_LIVE_MOUNT_HELD`. To be selected and
opened manually by the Hub or Steward. This lane cannot identify or
open that thread.

## Timing

Only after: (a) the credential `H1-CGPT-N8N-Inbound-Auth` is confirmed
present in that Codex runtime's own environment, and (b) the pilot
manifest has not expired — check `expires_at` in
`D007_WM_TO_CODEX_TRANSPORT_MANIFEST_v0.1.json` against current time
before sending. As of this reading (`2026-08-02T01:32:08Z` /
`2026-08-02T11:32:08+10:00`), the manifest's stated expiry is
`2026-08-02T14:00:00+10:00` — still open, but this fact will go stale;
re-check before use rather than trusting this line.

## Payload

The unmodified body of `CODEX_TARGET_PREFLIGHT_AND_LIVE_MOUNT_DISPATCH_v0.1.md`
(endpoint, fixed request JSON, authentication rule, required target
controls, required receipt fields, required outputs, and the three
allowed terminal verdicts — all already real values, since none of
them are secrets; only the credential value itself is withheld, by the
dispatch's own design, not by this lane's addition).

## Expected return

One of exactly three terminal verdicts, plus (on `TARGET_MOUNT_PASS_LIVE_GRAPH_COMPLETE`)
the full required output set: `TARGET_MOUNT_RECEIPT_RUN-WM-CODEX-A-20260802-01.json`,
`D007_WM_TO_CODEX_TRANSPORT_PILOT_TARGET_RETURN_v0.1.md`,
`LANE_A_CODEX_RUNTIME_REALITY_AND_INTEGRATION_GRAPH_RETURN_v0.3.md`,
`NAVIGATOR_INTEGRATION_OBJECTS_v0.3.json`,
`NAVIGATOR_INTEGRATION_RELATIONSHIPS_v0.3.json`,
`NAVIGATOR_INTEGRATION_GAPS_v0.3.md`, schemas, deterministic build
script, tests, and a final manifest with filenames/bytes/SHA-256 — as
specified in the source dispatch itself.

## Filing

`05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/WAVE_INTEGRATED_NAVIGATOR_MVP_20260802/D007_WM_TO_CODEX_TRANSPORT_PILOT_v0.1/`
(the same folder this readiness package files into).

## Boundary

No credential disclosure, no infrastructure mutation beyond the one
already-authorised pilot attempt, no N8N activation beyond what D007
already activated, no Odoo change, no PPV movement, no fabricated
acknowledgement of delivery or execution by this lane.
