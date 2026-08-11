"""Tests for wm_filing_compliance.py, grounded in real filenames this
session actually filed successfully (ground truth from live sp_write
results, not invented examples) plus the real M3C_DOCUMENT_INDEX case."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wm_filing_compliance import (  # noqa: E402
    validate_filename,
    validate_front_matter,
    slug_from_legacy_name,
    extract_legacy_version,
    build_compliant_filename,
)

# Real filenames this lane actually filed successfully this session via sp_write.
REAL_ACCEPTED_FILENAMES = [
    "20260811--claude-code--evidence-receipt--hermes-rule-cycle-option-ab-approved-vps-access-directive--v0-1.md",
    "20260811--claude-code--design-note--synapsys-agent-identity-anchor-loop-item1--v1-0.md",
    "20260811--claude-code--implementation-return--synapsys-agent-github-navigator-alignment--v1-0.md",
    "20260812--claude-code--evidence-receipt--synapsys-agent-loop-items-2to5-completion--v1-0.md",
    "20260812--claude-code--dispatch--wave-accelerator-alignment-request--v1-0.md",
    "20260812--claude-code--alignment-receipt--wave-accelerator-consumption--v1-0.md",
]

# Real filenames this lane's sp_write actually rejected this session.
REAL_REJECTED_FILENAMES = [
    "20260811_RET_GEN_claude-code-hermes-rule-cycle-option-ab-approved-vps-access-directive_v0.1.md",
    "SYNAPSYS_AGENT_GITHUB_NAVIGATOR_ALIGNMENT_RETURN_v1.0.md",
]


def test_all_real_accepted_filenames_validate_ok():
    for name in REAL_ACCEPTED_FILENAMES:
        result = validate_filename(name)
        assert result.ok, f"{name} should validate but didn't: {result.errors}"


def test_all_real_rejected_filenames_fail_validation():
    for name in REAL_REJECTED_FILENAMES:
        result = validate_filename(name)
        assert not result.ok, f"{name} should fail validation but passed"
        assert result.errors


def test_uppercase_filename_flagged():
    result = validate_filename("20260812--Claude-Code--dispatch--slug--v1-0.md")
    assert not result.ok
    assert any("lowercase" in e for e in result.errors)


def test_missing_double_dash_separator_flagged():
    result = validate_filename("20260812-claude-code-dispatch-slug-v1-0.md")
    assert not result.ok


def test_front_matter_all_required_fields_present():
    fields = {
        "title": "x", "work_object_id": "x", "created_date": "x",
        "owner_lane": "x", "ppv": "x", "evidence_state": "x",
        "aliases": [], "source_paths": [], "supersedes": None,
    }
    assert validate_front_matter(fields).ok


def test_front_matter_missing_fields_reported_by_name():
    fields = {"title": "x", "work_object_id": "x"}
    result = validate_front_matter(fields)
    assert not result.ok
    assert "created_date" in result.errors[0]
    assert "owner_lane" in result.errors[0]


def test_slug_from_real_m3c_legacy_name_preserves_literal_tokens():
    """The exact case this tool was built for: M3C_DOCUMENT_INDEX_..._v0.195.md"""
    slug = slug_from_legacy_name("M3C_DOCUMENT_INDEX_something_here_v0.195.md")
    assert "m3c" in slug
    assert "document" in slug
    assert "index" in slug
    assert "195" not in slug  # version stripped, handled separately
    assert slug == "m3c-document-index-something-here"


def test_extract_legacy_version_major_minor():
    assert extract_legacy_version("M3C_DOCUMENT_INDEX_..._v0.195.md") == "0-195"


def test_extract_legacy_version_major_only():
    assert extract_legacy_version("SOME_FILE_v3.md") == "3-0"


def test_extract_legacy_version_none_when_absent():
    assert extract_legacy_version("SOME_FILE_NO_VERSION.md") is None


def test_build_compliant_filename_for_real_m3c_case():
    """Reproduces the exact scenario from this session's own advice:
    M3C_DOCUMENT_INDEX_..._v0.195.md -> new pattern, same v0-195 slot."""
    name = build_compliant_filename(
        date_yyyymmdd="20260812",
        lane="chatgpt-hub",
        artifact_type="document-index",
        legacy_name="M3C_DOCUMENT_INDEX_synapsys_ecosystem_v0.195.md",
    )
    assert name == "20260812--chatgpt-hub--document-index--m3c-document-index-synapsys-ecosystem--v0-195.md"
    assert validate_filename(name).ok


def test_build_compliant_filename_falls_back_when_no_legacy_version():
    name = build_compliant_filename(
        date_yyyymmdd="20260812",
        lane="claude-code",
        artifact_type="design-note",
        legacy_name="SOME_UNVERSIONED_FILE.md",
        fallback_minor="1",
    )
    assert name.endswith("--v0-1.md")
    assert validate_filename(name).ok


def test_build_compliant_filename_always_produces_valid_output():
    """Regression guard: whatever legacy name comes in, the output must
    always pass validate_filename -- never a silent near-miss."""
    cases = [
        "WEIRD name with SPACES and_underscores-v2.7.md",
        "NoVersionAtAll.json",
        "already-lowercase-dashed-v1.0.md",
    ]
    for legacy in cases:
        name = build_compliant_filename(
            date_yyyymmdd="20260812", lane="claude-code",
            artifact_type="design-note", legacy_name=legacy,
            ext=legacy.rsplit(".", 1)[-1].lower() if "." in legacy else "md",
        )
        assert validate_filename(name).ok, f"build produced invalid name: {name}"
