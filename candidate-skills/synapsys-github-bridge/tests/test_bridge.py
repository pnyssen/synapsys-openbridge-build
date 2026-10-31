"""Unit tests (normaliser, label mapping, scan scoring, mirror plan) and the
dry-run golden check: CLI output must equal tests/expected byte for byte."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ss_github_bridge import cards, inbound, labels, mirror, scan  # noqa: E402

FIX = HERE / "fixtures"


def sig(type_="issue", title="t", body="", state="open", number=1):
    return {"repo": "o/r", "type": type_, "number": number, "title": title, "body": body,
            "state": state, "url": "u"}


# --- normaliser ---------------------------------------------------------
def test_card_fields_valid_and_potential():
    c = cards.normalise(sig(title="Add CI check for mirrors"))
    assert cards.validate_card(c) == []
    assert c["source_type"] == "github" and c["ppv"] == "Potential" and c["authority_state"].startswith("HELD")


@pytest.mark.parametrize("title,type_,expected", [
    ("Advisory GHSA-9xhq-2c8f-v4rm thing", "advisory", "security"),
    ("Who gives D007 release", "issue", "authority"),
    ("Odoo model field missing", "issue", "schema_field"),
    ("CI mcp-tests failure", "ci_failure", "tooling"),
    ("Something unrelated", "issue", "other"),
])
def test_categorise(title, type_, expected):
    assert cards.categorise(title, type_) == expected


def test_standard_refs_only_verbatim_and_unchecked():
    refs = cards.extract_standard_refs("see CVE-2099-12345 and CWE-79; OWASP LLM01 is not an id we match")
    assert [r["id"] for r in refs] == ["CVE-2099-12345", "CWE-79"]
    assert all(r["checked_on"] == cards.NOT_CHECKED and r["version"] == "[n]" for r in refs)
    assert cards.extract_standard_refs("no identifiers here") == []


def test_id_is_stable_and_validate_rejects_bad_enum():
    assert cards.card_id(sig()) == cards.card_id(sig())
    bad = cards.normalise(sig()); bad["category"] = "made_up"
    assert any("category" in e for e in cards.validate_card(bad))


def test_delete_merge_cap_order():
    s = [sig(number=1, title="Same thing"), sig(number=2, title="same  thing!"), sig(number=1, title="Same thing"),
         sig(number=3, state="closed"), sig("advisory", "Advisory x CVE-2099-1111", number=9),
         sig(number=4, title="Other widget")]
    out = cards.build_cards(s, cap=1)
    assert len(out["deleted"]) == 2          # exact duplicate + closed
    assert len(out["merged"]) == 1           # same category + normalised title
    assert [c["category"] for c in out["cards"]] == ["security"]   # cap keeps security first
    assert len(out["deferred_over_cap"]) == 2     # 3 cards after delete+merge, cap 1


# --- label mapping ------------------------------------------------------
def test_labels_for_card():
    c = cards.normalise(sig("advisory", "Advisory GHSA-9xhq-2c8f-v4rm"))
    assert labels.labels_for(c) == ["kind:defect", "category:security", "scope:synapsys_wide",
                                    "ppv:potential", "nist:manage"]


def test_mirror_eligibility_only_tooling_schema_security():
    for cat in cards.CATEGORIES:
        c = cards.normalise(sig()); c["category"] = cat
        assert labels.is_mirror_eligible(c) == (cat in ("tooling", "schema_field", "security"))


# --- mirror plan --------------------------------------------------------
def test_issue_links_wm_path_and_sha_and_plan_is_dry():
    c = cards.normalise(sig(title="Add CI check for mirrors"))
    p = mirror.issue_payload(c)
    assert mirror.card_wm_path(c) in p["body"] and mirror.card_sha256(c) in p["body"]
    plan = mirror.plan([c])
    assert plan["mode"] == "DRY_RUN" and plan["writes_performed"] == 0
    assert plan["canary"]["steps"][3].startswith("rollback: close")
    with pytest.raises(PermissionError):
        mirror.execute()


# --- inbound fixture ----------------------------------------------------
def test_inbound_fixture_counts():
    s = inbound.load_fixture(str(FIX / "github_payload.json"))
    kinds = sorted(x["type"] for x in s)
    assert kinds == ["advisory", "ci_failure", "issue", "issue", "issue", "issue", "issue", "pull_request"]


def test_live_without_token_stops(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(inbound.NeedsCredential):
        inbound.fetch_live("o/r")


# --- scan scoring -------------------------------------------------------
def test_scan_layers_first_vs_search_first():
    a = scan.score_lane(json.load(open(FIX / "calllog_layers_first.json")))
    b = scan.score_lane(json.load(open(FIX / "calllog_search_first.json")))
    assert a["layers_read_before_first_search_n"] == "5/5" and a["probes_scored"] == 3
    assert b["layers_read_before_first_search_n"] == "0/5"
    assert b["misses_corrected"] == 1                      # P1 miss then read of expected source
    assert [p["hit"] for p in b["per_probe"]] == [True, False]   # P4 miss never corrected


def test_p2_requires_the_gap_statement():
    log = {"lane": "x", "probes": [{"id": "P2", "calls": [],
           "answer_paths": ["MESH_QUEUE/KIT/FOUNDATION_INDEX_v1.md"], "states_gap": False}]}
    assert scan.score_lane(log)["per_probe"][0]["hit"] is False


# --- dry-run golden -----------------------------------------------------
def run_cli(out, *extra):
    env = dict(os.environ, PYTHONPATH=str(ROOT)); env.pop("GITHUB_TOKEN", None)
    return subprocess.run([sys.executable, "-m", "ss_github_bridge", "run", "--out", str(out), *extra],
                          cwd=ROOT, env=env, capture_output=True, text=True)


def test_dry_run_matches_expected_files(tmp_path):
    r = run_cli(tmp_path, "--fixture", str(FIX / "github_payload.json"),
                "--calllog", str(FIX / "calllog_layers_first.json"),
                "--calllog", str(FIX / "calllog_search_first.json"))
    assert r.returncode == 0, r.stderr
    exp = HERE / "expected"
    want = sorted(p.relative_to(exp).as_posix() for p in exp.rglob("*") if p.is_file())
    got = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert got == want
    for rel in want:
        assert (tmp_path / rel).read_bytes() == (exp / rel).read_bytes(), rel


def test_commit_flag_refused(tmp_path):
    r = run_cli(tmp_path, "--fixture", str(FIX / "github_payload.json"), "--commit")
    assert r.returncode == 3 and not list(tmp_path.iterdir())
