"""Tests for mesh_pointer_check.py (candidate C1, PKT-20261031-003)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mesh_pointer_check import REQUIRED_POINTERS, main, missing_pointers  # noqa: E402

REPO_CLAUDE_MD = Path(__file__).resolve().parent.parent.parent / "CLAUDE.md"


def test_real_claude_md_carries_every_pointer():
    assert missing_pointers(REPO_CLAUDE_MD.read_text(encoding="utf-8")) == []


def test_stripped_text_is_detected():
    stripped = REPO_CLAUDE_MD.read_text(encoding="utf-8").replace("NAVIGATOR_STATE_CAPSULE.json", "")
    assert missing_pointers(stripped) == ["NAVIGATOR_STATE_CAPSULE.json"]


def test_empty_text_misses_all():
    assert missing_pointers("") == list(REQUIRED_POINTERS)


def test_cli_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.md"
    good.write_text(" ".join(REQUIRED_POINTERS), encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("nothing here", encoding="utf-8")
    assert main([str(good)]) == 0
    assert main([str(bad)]) == 1
    assert "[MISSING] MESH_QUEUE/CURRENT.md" in capsys.readouterr().out
