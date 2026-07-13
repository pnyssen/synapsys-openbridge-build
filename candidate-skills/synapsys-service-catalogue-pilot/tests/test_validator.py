import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validator import (  # noqa: E402
    ALLOWED_ORIGIN_IDENTITY_STATE,
    ALLOWED_STATUS,
    check_self_hash,
    parse_front_matter,
    validate,
)


def _build_valid_doc(status="SUBMITTED", origin_state="ROSTER_MATCHED"):
    body = (
        "---\n"
        "artefact_type: service_request\n"
        f"request_id: SERVICE_REQUEST_PILOT_001_v0.1\n"
        f"origin_lane: claude_code\n"
        f"origin_identity_state: {origin_state}\n"
        f"status: {status}\n"
        "ppv_state: Potential\n"
        "authority_state: HELD\n"
        "---\n\n"
        "# Test body\n\n"
        "Some content describing the request.\n\n"
        "---\n"
        "RECEIPT: SHA-256 (self-hash of this document, computed over the content "
        "above this line, before this receipt block was appended):\n"
        "PLACEHOLDER\n"
    )
    head = body[: body.index("RECEIPT: SHA-256")].rstrip("\n") + "\n"
    real_hash = hashlib.sha256(head.encode()).hexdigest()
    return body.replace("PLACEHOLDER", real_hash), real_hash


def test_valid_document_passes():
    doc, expected_hash = _build_valid_doc()
    result = validate(doc)
    assert result.ok, result.errors
    assert result.errors == []
    assert result.hash_match_convention == "with_trailing_separator"
    assert result.front_matter["request_id"] == "SERVICE_REQUEST_PILOT_001_v0.1"


def test_missing_required_field_fails():
    doc, _ = _build_valid_doc()
    doc = doc.replace("authority_state: HELD\n", "")
    result = validate(doc)
    assert not result.ok
    assert any("authority_state" in e for e in result.errors)


def test_bad_status_value_fails():
    doc, _ = _build_valid_doc()
    doc = doc.replace("status: SUBMITTED", "status: MADE_UP_STATUS")
    result = validate(doc)
    assert not result.ok
    assert any("status" in e for e in result.errors)
    assert "MADE_UP_STATUS" not in ALLOWED_STATUS


def test_bad_origin_identity_state_fails():
    doc, _ = _build_valid_doc()
    doc = doc.replace("origin_identity_state: ROSTER_MATCHED", "origin_identity_state: TOTALLY_TRUSTED")
    result = validate(doc)
    assert not result.ok
    assert any("origin_identity_state" in e for e in result.errors)
    assert "TOTALLY_TRUSTED" not in ALLOWED_ORIGIN_IDENTITY_STATE


def test_declared_identity_gets_warning_not_failure():
    doc, _ = _build_valid_doc(origin_state="DECLARED")
    result = validate(doc)
    assert result.ok
    assert any("DECLARED" in w for w in result.warnings)


def test_tampered_content_fails_hash_check():
    doc, _ = _build_valid_doc()
    doc = doc.replace("Some content describing the request.", "Tampered content, different from what was hashed.")
    result = validate(doc)
    assert not result.ok
    assert any("does not match" in e for e in result.errors)


def test_no_front_matter_fails_cleanly():
    result = validate("# Just a markdown file\n\nNo front matter block at all.\n")
    assert not result.ok
    assert any("front matter" in e for e in result.errors)


def test_no_self_hash_present_warns_but_does_not_crash():
    doc = (
        "---\n"
        "artefact_type: service_request\n"
        "request_id: SERVICE_REQUEST_X_v0.1\n"
        "origin_lane: claude_code\n"
        "origin_identity_state: ROSTER_MATCHED\n"
        "status: SUBMITTED\n"
        "ppv_state: Potential\n"
        "authority_state: HELD\n"
        "---\n\n"
        "# No receipt block at all in this document.\n"
    )
    result = validate(doc)
    assert result.ok
    assert any("No self-hash found" in w for w in result.warnings)


def test_cowork_boundary_convention_matches_without_trailing_separator():
    # Reproduces the exact boundary convention independently confirmed
    # against CLAUDE_COWORK_REPLY_TO_SERVICE_CATALOGUE_LIFECYCLE_PROPOSAL_v0.1.md
    # this session: content hash excludes the trailing '---' separator line.
    prefix = (
        "---\n"
        "artefact_type: service_request\n"
        "request_id: SERVICE_REQUEST_Y_v0.1\n"
        "origin_lane: claude_cowork\n"
        "origin_identity_state: DECLARED\n"
        "status: WORKING\n"
        "ppv_state: Potential\n"
        "authority_state: HELD\n"
        "---\n\n"
        "# Body\n\nSome content.\n"
    )
    content_hash = hashlib.sha256(prefix.encode()).hexdigest()
    doc = prefix + "\n---\nRECEIPT: SHA-256 (self-hash...):\n" + content_hash + "\n"
    matched, convention = check_self_hash(doc)
    assert matched
    assert convention == "without_trailing_separator"


def test_front_matter_self_hash_field_is_read():
    fm = parse_front_matter(
        "---\nartefact_type: capability_card\nself_hash: abc123\n---\nbody\n"
    )
    assert fm["self_hash"] == "abc123"


def test_isolation_no_network_or_subprocess_imports():
    import ast

    source = Path(__file__).resolve().parents[1].joinpath("validator.py").read_text()
    tree = ast.parse(source)
    banned_modules = {"socket", "subprocess", "urllib", "requests", "http", "os"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(banned_modules), imported & banned_modules


def test_validate_file_reads_real_file(tmp_path):
    doc, _ = _build_valid_doc()
    p = tmp_path / "request.md"
    p.write_text(doc, encoding="utf-8")
    from validator import validate_file

    result = validate_file(str(p))
    assert result.ok
