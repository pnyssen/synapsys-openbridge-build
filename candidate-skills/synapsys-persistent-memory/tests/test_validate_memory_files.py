import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validate_memory_files import validate_synapsys_md, validate_steward_md  # noqa: E402

GOOD_SYNAPSYS = """# Title
## Purpose
Text.
## Operating discipline
Text.
## Standing rule
Text.
"""

GOOD_STEWARD = """# Title
## Role
Text.
## Observed this session (context, not authority)
Text.
## What this file is not
Not a grant of authority beyond what's stated above.
"""


def test_good_synapsys_md_passes():
    r = validate_synapsys_md(GOOD_SYNAPSYS)
    assert r.ok, (r.missing_headers, r.authority_flags)


def test_synapsys_md_missing_header_fails():
    broken = GOOD_SYNAPSYS.replace("## Standing rule\nText.\n", "")
    r = validate_synapsys_md(broken)
    assert not r.ok
    assert "Standing rule" in r.missing_headers


def test_synapsys_md_authority_assertion_fails():
    broken = GOOD_SYNAPSYS + "\nThis is now DECIDED for all lanes.\n"
    r = validate_synapsys_md(broken)
    assert not r.ok
    assert any("DECIDED" in f for f in r.authority_flags)


def test_good_steward_md_passes():
    r = validate_steward_md(GOOD_STEWARD)
    assert r.ok, (r.missing_headers, r.authority_flags)


def test_steward_md_missing_authority_qualifier_fails():
    broken = GOOD_STEWARD.replace(
        "Not a grant of authority beyond what's stated above.", "This is final."
    )
    r = validate_steward_md(broken)
    assert not r.ok
    assert any("grant of authority" in f for f in r.authority_flags)


def test_steward_md_missing_header_fails():
    broken = GOOD_STEWARD.replace("## Role\nText.\n", "")
    r = validate_steward_md(broken)
    assert not r.ok
    assert "Role" in r.missing_headers


def test_real_files_pass():
    here = os.path.join(os.path.dirname(__file__), "..")
    synapsys_report = validate_synapsys_md(open(os.path.join(here, "synapsys.md")).read())
    steward_report = validate_steward_md(open(os.path.join(here, "steward.md")).read())
    assert synapsys_report.ok, (synapsys_report.missing_headers, synapsys_report.authority_flags)
    assert steward_report.ok, (steward_report.missing_headers, steward_report.authority_flags)
