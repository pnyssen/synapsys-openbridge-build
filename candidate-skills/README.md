# candidate-skills

Git-tracked candidate code for the `claude_code` lane, per this repo's
own Capability Contract (see `CLAUDE.md`): "candidate code + test suite
for scoped capability gaps... GitHub delivery (branch/commit/PR
create+update — never direct-to-default-branch, never merge)."

## The standing convention (design ratified this session)

Full design: `05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_github-role-in-ecosystem-architecture-design_v0.1.md`
(mirrored to `Obsidian/30_PROJECTIONS/GOVERNANCE_MESH/GITHUB_ROLE_DESIGN_CANDIDATE_v0.1.md`).

Short version: Obsidian is the ecosystem's design authority (Steward
interface and projection — L1/L2/L3 routes, the 81-element×verb matrix,
the DIM/Antifragile Challenge protocol). GitHub is downstream of that —
the versioned implementation surface where an approved design becomes
tested, executable, reviewable code. Nothing here is a design authority
in its own right.

**Every candidate in this folder must declare a `mirrors` pointer** in
its README — either to the Working Memory receipt that records its
existence (required, no exceptions) or, where one exists, the Obsidian
design it implements. A candidate with no Obsidian counterpart says so
plainly rather than implying a link that isn't there. `check_mirrors.py`
enforces this structurally, not just by convention.

## What's here

| Candidate | Mirrors | Status |
|---|---|---|
| `synapsys-service-catalogue-pilot` | Pre-existing, predates this design — see its own README for authorisation basis | CANDIDATE_CODE_AUTHORISED |
| `synapsys-tobe-realignment` | `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-tobe-realignment-candidate-skill-receipt_v0.1.md` | CANDIDATE |
| `synapsys-persistent-memory` | `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-persistent-memory-candidate-skill-receipt_v0.1.md` | CANDIDATE |

## What this is not

Not an installed skill set. Nothing here is auto-loaded by any session
— see each candidate's own README for how it's meant to be used.
Promotion out of `candidate-skills/` (into a standing skill, or merged
to `main`) is a Steward decision, not something any lane here grants
itself.
