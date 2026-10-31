# synapsys-github-bridge

Candidate, dry run only. Implements the buildable slice of CAP-009 (capability and
learning scan) and CAP-010 (GitHub card mirror) from PKT-20261031-AVL-004.

**mirrors**: `MESH_QUEUE/STREAMS/DRAFTS/CAP-010-github-card-mirror--v0-1.json`

The Working Memory receipt for *this code* is **not yet filed** (the filing route was
unavailable when it was built). The pointer above is the candidate card it implements
(sha256 `2da63cd85db59deb7d49a90c2574c73d078eb4ac8d2731053aee23df3773ffd5`, recomputed equal
2026-10-31). CAP-009 is `345abbe494050698181efa0d30d86eb1ee285e1035de4a0c1a888ca0ae647510`.
No Obsidian design counterpart is known.

## Rules it keeps
Working Memory is the record; Odoo is operational truth; GitHub is a technical copy.
PPV is always Potential and authority HELD. No Odoo, N8N, canon, registry or PPV change.
No credential in the repo. The write path is absent: `--commit` is refused and
`mirror.execute` raises until a Steward ACCEPT, the release class and a token exist.

## What is here
| Module | Job |
|---|---|
| `cards.py` | LRN profile enums, signal -> card normaliser, delete / merge / cap, validator. `standard_refs` come only from ids present verbatim in the signal, always `checked_on` "[n]". |
| `inbound.py` | Signals from a recorded payload, or live GET with `GITHUB_TOKEN` (stops with NEEDS YOU if unset). Live path is not covered by tests. |
| `labels.py` | `kind:` `category:` `scope:` `ppv:` `nist:` labels; mirror only tooling, schema_field, security. |
| `mirror.py` | Issue payload (links WM path + sha256), label set, canary and rollback plan. No write. |
| `scan.py` | Scores a lane's call log against P1 to P5: layers read before first keyword search (of 5), terms tried, hit/miss, misses corrected, calls. |
| `returns.py` | `RETURNS/<task>--return.md` and an INBOX packet (verb `implements_candidate`). Text only. |

## Run and test
```
PYTHONPATH=. python3 -m ss_github_bridge run --fixture tests/fixtures/github_payload.json \
  --calllog tests/fixtures/calllog_layers_first.json --out ./out
PYTHONPATH=. python3 -m pytest -q tests
```
Output is laid out like the Working Memory folders it would be filed to, under `--out` only.

## Fixture provenance
`github_payload.json`: issue 32 and the PR 61 title are real; everything else, including the
advisory ids, is synthetic. Both call logs are synthetic. The golden files in `tests/expected`
are this CLI's own output, reviewed by eye, so they pin behaviour and do not prove it is right.

## Not done
Issue creation and canary (needs write authority), live inbound run (needs token), Working
Memory filing, CI wiring (workflow files are outside this lane without a CR), standards
verification against publisher pages.
