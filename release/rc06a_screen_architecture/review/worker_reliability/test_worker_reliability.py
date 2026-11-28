import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import worker_reliability as W

CLAUDE = {'id': 'claude-native', 'capabilities': ['build', 'verify'], 'rights': ['source_build'], 'available': True, 'measured_claim_p50_s': 40}
OPENAI = {'id': 'openai-n8n', 'capabilities': ['build', 'verify'], 'rights': ['source_build'], 'available': True, 'measured_claim_p50_s': None}
SPEC = {'needs': ['build'], 'right': 'source_build'}


def T(**k):
    t = {'id': 'task255', 'worker': 'openai-n8n', 'environment': 'openai-n8n', 'route': 'route-113', 'routed_at': 1000, 'accepted_at': None,
         'accepted_by': None, 'progress_at': None, 'blocker': None, 'observed': {}, 'owner': 'D007', 'spec': SPEC, 'may_recover': True}
    t.update(k); return t


class Selection(unittest.TestCase):
    def test_no_default_executor(self):
        w, why = W.select_worker(SPEC, [])
        self.assertIsNone(w)
        w, why = W.select_worker(SPEC, [dict(CLAUDE, available=False), dict(OPENAI, rights=[])])
        self.assertIsNone(w); self.assertEqual(why['claude-native'], ['UNAVAILABLE']); self.assertEqual(why['openai-n8n'], ['AUTHORITY'])

    def test_measured_latency_ranks_but_never_overrides_eligibility(self):
        self.assertEqual(W.select_worker(SPEC, [OPENAI, CLAUDE])[0]['id'], 'claude-native')
        self.assertEqual(W.select_worker(SPEC, [OPENAI, dict(CLAUDE, capabilities=[])])[0]['id'], 'openai-n8n')   # Claude is not assumed

    def test_chatgpt_can_be_chosen_when_faster(self):
        self.assertEqual(W.select_worker(SPEC, [dict(OPENAI, measured_claim_p50_s=5), CLAUDE])[0]['id'], 'openai-n8n')


class Timers(unittest.TestCase):
    def test_wait_then_escalate_at_60s(self):
        self.assertEqual(W.evaluate(T(), 1059)['action'], 'WAIT')
        r = W.evaluate(T(), 1060)
        self.assertEqual(r['action'], 'DIAGNOSE_AND_ESCALATE')
        for k in ('task', 'worker', 'environment', 'route', 'routed_at', 'acceptance_deadline', 'observed_runtime_evidence', 'failure_mechanism',
                  'recovery_attempted', 'remaining_blocker', 'responsible_owner', 'next_executable_action'):
            self.assertIn(k, r['receipt'])
        self.assertEqual(r['receipt']['acceptance_deadline'], 1060)

    def test_unknown_mechanism_is_not_asserted_as_fact(self):
        rc = W.evaluate(T(observed={'http_status': 200, 'execution_id': 'e1'}), 1100)['receipt']
        self.assertEqual(rc['failure_mechanism'], 'UNKNOWN'); self.assertFalse(rc['mechanism_established'])
        rc = W.evaluate(T(observed={'http_status': 403}), 1100)['receipt']
        self.assertEqual((rc['failure_mechanism'], rc['mechanism_established']), ('AUTH_REFUSED', True))

    def test_task254_37_minute_claim_is_an_escalation_not_a_pass(self):
        t = T(id='task254', accepted_at=1000 + 37 * 60, accepted_by='openai-n8n')
        self.assertEqual(W.evaluate(dict(t, accepted_at=None), 1000 + 37 * 60)['action'], 'DIAGNOSE_AND_ESCALATE')   # at every moment past 60s with no claim
        m = W.measure([{'environment': 'openai-n8n', 'routed_at': 0, 'http_receipt_at': 2, 'claim_at': 37 * 60}])['openai-n8n']
        self.assertEqual(m['within_60s']['n_claimed_within_60s'], 0); self.assertFalse(m['sla_asserted'])

    def test_unattributable_acceptance_escalates(self):
        self.assertEqual(W.evaluate(T(accepted_at=1010, accepted_by='someone-else'), 1020)['action'], 'DIAGNOSE_AND_ESCALATE')

    def test_five_minute_progress_or_precise_blocker(self):
        t = T(accepted_at=1010, accepted_by='openai-n8n')
        self.assertEqual(W.evaluate(t, 1309)['action'], 'WAIT'); self.assertEqual(W.evaluate(t, 1310)['action'], 'ESCALATE_BLOCKER')
        self.assertEqual(W.evaluate(dict(t, progress_at=1100), 1400)['action'], 'OK')
        self.assertEqual(W.evaluate(dict(t, blocker='credential expired'), 1400)['action'], 'OK')


class ClaimAndRecovery(unittest.TestCase):
    def test_duplicate_execution_prevented(self):
        s, k = W.ClaimStore(), W.idempotency_key('task255', 'route-113', 'abc')
        self.assertEqual(s.claim(k, 'openai-n8n', 1), 'CLAIMED')
        self.assertEqual(s.claim(k, 'claude-native', 2), 'REFUSED_DUPLICATE')
        self.assertEqual(s.claim(k, 'openai-n8n', 3), 'IDEMPOTENT_REPLAY')
        self.assertEqual(len(s.owner), 1)

    def test_idempotency_key_is_deterministic_and_input_sensitive(self):
        a = W.idempotency_key('t', 'r', 'h'); self.assertEqual(a, W.idempotency_key('t', 'r', 'h')); self.assertNotEqual(a, W.idempotency_key('t', 'r', 'h2'))

    def test_recovery_reselects_other_worker_within_authority(self):
        s, k = W.ClaimStore(), 'k'; s.claim(k, 'openai-n8n', 1)
        r = W.recover(T(), s, [OPENAI, CLAUDE], k, 70)
        self.assertEqual((r['recovered'], r['reselected'], r['claim']), (True, 'claude-native', 'CLAIMED'))
        self.assertEqual(s.owner[k]['worker'], 'claude-native')

    def test_recovery_refused_without_authority_and_never_duplicates(self):
        s, k = W.ClaimStore(), 'k'; s.claim(k, 'openai-n8n', 1)
        r = W.recover(T(may_recover=False), s, [OPENAI, CLAUDE], k, 70)
        self.assertFalse(r['recovered']); self.assertEqual(s.owner[k]['worker'], 'openai-n8n')

    def test_recovery_with_no_eligible_alternate_holds(self):
        s, k = W.ClaimStore(), 'k'; s.claim(k, 'openai-n8n', 1)
        r = W.recover(T(), s, [OPENAI], k, 70)
        self.assertEqual((r['recovered'], r['why']), (False, 'NO_ELIGIBLE_WORKER'))

    def test_accepted_task_is_never_recovered(self):
        self.assertFalse(W.recover(T(accepted_at=1005, accepted_by='openai-n8n'), W.ClaimStore(), [CLAUDE], 'k', 70)['recovered'])


class ChainAndMeasure(unittest.TestCase):
    H = 'a' * 64
    def ev(self, drop=None, bad=None):
        return [{'stage': s, 'sha256': ('b' * 64 if s == bad else self.H)} for s in W.STAGES if s != drop]

    def test_complete_chain(self): self.assertTrue(W.verify_chain(self.ev(), self.H)['complete'])
    def test_missing_stage_fails(self): self.assertEqual(W.verify_chain(self.ev(drop='CONSUMED'), self.H)['missing'], ['CONSUMED'])
    def test_hash_mismatch_fails(self): self.assertEqual(W.verify_chain(self.ev(bad='DELIVERED'), self.H)['hash_mismatch'], ['DELIVERED'])
    def test_out_of_order_fails(self):
        e = self.ev(); e[1], e[2] = e[2], e[1]; self.assertFalse(W.verify_chain(e, self.H)['in_order'])

    def test_environments_never_pooled_and_three_latencies_separate(self):
        m = W.measure([{'environment': 'openai-n8n', 'routed_at': 0, 'http_receipt_at': 1, 'claim_at': 2220, 'provider_exec_at': 2300},
                       {'environment': 'claude-native', 'routed_at': 0, 'http_receipt_at': 1, 'claim_at': 30, 'provider_exec_at': 90},
                       {'environment': 'openai-n8n', 'routed_at': 0, 'http_receipt_at': 1}])
        self.assertEqual(set(m), {'openai-n8n', 'claude-native'})
        self.assertEqual(m['openai-n8n']['unclaimed'], 1); self.assertEqual(m['claude-native']['claim_s']['max'], 30)
        self.assertEqual(m['openai-n8n']['http_receipt_s']['n'], 2); self.assertEqual(m['openai-n8n']['claim_s']['n'], 1)
        self.assertTrue(all(not v['sla_asserted'] for v in m.values()))


if __name__ == '__main__':
    unittest.main()
