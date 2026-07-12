---
name: synapsys-security-audit
status: CANDIDATE — not adopted, not installed, not activated
work_object: D001-EXT-TOOLING-CODE-01
version: 0.1
---

# synapsys-security-audit (CANDIDATE)

Read-only static security scan of a local codebase. Pattern derived from the *structure* of gstack's `/cso` skill (phased scan → confidence-gated findings → exploit-scenario-required report), independently reimplemented — no code, prompts, or scripts copied from that source.

## What it does

Scans a target directory for:
- hardcoded-secret patterns (API keys, private key headers, password-literal assignments)
- risky-code patterns (`eval(`, `exec(`, `subprocess` with `shell=True`, `os.system(`)
- presence of dependency manifests (reported as a list only — no CVE lookup, no network call of any kind)

Produces a structured JSON report and a human-readable Markdown summary.

## What it deliberately does not do

- No file modification of scanned targets.
- No remediation, auto-fix, or code changes of any kind.
- No network access — zero external calls, by design, not just by convention (see THREAT_MODEL.md and tests).
- No `Agent`/sub-process fan-out.
- No git operations of any kind.
- No writes outside the single caller-specified output path.

## Usage

```
python audit.py <target_dir> --out <output_dir>
```

Exits non-zero only on a usage error. Findings never raise — they are data, not control flow.

## Authority state

CANDIDATE. Not filed as an adopted SynapSys skill. Requires D009 assurance challenge before any adoption consideration, per Work Object D001-EXT-TOOLING-CODE-01.
