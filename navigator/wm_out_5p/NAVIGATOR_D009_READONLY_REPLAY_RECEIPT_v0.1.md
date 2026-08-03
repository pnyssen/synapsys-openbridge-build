# NAVIGATOR_D009_READONLY_REPLAY_RECEIPT_v0.1

CONTROL MARKER: CLAUDE-CODE-FIVE-PRIORITY-NESTED-COMPLETION-v0.1
Work Object: WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001
Lane: claude_code · PPV: Potential · Replay-validity: PRESERVED
Date: 2026-08-03 (AEST)

Nature: READ-ONLY replay of the executed state, performed after the RC12
projection reconciliation, from live and filed sources only. No Odoo, N8N
or Stream A execution of any kind occurred. This replay is performed by
the implementing lane; every step below is stated so an independent D009
lane can repeat it verbatim from the same inputs.

## Leg 1 — Odoo (live, read-only)

Fresh search on x_ss_work_object_register where x_work_object_code =
WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001: exactly one record
(id 2), status active, PPV Potential, authority "HELD — D009 PASS WITH
CONDITIONS; D007 CORRECTION ONLY", x_project_id [101], x_service_catalogue_id
[1 SC-01], x_method_id [1 D002-PTF], x_context_id [1 CTX-SS], x_company_id
[1 SynapSys Pty Ltd]. Fresh read of historical pilot id 1: WO-MVP-001,
complete, Potential, held — unchanged.

## Leg 2 — Deployed current surfaces (fresh sp_read after reconciliation)

All reconciled surfaces re-fetched fresh from SharePoint and hash-compared:
navigator v1.5 (45,742 B, e23893fd...), parallel delivery control v1.1
(34,286 B, c74b0d60...), delivery state .json (16,608 B, afc8952b...) and
.js (15,611 B, f35bece8...), priority model (2,821 B, 907530bc...),
parallel streams (8,623 B, ca60860f...) - 100% hash match. Each readback
scanned for 23 stale markers plus a semantic scan for ANY phrasing framing
the D007 correction as not yet executed: ZERO hits on the final pass.
Every D007 reference in stored content reads executed once / receipted /
CONSUMED_EXECUTED_ONCE, with the read-only D009 replay and Steward
acceptance as the only remaining steps.

## Leg 3 — Regression and runtime

36 static tests (including new coherence test 36) and 134 browser
interaction checks PASS on the reconciled build; live Chromium render
verified: no stale priority text can regress the screen (the hardcoded
applyCurrentUiPatch override is removed; the generated DATA state files
are the single runtime source), zero JS errors.

## Result

The deployed Navigator state and the Odoo operational register now say the
same thing everywhere. Remaining for final acceptance: independent D009
replay of this receipt's three legs (all read-only, all inputs filed), and
Steward cold-start acceptance from 00_HOME.md.

Held, unchanged: any further Odoo mutation (packet CONSUMED_EXECUTED_ONCE),
N8N mutation/activation, Stream A replay, Pattern/Asset/canon movement,
Benefit-realisation declaration, PPV movement, bridge Pattern qualification.
