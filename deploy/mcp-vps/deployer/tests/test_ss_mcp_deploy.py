"""Isolated tests for ss-mcp-deploy.sh (CHG-2027-093).

Every scenario runs the real script against a throwaway git origin + clone,
a fake `docker` that builds "images" from the checkout exactly as the
Dockerfile's COPY lines say and runs "containers" as copies of them, and a
file:// stand-in for the GitHub check-runs API. Nothing touches a real
Docker daemon, GitHub, or the VPS.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "ss-mcp-deploy.sh"
GH_REPO = "o/r"

FAKE_DOCKER = r'''#!/usr/bin/env python3
import hashlib, os, shutil, sys
from pathlib import Path
root = Path(os.environ["FAKE_DOCKER_ROOT"]); images = root / "images"; ctrs = root / "containers"
a = sys.argv[1:]
img = lambda s: f"mcp-vps-{s}"
def copy(src, dst):
    shutil.rmtree(dst, ignore_errors=True); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copytree(src, dst)
if a[0] == "compose":
    a = a[3:]
    if a[0] == "up":
        svcs = [x for x in a[1:] if not x.startswith("-")]
        if "--build" in a:
            if os.environ.get("FAKE_BUILD_FAIL"): sys.exit(1)
            for s in svcs:
                d = images / img(s); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
                for line in open("deploy/mcp-vps/Dockerfile"):
                    p = line.split()
                    if p and p[0] == "COPY":
                        for src in p[1:-1]:
                            if src.startswith("mcp-servers/"): shutil.copy(src, d / Path(src).name)
        for s in svcs: copy(images / img(s), ctrs / s)
    elif a[0] == "images":
        if (images / img(a[-1])).exists(): print(img(a[-1]))
    elif a[0] == "config":
        print(img(a[-1]))
    elif a[0] == "exec":
        s, rest = a[2], a[3:]
        if rest[0] == "sha256sum":
            f = ctrs / s / Path(rest[1]).name
            if not f.exists(): sys.exit(1)
            print(hashlib.sha256(f.read_bytes()).hexdigest() + "  " + rest[1])
        else:  # health probe
            entry = ctrs / s / ("odoo_mcp.py" if s == "odoo-mcp" else "n8n_mcp.py")
            sys.exit(1 if b"BROKEN_HEALTH" in entry.read_bytes() else 0)
elif a[:2] == ["image", "inspect"]:
    sys.exit(0 if (images / a[2]).exists() else 1)
elif a[0] == "tag":
    copy(images / a[1], images / a[2])
'''


def _git(cwd: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout.strip()


class Env:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.origin = tmp / "origin.git"
        self.work = tmp / "work"      # where "the Steward" merges to main
        self.repo = tmp / "vps-src"   # the VPS checkout the deployer manages
        self.state = tmp / "state"
        self.fake = tmp / "fake"
        self.gh = tmp / "gh"
        self.log = tmp / "deploy.log"
        docker = tmp / "docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(0o755)
        self.env = {**os.environ, "SS_REPO": str(self.repo), "SS_STATE_DIR": str(self.state),
                    "SS_LOG": str(self.log), "SS_DOCKER": str(docker), "SS_HEALTH_WAIT": "0",
                    "SS_GH_API": f"file://{self.gh}", "SS_GH_REPO": GH_REPO,
                    "FAKE_DOCKER_ROOT": str(self.fake)}

        _git(tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        _git(tmp, "clone", "-q", str(self.origin), str(self.work))
        self.write({
            "deploy/mcp-vps/Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\n"
                                         "COPY mcp-servers/requirements.txt .\n"
                                         "COPY mcp-servers/odoo_mcp.py mcp-servers/n8n_mcp.py mcp-servers/_shared.py ./\n",
            "deploy/mcp-vps/docker-compose.yml": "services: {}\n",
            "mcp-servers/requirements.txt": "fastmcp==4.1.1\n",
            "mcp-servers/odoo_mcp.py": "# odoo v1\n",
            "mcp-servers/n8n_mcp.py": "# n8n v1\n",
            "mcp-servers/_shared.py": "# shared v1\n",
        })
        self.base = self.commit("base", green=True)
        _git(tmp, "clone", "-q", str(self.origin), str(self.repo))
        # What production is running now: built from base.
        self.docker_up_from(self.base)

    def write(self, files: dict[str, str]) -> None:
        for rel, content in files.items():
            p = self.work / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

    def commit(self, msg: str, *, green: bool | None, force: bool = False) -> str:
        _git(self.work, "add", "-A")
        _git(self.work, "commit", "-q", "-m", msg)
        _git(self.work, "push", "-q", *(["-f"] if force else []), "origin", "HEAD:main")
        sha = _git(self.work, "rev-parse", "HEAD")
        if green is not None:
            self.set_ci(sha, "success" if green else "failure")
        return sha

    def set_ci(self, sha: str, conclusion: str, status: str = "completed") -> None:
        d = self.gh / "repos" / GH_REPO / "commits" / sha
        d.mkdir(parents=True, exist_ok=True)
        (d / "check-runs").write_text(json.dumps({"check_runs": [
            {"name": "test", "status": status, "conclusion": conclusion, "started_at": "2026-10-22T00:00:00Z"},
        ]}))

    def docker_up_from(self, sha: str) -> None:
        _git(self.repo, "-c", "advice.detachedHead=false", "checkout", "-q", "--detach", sha)
        subprocess.run([self.env["SS_DOCKER"], "compose", "-f", "x", "up", "-d", "--build", "odoo-mcp", "n8n-mcp"],
                       cwd=self.repo, env=self.env, check=True)

    def ctr(self, svc: str, name: str) -> str:
        return (self.fake / "containers" / svc / name).read_text()

    def run(self, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(SCRIPT), *args], env={**self.env, **extra},
                              capture_output=True, text=True)

    def deployed(self) -> str | None:
        p = self.state / "deployed_sha"
        return p.read_text().strip() if p.exists() else None

    def logtext(self) -> str:
        return self.log.read_text() if self.log.exists() else ""

    def adopt_and_enable(self) -> None:
        assert self.run("adopt", self.base).returncode == 0, self.logtext()
        assert self.run("enable", "CHG-2027-093").returncode == 0, self.logtext()


@pytest.fixture
def env(tmp_path):
    for tool in ("git", "flock", "curl", "sha256sum", "python3"):
        if shutil.which(tool) is None:
            pytest.skip(f"{tool} not available")
    return Env(tmp_path)


def test_bash_syntax():
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0


# --- gates before anything is deployed --------------------------------------

def test_run_is_held_until_enabled(env):
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    env.commit("n8n change", green=True)
    assert env.run("adopt", env.base).returncode == 0
    r = env.run("run")
    assert r.returncode == 0
    assert "HOLD auto-deploy disabled" in env.logtext()
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    assert env.deployed() == env.base


def test_adopt_refused_when_running_source_differs(env):
    # Production is running a VPS-only build that is not any commit on main.
    (env.fake / "containers" / "n8n-mcp" / "n8n_mcp.py").write_text("# n8n VPS-only hotfix\n")
    r = env.run("adopt", env.base)
    assert r.returncode == 1
    assert "HOLD adopt" in env.logtext() and "n8n-mcp:n8n_mcp.py differs" in env.logtext()
    assert env.deployed() is None


def test_enable_requires_change_ref_and_verified_baseline(env):
    assert env.run("enable", "please").returncode == 2
    assert env.run("enable", "CHG-2027-093").returncode == 1  # no baseline yet
    assert not (env.state / "auto_deploy_enabled").exists()
    env.adopt_and_enable()
    assert (env.state / "auto_deploy_enabled").read_text().startswith("CHG-2027-093 ")
    assert env.run("disable").returncode == 0
    assert not (env.state / "auto_deploy_enabled").exists()


def test_divergent_history_is_hold_not_deploy(env):
    env.adopt_and_enable()
    # Rewrite main so the deployed SHA is no longer an ancestor.
    _git(env.work, "checkout", "-q", "--orphan", "rewritten")
    env.write({"mcp-servers/n8n_mcp.py": "# n8n rewritten\n"})
    new = env.commit("rewritten history", green=True, force=True)
    r = env.run("run")
    assert r.returncode == 1
    assert "HOLD divergent deployment history" in env.logtext()
    assert "WARN" not in env.logtext()
    assert env.deployed() == env.base
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    assert new not in (env.state / "deployed_sha").read_text()


@pytest.mark.parametrize("ci", ["failure", "in_progress", None])
def test_commit_without_green_ci_is_held(env, ci):
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    sha = env.commit("n8n change", green=None)
    if ci == "failure":
        env.set_ci(sha, "failure")
    elif ci == "in_progress":
        env.set_ci(sha, None, status="in_progress")
    r = env.run("run")
    assert r.returncode == 0
    assert "not green on this commit" in env.logtext()
    assert env.deployed() == env.base
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"


def test_drift_since_baseline_is_held(env):
    env.adopt_and_enable()
    (env.fake / "containers" / "odoo-mcp" / "_shared.py").write_text("# hand-edited in container\n")
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    env.commit("n8n change", green=True)
    r = env.run("run")
    assert r.returncode == 1
    assert "HOLD drift" in env.logtext()
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"


def test_local_edits_block_deploy(env):
    env.adopt_and_enable()
    (env.repo / "mcp-servers" / "odoo_mcp.py").write_text("# local edit on VPS\n")
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    env.commit("n8n change", green=True)
    assert env.run("run").returncode == 1
    assert "HOLD local edits" in env.logtext()


# --- deploy, verify, roll back -----------------------------------------------

def test_happy_path_rebuilds_only_changed_service_with_provenance(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    new = env.commit("n8n change", green=True)
    r = env.run("run")
    assert r.returncode == 0, env.logtext()
    assert env.deployed() == new
    assert (env.state / "previous_sha").read_text().strip() == env.base
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v2\n"
    assert env.ctr("odoo-mcp", "n8n_mcp.py") == "# n8n v1\n"  # odoo not rebuilt
    ident = (env.state / "rollback_identity").read_text()
    assert f"sha {env.base}" in ident and "image n8n-mcp mcp-vps-n8n-mcp" in ident
    assert "OK deployed" in env.logtext() and "provenance verified" in env.logtext()


def test_health_failure_rolls_back_to_verified_previous_source(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2 BROKEN_HEALTH\n"})
    new = env.commit("broken n8n", green=True)
    r = env.run("run")
    assert r.returncode == 1
    log = env.logtext()
    assert "FAIL health n8n-mcp" in log and "ROLLBACK done" in log and "(verified)" in log
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    assert env.deployed() == env.base
    assert (env.state / "failed_sha").read_text().strip() == new
    # The failed commit is not retried.
    env.log.write_text("")
    assert env.run("run").returncode == 0
    assert "DEPLOY" not in env.logtext()


def test_build_failure_rolls_back(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/_shared.py": "# shared v2\n"})
    env.commit("shared change", green=True)
    r = env.run("run", FAKE_BUILD_FAIL="1")
    assert r.returncode == 1
    assert "FAIL build" in env.logtext() and "ROLLBACK done" in env.logtext()
    assert env.ctr("odoo-mcp", "_shared.py") == "# shared v1\n"
    assert env.deployed() == env.base


def test_manual_rollback_restores_and_verifies_previous(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/_shared.py": "# shared v2\n"})
    env.commit("shared change", green=True)
    assert env.run("run").returncode == 0
    assert env.ctr("odoo-mcp", "_shared.py") == "# shared v2\n"
    r = env.run("rollback")
    assert r.returncode == 0, env.logtext()
    assert env.ctr("odoo-mcp", "_shared.py") == "# shared v1\n"
    assert env.ctr("n8n-mcp", "_shared.py") == "# shared v1\n"
    assert env.deployed() == env.base


def test_rollback_that_cannot_be_verified_reports_failure(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/_shared.py": "# shared v2\n"})
    env.commit("shared change", green=True)
    assert env.run("run").returncode == 0
    shutil.rmtree(env.fake / "images" / "ss-prev")  # rollback images lost
    r = env.run("rollback")
    assert r.returncode == 1
    assert "ROLLBACK FAILED provenance" in env.logtext()
    assert "ROLLBACK done" not in env.logtext().split("ROLLBACK to")[-1]


def test_env_file_is_never_read(env):
    secret = "ENV-SECRET-MUST-NOT-APPEAR"
    # Untracked and NOT git-ignored, exactly as on the VPS: must neither be
    # read nor count as a local edit that blocks the deploy.
    (env.repo / "deploy" / "mcp-vps" / ".env").write_text(f"TOKEN={secret}\n")
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    env.commit("n8n change", green=True)
    r = env.run("run")
    st = env.run("status")
    assert r.returncode == 0, env.logtext()
    assert secret not in env.logtext() + r.stdout + r.stderr + st.stdout + st.stderr


def test_manual_rollback_is_not_redeployed_by_the_timer(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2 (bad but healthy)\n"})
    bad = env.commit("bad n8n", green=True)
    assert env.run("run").returncode == 0
    assert env.run("rollback").returncode == 0, env.logtext()
    assert (env.state / "failed_sha").read_text().strip() == bad
    env.log.write_text("")
    assert env.run("run").returncode == 0
    assert "DEPLOY" not in env.logtext()
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    # A new merge is deployed as usual.
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v3\n"})
    env.commit("fixed n8n", green=True)
    assert env.run("run").returncode == 0, env.logtext()
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v3\n"


def test_manual_rollback_restores_only_last_rebuilt_services(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/_shared.py": "# shared v2\n"})          # X -> Y rebuilds both
    y = env.commit("shared change", green=True)
    assert env.run("run").returncode == 0, env.logtext()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})             # Y -> Z rebuilds n8n only
    env.commit("n8n change", green=True)
    assert env.run("run").returncode == 0, env.logtext()
    r = env.run("rollback")
    assert r.returncode == 0, env.logtext()
    assert env.deployed() == y
    assert env.ctr("odoo-mcp", "_shared.py") == "# shared v2\n"      # not reverted to X's stale image
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v1\n"
    assert env.ctr("n8n-mcp", "_shared.py") == "# shared v2\n"
    assert "ROLLBACK done" in env.logtext()


def test_rollback_without_matching_identity_changes_nothing(env):
    env.adopt_and_enable()
    env.write({"mcp-servers/n8n_mcp.py": "# n8n v2\n"})
    new = env.commit("n8n change", green=True)
    assert env.run("run").returncode == 0
    (env.state / "rollback_identity").write_text("sha deadbeef\n")
    assert env.run("rollback").returncode == 1
    assert "rollback identity missing" in env.logtext()
    assert env.deployed() == new
    assert env.ctr("n8n-mcp", "n8n_mcp.py") == "# n8n v2\n"
