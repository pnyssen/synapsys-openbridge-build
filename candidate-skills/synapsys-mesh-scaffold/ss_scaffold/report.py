"""One report per Context: one verb, one tested number (RACI coverage, the module the packet
fixes), the other three coverage numbers in the drill-down. Text only."""
from __future__ import annotations

from typing import Any, Dict

ORDER = ("contribution", "raci", "baselines", "shock_readiness")


def render(context: str, results: Dict[str, Any]) -> str:
    def num(m):
        return results[m]["coverage"]["text"] if m in results else "[n] not supplied"
    errs = sum(len(r["errors"]) for r in results.values())
    lines = [f"# {context} — scaffold coverage report", "",
             "**Verb:** verify",
             f"**Tested number:** RACI coverage {num('raci')} accepted",
             "**PPV:** Potential · authority HELD · candidate, dry run · no Odoo, N8N, canon, registry or PPV change", "",
             "## Drill-down (the four coverage numbers)"]
    for m in ORDER:
        lines.append(f"- {m}: {num(m)}" + (f" — {results[m]['definition']}" if m in results else ""))
    lines += ["", f"## Rule violations: {errs}"]
    for m in ORDER:
        for e in results.get(m, {}).get("errors", []):
            lines.append(f"- [{m}] {e}")
    lines += ["", "## Gaps (unknown or unaccepted, not counted)"]
    for m in ORDER:
        for g in results.get(m, {}).get("gaps", [])[:20]:
            lines.append(f"- [{m}] {g}")
    return "\n".join(lines) + "\n"
