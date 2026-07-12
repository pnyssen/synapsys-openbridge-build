# Threat Model — synapsys-browser-verify (CANDIDATE)

## Permission declaration

| Capability | Used? | Notes |
|---|---|---|
| Browser control | Yes, narrow | Single navigate + screenshot + console-capture pass per invocation |
| Cookie / session import | **No** | Context created via `new_context()` with no `storage_state` argument — never reads any installed browser's cookie store or profile directory |
| Persistent browser profile | **No** | No `user_data_dir` used; context and browser are both closed at the end of every call |
| Proxy | **No** | Not exposed as a parameter anywhere in the module; nothing to configure even if a caller wanted it |
| Arbitrary JS eval on caller's behalf | **No** | The only script execution is Playwright's own console-message instrumentation, not a caller-suppliable eval endpoint |
| Filesystem write | Yes, narrow | Exactly three files per run (screenshot, JSON report, Markdown report), all into the caller-specified `--out` directory |
| Git operations | **No** | No `git` invocation anywhere |
| Auto-fix / source modification | **No** | The tool never opens a source file for writing — it has no code-modification code path to misuse |
| Persistent daemon | **No** | Browser process starts and is torn down (`browser.close()`) within a single `verify()` call; nothing survives the call |
| Network | Yes, narrow | Only to the single caller-supplied URL, once, for the navigation itself |

## Compared to gstack `/browse` + `/qa` (source pattern)

The source pattern runs a **persistent** headless Chromium daemon, imports cookies from the user's actual installed browsers, supports credentialed SOCKS5/HTTP proxies, and (in `/qa`) autonomously runs `git add`/`git commit` as part of a self-regulated fix loop. This candidate removes all of that rather than bounding it:

- no daemon — process-per-call instead of long-lived;
- no cookie import path exists in the code at all (not just "off by default");
- no proxy parameter exists to be misused;
- no fix loop, no git commands, no code-modification capability of any kind — "verify-and-report" is enforced by the absence of a write-to-source code path, not by a policy flag that could be flipped.

## Failure behaviour

- Navigation timeout (15s) raises a Playwright `TimeoutError`, which propagates — the tool does not silently report a false "success."
- Any exception during the `with sync_playwright()` block still reaches `browser.close()` via the `finally` block, so no orphaned browser process survives a failure.

## Known gaps (not resolved by this candidate)

- No test yet against a target that requires authentication — by design, since no session/cookie capability exists; the tool would simply report the unauthenticated page, which is correct-but-limited behaviour worth being explicit about rather than surprising.
- No sandboxing of the target URL itself — the tool will navigate to whatever URL it's given. Per Work Object condition 6 and this SKILL.md, it's authorised only against local fixtures or an explicitly authorised isolated sandbox target; the tool itself does not enforce that restriction in code (an allowlist could be added, but that's a scope decision, not assumed here).
- Screenshot/report files are not currently size-capped — a pathological page could produce a very large screenshot. Not a boundary-violation risk, but worth noting before real use.

## STOP conditions

This tool must not be modified, in any future iteration, to add: cookie/session import, proxy support, persistent daemon mode, auto-fix/auto-commit, or arbitrary caller-suppliable JS execution, without a separate authority decision and a corresponding new threat-model version.
