---
name: synapsys-browser-verify
status: CANDIDATE — not adopted, not installed, not activated
work_object: D001-EXT-TOOLING-CODE-01
version: 0.1
---

# synapsys-browser-verify (CANDIDATE)

Verify-and-report browser check of a rendered page. Pattern derived from the
*structure* of gstack's `/browse`+`/qa` (navigate → document → structured
report) — independently reimplemented. No code, prompts, cookie-import logic,
daemon logic, or fix-loop logic copied from that source.

## What it does

Given a URL, launches a single fresh, non-persistent Chromium context via
Playwright, navigates once, captures:
- a full-page screenshot
- the page title and final URL (post-redirect)
- the HTTP response status of the initial navigation
- any browser console `error`-level messages during load

Writes one screenshot file and one structured JSON+Markdown report per run
to a caller-specified output directory, then closes the browser. Process
exits after each invocation — no daemon, no persistent session.

## What it deliberately does not do

- **No cookie import.** The browser context is created fresh (`new_context()`
  with no `storage_state`); it never reads any installed browser's cookie
  store or profile directory.
- **No proxy support of any kind** — not exposed as an option.
- **No auto-fix.** Findings are reported; no source file is ever opened for
  writing by this tool.
- **No git operations** — no `git` invocation of any kind, anywhere.
- **No persistent daemon** — the browser process is started and torn down
  within a single call; nothing is left running.
- **No arbitrary JS `eval` on the caller's behalf** — the only script
  execution is Playwright's own internal instrumentation for console-message
  capture, not a caller-suppliable eval surface.

## Usage

```
python verify.py <url> --out <output_dir>
```

Intended for use only against local fixture pages or an explicitly
authorised isolated sandbox target, per Work Object D001-EXT-TOOLING-CODE-01
condition 6. Not authorised against production URLs, and contains no special
handling that would make production use safe (no auth, no session — it would
simply see an unauthenticated page).

## Authority state

CANDIDATE. Not filed as an adopted SynapSys skill. Requires D009 assurance
challenge and D007 sandbox confirmation before any adoption consideration.
