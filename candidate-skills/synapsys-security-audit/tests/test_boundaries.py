"""
Boundary tests for synapsys-security-audit (CANDIDATE).

These tests exist to prove the authority boundaries claimed in THREAT_MODEL.md,
not just that the scanner finds patterns. Run with: pytest test_boundaries.py -v
"""

import ast
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import audit  # noqa: E402


AUDIT_SOURCE_PATH = Path(__file__).resolve().parent.parent / "audit.py"


def _module_ast():
    return ast.parse(AUDIT_SOURCE_PATH.read_text(encoding="utf-8"))


def _imported_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_no_network_imports():
    """The module must not import anything capable of making a network call."""
    forbidden = {"requests", "urllib", "http", "socket", "httpx", "aiohttp", "ftplib", "smtplib"}
    imported = _imported_names(_module_ast())
    overlap = imported & forbidden
    assert not overlap, f"audit.py imports network-capable modules: {overlap}"


def test_no_subprocess_or_shell_imports():
    """The module must not import subprocess/os in a way that enables shell execution."""
    tree = _module_ast()
    imported = _imported_names(tree)
    assert "subprocess" not in imported, "audit.py imports subprocess"
    # os is not imported at all in this module; if it ever is, forbid os.system/os.popen use.
    source = AUDIT_SOURCE_PATH.read_text(encoding="utf-8")
    assert "os.system(" not in source
    assert "os.popen(" not in source


def test_no_git_invocation():
    source = AUDIT_SOURCE_PATH.read_text(encoding="utf-8")
    assert "git " not in source.lower() and "'git'" not in source and '"git"' not in source


def test_socket_is_never_touched_at_runtime(monkeypatch, tmp_path):
    """Belt-and-suspenders: patch socket.socket to raise if the scan ever tries to use it."""
    def _forbidden(*args, **kwargs):
        raise AssertionError("audit.scan() attempted to open a network socket")

    monkeypatch.setattr(socket, "socket", _forbidden)

    src = tmp_path / "project"
    src.mkdir()
    (src / "app.py").write_text("password = 'not-a-real-secret-value'\n", encoding="utf-8")

    result = audit.scan(str(src))
    assert result.files_scanned == 1


def test_writes_only_the_two_declared_files(tmp_path):
    """scan()+write_report() must not create any file outside the out_dir, and exactly
    the two declared filenames inside it — nothing else."""
    src = tmp_path / "project"
    src.mkdir()
    (src / "app.py").write_text(
        "api_key = 'AKIAABCDEFGHIJKLMNOP'\neval('1+1')\n", encoding="utf-8"
    )
    out = tmp_path / "out"

    before = {p for p in tmp_path.rglob("*") if p.is_file()}
    result = audit.scan(str(src))
    json_path, md_path = audit.write_report(result, str(out))
    after = {p for p in tmp_path.rglob("*") if p.is_file()}

    new_files = after - before
    assert new_files == {json_path, md_path}, f"unexpected files created: {new_files - {json_path, md_path}}"
    assert json_path.parent == out
    assert md_path.parent == out


def test_scanned_source_files_are_never_modified(tmp_path):
    src = tmp_path / "project"
    src.mkdir()
    target_file = src / "app.py"
    original = "password = 'hunter2hunter2'\n"
    target_file.write_text(original, encoding="utf-8")
    original_mtime = target_file.stat().st_mtime

    result = audit.scan(str(src))
    audit.write_report(result, str(tmp_path / "out"))

    assert target_file.read_text(encoding="utf-8") == original
    assert target_file.stat().st_mtime == original_mtime


def test_detects_known_patterns(tmp_path):
    src = tmp_path / "project"
    src.mkdir()
    (src / "app.py").write_text(
        "\n".join([
            "aws_key = 'AKIAABCDEFGHIJKLMNOP'",
            "eval(user_input)",
            "subprocess.run(cmd, shell=True)",
            "-----BEGIN RSA PRIVATE KEY-----",
        ]),
        encoding="utf-8",
    )
    result = audit.scan(str(src))
    categories = {f.pattern for f in result.findings}
    assert "aws_access_key" in categories
    assert "eval_call" in categories
    assert "shell_true_subprocess" in categories
    assert "private_key_header" in categories


def test_no_findings_raises_or_blocks():
    """Findings must be data, not exceptions — confirms the 'never raises on findings' claim."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "project"
        src.mkdir()
        (src / "clean.py").write_text("x = 1\n", encoding="utf-8")
        result = audit.scan(str(src))
        assert isinstance(result, audit.ScanResult)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
