"""Reproduces the five RC01 defects against the ORIGINAL candidate (commit c570366e). Loads the base source with `git show`; every assertion states the
DEFECT as observed. If a future change makes one of these fail, the base is not what this return says it is. v2 fixes are asserted in test_worker_reliability.py."""
import importlib.util, os, subprocess, sys, tempfile, unittest
BASE_COMMIT = 'c570366e78cdd2bad8fb2453cb748f2a1aecd432'
PATH = 'release/rc06a_screen_architecture/review/worker_reliability/worker_reliability.py'


def load_base():
    top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=os.path.dirname(os.path.abspath(__file__)), text=True).strip()
    src = subprocess.check_output(['git', 'show', '%s:%s' % (BASE_COMMIT, PATH)], cwd=top)
    p = os.path.join(tempfile.mkdtemp(), 'wr_base.py'); open(p, 'wb').write(src)
    spec = importlib.util.spec_from_file_location('wr_base', p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


B = load_base()
SPEC = {'needs': ['build'], 'right': 'source_build'}
OA = {'id': 'openai-n8n', 'capabilities': ['build'], 'rights': ['source_build'], 'available': True}
CL = {'id': 'claude-native', 'capabilities': ['build'], 'rights': ['source_build'], 'available': True}


def T(**k):
    t = {'id': 'task256', 'worker': 'openai-n8n', 'environment': 'openai-n8n', 'route': 'A', 'routed_at': 0, 'accepted_at': None, 'accepted_by': None,
         'progress_at': None, 'blocker': None, 'observed': {}, 'spec': SPEC, 'may_recover': True}
    t.update(k); return t


class ReproducedOnBase(unittest.TestCase):
    def test_F1_late_acceptance_yields_WAIT(self):
        self.assertEqual(B.evaluate(T(accepted_at=2220, accepted_by='openai-n8n'), 2221)['action'], 'WAIT')

    def test_F2_five_minute_clock_starts_at_acceptance(self):
        self.assertEqual(B.evaluate(T(accepted_at=59, accepted_by='openai-n8n'), 301)['action'], 'WAIT')

    def test_F3_authority_bypass_when_no_claim(self):
        r = B.recover(T(may_recover=False), B.ClaimStore(), [OA, CL], 'k', 10)
        self.assertTrue(r['recovered'])

    def test_F4_owner_deleted_before_alternate_checked(self):
        s = B.ClaimStore(); s.claim('k', 'openai-n8n', 1)
        r = B.recover(T(), s, [OA], 'k', 10)
        self.assertFalse(r['recovered']); self.assertNotIn('k', s.owner)                      # task now has no owner

    def test_F5_route_scoped_key_allows_two_owners(self):
        s = B.ClaimStore()
        a = s.claim(B.idempotency_key('task256', 'route-A', 'h'), 'openai-n8n', 1); b = s.claim(B.idempotency_key('task256', 'route-B', 'h'), 'claude-native', 2)
        self.assertEqual((a, b), ('CLAIMED', 'CLAIMED'))


if __name__ == '__main__':
    unittest.main()
