# RETURN: RC06b batch 1, noun declarations for the 15 RULED nouns, source-only candidate (claude_code), 27 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | CANDIDATE | NON_AUTHORISING
Contract: BUILD_CONTRACT_ENABLE_NOUN_DECLARATIONS_BATCH1_RC06B_20261127_v1.md, sha256 c66ec9910b6b862295c84fa4ecf98a0e044daee3240ffb65814c5d91a2e823eb (read via sp_read_bytes, hash matched).
Evidence state: offline tests run and passing; live tests: none. Authority: none conferred. Implementation: source built, NOT installed. PPV: no movement. Filed status: new file only.

## Consumed base state and hash (verified before any change or push)
- Branch claude/synapsys-v20-release-service-tvjpyn, HEAD e423bb1 (RC06a), equal to origin; no later commit existed.
- Addon tree release/rc06a_screen_architecture/addon/synapsys: 58 files, tree hash f53ea79ea501cf63feae758bdcc0efbaa0994cc2136acb287eb6af84435beb5f with rc04g_baseline_hash_20261126_v3.sh. EQUAL to the contract's value. Working tree was clean.
- RC06a was extended, not rebuilt. The RC06a declaration file and screen_render.py are byte-identical to e423bb1 (checked by cmp).

## What was built (D1 to D6)
- D1: 15 noun-screen declarations (Strategy, Portfolio, Offering, Shape, Domain, Canonical, Programme, Project, Service, Workflow, Outcome, Benefit, Asset, Fractal, Mesh) on schema synapsys.screen.declaration/1, in a SIBLING file data/screen_declarations_batch1.json. Why a sibling and not the RC06a file: Context's Technical details prints a fingerprint of its declaring file, so adding 15 screens to that file would change Context's output; the contract requires Context to stay byte-identical. Every screen is screen_type noun, no stage, verbs empty (HOLD).
- Content rule applied to every noun: answer, status, definition source and open questions are read from the registry 0.3.5 element; the one trust-table row is bound to source chips whose quote exists in the registry text (RC06a D3 rule: dropped and noted otherwise); no date is written that is not in the registry text.
- D2 (minimal changes, reported): the validator and loader gained (a) multi-file loading with a per-screen fingerprint (each screen reports the sha256 of the file that declares it; a screen id declared twice is refused), (b) validation of an optional serves list (for Mesh), and the wire gained scaffold_noun(env, screen_id, depth), a read-only entry for any declared noun screen (rights as the caller; no route, no menu). screen_render.py is unchanged. No real gap in the renderer appeared.
- Mesh: one declaration, SCR.MESH.NOUN, with serves = Registry, Elements, Clusters, Verbs (informational only; no binding made). Verbs empty: HOLD, "verbs not yet bound".
- Generator: tools/gen_batch1_declarations.py writes the declaration file and refuses a chip whose quote or date is not in the registry text; a test proves the committed file equals its output byte for byte.

## Diff and file list
Patch against the RC06a tree: RC06b_batch1_noun_declarations_vs_RC06a.patch, sha256 de9d52fb0195a978b846f5d5ef1e494208a78974a4cb9410a84d004b96acaa57 (apply with cd /opt/odoo20/addons && patch -p1). Applied and reversed offline on a clean RC06a tree: forward 936d365b..., reverse f53ea79e....
| File (under addon/synapsys) | Expected | Actual | sha256 |
|---|---|---|---|
| data/screen_declarations_batch1.json | new | new | 2e278bc8c73f1bd20ddcd0c5549a40c037c1749f37f7a680b26047c7593290ff |
| screen_decl.py | changed | changed | abfb878957f8458a5a78ce1a1c58dc2012b078941843871e9eb1426c19faa39e |
| scaffold_wire.py | changed | changed | 2af9a7813ab50acd5340b07a1d77d55d5bb9bc19a9f3b3f1c7019d7366f4b8ed |
| the other 56 files | unchanged | unchanged | n/a |
New tree: 59 files, tree hash **936d365b0b11f3d80ce96de96048d65ec5039dda741e288d684790ca215c6c0d** (the repo's tree-hash method). Not installed anywhere. Outside the addon: tools/ (generator, D6 report, golden generator), tests/test_batch1.py, tests/fakes_core.py, golden files for Context, the offline log.

## Offline tests run versus live tests not run
Run: 96 tests, all pass (log tests/TEST_LOG_rc06b_batch1_offline.txt, sha256 29ff3aaafa9ae347fb8704704a936a5339f61ed5803822488078c968b249ace7): 63 test_screen_arch (RC06a, unchanged except that the all-declarations list now includes the 15 nouns, so acceptance checks 1 to 17 run over all 18 declarations) + 3 test_ui_script + 30 new test_batch1. The RC06a tests that enumerated "the three declarations" were widened (a set-equality became a subset check); no assertion was weakened.
New tests: per-noun provenance (each chip quote and date found in the registry text; none dropped on the real registry; a missing quote drops and notes the chip for every noun); status (read from the registry for RULED, PROPOSAL, OPEN and absent, for all 15; RULED never shown unless the registry says so); Context byte-identity against golden HTML and route JSON generated from e423bb1; Mesh shared declaration; sibling-file loader; no peers invented; made-of derivation re-computed independently of the generator; wire read-only for all 15 nouns at 3 depths.
Mutation sanity (6 new faults, each made tests fail): a changed chip quote (6 failures), status hardcoded RULED (1), an invented chip date (1), a verb bound on Mesh (3), a peer invented for Service (3), the RC06a Context file edited (3).
NOT run: any live test, any install, any browser render, the Odoo TransactionCase file from RC06a, the UI script against dev. Real-size layout (check 10) remains UNOBSERVED.

## D6: per noun (all 15 are RULED in the registry; no chip was dropped on the real registry, because every quote exists)
| Noun | Registry status | Chips kept | Chips dropped | Open questions | made_of (registry relationship) | Sections that read "None recorded" or say nothing is declared |
|---|---|---|---|---|---|---|
| Strategy | RULED | 3 of 3 | 0 | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Portfolio | RULED | 4 of 4 | 0 | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Offering | RULED | 4 of 4 | 0 | 2 | H.OFR | Linked peers: none declared |
| Shape | RULED | 4 of 4 | 0 | 3 | none | Made of: no roles declared; Linked peers: none declared |
| Domain | RULED | 4 of 4 | 0 | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Canonical | RULED | 4 of 4 | 0 | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Programme | RULED | 3 of 3 | 0 | 2 | H.PRG | Linked peers: none declared |
| Project | RULED | 4 of 4 | 0 | 1 | none | Made of: no roles declared; Linked peers: none declared |
| Service | RULED | 4 of 4 | 0 | 2 | H.SVC | Linked peers: none declared |
| Workflow | RULED | 5 of 5 | 0 | 2 | none | Made of: no roles declared; Linked peers: none declared |
| Outcome | RULED | 7 of 7 | 0 | 0 | H.OUT | Linked peers: none declared; Open questions: none recorded |
| Benefit | RULED | 4 of 4 | 0 | 1 | H.BEN | Linked peers: none declared |
| Asset | RULED | 4 of 4 | 0 | 3 | H.AST | Linked peers: none declared |
| Fractal | RULED | 4 of 4 | 0 | 1 | H.FRC | Linked peers: none declared |
| Mesh | RULED | 4 of 4 | 0 | 4 | none | Made of: no roles declared; Linked peers: none declared |
Chips are a subset of each noun's registry citations: only citations I could tie to a quote are chipped; other segments (for example the dates inside a parenthesis such as "confirms 19 Nov 13:34, 13:39" for Strategy) stay in the full citation, which is shown in full on request.

## Findings and choices to review (mine, not rulings)
1. Made of is declared for 7 of 15 nouns: Offering H.OFR, Programme H.PRG, Service H.SVC, Outcome H.OUT, Benefit H.BEN, Asset H.AST, Fractal H.FRC. Rule (checked by test): the registry relationship in which the noun is the named subject of a REQUIRED role. Left null: Portfolio (subject in two, H.AST and H.PRG) and Domain (two, H.GOV and H.SVC), because choosing one would be my decision; Shape, because its only relationship H.KIN binds the 27 verbs, and verb binding is its own gate; Strategy, Canonical, Project, Workflow, Mesh, because no registry relationship names them a required subject. Those screens say "No roles are declared for this screen." Enhance is therefore thin for 8 of 15 nouns. Declaring a chosen relationship for Portfolio, Domain, Workflow and others is a Steward decision.
2. No peers are declared for any of the 15: the registry holds no peer list for them, and Context's peers (Capability, Service) came from the RC05 scaffold, not from the registry. Enhance says "No linked peers are declared for this screen."
3. Date handling. Where the registry text gives only a time after a dated ledger entry (Service "10:51", Fractal "07:10" and "07:16", Mesh "06:40" and "06:49"), the chip shows the time as read ("Ledger 10:51"); no date is inherited. RC06a's Context declaration, unchanged, shows its Service peer chip as "20 Nov 10:51" (inherited from the Claude Doc specimen). The two now differ for the same fact. Not changed here; Context is frozen by the contract.
4. Chip short names ("Ledger", "Project instr. v2.2.2", "design_d.json", "Steward ruling", "Registry PART Offering/Platform" and so on) are authored by me, each tied to a registry quote. The Steward may rename them.
5. Mesh serves is informational; menu binding and routes are out of scope, so nothing yet maps the Registry, Elements, Clusters and Verbs screens to this declaration.
6. The wire still reads the SP-01 catalogue record for every screen, including noun screens that declare no peer (existing RC05 behaviour, unchanged). It is not shown on those screens (tested) but it is a needless read.
7. Open questions are shown as the registry holds them; Outcome has none ("none recorded"). Several registry open questions bear on rulings the screens cannot make (for example home domain for most nouns); the screens only report them.

## Rights and gaps
Rights: reads only, as the caller (no sudo, no writes, no raw SQL; the existing source scan test still passes). Nothing written to dev or V20. Registry 0.3.5 unchanged (sha 7c31aa1d...). Out of scope and not touched: menu binding, routes, install, registry release, verb binding, PROPOSAL/OPEN nouns, project-document and action screens.
Gaps: never rendered in a browser; no live run; the patch assumes the installed tree equals the RC06a tree hash above (RC06a itself is not installed).

## Dissent
None against the rulings. One observation: with no peers and mostly no Made of, the Enhance depth for these nouns adds almost nothing to Enable, which is faithful to the registry but weakens the one-question-per-depth ladder until the Steward rules which relationships Enhance should show.

## Delivered versus Realised
Delivered: 15 declarations, minimal loader and wire changes, 96 passing offline tests, patch and hashes, this return. Realised: UNOBSERVED until the Steward accepts on dev; nothing is installed.

## Release path (not authorised here)
Needs a fresh Steward word and the dev fast path (backup, verified transfer, upgrade, restart, read-back, rollback patch recorded). RC06a and RC06b would install together, since RC06b is built on the uninstalled RC06a tree; reversing both patches restores RC05e (15c37960...).

## ONE NEXT
Owner: Steward. Rule on finding 1 (which relationship, if any, Enhance should show for Portfolio, Domain, Workflow, Strategy, Canonical, Project, Shape and Mesh), then say whether RC06a plus RC06b go to the dev fast path or batch 2 (PROPOSAL/OPEN nouns) is built first.
