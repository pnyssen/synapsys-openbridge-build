"""Concurrency-safe write precondition checker for the shared SynapSys
Obsidian vault (`SynapSys-Control/11_WORKING_MEMORY/Obsidian`, reached via
the `mcp__SynapSys_SharePoint__sp_read`/`sp_list`/`sp_write` tools).

Why this exists: that vault is edited live by a human (Phil, in the
Obsidian desktop app) and written to independently by multiple AI lanes
(this lane, Claude Cowork, Fable) with no locking and no version check --
confirmed this session by `sp_list("Obsidian")` showing a subfolder
(`GOVERNANCE_MESH_SUITE`) modified same-day by a lane other than this one.
A blind `sp_write` from any lane can silently clobber a concurrent edit,
or corrupt a `.canvas` file (which Obsidian's Canvas view will then fail
to open) if the JSON is malformed.

What this module is: pure decision logic only. It never calls the
SharePoint MCP tools itself -- the caller injects `read_fn`/`write_fn`
(e.g. thin wrappers around `sp_read`/`sp_write`) so this module stays
zero-network, zero-subprocess, and fully unit-testable in isolation, per
this repo's existing candidate-skill discipline (see
`candidate-skills/synapsys-service-catalogue-pilot/scoping_validator.py`
and its `test_isolation_no_network_or_subprocess_imports` test, mirrored
below).

Two independent protections, both required, neither sufficient alone:

1. **Path allowlist (default-deny)**. This lane's write authorization is
   `05_AI_RETURNS_HASHED` only (CLAUDE.md's write-authorization boundary)
   -- the vault is a distinct, not-yet-authorized location. Rather than
   hard-coding "no vault access" here (which would need a code change the
   moment a Steward ruling grants scoped access), the allowlist is a
   parameter the caller supplies at call time from whatever scope
   decision is currently on file. An empty/missing allowlist entry means
   deny, not allow -- this module never assumes scope for a path it
   wasn't explicitly told about.

2. **Optimistic concurrency (read-before-write hash compare)**. The
   caller passes `expected_prior_hash`: the SHA-256 of the content this
   lane last read from that path (or `None` if this lane believes the
   path doesn't exist yet). This module re-reads the path via `read_fn`
   at write time and compares. A mismatch -- whether "someone already
   created this file" or "someone changed it since I last read it" --
   blocks the write and reports a conflict instead of overwriting. This
   is deliberately stricter than "last write wins": on a vault a human
   has open live, silent overwrite is the expensive failure mode, a
   blocked write that has to be retried is the cheap one.

Canvas-file corruption check: `.canvas` files are JSON; Obsidian's Canvas
view simply fails to render a file that isn't valid JSON. `guarded_write`
checks this for any `.canvas` path before calling `write_fn`, using only
the `json` stdlib module (not on the banned-import list -- it does no I/O
of its own).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable, Optional


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_path_allowed(path: str, allowed_prefixes: list[str]) -> bool:
    """Default-deny: `path` must fall under one of `allowed_prefixes`
    (exact match or `prefix/...`). An empty `allowed_prefixes` list denies
    everything -- there is no implicit-allow case."""
    normalized = path.strip("/")
    for prefix in allowed_prefixes:
        p = prefix.strip("/")
        if normalized == p or normalized.startswith(p + "/"):
            return True
    return False


def validate_vault_file_format(path: str, content: str) -> list[str]:
    """Format-corruption check for file types Obsidian is strict about.
    Returns a list of error strings; empty list means no format issue
    found (this is not a full lint -- see module docstring)."""
    errors: list[str] = []
    if path.endswith(".canvas"):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in .canvas file: {e}")
        else:
            if not isinstance(parsed, dict) or "nodes" not in parsed or "edges" not in parsed:
                errors.append(
                    "Canvas JSON is valid but missing the required "
                    "top-level 'nodes'/'edges' keys (JSON Canvas spec)."
                )
    return errors


@dataclass
class GuardResult:
    ok: bool
    reason: str
    conflict: bool = False
    prior_remote_hash: Optional[str] = None
    new_hash: Optional[str] = None
    format_errors: list = field(default_factory=list)


def check_write_precondition(
    path: str,
    content: str,
    allowed_prefixes: list[str],
    current_remote_content: Optional[str],
    expected_prior_hash: Optional[str],
) -> GuardResult:
    """Pure precondition check -- no I/O. `current_remote_content` is
    whatever `read_fn(path)` returned *right now* (None if the path
    doesn't exist remotely); `expected_prior_hash` is the hash of what
    the caller last read (None if the caller believes this is a new
    file)."""
    if not is_path_allowed(path, allowed_prefixes):
        return GuardResult(
            ok=False,
            reason=f"Path {path!r} is not in the current write allowlist "
            "(default-deny -- no scope decision covers this path yet).",
        )

    format_errors = validate_vault_file_format(path, content)
    if format_errors:
        return GuardResult(
            ok=False,
            reason="Content fails format validation, refusing to write.",
            format_errors=format_errors,
        )

    current_remote_hash = (
        compute_sha256(current_remote_content)
        if current_remote_content is not None
        else None
    )

    if expected_prior_hash is None and current_remote_content is not None:
        return GuardResult(
            ok=False,
            reason=f"Expected {path!r} not to exist yet, but remote content "
            "is already present -- another lane or the human vault owner "
            "created it since this lane last checked. Refusing to overwrite.",
            conflict=True,
            prior_remote_hash=current_remote_hash,
        )

    if expected_prior_hash is not None and expected_prior_hash != current_remote_hash:
        return GuardResult(
            ok=False,
            reason=f"Remote content at {path!r} has changed since this lane "
            "last read it (expected prior hash "
            f"{expected_prior_hash!r}, found {current_remote_hash!r}). "
            "Refusing to overwrite a concurrent edit -- re-read and retry.",
            conflict=True,
            prior_remote_hash=current_remote_hash,
        )

    return GuardResult(
        ok=True,
        reason="Precondition satisfied: path allowed, format valid, no "
        "concurrent-edit conflict detected.",
        prior_remote_hash=current_remote_hash,
        new_hash=compute_sha256(content),
    )


def guarded_write(
    path: str,
    content: str,
    allowed_prefixes: list[str],
    read_fn: Callable[[str], Optional[str]],
    write_fn: Callable[[str, str], None],
    expected_prior_hash: Optional[str] = None,
) -> GuardResult:
    """Orchestrates one guarded write: re-reads `path` via `read_fn`,
    checks preconditions, and only calls `write_fn` if they pass.
    `read_fn` must return `None` (not raise) for a path that doesn't
    exist. Never calls `write_fn` when the result is not `ok`."""
    current_remote_content = read_fn(path)
    result = check_write_precondition(
        path=path,
        content=content,
        allowed_prefixes=allowed_prefixes,
        current_remote_content=current_remote_content,
        expected_prior_hash=expected_prior_hash,
    )
    if result.ok:
        write_fn(path, content)
    return result
