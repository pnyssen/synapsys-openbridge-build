# Threat Model — synapsys-security-audit (CANDIDATE)

## Permission declaration

| Capability | Used? | Notes |
|---|---|---|
| Filesystem read | Yes | Recursive read of target directory only |
| Filesystem write | Yes, narrow | Exactly two files, into caller-specified `--out` directory only |
| Network | **No** | Zero network calls anywhere in the module — no `requests`, `urllib`, `socket`, `http.client` import, no CVE lookup, no telemetry |
| Subprocess / shell exec | **No** | No `subprocess`, `os.system`, `os.popen` import or call anywhere in the module |
| Git operations | **No** | No `git` invocation of any kind |
| Credentials / secrets use | No | The tool *detects* secret-like patterns in scanned text; it never reads, transmits, or uses any credential itself |
| Multi-agent / sub-process fan-out | No | Single-process, single-pass scan |

## Compared to gstack `/cso` (source pattern)

`/cso` optionally uses `WebSearch` for CVE lookups and an `Agent` tool for parallel sub-verification, and defaults to `Write` access for its own report directory. This candidate:
- drops `WebSearch` and any network path entirely — dependency manifests are *listed*, never checked against a CVE database, removing an entire external-call surface;
- drops the `Agent` fan-out — no sub-process spawning of any kind, removing a multi-agent authority-boundary question entirely rather than bounding it;
- keeps a `Write`-equivalent capability but narrows it to exactly two fixed filenames in one caller-specified directory, verified by test (see `tests/test_boundaries.py`).

## Failure behaviour

- Unreadable files are skipped silently (counted as scanned-but-unparsed is not currently tracked — noted as an open gap below).
- No exception path leads to a write outside `--out`.
- No exception path leads to a network call, because none exist in the code to fail into.

## Known gaps (not resolved by this candidate)

- Pattern-matching only — no semantic analysis, no dependency-CVE checking, no OWASP/STRIDE modeling. Materially less capable than `/cso`, by design, until a scoped decision authorizes adding any of those (each would need its own permission/threat review — CVE lookup in particular reintroduces a network-call surface).
- No test yet for extremely large target directories (performance/DoS-of-self via huge repos) — not a security boundary issue, but worth flagging before any real use.
- Redaction of matched secret excerpts is truncation-based (first 80 chars), not pattern-aware — a very long secret could still leak more characters into the report than intended. Should be revisited before any real (non-fixture) use.

## STOP conditions

This tool must not be modified, in any future iteration, to add: network calls, subprocess/shell execution, git operations, or auto-remediation, without a separate authority decision and a corresponding new threat-model version.
