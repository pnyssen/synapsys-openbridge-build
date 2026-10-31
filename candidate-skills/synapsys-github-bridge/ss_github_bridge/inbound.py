"""Inbound (read-only): GitHub issues, PRs, failing CI and advisories -> Signals.

Two sources, same Signal shape:
  * load_fixture(path)  - a recorded API response set (tests, dry-run goldens).
  * fetch_live(repo)    - GitHub REST, GET only. Needs GITHUB_TOKEN in the
    environment; with none, raises NeedsCredential so the caller stops and asks.
    Not exercised by the test suite (no network in tests).
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List


class NeedsCredential(RuntimeError):
    """Raised instead of guessing: a token must be provided via the approved route."""


def _signal(repo: str, type_: str, number: Any, title: str, body: Any, state: str, url: str) -> Dict[str, Any]:
    return {"repo": repo, "type": type_, "number": number, "title": title or "",
            "body": body or "", "state": state, "url": url}


def signals_from_payload(repo: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in payload.get("issues", []):
        out.append(_signal(repo, "issue", it["number"], it["title"], it.get("body"),
                           it["state"].lower(), it.get("html_url", it.get("url", ""))))
    for it in payload.get("pulls", []):
        out.append(_signal(repo, "pull_request", it["number"], it["title"], it.get("body"),
                           it["state"].lower(), it.get("html_url", "")))
    for it in payload.get("check_runs", []):
        if it.get("conclusion") in ("failure", "timed_out", "cancelled", "action_required"):
            out.append(_signal(repo, "ci_failure", it["id"], f"CI {it['name']} {it['conclusion']}",
                               (it.get("output") or {}).get("summary"), "open", it.get("html_url", "")))
    for it in payload.get("advisories", []):
        if it.get("state", "open") == "open":
            ghsa = it.get("ghsa_id", "")
            out.append(_signal(repo, "advisory", ghsa or it.get("number"),
                               f"Advisory {ghsa} {it.get('summary', '')}".strip(),
                               f"{it.get('cve_id') or ''} {it.get('description') or ''}".strip(),
                               "open", it.get("html_url", "")))
    return out


def load_fixture(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return signals_from_payload(data["repo"], data)


def _get(url: str, token: str) -> Any:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                               "Accept": "application/vnd.github+json",
                                               "X-GitHub-Api-Version": "2022-11-28"}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:   # noqa: S310 (fixed https host)
        return json.load(resp)


def fetch_live(repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise NeedsCredential("GITHUB_TOKEN not set in the environment. Provide it through the approved "
                              "route (environment or secret store); it is never read from the repo.")
    base = f"https://api.github.com/repos/{repo}"
    issues = [i for i in _get(f"{base}/issues?state=open&per_page={per_page}", token) if "pull_request" not in i]
    pulls = _get(f"{base}/pulls?state=open&per_page={per_page}", token)
    head = _get(f"{base}/commits/HEAD", token)["sha"]
    checks = _get(f"{base}/commits/{head}/check-runs?per_page={per_page}", token).get("check_runs", [])
    try:
        advisories = _get(f"{base}/dependabot/alerts?state=open&per_page={per_page}", token)
        advisories = [{"ghsa_id": a["security_advisory"]["ghsa_id"], "cve_id": a["security_advisory"].get("cve_id"),
                       "summary": a["security_advisory"]["summary"], "description": "", "html_url": a["html_url"],
                       "state": "open"} for a in advisories]
    except Exception:    # alerts need extra scope; absence is not "no advisories"
        advisories = []
    return signals_from_payload(repo, {"issues": issues, "pulls": pulls, "check_runs": checks,
                                       "advisories": advisories})
