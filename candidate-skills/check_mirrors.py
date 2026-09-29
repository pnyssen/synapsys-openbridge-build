"""Offline, zero-network check: every candidate-skills/* subfolder must
declare a `mirrors` pointer in its README.md.

Enforces the standing convention filed at
05_AI_RETURNS_HASHED/20260810_GV-STR_CLAUDE_github-role-in-ecosystem-architecture-design_v0.1.md:
a candidate either points to the Working Memory receipt that records
its existence, or explicitly states no Obsidian counterpart exists.
A README with no "mirrors" line at all is the failure mode this exists
to catch -- a candidate nobody could trace back to a filed record.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

MIRRORS_LINE_RE = re.compile(r"\*\*mirrors\*\*:\s*`([^`]+)`", re.IGNORECASE)


@dataclass
class CandidateReport:
    name: str
    has_readme: bool
    has_mirrors_line: bool
    mirrors_target: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.has_readme and self.has_mirrors_line and not self.errors


def check_candidate(path: Path) -> CandidateReport:
    name = path.name
    readme = path / "README.md"
    if not readme.exists():
        return CandidateReport(name=name, has_readme=False, has_mirrors_line=False,
                                errors=["no README.md found"])

    text = readme.read_text()
    match = MIRRORS_LINE_RE.search(text)
    if not match:
        return CandidateReport(name=name, has_readme=True, has_mirrors_line=False,
                                errors=["no '**mirrors**: `...`' line found in README.md"])

    target = match.group(1)
    errors = []
    # A mirrors target must look like a real path (contains a slash or
    # ends in .md) -- not a placeholder or a bare description.
    if "/" not in target and not target.endswith(".md"):
        errors.append(f"mirrors target doesn't look like a path: {target!r}")

    return CandidateReport(name=name, has_readme=True, has_mirrors_line=True,
                            mirrors_target=target, errors=errors)


def check_all(candidate_skills_dir: Path) -> list[CandidateReport]:
    reports = []
    for entry in sorted(candidate_skills_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith(("_", ".")) or entry.name == "tests":
            continue
        reports.append(check_candidate(entry))
    return reports


if __name__ == "__main__":
    here = Path(__file__).parent
    reports = check_all(here)
    ok = True
    for r in reports:
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.name}" + (f" -> {r.mirrors_target}" if r.mirrors_target else ""))
        for e in r.errors:
            print(f"    {e}")
        ok = ok and r.ok
    sys.exit(0 if ok else 1)
