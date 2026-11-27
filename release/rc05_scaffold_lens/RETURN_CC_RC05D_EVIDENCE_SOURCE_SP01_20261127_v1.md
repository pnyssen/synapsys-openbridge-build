# RETURN: Claude Code, RC05d evidence source for the Service peer (SP-01), source-ready delta
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | 27 Nov 2026 | Status: CANDIDATE, SOURCE-READY, NOT INSTALLED. Not D007, not D009, not Steward-accepted. Basis: Steward's chat word "proceed" after the Navigator's request for "one source-bound library relationship".

## What V20 actually holds (read-only, V20 connector, 27 Nov 2026)
x_service_catalogue has 4 records: GV-GOV-003 (deprecated), GV-GOV-004 (active), SC-10 (active, validation pending, source document and authority reference present), SP-01 "Strategic Planning & Context Establishment" (active, lifecycle active, processability structured, domain D001, NO validation status, NO source document, NOT bound to a Context). SC-04, GV-NAV-002, GV-TEC-001 and SC-05 are NOT in V20 (they exist in V19). So the Navigator's named Methods cannot be bound in V20 today.

## The relationship built (PROPOSED by Claude Code, a name-and-domain inference, not a ruling)
N.SERVICE (peer of N.CONTEXT) is bound to the catalogue record SP-01. The binding table is one dictionary in scaffold_wire.py (EVIDENCE_BINDINGS); the Steward may change it. The record is read with the caller's own rights (one search, limit 1, no sudo). It is pinned by sha256 608938cd399ef7b5694658dc6e34db063f9317d950439de537be0f5d663fe17c over nine of its fields (canonical JSON), computed from the live values; any edit of the record shows as SOURCE_HASH_MISMATCH and the peer returns to HOLD until a patch re-pins it. N.CAPABILITY has no record and stays "NO OPERATING SOURCE: HOLD".
What the screen says: "CATALOGUE RECORD FOUND" plus a Qualification list built from the record: "catalogue record only: existence is not operation", "validation: none recorded", "no source document recorded", "not bound to a Context". It does NOT say the Service operates or is accepted. Unreadable or missing record: HOLD plus a note, never an error.
New evidence scope "catalogue" (global Service Catalogue record, no Context needed) alongside the existing Context-bound evidence, which is unchanged and still fails closed (foreign Context, actor not in Context). Hash and group gates apply to both.
Also in this patch: D13 spacing fix (the link card now sits inside the lens page's own wrapper).

## Delta (RC05d_evidence_sp01_vs_RC05c_installed.patch.txt, 9,541 B, sha256 51d8fc4cc43e0d9def5635e466474bc40fee2a4ec2f10275cc2bd2be01ff3c47)
Four files: scaffold_lens.py, scaffold_wire.py, scaffold_view.py, controllers/lenses.py. No model, ACL, schema, data or manifest change; restart only. Pinned: prestate tree hash f963b951fc1706c25983e1e2bd6fbd39c60b60073dd48edca9dc3d9c9ebb291e (the RC05c state); expected poststate tree hash 5422298f65c9e0654c4248d93a3d7b277c5b43993cab797ce1cb77242f942ef6 (54 files, computed offline). Dry run and apply verified on a reconstruction of the RC05c tree.

## Tests (offline, no Odoo): 66/66 pass
18 core + 17 wiring + 23 UI/JS/controller + 8 install-script. New mutation controls each fail tests: pin check removed (W12), sudo on the catalogue read (W1, W2, W8, W11), catalogue scope removed (S16), Context scope exempted (S7, S10, S17), qualification not shown (V12).

## NOT established
Nothing ran in Odoo: whether the Steward's (and an internal Collaborator's) real rights can read x_service_catalogue (an AccessError would show HOLD plus a note), the live rendering of the new evidence block, the 390/1024 layouts, portal behaviour (Option A: not served). Whether SP-01 is the right record for N.SERVICE is the Steward's or Navigator's call; Claude Code inferred it from the name and domain. SC-04/GV-NAV-002 reconciliation with the V19 definitions is not done here and still needs the V19 records.

## ONE NEXT
Steward confirms or changes the SP-01 binding (one word: keep SP-01, use SC-10, or none), then says "apply RC05d"; Claude Code supplies the one-command install with the pinned hashes. Then one screenshot of the scaffold view at Enrich.
