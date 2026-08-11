import pytest

from sharepoint_write_preflight import (
    normalize_filename,
    preflight_write,
    validate_filename,
)


def test_validate_filename_accepts_server_confirmed_example():
    ok, reason = validate_filename(
        "20260811--codex--evidence-receipt--sharepoint-search-repair--v0-1.md"
    )
    assert ok is True
    assert reason is None


@pytest.mark.parametrize(
    "filename",
    [
        "",
        "invalid<>name?.md",
        "20260811_RET_GEN_claude-code-old-style_v0.1.md",
        "2026-08-11--claude-code--evidence-receipt--slug--v0-1.md",
        "20260811--Claude-Code--evidence-receipt--slug--v0-1.md",
        "20260811--claude-code--evidence-receipt--slug--v0.1.md",
    ],
)
def test_validate_filename_rejects_non_conforming_names(filename):
    ok, reason = validate_filename(filename)
    assert ok is False
    assert reason


def test_normalize_filename_builds_compliant_name():
    name = normalize_filename(
        date="20260811",
        lane="claude-code",
        artifact_type="evidence-receipt",
        slug="sharepoint-mcp-verification-smoke-test",
        major=0,
        minor=1,
    )
    assert name == (
        "20260811--claude-code--evidence-receipt--"
        "sharepoint-mcp-verification-smoke-test--v0-1.md"
    )


def test_normalize_filename_never_silently_corrects_bad_input():
    with pytest.raises(ValueError):
        normalize_filename(
            date="2026-08-11",
            lane="Claude Code",
            artifact_type="evidence receipt",
            slug="slug",
            major=0,
            minor=1,
        )


def test_preflight_write_rejects_empty_path():
    result = preflight_write("", "content")
    assert result["ok"] is False
    assert "path must not be empty" in result["errors"]


def test_preflight_write_rejects_path_traversal():
    result = preflight_write(
        "../05_AI_RETURNS_HASHED/"
        "20260811--claude-code--evidence-receipt--slug--v0-1.md",
        "content",
    )
    assert result["ok"] is False
    assert any("must not contain" in e for e in result["errors"])


def test_preflight_write_rejects_non_conforming_filename():
    result = preflight_write("05_AI_RETURNS_HASHED/not-conforming.md", "content")
    assert result["ok"] is False


def test_preflight_write_accepts_conforming_relative_path():
    result = preflight_write(
        "05_AI_RETURNS_HASHED/"
        "20260811--claude-code--evidence-receipt--"
        "sharepoint-mcp-verification-smoke-test--v0-1.md",
        "content",
    )
    assert result["ok"] is True
    assert result["errors"] == []
