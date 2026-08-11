"""Tests for admin_task_dry_run.py, including a case built from the real,
read-only sp_list result obtained this session against 08_MOBILE_DISPATCH
(empty -- no prior Obsidian mobile publication exists)."""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admin_task_dry_run import (  # noqa: E402
    is_valid_backup_name,
    sorted_backup_names,
    plan_retention_prune,
    first_publish_precondition,
    preflight,
)

FORBIDDEN_MODULES = {"socket", "subprocess", "urllib", "requests", "http"}


def test_isolation_no_forbidden_imports():
    path = os.path.join(os.path.dirname(__file__), "..", "admin_task_dry_run.py")
    with open(path, "r") as f:
        tree = ast.parse(f.read(), filename=path)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    assert not (found & FORBIDDEN_MODULES), f"Forbidden imports: {found & FORBIDDEN_MODULES}"


def test_valid_backup_name():
    assert is_valid_backup_name("Obsidian_BACKUP_20260812-140000")


def test_invalid_backup_names_rejected():
    assert not is_valid_backup_name("Obsidian")
    assert not is_valid_backup_name("Obsidian_BACKUP_bad")
    assert not is_valid_backup_name("Obsidian_backup_20260812-140000")  # case-sensitive
    assert not is_valid_backup_name("Obsidian_BACKUP_20260812")  # missing time part


def test_sorted_backup_names_ignores_non_backup_entries():
    children = ["Obsidian", "Obsidian_BACKUP_20260810-090000", "randomfile.txt",
                "Obsidian_BACKUP_20260811-090000"]
    assert sorted_backup_names(children) == [
        "Obsidian_BACKUP_20260810-090000",
        "Obsidian_BACKUP_20260811-090000",
    ]


def test_retention_prune_plan_empty_when_under_limit():
    children = [f"Obsidian_BACKUP_2026080{i}-090000" for i in range(1, 6)]  # 5 backups
    assert plan_retention_prune(children, keep=10) == []


def test_retention_prune_plan_prunes_oldest_first():
    children = [f"Obsidian_BACKUP_202608{str(i).zfill(2)}-090000" for i in range(1, 13)]  # 12 backups
    plan = plan_retention_prune(children, keep=10)
    assert len(plan) == 2
    assert plan == sorted(children)[:2]


def test_retention_prune_never_negative_or_over():
    assert plan_retention_prune([], keep=10) == []
    assert plan_retention_prune(["Obsidian_BACKUP_20260101-000000"], keep=0) == [
        "Obsidian_BACKUP_20260101-000000"
    ]


def test_first_publish_precondition_true_when_no_obsidian_folder():
    assert first_publish_precondition([]) is True
    assert first_publish_precondition(["Obsidian_BACKUP_20260101-000000"]) is True


def test_first_publish_precondition_false_when_obsidian_present():
    assert first_publish_precondition(["Obsidian"]) is False


def test_preflight_real_empty_target_from_this_session():
    """Uses the actual sp_list result obtained this session for
    08_MOBILE_DISPATCH (empty list) and a plausible source listing
    (Obsidian/00_SYSTEM confirmed present and populated via sp_list)."""
    source_listing = [
        "AGENT_CONTROLS", "CONTROL", "DESIGN_STANDARDS", "ENTITY_TYPES",
        "NAVIGATOR", "NAVIGATOR_SUPPORT", "OBSIDIAN_CONFIG",
        "OBSIDIAN_MVP_VIEWING_LAYER_v1.0", "RELATIONSHIP_TYPES",
        "SCHEMAS_AND_REGISTRIES", "STEWARD_REVIEW", "TEMPLATES",
        "VIEWING_LAYER", "VOCABULARIES_AND_RULES",
        "00_HOME.md", "00_SYSTEM",
    ]
    target_listing = []  # real result: 08_MOBILE_DISPATCH is empty

    result = preflight(source_listing, target_listing)
    assert result.ok is True  # not blocking -- first publish is a valid, expected state
    assert any("FIRST_PUBLISH" in f for f in result.findings)
    assert not any("RETENTION" in f for f in result.findings)  # no retention question on first publish


def test_preflight_blocks_when_critical_source_path_missing():
    source_listing = ["AGENT_CONTROLS", "CONTROL"]  # no 00_HOME.md, no 00_SYSTEM
    target_listing = []
    result = preflight(source_listing, target_listing)
    assert result.ok is False
    assert result.blocking
