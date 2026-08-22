import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from check_mirrors import check_candidate, check_all  # noqa: E402


def _write_readme(dir_path: Path, content: str) -> None:
    (dir_path / "README.md").write_text(content)


def test_missing_readme_fails():
    with tempfile.TemporaryDirectory() as td:
        candidate = Path(td) / "some-candidate"
        candidate.mkdir()
        r = check_candidate(candidate)
        assert not r.ok
        assert "no README.md found" in r.errors[0]


def test_missing_mirrors_line_fails():
    with tempfile.TemporaryDirectory() as td:
        candidate = Path(td) / "some-candidate"
        candidate.mkdir()
        _write_readme(candidate, "# some-candidate\n\nJust a description, no mirrors line.\n")
        r = check_candidate(candidate)
        assert not r.ok
        assert any("no '**mirrors**" in e for e in r.errors)


def test_valid_mirrors_line_passes():
    with tempfile.TemporaryDirectory() as td:
        candidate = Path(td) / "some-candidate"
        candidate.mkdir()
        _write_readme(
            candidate,
            "# some-candidate\n\n"
            "**mirrors**: `05_AI_RETURNS_HASHED/SOME_RECEIPT_v0.1.md`\n",
        )
        r = check_candidate(candidate)
        assert r.ok, r.errors
        assert r.mirrors_target == "05_AI_RETURNS_HASHED/SOME_RECEIPT_v0.1.md"


def test_mirrors_target_not_a_path_fails():
    with tempfile.TemporaryDirectory() as td:
        candidate = Path(td) / "some-candidate"
        candidate.mkdir()
        _write_readme(candidate, "# some-candidate\n\n**mirrors**: `somewhere probably`\n")
        r = check_candidate(candidate)
        assert not r.ok
        assert any("doesn't look like a path" in e for e in r.errors)


def test_real_repo_candidates_all_pass():
    real_dir = Path(__file__).parent.parent
    reports = check_all(real_dir)
    names = {r.name for r in reports}
    assert "synapsys-tobe-realignment" in names
    assert "synapsys-persistent-memory" in names
    assert "synapsys-service-catalogue-pilot" in names
    for r in reports:
        assert r.ok, (r.name, r.errors)


def test_underscore_and_dot_and_tests_dirs_skipped():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "_scratch").mkdir()
        (root / ".hidden").mkdir()
        (root / "tests").mkdir()
        (root / "real-candidate").mkdir()
        _write_readme(root / "real-candidate", "**mirrors**: `x/y.md`\n")
        reports = check_all(root)
        assert len(reports) == 1
        assert reports[0].name == "real-candidate"
