import copy, json, subprocess, sys
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from ss_scaffold import report, rules  # noqa: E402

DOC = json.load(open(HERE / "fixtures" / "generic_context.json"))


def fresh():
    return copy.deepcopy(DOC)


# --- fixture: 0 of 13 accepted (the number the packet expects) ----------------
def test_fixture_raci_is_zero_of_thirteen_accepted():
    r = rules.validate_raci(DOC["raci"])
    assert r["coverage"] == {"n": 0, "of": 13, "text": "0 of 13"}
    assert r["errors"] == []                      # proposals are gaps, not violations
    assert any("proposal" in g for g in r["gaps"])


# --- RACI rules ---------------------------------------------------------------
def test_two_accountables_fail():
    d = fresh(); d["raci"]["rows"][4]["cells"][0] = "A"; d["raci"]["rows"][4]["cells"][1] = "A"
    assert any("2 Accountable cells" in e for e in rules.validate_raci(d["raci"])["errors"])


def test_decider_without_real_decision_fails():
    d = fresh(); d["raci"]["rows"][12].pop("decision")
    assert any("Decider present" in e for e in rules.validate_raci(d["raci"])["errors"])


def test_missing_revision_date_fails():
    d = fresh(); d["raci"].pop("revision_date")
    assert any("revision_date" in e for e in rules.validate_raci(d["raci"])["errors"])


def test_proposed_cells_never_count_and_accepted_row_does():
    d = fresh()
    row = d["raci"]["rows"][0]
    row["cells"] = [{"role": "R", "accepted": True}, "[n]", "[n]", "[n]", "[n]", "[n]"]
    row["accountable"] = {"party": "P1", "accepted": True}
    assert rules.validate_raci(d["raci"])["coverage"]["n"] == 0          # no acceptance evidence yet
    row["acceptance_evidence"] = "REVIEWS row, source path"
    assert rules.validate_raci(d["raci"])["coverage"]["n"] == 1


def test_accountable_with_proposal_wording_does_not_count_even_with_evidence():
    d = fresh(); row = d["raci"]["rows"][0]
    row["cells"] = [{"role": "R", "accepted": True}] + ["[n]"] * 5
    row["accountable"] = "P1 (proposal)"; row["acceptance_evidence"] = "x"
    assert rules.validate_raci(d["raci"])["coverage"]["n"] == 0


# --- contribution test --------------------------------------------------------
def test_target_without_bear_case_fails():
    r = rules.validate_contribution(DOC["contribution_test"])
    assert any("benefit B1: has a target and no bear case" in e for e in r["errors"])
    assert r["coverage"]["text"] == "1 of 2"


def test_operational_benefit_needs_verdict_keep():
    rows = [{"benefit": "B9", "kind": "operational", "has_target": False, "in_chain": True, "verdict": "reframe"}]
    assert any("operational" in e for e in rules.validate_contribution(rows)["errors"])


def test_bad_verdict_value_fails():
    rows = [{"benefit": "B9", "verdict": "maybe"}]
    assert any("verdict" in e for e in rules.validate_contribution(rows)["errors"])


# --- baselines ----------------------------------------------------------------
def test_zero_baseline_without_observed_fails():
    rows = [{"id": "X", "baseline": 0.0, "observed": False}]
    assert any("never 0" in e for e in rules.validate_baselines(rows)["errors"])


def test_zero_baseline_with_observed_is_valid():
    rows = [{"id": "X", "baseline": 0.0, "observed": True, "unit": "t", "as_at": "2026-10-01", "source": "s"}]
    r = rules.validate_baselines(rows)
    assert r["errors"] == [] and r["coverage"]["n"] == 1


def test_target_without_observed_baseline_is_a_gap_not_an_error():
    r = rules.validate_baselines(DOC["baselines"])
    assert r["errors"] == [] and r["coverage"]["text"] == "1 of 2"
    assert any("cannot be tested" in g for g in r["gaps"])


# --- shock readiness ----------------------------------------------------------
def test_high_dependence_without_mitigation_fails():
    rows = [{"id": "X", "shocks": {"finance_shock": {"dependence": "high", "evidence": "e"}}}]
    assert any("no mitigation" in e for e in rules.validate_shock(rows)["errors"])


def test_key_person_dependence_needs_owner_and_successor():
    rows = [{"id": "X", "shocks": {"key_person_lost": {"dependence": "low", "evidence": "e"}}}]
    assert any("successor role" in e for e in rules.validate_shock(rows)["errors"])
    rows[0]["shocks"]["key_person_lost"].update(owner="P1", successor_role="deputy")
    assert rules.validate_shock(rows)["errors"] == []


def test_shock_coverage_counts_all_five_shocks_per_row():
    r = rules.validate_shock(DOC["shock_readiness"])
    assert r["coverage"] == {"n": 1, "of": 5, "text": "1 of 5"}


# --- whole-document behaviour and report ---------------------------------------
def test_absent_module_is_not_supplied_never_zero():
    d = fresh(); d.pop("baselines")
    text = report.render("CTX-GENERIC-A", rules.validate_context(d))
    assert "- baselines: [n] not supplied" in text and "baselines: 0" not in text


def test_report_has_one_verb_and_one_tested_number():
    text = report.render("CTX-GENERIC-A", rules.validate_context(DOC))
    assert text.count("**Verb:**") == 1 and text.count("**Tested number:**") == 1
    assert "RACI coverage 0 of 13 accepted" in text and "Potential" in text


def test_cli_writes_one_report_per_context_and_nothing_else(tmp_path):
    other = fresh(); other["context"] = "CTX-GENERIC-B"
    p2 = tmp_path / "b.json"; p2.write_text(json.dumps(other))
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, "-m", "ss_scaffold", str(HERE / "fixtures" / "generic_context.json"), str(p2), "--out", str(out)],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert sorted(f.name for f in out.iterdir()) == ["CTX-GENERIC-A--scaffold-report.md", "CTX-GENERIC-B--scaffold-report.md"]


def test_no_context_or_third_party_names_in_the_package():
    banned = ("avalira", "powerwells", "basin", "actioncoach", "pnyssen")
    for f in list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.json")) + list(ROOT.rglob("*.md")):
        if f.name == "test_scaffold.py":
            continue
        text = f.read_text().lower()
        assert not any(b in text for b in banned), f
