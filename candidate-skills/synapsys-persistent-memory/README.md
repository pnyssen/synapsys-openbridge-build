# synapsys-persistent-memory

**mirrors**: `05_AI_RETURNS_HASHED/20260810_RET_GEN_claude-code-persistent-memory-candidate-skill-receipt_v0.1.md`
(SHA-256 `ad1a4ec7d1e3e52d68e4f767082c5568ef871d0709e2614492d32f95686ca47c`). No Obsidian
counterpart exists for this candidate — stated plainly, not assumed.

A candidate two-file persistent-memory core for SynapSys, built by
following Hermes Agent's own architecture directly — `MEMORY.md` (a
system's own durable knowledge) + `USER.md` (context about the person
it works for) — rather than one large blob file. OpenClaw was
deliberately not used as a source here: nothing verified about it this
session showed an equivalent persistent-purpose-file pattern, and
forcing parity would have meant inventing content, not reporting it.

## The mapping

| Hermes | This candidate | Purpose |
|---|---|---|
| `MEMORY.md` | `synapsys.md` | The system's own durable identity: Purpose, operating discipline, the one standing verification rule. Deliberately small — Hermes's own design principle, not a stylistic choice. |
| `USER.md` | `steward.md` | Context about Phil specifically — role, relay constraints, observed preferences. Not authority; corrected in place when wrong. |
| Pluggable deep storage | Working Memory (`11_WORKING_MEMORY/`, SharePoint) | Already exists, unchanged. Everything too detailed or too changeable for the small core files lives there, same as it already does. |
| Staged memory writes (propose, then approve) | Same rule, applied here | Neither `synapsys.md` nor `steward.md` gets edited silently. Every change is a proposed diff — same discipline as every PPV-gated filing this session, not a new invention. |

## Why two files, not one

Hermes keeps `MEMORY.md` and `USER.md` separate on purpose: system
identity and user context change for different reasons, at different
rates, under different authority. Collapsing them into one file would
make every future edit ambiguous about which kind of change it is —
exactly the kind of role/authority collapse this ecosystem's own
governance discipline already flags as a failure mode elsewhere.

## Validation

`validate_memory_files.py` checks both files for required section
headers and rejects any line asserting authority the file doesn't
have (e.g. `steward.md` claiming something as decided rather than
observed). Run: `python3 validate_memory_files.py` (validates the
SynapSys instance by default) or
`python3 validate_memory_files.py <identity.md> <role.md>` to validate
any other pair by path.

## The portable core (`template/`)

Checked this session, not assumed: the validator's own logic was
already generic before this addition — it checks for three named
section headers ("Purpose", "Operating discipline", "Standing rule")
and generic English authority-assertion words, with no SynapSys-specific
string anywhere in the checking logic itself. The only thing tying it
to SynapSys was the CLI hardcoding `synapsys.md`/`steward.md` by
filename — now fixed (`validate_pair(identity_path, role_path)` takes
any two paths).

`template/PRINCIPAL_IDENTITY_TEMPLATE.md` and
`template/PRINCIPAL_ROLE_TEMPLATE.md` extract the pattern itself —
raw, `<angle-bracket>`-placeholder versions of `synapsys.md`/
`steward.md` for a collaborator to instantiate their own pair from.
`template/example/` is a **worked, filled-in example** (a fictional
"Example Collaborator Co", deliberately using different maturity/
evidence-ladder wording than SynapSys's own FORM/FLOW/EVOLVE) that
passes the exact same, unmodified `validate_memory_files.py` — that's
the actual proof the pattern is portable, not just a claim of it. See
`tests/test_validate_memory_files.py::test_worked_example_proves_pattern_is_portable`.

**What this is not yet**: a deployment mechanism. Nothing here answers
how a collaborator would actually receive and run this (a template
repo they fork, a packaged skill, a hosted service) — that question is
still open, not addressed by this candidate.

## What this is not

Not installed. Not auto-loaded — Claude Code only auto-reads
`CLAUDE.md` at session start; a file sitting in this folder does not
get read automatically. It becomes load-bearing only if (a) merged
into `CLAUDE.md` itself, which needs Phil's explicit sign-off given
this repo's own past practice on CLAUDE.md changes, or (b) referenced
by a skill that does get invoked — see the cross-reference in
`candidate-skills/synapsys-tobe-realignment/README.md`, which now
points here.

## Status

CANDIDATE — filed per direct Phil instruction this session, structure
confirmed before content was written. Not adopted.
