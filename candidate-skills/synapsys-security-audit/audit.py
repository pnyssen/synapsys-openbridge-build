"""
synapsys-security-audit (CANDIDATE, work object D001-EXT-TOOLING-CODE-01)

Read-only static scan. No network access, no subprocess execution, no writes
outside the caller-specified output path, no remediation.

Independently written for SynapSys. Not derived from, and does not import,
copy, or execute, any code from garrytan/gstack or any other external
repository.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SECRET_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_api_key_assignment", re.compile(
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]"
    )),
    ("private_key_header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("hardcoded_password_assignment", re.compile(
        r"(?i)password\s*=\s*['\"](?!\{|\$|<|CHANGE_ME|REDACTED)[^'\"]{6,}['\"]"
    )),
]

RISKY_CODE_PATTERNS = [
    ("eval_call", re.compile(r"\beval\s*\(")),
    ("exec_call", re.compile(r"\bexec\s*\(")),
    ("shell_true_subprocess", re.compile(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True")),
    ("os_system_call", re.compile(r"\bos\.system\s*\(")),
]

DEPENDENCY_MANIFESTS = [
    "package.json", "requirements.txt", "pyproject.toml", "Gemfile",
    "go.mod", "Cargo.toml", "composer.json",
]

SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rb", ".go", ".java", ".php",
    ".env", ".yml", ".yaml", ".json", ".sh",
}

SKIP_DIRS = {".git", "node_modules", "vendor", "__pycache__", ".venv", "venv"}


@dataclass
class Finding:
    category: str
    pattern: str
    file: str
    line: int
    excerpt: str


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    manifests_found: list[str] = field(default_factory=list)
    files_scanned: int = 0


def _iter_scan_files(target: Path):
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in SCAN_EXTENSIONS or path.name in DEPENDENCY_MANIFESTS:
            yield path


def _redact(excerpt: str) -> str:
    return excerpt.strip()[:80] + ("…" if len(excerpt.strip()) > 80 else "")


def scan(target_dir: str) -> ScanResult:
    """Read-only scan. Never writes, never executes, never makes network calls."""
    target = Path(target_dir).resolve()
    result = ScanResult()

    for path in _iter_scan_files(target):
        result.files_scanned += 1
        if path.name in DEPENDENCY_MANIFESTS:
            result.manifests_found.append(str(path.relative_to(target)))

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            for category, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    result.findings.append(Finding(
                        category="secret", pattern=category,
                        file=str(path.relative_to(target)), line=lineno,
                        excerpt=_redact(line),
                    ))
            for category, pattern in RISKY_CODE_PATTERNS:
                if pattern.search(line):
                    result.findings.append(Finding(
                        category="risky_code", pattern=category,
                        file=str(path.relative_to(target)), line=lineno,
                        excerpt=_redact(line),
                    ))

    return result


def write_report(result: ScanResult, out_dir: str) -> tuple[Path, Path]:
    """Writes exactly two files into out_dir. No other filesystem writes occur anywhere."""
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "security_audit_report.json"
    md_path = out / "security_audit_report.md"

    payload = {
        "files_scanned": result.files_scanned,
        "manifests_found": result.manifests_found,
        "findings": [f.__dict__ for f in result.findings],
        "disclaimer": (
            "CANDIDATE tool output. Not a substitute for professional security "
            "review. Findings are pattern matches, not confirmed vulnerabilities."
        ),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Security Audit Report (CANDIDATE)",
        "",
        f"Files scanned: {result.files_scanned}",
        f"Dependency manifests found: {', '.join(result.manifests_found) or 'none'}",
        f"Findings: {len(result.findings)}",
        "",
    ]
    for f in result.findings:
        lines.append(f"- **{f.category}/{f.pattern}** — `{f.file}:{f.line}` — `{f.excerpt}`")
    if not result.findings:
        lines.append("No pattern matches found.")
    lines.append("")
    lines.append(
        "_CANDIDATE tool output. Not a substitute for professional security review._"
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir")
    parser.add_argument("--out", required=True, dest="out_dir")
    args = parser.parse_args()

    result = scan(args.target_dir)
    json_path, md_path = write_report(result, args.out_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
