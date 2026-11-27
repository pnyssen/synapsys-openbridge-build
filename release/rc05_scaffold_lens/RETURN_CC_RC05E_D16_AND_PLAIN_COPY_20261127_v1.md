# RETURN: Claude Code, RC05e D16 ruling applied and plain-language copy (source-ready delta)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | 27 Nov 2026 | Status: CANDIDATE, SOURCE-READY, NOT INSTALLED. Not D007, not D009, not Steward acceptance.

## Steward words received (chat, 27 Nov 2026; not a filed decision or D007 release)
"approve D16 as proposed", the proposal in RETURN_CC_V19_V20_CATALOGUE_RECONCILIATION_AND_D16_PROPOSAL_20261127_v1.md (sha256 8e74415f...): (1) Depth applies to element views only; (2) Lenses list screens (levels 1 and 2) do not change with depth, by design; (3) the level line states position only, no stage word; (4) list screens carry one plain line, "Depth applies when you open a lens or element."

## Delta (RC05e_D16_and_plain_copy_vs_RC05d_installed.patch.txt, 6,496 B, sha256 dd5cd95350e2e555592dc7bfb671860ba36d6f6e117cb781276a11e8ec3add7d)
Two files, restart only, no model, ACL, schema, manifest or lens_render.py change: controllers/lenses.py (removes the stage word from the level line using the exact formats read from the live lens_render.crumb(); adds the one list-screen note for every role; the Steward-only scaffold card is unchanged) and scaffold_view.py (plain role names such as "Rights holder", "Intersecting chains", "Portfolios", "Strategies", "The Context itself", "one or more" instead of registry codes; heading "What a Context is made of"; evidence line shows the record's name only; a collapsed "Technical details" area at Enrich holds the registry fingerprint, the H.CTX cluster and the evidence source with its fingerprint). Quoted source text (definition sources, open questions) is shown verbatim and may still contain codes; authored copy is plain.
Pinned: prestate tree hash 5422298f65c9e0654c4248d93a3d7b277c5b43993cab797ce1cb77242f942ef6 (the RC05d state); expected poststate tree hash 15c37960d1707be2be9b1dbdf18e623d82c97f78f1b009e02af34e46a5837e4b (54 files, computed offline). Dry run and apply verified on a reconstruction of the RC05d tree.

## Tests (offline, no Odoo): 73/73 pass
18 core, 17 wiring, 30 UI/JS/controller (new: level line has no stage word at all three levels and keeps "of 3"; unrelated "Enable, Enhance, Enrich" text untouched; note present on levels 1 and 2 for Steward and non-Steward and absent at level 3; the crumb rule leaves unexpected HTML alone; plain role names; Technical details labelled and holding the codes; none below Enrich) and 8 install-script. Mutation controls fail as intended: crumb rule removed, note removed, note on every level, rule not anchored to the level line, raw role labels, hash in ordinary copy.

## NOT established
Nothing ran in Odoo or a browser. The crumb rule relies on the exact formats of the live lens_render.crumb() (read byte-exact from the box); if that file changes, the rule leaves the line unchanged (fail-safe, tested) and D16 (3) would silently not apply, so a re-read is needed after any lens_render change. 390/1024 px not tested (Steward set aside). Collaborator and portal behaviour unchanged (Option A). D6 open. The depth precedence (element default, Context allocation, Client choice) is still not built (depth remains browser-local).

## ONE NEXT
Steward runs the pinned one-command install (supplied in chat), then two screenshots as admin: Lenses level 1 and level 2, and the scaffold view at Enrich with the Technical details area open.
