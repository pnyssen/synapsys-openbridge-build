"""Dry-run validator for the 'Publish Obsidian Mobile' Admin Task.

The full execution spec already exists, filed by ChatGPT Hub:
Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/CONTROLS/NAVIGATOR_ADMIN_TASK_OBSIDIAN_MOBILE_PUBLISH_v1.0.md
That spec is not duplicated here. What's missing from the ecosystem
today, per this repo's own alignment return, is an execution mechanism --
this module is NOT that mechanism. It performs the one thing safely
buildable from a design-only authority boundary: validating the task's
own preconditions against already-fetched folder listings, with zero
network/SharePoint/Graph calls of its own. A caller (a future Agent
adapter, or a human operator) fetches the two listings independently and
passes them in; this module never fetches anything itself.

Real preflight run performed this session via sp_list (read-only, already
authorised): 08_MOBILE_DISPATCH is EMPTY -- no 'Obsidian' folder exists
there yet. That is a genuine finding the existing spec's step 3 ("rename
the current published folder to a timestamped backup") does not explicitly
cover -- there is nothing to rename on a first publish. See
first_publish_precondition() below, which this real finding motivated.
"""

import re
from dataclasses import dataclass, field
from typing import List

BACKUP_NAME_PATTERN = re.compile(r"^Obsidian_BACKUP_(\d{8})-(\d{6})$")
REQUIRED_CRITICAL_FILES = (
    "00_HOME.md",
    "00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/SYNAPSYS_NAVIGATOR.html",
)
DEFAULT_RETENTION = 10


@dataclass(frozen=True)
class PreflightFinding:
    ok: bool
    findings: List[str] = field(default_factory=list)
    blocking: List[str] = field(default_factory=list)


def is_valid_backup_name(name: str) -> bool:
    return bool(BACKUP_NAME_PATTERN.match(name))


def sorted_backup_names(existing_target_children: List[str]) -> List[str]:
    """Returns valid Obsidian_BACKUP_* names, oldest first, by the
    timestamp encoded in the name itself -- not by any external mtime,
    since folder-copy operations can produce misleading mtimes."""
    valid = [n for n in existing_target_children if is_valid_backup_name(n)]
    return sorted(valid)


def plan_retention_prune(existing_target_children: List[str], keep: int = DEFAULT_RETENTION) -> List[str]:
    """Returns the backup names that WOULD be pruned under the task's
    stated retention rule, given the current listing -- a plan, not an
    action. Never returns more than len(existing) - keep names, never
    negative."""
    backups = sorted_backup_names(existing_target_children)
    if len(backups) <= keep:
        return []
    excess = len(backups) - keep
    return backups[:excess]


def first_publish_precondition(existing_target_children: List[str]) -> bool:
    """True when there is no live 'Obsidian' folder in the target
    directory to rename to a backup -- i.e. this would be a first
    publish, not a republish. The existing spec's step 3 assumes a
    folder to rename; this flags when that assumption doesn't hold."""
    return "Obsidian" not in existing_target_children


def preflight(
    source_listing_names: List[str],
    target_listing_names: List[str],
    keep: int = DEFAULT_RETENTION,
) -> PreflightFinding:
    """Validate preconditions against two already-fetched folder listings.
    Performs no I/O itself -- the caller is responsible for how those
    listings were obtained (this session used sp_list, read-only)."""
    findings: List[str] = []
    blocking: List[str] = []

    for critical in REQUIRED_CRITICAL_FILES:
        top_level = critical.split("/")[0]
        if top_level not in source_listing_names and critical not in source_listing_names:
            blocking.append(
                f"Required critical path not found at the top level of the "
                f"source listing: {critical} (or its containing folder "
                f"{top_level}). Source listings passed to this function "
                f"should be recursive enough to confirm this, or this check "
                f"should be treated as inconclusive, not passing."
            )

    if first_publish_precondition(target_listing_names):
        findings.append(
            "FIRST_PUBLISH: no 'Obsidian' folder exists in the target "
            "directory today (confirmed via a real read-only sp_list this "
            "session against 08_MOBILE_DISPATCH). Step 3 of the existing "
            "execution spec ('rename current published folder to a "
            "timestamped backup') does not apply on this run -- there is "
            "nothing to rename. The copy step (4) can proceed directly to "
            "creating 'Obsidian' fresh, with no backup created this cycle "
            "since there was no prior publication to preserve."
        )
    else:
        prune_plan = plan_retention_prune(target_listing_names, keep=keep)
        if prune_plan:
            findings.append(
                f"RETENTION: {len(prune_plan)} backup(s) would be pruned "
                f"after a successful copy, under the {keep}-backup retention "
                f"rule: {prune_plan}. Not pruned by this function -- planning "
                f"only, per this task's own authority boundary."
            )
        else:
            findings.append(
                f"RETENTION: no pruning would be required; backup count is "
                f"within the {keep}-backup limit."
            )

    return PreflightFinding(ok=not blocking, findings=findings, blocking=blocking)
