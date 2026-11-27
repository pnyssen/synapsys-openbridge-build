# RETURN: Claude Code, V19 to V20 Service Catalogue reconciliation (SC-04, GV-NAV-002), GV-NAV-002 conformance review of the scaffold view, and a proposed D16 ruling (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: CANDIDATE, read-only analysis and a candidate load packet. Nothing written to V19, V20, canon or the Service Catalogue. Not D007, not D009, not Steward ruling. The Steward directed (chat, 27 Nov): reconcile the V19 records, get a ruling on D16, ignore the width checks.

## 1. What the two catalogues hold (read-only connector reads, 27 Nov 2026)
V19: 34 x_service_catalogue records. V20: 4 (GV-GOV-003 deprecated, GV-GOV-004, SC-10, SP-01). SP-01 and SC-10 are identical in both (SP-01 has no validation, no source document, no authority reference in either; SC-10 validation pending in both). SC-04, GV-NAV-002, GV-TEC-001 and SC-05 exist only in V19.
| Code | V19 state | Provenance in the record | Fit to the scaffold |
|---|---|---|---|
| SC-04 Capability Encoding and Reuse | active, validated 2026-09-19, executable, bound to CTX-SS, domain D002, offering layer C, linked Method D002-WRB | source "ESA v1.0 + SDF Pack v3.1", authority "D001 adoption of ESA Service Catalogue v1.0 (26 March 2026)" | The Service that encodes and reuses capability: the right neighbour of the Capability peer; a validated Service record for the Service peer. Record says collaborator AI access HIDDEN, scope internal_only. |
| GV-NAV-002 Common Interface Design Governance Service | active, validated 2026-10-05, structured, domain D010, class membrane | source Obsidian generic reference architecture v1.1; authority D001 adoption + D007 release (CHG-2027-018) | Governs interface surfaces such as the Lenses screens. A governing Service, not a peer of Context. |
| GV-TEC-001 Recursive Claude Code Technology Enablement Service | active, validated 2026-07-18, Method role, domain D007, CTX-SS | authority: Steward direct decision, CHG-2026-469; no source document | Governs protected Package, Execute, Verify. Not part of the lens. |
| SC-05 Assurance Audit and Learning | active, validated 2026-10-05, structured, domain D009 | same ESA source | Assurance; not part of the lens. |

## 2. Reconciliation result
- Do not register a new Service or Method. The proposed scaffolding Method v0.1 stays unregistered (it also wrongly derives depth from K-kind alone; the ruled precedence is element default, then Context allocation, then Client choice, not implemented in RC05, where depth is a browser-local setting).
- The scaffold lens is a surface governed by GV-NAV-002; capability intake and reuse belong to SC-04; protected package/execute/verify to GV-TEC-001; assurance to SC-05. This matches the Navigator's service-selection candidates.
- Candidate load packet (scalar and text fields only, relations by name, no V19 ids): V19_TO_V20_CATALOGUE_LOAD_PACKET_CANDIDATE_20261127_v1.json, 75,977 B, sha256 1431258bc5609c8eca4e92daf337d7be155cfbe3f1643bec70811a529cc82b6d; per-record field hashes SC-04 a9192ed97d9ef294..., GV-NAV-002 237c113559677b13... (first 16). NOT loaded; loading is a protected write for the D007 route.
- Blockers found for any load: V20 has no Context records readable (x_ss_context_master 0, V19 has 42), no Methods (x_ss_method_registry 0), no Patterns (0), 2 canonical library records. SC-04's Context, Method, pattern, benefit and library links therefore cannot be set in V20 yet. V19 numeric ids must never be copied: V19 user 5 is Phil Nyssen while V20 user 5 is the read-only connector account.
- Whether V19's "validated" status carries into V20 is a D001/D007 decision, not assumed.

## 3. Proposed follow-on for the evidence binding (not built, needs the load first)
After a D007-controlled load of SC-04: bind the Service peer to SC-04 in place of SP-01 (SP-01 is weak in both systems: no validation or source). The Capability peer stays HOLD (the registry says Capability has no V20 model; SC-04 is a Service about capability, not a Capability record). GV-NAV-002 would be shown as the Service governing the screen. Each is a one-table change plus a re-pin, tested the same way.

## 4. GV-NAV-002 conformance review of the RC05 scaffold view (its own acceptance contract, observed on desktop only)
PASS: states object category and status; claims relationships only where the live registry or record holds them; does not present a catalogue record as qualified or operating; presentation-only; no new competing model; reads with the caller's rights.
GAP (copy): role labels are raw registry codes ("rights_holder", "intersects+", "portfolio+"), the heading says "H.CTX", and the evidence line shows a hash prefix in ordinary copy. The contract wants plain language, internal names kept out of ordinary copy, human names primary with codes secondary, and technical details in a labelled area.
PARTIAL: first contact should show only two or three decision-useful relationships; Enhance shows seven roles. Mobile rendering not reviewed (the Steward set 390/1024 aside).
PROCESS GAP: the contract expects an input contract (Context, Work Object, Goal Anchor, acceptance criteria) and a return against its acceptance schema; RC05 to RC05d ran as dev fast-path steps without a GV-NAV-002 invocation record. Production UI mutation requires D007 under the same contract. Suggested: a retrospective GV-NAV-002 record for the Lenses surface by the Hub or D007.

## 5. Proposed D16 ruling (for the Steward to confirm; Claude Code recommends it)
Problem: the Depth bar does nothing on Lenses levels 1 and 2, and the level line shows a fixed stage word (Enable, Enhance, Enrich) that contradicts the bar.
Proposed ruling: (1) Depth applies to element views only: the scaffold, Architecture map and lens element detail. (2) Lenses list screens (levels 1 and 2) do not change with depth, by design. (3) The level line states position only ("Level 2 of 3 . Architecture, Lenses / The lens pattern"), with no stage word. (4) List screens carry one plain line: "Depth applies when you open a lens or element." The ruled precedence for who sets depth (element default, Context allocation, Client choice) is unchanged and not built here.
Alternative considered and not recommended: making list screens vary with depth (density), which invents content the sources do not define.
Implementation after confirmation: change the crumb and add the one-line note in lens_render.py (live, byte-exact copy already read from the box, sha256 70b4c9e9c76862a629d37f769520e2f1f6af9fecee54aa6f15a886dd8f57334f), with the copy fixes from section 4 (plain role names, hash moved to a labelled technical line), tests, pinned patch and the same one-command install.

## ONE NEXT
Steward: reply "approve D16 as proposed" (or amend it). Hub/D007: take the load packet and the retrospective GV-NAV-002 record as their own work. Claude Code then builds RC05e (D16 and the copy fixes).
