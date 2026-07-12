# AGENTS.md — synapsys-openbridge-build

This file follows the open [AGENTS.md](https://agents.md) convention so any
compliant tool (Claude Code, Codex, Cursor, Gemini CLI, etc.) reads the same
role definitions. It defines **who is responsible for what** once this repo
has real application code in it. As of this writing the repo has no
application code — this file sets the structure in advance so roles are
clear from the first PR rather than invented ad hoc later.

Modeled on the specialist-role pattern from
[garrytan/gstack](https://github.com/garrytan/gstack) (verified: 121k★, MIT,
active) — narrow, named roles instead of one generalist agent, each with a
scoped responsibility and a way to check whether it did its job. Unlike the
ecosystem framing in `CLAUDE.md`, nothing here depends on another agent's
unverifiable say-so: every role's output is a real, checkable git artifact
(a review comment, a passing check, a merged PR) in *this* repository.

## Roles

| Role | Responsible for | Invoked at |
|---|---|---|
| **Eng Manager** | Architecture review before implementation: data flow, edge cases, test plan. Blocks work that hasn't been thought through, not work that's merely imperfect. | Before a nontrivial change starts |
| **Code Reviewer** | Pre-merge review of the diff: correctness bugs, reuse/simplification, obvious security issues (OWASP-class). Uses this repo's `/code-review` skill. | Every PR, before merge |
| **QA Lead** | Exercises the actual change end-to-end (not just tests passing) before it's called done. Uses this repo's `/verify` skill. | Before marking work complete |
| **Security Officer** | Enforces the boundaries already set in `CLAUDE.md`'s GitHub Change Control Rule — CR required before default-branch merges, workflow-file edits, or anything touching secrets/deploy config; the "never, no CR" list (access controls, force-push to shared branches, secret exfiltration) is a hard stop, not a review comment. | Any change touching CI/CD, permissions, or the default branch |
| **Release Engineer** | Runs the actual push/PR flow per this repo's git conventions (feature branch → PR → CR if default-branch-bound). No deploy pipeline exists yet; this role owns setting one up correctly when it's needed, not before. | Landing a change |
| **Doc Engineer** | Keeps `README`/`AGENTS.md`/`CLAUDE.md` in sync with what the code actually does. Deletes stale docs rather than layering corrections on top. | When behavior changes |

## Conventions

- No build/test/lint commands exist yet because there is no application
  code. The first PR that adds real code should also add this section with
  the actual commands — don't leave it aspirational.
- Git flow: feature branches, PRs into the default branch, no direct pushes
  to default (see `CLAUDE.md` § GitHub Change Control Rule).
- Roles above are responsibilities, not separate people or bots to invoke by
  name — one session can carry all of them. The table exists so a reviewer
  (human or AI) can check "did architecture get reviewed, did QA actually
  run the thing, was this CR-gated if it needed to be" without relying on
  any party's unverified claim that it happened.
