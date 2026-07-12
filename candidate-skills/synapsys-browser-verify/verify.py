"""
synapsys-browser-verify (CANDIDATE, work object D001-EXT-TOOLING-CODE-01)

Verify-and-report only. No cookie import, no persistent context, no proxy,
no auto-fix, no git operations, no daemon.

Independently written for SynapSys. Not derived from, and does not import,
copy, or execute, any code from garrytan/gstack or any other external
repository. Uses Playwright directly (a general-purpose browser automation
library, not gstack's browse binary or any gstack code).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright


@dataclass
class VerifyResult:
    url: str
    final_url: str = ""
    title: str = ""
    status: int | None = None
    console_errors: list[str] = field(default_factory=list)
    screenshot_path: str = ""


def verify(url: str, out_dir: str, executable_path: str | None = None) -> VerifyResult:
    """Single navigate-and-capture pass. Fresh context every call — no storage_state,
    no persistent profile, no proxy argument accepted or forwarded."""
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    result = VerifyResult(url=url)

    with sync_playwright() as p:
        launch_kwargs = {"headless": True}
        if executable_path:
            launch_kwargs["executable_path"] = executable_path
        browser = p.chromium.launch(**launch_kwargs)
        try:
            # Fresh context: no storage_state (= no cookie import), no proxy kwarg passed.
            context = browser.new_context()
            page = context.new_page()

            def _on_console(msg):
                if msg.type == "error":
                    result.console_errors.append(msg.text)

            page.on("console", _on_console)

            response = page.goto(url, wait_until="load", timeout=15000)
            result.status = response.status if response else None
            result.final_url = page.url
            result.title = page.title()

            screenshot_path = out / "verify_screenshot.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            result.screenshot_path = str(screenshot_path)

            context.close()
        finally:
            browser.close()

    return result


def write_report(result: VerifyResult, out_dir: str) -> tuple[Path, Path]:
    """Writes exactly two report files (the screenshot is written separately, inside
    verify()). No git, no source-file writes, no writes outside out_dir."""
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "verify_report.json"
    md_path = out / "verify_report.md"

    payload = {
        "url": result.url,
        "final_url": result.final_url,
        "title": result.title,
        "status": result.status,
        "console_errors": result.console_errors,
        "screenshot_path": result.screenshot_path,
        "disclaimer": (
            "CANDIDATE tool output. Verify-and-report only — no fixes were "
            "attempted or possible; this tool has no code-modification capability."
        ),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Browser Verify Report (CANDIDATE)",
        "",
        f"URL requested: {result.url}",
        f"Final URL: {result.final_url}",
        f"Title: {result.title}",
        f"HTTP status: {result.status}",
        f"Console errors: {len(result.console_errors)}",
    ]
    for err in result.console_errors:
        lines.append(f"- {err}")
    lines.append("")
    lines.append(f"Screenshot: {result.screenshot_path}")
    lines.append("")
    lines.append("_CANDIDATE tool output. Verify-and-report only, no auto-fix._")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out", required=True, dest="out_dir")
    args = parser.parse_args()

    result = verify(args.url, args.out_dir)
    json_path, md_path = write_report(result, args.out_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {result.screenshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
