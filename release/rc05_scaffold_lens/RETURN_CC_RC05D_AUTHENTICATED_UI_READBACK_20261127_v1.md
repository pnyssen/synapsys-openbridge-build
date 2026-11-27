# RETURN: Claude Code, RC05d authenticated UI verification and hash-bound readback (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: OBSERVED on dev V20 (desktop, Steward session as login admin). Not D007 release, not D009 finding, not Steward acceptance, no PPV or canon movement.

## Inputs consumed (fresh reads)
- Hub record MESH_QUEUE/HEALTH/REVIEWS_APPEND_20261127_STEWARD_ODOO20_ESTABLISHMENT_APPROVAL_v1.md: exists, 3,925 B, sha256 89e2162259e7f8fadf60b2d295e6c1a9d4b4f1e4724b11cbdca14f7d533edad2 as computed by the byte-preserving read tool (matches the cited value). Its content was read; it records the Steward's programme direction narrowly: no release, no D009 finding, protected writes still need the D007 pipeline, no authorisation for portal-right changes, production migration, credentials or PPV/canon movement. This return does not restart source installation or ask for repeat Steward permission.
- RC05d receipt RECEIPT_CC_RC05D_DEV_INSTALL_20261127_v1.md (sha256 5e0b28cb412d5b57eb55faad2ddd1b67fbabc886c5d56ec69e51581991ba4638), filed by Claude Code.
- Steward screenshots after hard reload (4), read by Claude Code. The Steward zoomed the browser out to fit one capture, which explains the reduced layout and the off-centre column in the Enhance and Enrich captures (D15 explained by zoom; not a layout fault found).

## Observed (RC05d installed; tree 5422298f65c9e0654c4248d93a3d7b277c5b43993cab797ce1cb77242f942ef6 per install receipt)
1. Lenses level 1: the "Context scaffold (read-only)" card now sits at normal spacing under the footnote. D13 FIXED (observed).
2. Scaffold view, Enable: headline only. Enhance: seven H.CTX roles; Capability PROPOSAL with "NO OPERATING SOURCE: HOLD"; Service RULED with "CATALOGUE RECORD FOUND".
3. Enrich, Service peer: Operating source "CATALOGUE RECORD FOUND"; Qualification list "catalogue record only: existence is not operation", "validation: none recorded", "no source document recorded", "not bound to a Context"; Evidence "SP-01 Strategic Planning & Context Establishment (608938cd399e)". Capability: HOLD, evidence none, open questions, definition source. Provenance block present. The footer states presentation only.
4. The evidence hash prefix 608938cd399e shown by the live page equals the first 12 characters of the pinned value 608938cd399ef7b5694658dc6e34db063f9317d950439de537be0f5d663fe17c, which Claude Code had computed offline from values read through the connector. So the Steward login can read x_service_catalogue, the record is unchanged since the pin, and the offline canonical hash agrees with the runtime computation.
5. Open-question lists (Enrich) show bullets with left-aligned text: D14 FIXED.

## Verification items requested by the Hub
| Item | Result |
|---|---|
| Service SP-01 with the four qualifiers | OBSERVED, pass |
| Capability HOLD | OBSERVED, pass |
| Lenses spacing | OBSERVED, pass |
| 390 px and 1024 px layouts | NOT TESTED (Steward captured at a zoomed-out desktop width; no device-toolbar test) |
| Collaborator / role-specific negative tests | NOT TESTED: V20 has only two active users, admin (Steward group) and the read-only connector account jq003 (Collaborator group, no web password held by anyone in this lane). No Collaborator or portal login exists and none was created (cost and rights). Offline tests cover the role logic (66 pass); no runtime proof. |
| D16 depth bar inert on Lenses list screens, level label clash | OPEN, needs a Steward ruling |
| D6 /synapsys/lenses/data open to any logged-in user | OPEN, unchanged by RC05 |

## Gate disposition
D007: no exact release is claimed for RC05 to RC05d; the installs were dev fast-path steps on the Steward's chat words with pinned prestate/poststate hashes, backups and tested rollback (the Hub record keeps D007 for any protected write). D009: no independent challenge was requested or performed; it is required before production, access/security, canon/PPV or cutover acceptance. Module upgrade: none performed (synapsys 20.0.2.4.9, synapsys_mesh 20.0.0.7.0, write_date 2026-11-25 14:43:36, re-read). Portal and anonymous rights: unchanged and not served by the new routes (Option A). SSH key to the VPS: removed (API listing empty).

## Defects now
Open: D15 (explained, retest pending only if the Steward wants the width checks), D16, D6; label clash D9; touch-target and level-address defects from the RC04 returns for other lens levels are unchanged. Fixed and observed: D13, D14.

## ONE NEXT
Steward chooses the next bounded step: (a) device-toolbar captures at 390 and 1024 px for the scaffold view, (b) a ruling on D16 (what depth means on Lenses list screens), (c) reconcile the V19 SC-04 and GV-NAV-002 Method records into V20 (a D001/D007 task: they are not in the V20 Service Catalogue), or (d) stop here with the desktop slice observed and unaccepted.
