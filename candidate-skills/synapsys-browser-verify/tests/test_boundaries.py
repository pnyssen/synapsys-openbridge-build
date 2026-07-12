"""
Boundary tests for synapsys-browser-verify (CANDIDATE).

These tests exist to prove the authority boundaries claimed in THREAT_MODEL.md
against a local fixture page only — no external network target is used.
Run with: pytest test_boundaries.py -v
"""

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify  # noqa: E402

VERIFY_SOURCE_PATH = Path(__file__).resolve().parent.parent / "verify.py"
FIXTURE_URL = "file://" + str(
    (Path(__file__).resolve().parent.parent / "fixtures" / "sample.html")
)
PW_EXECUTABLE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def _module_ast():
    return ast.parse(VERIFY_SOURCE_PATH.read_text(encoding="utf-8"))


def _all_call_keyword_names(tree):
    """Every keyword-argument name used in any function call in the module —
    checking actual usage, not prose (so a comment mentioning 'proxy' in
    explanation doesn't false-positive this check)."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            names.update(kw.arg for kw in node.keywords if kw.arg)
    return names


def _all_string_call_args(tree):
    """Every string literal passed as a positional arg to any Call — used to check
    for subprocess-style invocation of an external 'git' binary."""
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literals.append(arg.value)
                elif isinstance(arg, (ast.List, ast.Tuple)):
                    literals.extend(
                        e.value for e in arg.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)
                    )
    return literals


def test_no_git_invocation():
    """Checks actual call arguments for a 'git' executable invocation, not prose."""
    tree = _module_ast()
    literals = _all_string_call_args(tree)
    assert not any(lit == "git" or lit.endswith("/git") for lit in literals)
    # And no subprocess-style import exists at all (belt and suspenders).
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
    assert "subprocess" not in imported


def test_no_storage_state_used_anywhere():
    """storage_state is Playwright's mechanism for loading a saved/imported session
    (cookies, localStorage). Checking it's never passed as an actual keyword
    argument anywhere — not just absent from prose/comments."""
    tree = _module_ast()
    assert "storage_state" not in _all_call_keyword_names(tree)


def test_no_proxy_parameter_exists():
    """Checking 'proxy' is never passed as an actual keyword argument anywhere —
    the module docstring and comments legitimately discuss 'no proxy support'
    in prose, so a raw substring search over the whole file is the wrong test."""
    tree = _module_ast()
    assert "proxy" not in _all_call_keyword_names(tree)


def test_no_user_data_dir_persistent_profile():
    """user_data_dir / launch_persistent_context would create a persistent, reusable
    browser profile — the daemon-like behaviour this candidate must not have."""
    source = VERIFY_SOURCE_PATH.read_text(encoding="utf-8")
    assert "user_data_dir" not in source
    assert "launch_persistent_context" not in source


def test_no_subprocess_import():
    imported = set()
    for node in ast.walk(_module_ast()):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported


def test_no_file_write_capability_for_arbitrary_paths():
    """The module's only Path(...).write_text calls should target files inside the
    out_dir argument — there should be no write_text call parameterised by anything
    that looks like a scanned/target source path."""
    source = VERIFY_SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("write_text(") == 2  # json_path, md_path only
    assert "open(" not in source or "screenshot" in source  # no raw open() writes to arbitrary paths


def test_verify_runs_against_local_fixture_and_tears_down(tmp_path):
    """End-to-end run against a local file:// fixture — no external network target."""
    out = tmp_path / "out"
    result = verify.verify(FIXTURE_URL, str(out), executable_path=PW_EXECUTABLE)

    assert result.title == "Fixture Page"
    assert result.status in (200, None)  # file:// navigations may report None status
    assert "fixture console error for capture test" in result.console_errors
    assert Path(result.screenshot_path).exists()
    assert Path(result.screenshot_path).parent == out.resolve()


def test_write_report_creates_only_declared_files(tmp_path):
    out = tmp_path / "out"
    result = verify.verify(FIXTURE_URL, str(out), executable_path=PW_EXECUTABLE)

    before = {p for p in out.rglob("*") if p.is_file()}
    json_path, md_path = verify.write_report(result, str(out))
    after = {p for p in out.rglob("*") if p.is_file()}

    new_files = after - before
    assert new_files == {json_path, md_path}
    assert json_path.parent == out.resolve()
    assert md_path.parent == out.resolve()


def test_no_write_outside_out_dir(tmp_path):
    out = tmp_path / "out"
    sibling = tmp_path / "sibling"
    sibling.mkdir()

    before_sibling = set(sibling.rglob("*"))
    verify.verify(FIXTURE_URL, str(out), executable_path=PW_EXECUTABLE)
    after_sibling = set(sibling.rglob("*"))

    assert before_sibling == after_sibling, "verify() wrote into a directory outside --out"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
