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

from ss_github_bridge import cards, inbound, labels, mirror, returns, scan  # noqa: E402

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


# --- negative case 1: the emitted packet must meet Mesh Queue Contract v2 --
# Governed 27 verbs as listed in MESH_QUEUE/LENS/HANDOVER_QUEUE.json (verbs_27, read 2026-10-31).
GOVERNED_27 = (
    "sense", "map", "capture", "derive", "instantiates", "compound", "composes", "consumes", "route",
    "engage", "balance", "evidences", "join", "commit", "execute", "parent", "succeed", "package",
    "seize", "transform", "supersedes", "filter", "requires", "implements_candidate", "validates",
    "challenge", "verify",
)
PACKET_REQUIRED = ("id", "from", "verb", "goal", "context", "oba_test", "sources", "scope",
                   "expected_return", "priority", "created")


def packet_contract_errors(packet):
    """Transcription of MESH_QUEUE_CONTRACT_v2 'Packet (JSON <= 4 KB)'. Malformed = worker returns HOLD."""
    errs = [f"missing {k}" for k in PACKET_REQUIRED if k not in packet]
    if packet.get("verb") not in GOVERNED_27:
        errs.append("verb not in the governed 27")
    oba = packet.get("oba_test")
    if isinstance(oba, dict):
        errs += [f"oba_test missing {k}" for k in ("outcome", "measure", "benefit", "asset", "boundary") if k not in oba]
    srcs = packet.get("sources")
    if isinstance(srcs, list):
        import re as _re
        for s in srcs:
            if not (isinstance(s, dict) and s.get("path") and _re.fullmatch(r"[0-9a-f]{64}", str(s.get("sha256", "")))):
                errs.append(f"bad source entry {s!r}")
        if not srcs:
            errs.append("no sources")
    scope = packet.get("scope")
    if isinstance(scope, dict):
        errs += [f"scope missing {k}" for k in ("allowed", "excluded", "release_class") if k not in scope]
        if not str(scope.get("release_class", "")).startswith("RC-"):
            errs.append("unknown release class")
    if packet.get("priority") not in ("NOW", "WATCH"):
        errs.append("priority must be NOW or WATCH")
    if len(json.dumps(packet).encode()) > 4096:
        errs.append("over 4 KB")
    return errs


H64 = "a" * 64


def test_inbound_packet_meets_mesh_queue_v2_contract():
    p = returns.inbound_packet("PKT-20261031-GHB-001", "github-bridge-dry-run", "8 signals -> 5 cards",
                               {"MESH_QUEUE/STREAMS/DRAFTS/x.json": H64}, "2026-10-31")
    assert packet_contract_errors(p) == []
    assert "release_class" not in p and "excluded" not in p      # they belong inside scope
    assert p["scope"]["release_class"] == "RC-00"


def test_contract_validator_rejects_the_old_packet_shape():
    old = {"id": "PKT-1", "from": "claude-code", "verb": "implements_candidate", "context": "CTX-SS",
           "release_class": "RC-00", "job": "x", "artefacts": [], "excluded": [], "priority": "WATCH",
           "created": "2026-10-31"}
    errs = packet_contract_errors(old)
    for k in ("goal", "oba_test", "sources", "scope", "expected_return"):
        assert f"missing {k}" in errs
    assert packet_contract_errors({**old, "verb": "nine-verb loop"}).count("verb not in the governed 27") == 1


def test_committed_golden_packet_meets_the_contract():
    golden = json.load(open(HERE / "expected" / "INBOX" / "PKT-20261031-GHB-001.json"))
    assert packet_contract_errors(golden) == []


# --- negative case 2: a merged PR is a learning Signal and must not be deleted ---
def _pr(number, **kw):
    return {"number": number, "title": f"PR {number} change", "body": "", "html_url": f"u/{number}", **kw}


def test_merged_pr_is_kept_in_both_api_shapes_and_other_non_open_are_still_deleted():
    payload = {"repo": "o/r", "pulls": [
        _pr(1, state="closed", merged_at="2026-10-31T06:04:26Z"),   # REST: closed + merged_at
        _pr(2, state="MERGED"),                                      # GraphQL shape
        _pr(3, state="open"),                                        # control: open PR kept
        _pr(4, state="closed", merged_at=None),                      # control: closed unmerged dropped
    ], "issues": [{"number": 9, "state": "CLOSED", "title": "Old issue", "body": "", "html_url": "u/9"}]}
    out = cards.build_cards(inbound.signals_from_payload("o/r", payload), cap=None)
    kept = {c["merged_signals"][0].split("#")[-1]: c for c in out["cards"]}
    assert set(kept) == {"1", "2", "3"}
    assert kept["1"]["evidence"]["state"] == "merged" and kept["2"]["evidence"]["state"] == "merged"
    assert kept["3"]["evidence"]["state"] == "open"
    assert sorted(out["deleted"]) == ["o/r#issue#9", "o/r#pull_request#4"]
    assert all(cards.validate_card(c) == [] for c in out["cards"])
