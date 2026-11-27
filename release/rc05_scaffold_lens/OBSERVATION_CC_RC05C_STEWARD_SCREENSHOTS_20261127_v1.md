# OBSERVATION: RC05c on dev V20, Steward screenshots after hard reload (27 Nov 2026)
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: OBSERVED (desktop, Steward session). Not D007, not D009, not Steward acceptance. Four screenshots read by Claude Code; installed state per RECEIPT_CC_RC05C_DEV_INSTALL_20261127_v1.md (sha256 0d1c3bfa...).

## Observed
1. Lenses level 1: the "Context scaffold (read-only)" card is present. The vertical gap between the lens footnote and the card is STILL large (about 110 screenshot pixels). D13 (spacing) is NOT fixed by RC05c: the gap comes from the lens page's own wrapper (bottom padding), not from the card's wrapper.
2. Scaffold view at Enable: headline only; back link present; no errors.
3. Scaffold view at Enhance: roles (required first) and both peers, "NO OPERATING SOURCE: HOLD"; back link; footer states presentation only, registry 0.3.5 candidate.
4. Scaffold view at Enrich: Evidence "none"; Open questions now show bullets with left-aligned text; Definition source; Provenance block. D14 (list alignment) is FIXED as seen.
5. D15 (view sitting in the right half in some screenshots): all screenshots crop the right edge of the window (the SynapSys company and user items are cut off in every capture), so a window wider than the capture would explain an off-centre column. No evidence of a layout fault; not proven either way. 390 px and 1024 px remain NOT TESTED.

## Status
Desktop render of the Context scaffold view: observed working at all three depths. D13 open (cosmetic). D14 closed. D15 probably a capture artefact. D16 (depth bar inert on list screens, label clash) unchanged, needs a Steward ruling. No acceptance claimed.

## ONE NEXT
Steward decides: accept the desktop view as observed (D13 carried, fix rides with the next functional patch), or hold for the spacing fix. Next functional piece: a registered evidence source for the peers.
