"""Isolated tests for ss-mcp-first-release.sh (CHG-2027-093).

Reuses the deployer harness: a throwaway git origin + VPS clone, a fake
`docker` that builds images from the real Dockerfile COPY set, and a file://
check-runs API. The VPS starts on a local-only commit, the way production runs
4d6d332 (not a commit on main), so `ss-mcp-deploy adopt` alone would refuse it.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from test_ss_mcp_deploy import Env, _git

HERE = Path(__file__).resolve().parents[1]
RELEASE = HERE / "ss-mcp-first-release.sh"
DEPLOYER_FILES = ("ss-mcp-deploy.sh", "ss-mcp-deploy.service", "ss-mcp-deploy.timer")
ENV_SECRET = "ENV-SECRET-MUST-NOT-APPEAR"


class ReleaseEnv(Env):
    def __init__(self, tmp: Path):
        super().__init__(tmp)
        # main carries the deployer, as it does after #56.
        self.write({f"deploy/mcp-vps/deployer/{f}": (HERE / f).read_text() for f in DEPLOYER_FILES})
        self.main = self.commit("deployer on main", green=True)
        _git(self.repo, "fetch", "-q", "origin")
        # Production: a hand-built local commit that is not on main.
        _git(self.repo, "-c", "advice.detachedHead=false", "checkout", "-q", "--detach", self.base)
        (self.repo / "mcp-servers" / "n8n_mcp.py").write_text("# n8n VPS-only hotfix\n")
        _git(self.repo, "commit", "-q", "-am", "vps-only hotfix")
        self.vps_only = _git(self.repo, "rev-parse", "HEAD")
        self.docker_up_from(self.vps_only)
        (self.repo / "deploy" / "mcp-vps" / ".env").write_text(f"TOKEN={ENV_SECRET}\n")
        self.bin = tmp / "sbin" / "ss-mcp-deploy"
        self.bin.parent.mkdir()
        self.units = tmp / "units"
        self.units.mkdir()
        self.env.update({
            "SS_PUBLIC_URL": str(self.origin), "SS_DEPLOYER_BIN": str(self.bin),
            "SS_UNIT_DIR": str(self.units), "SS_SYSTEMCTL": "true",
            "SS_SKIP_HOST_PREFLIGHT": "1", "SS_ALLOW_NONROOT": "1",
        })

    def release(self, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(RELEASE), *args], env={**self.env, **extra},
                              capture_output=True, text=True)


@pytest.fixture
def renv(tmp_path):
    for tool in ("git", "flock", "curl", "sha256sum", "python3"):
        if shutil.which(tool) is None:
            pytest.skip(f"{tool} not available")
    return ReleaseEnv(tmp_path)


def _all_output(renv, *results) -> str:
    return renv.logtext() + "".join(r.stdout + r.stderr for r in results)


def test_bash_syntax():
    assert subprocess.run(["bash", "-n", str(RELEASE)]).returncode == 0


def test_plain_adopt_would_refuse_the_vps_only_build(renv):
    # Why this script exists: the deployer correctly refuses to adopt main.
    r = renv.run("adopt", renv.main)
    assert r.returncode == 1
    assert "HOLD adopt" in renv.logtext()


def test_preflight_is_read_only(renv):
    r = renv.release()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PREFLIGHT OK" in r.stdout
    assert _git(renv.repo, "rev-parse", "HEAD") == renv.vps_only
    assert renv.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n VPS-only hotfix\n"
    assert not renv.bin.exists() and renv.deployed() is None
    assert not (renv.state / "first_release_rollback").exists()


def test_apply_releases_main_and_adopts_with_provenance(renv):
    r = renv.release("--apply")
    assert r.returncode == 0, _all_output(renv, r)
    assert renv.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    assert renv.ctr("odoo-mcp", "odoo_mcp.py") == "# odoo v1\n"
    assert renv.deployed() == renv.main
    assert renv.bin.exists() and (renv.units / "ss-mcp-deploy.timer").exists()
    assert not (renv.state / "auto_deploy_enabled").exists()  # timer stays OFF
    assert "provenance:  OK" in r.stdout
    rb = (renv.state / "first_release_rollback").read_text()
    assert f"sha {renv.vps_only}" in rb and "image n8n-mcp mcp-vps-n8n-mcp" in rb
    assert ENV_SECRET not in _all_output(renv, r)


def test_apply_health_failure_rolls_back_to_the_vps_build(renv):
    renv.write({"mcp-servers/n8n_mcp.py": "# n8n BROKEN_HEALTH\n"})
    bad = renv.commit("broken main", green=True)
    r = renv.release("--apply", bad)
    assert r.returncode == 1
    log = renv.logtext()
    assert "FAIL health n8n-mcp" in log and "auto-rollback verified" in log
    assert renv.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n VPS-only hotfix\n"
    assert _git(renv.repo, "rev-parse", "HEAD") == renv.vps_only
    assert renv.deployed() is None


@pytest.mark.parametrize("ci", ["failure", None])
def test_target_without_green_ci_is_held(renv, ci):
    renv.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    sha = renv.commit("unverified", green=None)
    if ci:
        renv.set_ci(sha, ci)
    r = renv.release("--apply", sha)
    assert r.returncode == 1
    assert "not green" in renv.logtext()
    assert renv.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n VPS-only hotfix\n"


def test_target_not_on_main_is_held(renv):
    r = renv.release("--apply", renv.vps_only)
    assert r.returncode == 1
    assert "is not on origin/main" in renv.logtext()


def test_tracked_local_edits_are_held(renv):
    (renv.repo / "mcp-servers" / "odoo_mcp.py").write_text("# hand edit\n")
    r = renv.release("--apply")
    assert r.returncode == 1
    assert "tracked local edits" in renv.logtext()
    assert renv.deployed() is None


def test_missing_env_is_held(renv):
    (renv.repo / "deploy" / "mcp-vps" / ".env").unlink()
    r = renv.release()
    assert r.returncode == 1
    assert ".env missing" in renv.logtext()


def test_manual_rollback_restores_pre_release_state(renv):
    assert renv.release("--apply").returncode == 0, renv.logtext()
    r = renv.release("--rollback")
    assert r.returncode == 0, _all_output(renv, r)
    assert renv.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n VPS-only hotfix\n"
    assert _git(renv.repo, "rev-parse", "HEAD") == renv.vps_only
    assert renv.deployed() is None
    assert "ROLLBACK done" in renv.logtext()


def test_credentialed_remote_is_replaced_and_never_printed(renv):
    token_url = "https://x-access-token:ghp_FAKE0123456789@example.invalid/o/r.git"
    _git(renv.repo, "remote", "set-url", "origin", token_url)
    pre = renv.release()
    assert pre.returncode == 0, _all_output(renv, pre)
    assert "carries credentials" in pre.stdout
    r = renv.release("--apply")
    assert r.returncode == 0, _all_output(renv, r)
    assert _git(renv.repo, "remote", "get-url", "origin") == str(renv.origin)
    assert "ghp_FAKE" not in _all_output(renv, pre, r)


def test_refuses_to_run_from_inside_the_checkout(renv):
    inside = renv.repo / "ss-mcp-first-release.sh"
    shutil.copy(RELEASE, inside)
    r = subprocess.run(["bash", str(inside), "--apply"], env=renv.env, capture_output=True, text=True)
    assert r.returncode == 1
    assert "run a copy from outside" in r.stdout
    assert _git(renv.repo, "rev-parse", "HEAD") == renv.vps_only
    assert not (renv.state / "first_release_rollback").exists()
