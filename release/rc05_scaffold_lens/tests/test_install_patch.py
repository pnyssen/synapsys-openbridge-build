import hashlib, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SCRIPT = os.environ.get("INSTALL_SH", os.path.join(ROOT, "install_patch.sh"))
HASHER = os.path.join(ROOT, "..", "rc04g_baseline", "rc04g_baseline_hash_20261126_v3.sh")
def sh(cmd, **kw): return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); d = self.d
        os.makedirs(f"{d}/a/synapsys/controllers"); os.makedirs(f"{d}/b/synapsys/controllers"); os.makedirs(f"{d}/rep"); os.makedirs(f"{d}/bin")
        for base in ("a", "b"):
            open(f"{d}/{base}/synapsys/__manifest__.py", "w").write("{'version': '1'}\n")
            open(f"{d}/{base}/synapsys/controllers/lenses.py", "w").write("x = 1\n")
        open(f"{d}/b/synapsys/controllers/lenses.py", "w").write("x = 2\n")
        open(f"{d}/b/synapsys/new_mod.py", "w").write("y = 3\n")
        sh(f"cd {d} && diff -ruN a b > patch.diff")
        self.patch = f"{d}/patch.diff"; self.psha = sha(self.patch)
        os.makedirs(f"{d}/addons"); shutil.copytree(f"{d}/a/synapsys", f"{d}/addons/synapsys")
        open(f"{d}/bin/docker", "w").write(f'#!/bin/sh\necho "$@" >> {d}/docker.log\nexit 0\n'); os.chmod(f"{d}/bin/docker", 0o755)
        self.pre = self.tree(f"{d}/addons"); self.post = self.tree_of_applied()
        self.env = f"ADDONS={d}/addons HASHER={HASHER} DOCKER={d}/bin/docker REPORTS={d}/rep WAIT=0"
    def tearDown(self): shutil.rmtree(self.d, ignore_errors=True)
    def tree(self, addons):
        r = sh(f"cd {self.d} && OUT={self.d}/rep/t_{os.urandom(4).hex()}.txt bash {HASHER} {addons}/synapsys | sed -n '/## tree hash/{{n;p}}'"); return r.stdout.strip()
    def tree_of_applied(self):
        shutil.copytree(f"{self.d}/addons", f"{self.d}/tmpapply"); sh(f"cd {self.d}/tmpapply && patch -p1 -s < {self.patch}"); t = self.tree(f"{self.d}/tmpapply"); return t
    def run_install(self, psha=None, pre=None, post=None, bk=None):
        bk = bk or f"{self.d}/backup"
        return sh(f"{self.env} bash {SCRIPT} {self.patch} {psha or self.psha} {pre or self.pre} {post or self.post} {bk}")
    def docker_calls(self): p = f"{self.d}/docker.log"; return open(p).read() if os.path.exists(p) else ""
    def unchanged(self): return self.tree(f"{self.d}/addons") == self.pre
    def test_I1_success(self):
        r = self.run_install(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for tag in ("PRESTATE_OK", "BACKUP_OK", "APPLIED", "PARSES_OK", "POSTSTATE_OK", "INSTALL_DONE"): self.assertIn(tag, r.stdout)
        self.assertEqual(self.tree(f"{self.d}/addons"), self.post); self.assertIn("restart", self.docker_calls())
        self.assertEqual(sh(f"diff -r {self.d}/backup {self.d}/a/synapsys").returncode, 0)
    def test_I2_wrong_patch_hash(self):
        r = self.run_install(psha="0" * 64); self.assertEqual(r.returncode, 1); self.assertIn("PATCH_HASH_MISMATCH", r.stdout)
        self.assertTrue(self.unchanged()); self.assertFalse(os.path.exists(f"{self.d}/backup")); self.assertEqual(self.docker_calls(), "")
    def test_I3_wrong_prestate(self):
        open(f"{self.d}/addons/synapsys/__manifest__.py", "a").write("# drift\n")
        r = self.run_install(); self.assertEqual(r.returncode, 1); self.assertIn("PRESTATE_MISMATCH", r.stdout)
        self.assertFalse(os.path.exists(f"{self.d}/backup")); self.assertEqual(self.docker_calls(), "")
        self.assertFalse(os.path.exists(f"{self.d}/addons/synapsys/new_mod.py"))
    def test_I4_existing_backup_refused(self):
        os.makedirs(f"{self.d}/backup"); r = self.run_install(); self.assertEqual(r.returncode, 1); self.assertIn("BACKUP_DIR_EXISTS", r.stdout); self.assertTrue(self.unchanged())
    def test_I5_poststate_mismatch_reverses_and_does_not_restart(self):
        r = self.run_install(post="f" * 64); self.assertEqual(r.returncode, 1); self.assertIn("POSTSTATE_MISMATCH", r.stdout); self.assertIn("REVERSED_PATCH", r.stdout)
        self.assertTrue(self.unchanged()); self.assertEqual(self.docker_calls(), "")
    def test_I6_patch_that_does_not_apply_changes_nothing(self):
        open(f"{self.d}/addons/synapsys/controllers/lenses.py", "w").write("x = 99\n"); self.pre = self.tree(f"{self.d}/addons")
        r = self.run_install(); self.assertEqual(r.returncode, 1); self.assertIn("DRYRUN_FAILED", r.stdout)
        self.assertEqual(self.tree(f"{self.d}/addons"), self.pre); self.assertEqual(self.docker_calls(), "")
    def test_I7_python_syntax_error_is_reversed(self):
        open(f"{self.d}/b/synapsys/new_mod.py", "w").write("def broken(:\n"); sh(f"cd {self.d} && diff -ruN a b > patch.diff")
        self.psha = sha(self.patch); r = self.run_install(post="0" * 64); self.assertEqual(r.returncode, 1); self.assertIn("PARSE_FAILED", r.stdout)
        self.assertTrue(self.unchanged()); self.assertEqual(self.docker_calls(), "")
    def test_I8_script_never_uses_rm(self):
        import re; code = "\n".join(l.split("#")[0] for l in open(SCRIPT).read().splitlines())
        self.assertIsNone(re.search(r"\brm\b", code)); self.assertIsNone(re.search(r"sudo|--force|rsync --delete|find .* -delete", code))
if __name__ == "__main__": unittest.main(verbosity=2)
