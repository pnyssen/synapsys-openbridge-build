import multiprocessing, os, sys, tempfile, threading, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import worker_reliability as W

CL = {'id': 'claude-native', 'capabilities': ['build'], 'rights': ['source_build'], 'available': True, 'measured_claim_p50_s': 40}
OA = {'id': 'openai-n8n', 'capabilities': ['build'], 'rights': ['source_build'], 'available': True, 'measured_claim_p50_s': None}
SPEC = {'needs': ['build'], 'right': 'source_build'}
H = 'a' * 64


def led(routed=1000, worker='openai-n8n', route='route-A'):
    L = W.Ledger(); L.route('task256', 'CTX-SS', worker, worker, route, routed, H); return L


def own():
    return W.Ownership(W.PersistentKV(tempfile.mkdtemp()))


class Selection(unittest.TestCase):                                         # ported from the original suite
    def test_no_default_executor(self):
        self.assertIsNone(W.select_worker(SPEC, [])[0])
        w, why = W.select_worker(SPEC, [dict(CL, available=False), dict(OA, rights=[])])
        self.assertIsNone(w); self.assertEqual((why['claude-native'], why['openai-n8n']), (['UNAVAILABLE'], ['AUTHORITY']))

    def test_latency_ranks_but_not_over_eligibility(self):
        self.assertEqual(W.select_worker(SPEC, [OA, CL])[0]['id'], 'claude-native')
        self.assertEqual(W.select_worker(SPEC, [OA, dict(CL, capabilities=[])])[0]['id'], 'openai-n8n')
        self.assertEqual(W.select_worker(SPEC, [dict(OA, measured_claim_p50_s=5), CL])[0]['id'], 'openai-n8n')


class F1_LateAcceptance(unittest.TestCase):
    def test_2220s_late_claim_is_a_breach_not_wait(self):
        L = led(); L.accept('task256', 'CTX-SS', 'openai-n8n', 1000 + 2220)
        r = W.evaluate(L.view('task256', 'CTX-SS'), 1000 + 2221)
        self.assertIn('LATE_ACCEPTANCE', r['breaches']); self.assertNotEqual(r['action'], 'WAIT'); self.assertNotEqual(r['action'], 'OK')
        self.assertFalse(r['sla_asserted'])

    def test_boundaries_59_60_61(self):
        for at, late in ((1059, False), (1060, False), (1061, True)):
            L = led(); L.accept('task256', 'CTX-SS', 'openai-n8n', at); L.progress('task256', 'CTX-SS', at + 1)
            self.assertEqual('LATE_ACCEPTANCE' in W.evaluate(L.view('task256', 'CTX-SS'), 1100)['breaches'], late, at)

    def test_unaccepted_waits_59_escalates_60(self):
        t = led().view('task256', 'CTX-SS')
        self.assertEqual(W.evaluate(t, 1059)['action'], 'WAIT'); self.assertEqual(W.evaluate(t, 1060)['action'], 'DIAGNOSE_AND_ESCALATE')


class F2_FiveMinuteClock(unittest.TestCase):
    def test_anchored_to_routing_not_acceptance(self):
        L = led(routed=0); L.accept('task256', 'CTX-SS', 'openai-n8n', 59)
        t = L.view('task256', 'CTX-SS')
        self.assertEqual(W.evaluate(t, 299)['action'], 'WAIT')
        r = W.evaluate(t, 301); self.assertEqual(r['action'], 'ESCALATE_BLOCKER'); self.assertIn('NO_PROGRESS_OR_BLOCKER_WITHIN_5MIN_OF_ROUTING', r['breaches'])

    def test_boundaries_299_300_301(self):
        t = led(routed=0).view('task256', 'CTX-SS'); t.update(accepted_at=10, accepted_by='openai-n8n')
        self.assertEqual([W.evaluate(t, n)['action'] for n in (299, 300, 301)], ['WAIT', 'ESCALATE_BLOCKER', 'ESCALATE_BLOCKER'])
        self.assertEqual(W.evaluate(dict(t, progress_at=100), 400)['action'], 'OK')
        self.assertEqual(W.evaluate(dict(t, blocker='credential expired'), 400)['action'], 'OK')

    def test_unattributable_acceptance_escalates(self):
        L = led(); L.accept('task256', 'CTX-SS', 'someone-else', 1010)
        self.assertEqual(W.evaluate(L.view('task256', 'CTX-SS'), 1020)['reason'], 'ACCEPTANCE_NOT_ATTRIBUTABLE')


class Immutability(unittest.TestCase):
    def test_routing_and_acceptance_cannot_be_rewritten(self):
        L = led(); self.assertEqual(L.route('task256', 'CTX-SS', 'x', 'x', 'r', 5, H), 'REFUSED_ALREADY_ROUTED')
        self.assertEqual(L.accept('task256', 'CTX-SS', 'openai-n8n', 1010), 'ACCEPTED')
        self.assertEqual(L.accept('task256', 'CTX-SS', 'openai-n8n', 1005), 'REFUSED_ALREADY_ACCEPTED')
        self.assertEqual(L.view('task256', 'CTX-SS')['accepted_at'], 1010); self.assertEqual(L.view('task256', 'CTX-SS')['routed_at'], 1000)
        L2 = led(); self.assertEqual(L2.accept('task256', 'CTX-SS', 'openai-n8n', 999), 'REFUSED_BEFORE_ROUTING')
        self.assertEqual(W.Ledger().accept('t', 'c', 'w', 1), 'REFUSED_NOT_ROUTED')


class Receipt(unittest.TestCase):
    def test_fields_and_unknown_mechanism(self):
        t = led().view('task256', 'CTX-SS'); t['observed'] = {'http_status': 200, 'execution_id': 'e'}
        rc = W.evaluate(t, 1100)['receipt']
        for k in ('task', 'worker', 'environment', 'route', 'routed_at', 'acceptance_deadline', 'progress_deadline', 'observed_runtime_evidence', 'failure_mechanism',
                  'recovery_attempted', 'remaining_blocker', 'responsible_owner', 'next_executable_action'):
            self.assertIn(k, rc)
        self.assertEqual((rc['failure_mechanism'], rc['mechanism_established']), ('UNKNOWN', False))
        t['observed'] = {'http_status': 403}
        self.assertEqual(W.evaluate(t, 1100)['receipt']['failure_mechanism'], 'AUTH_REFUSED')


class F5_StableIdentity(unittest.TestCase):
    def test_same_task_two_routes_one_owner(self):
        o = own()
        a = o.claim('task256', 'CTX-SS', 'openai-n8n', 'route-A', H, 1)
        b = o.claim('task256', 'CTX-SS', 'claude-native', 'route-B', H, 2)
        self.assertEqual((a['result'], b['result']), ('CLAIMED', 'REFUSED_DUPLICATE'))
        self.assertEqual(o.claim('task256', 'CTX-SS', 'openai-n8n', 'route-B', H, 3)['result'], 'IDEMPOTENT_REPLAY')
        self.assertEqual(o.owner_of('task256', 'CTX-SS')['routes'], ['route-A', 'route-B'])

    def test_payload_hash_is_conflict_metadata_not_key(self):
        o = own(); o.claim('t', 'C', 'w1', 'r', H, 1)
        self.assertEqual(o.claim('t', 'C', 'w1', 'r', 'b' * 64, 2)['result'], 'REFUSED_PAYLOAD_CONFLICT')
        self.assertEqual(o.claim('t', 'C', 'w2', 'r2', 'b' * 64, 2)['result'], 'REFUSED_PAYLOAD_CONFLICT')

    def test_context_is_part_of_identity_and_required(self):
        self.assertNotEqual(W.task_key('t', 'C1'), W.task_key('t', 'C2')); self.assertEqual(W.task_key('t', 'C1'), W.task_key('t', 'C1'))
        with self.assertRaises(ValueError): W.task_key('t', '')
        o = own(); o.claim('t', 'C1', 'w1', 'r', H, 1)
        self.assertEqual(o.claim('t', 'C2', 'w2', 'r', H, 1)['result'], 'CLAIMED')                  # different Context = different task


class F3_F4_Recovery(unittest.TestCase):
    def setup(self, accepted=False):
        o = own(); o.claim('task256', 'CTX-SS', 'openai-n8n', 'route-A', H, 1, lease_s=100)
        t = led().view('task256', 'CTX-SS'); 
        if accepted: t.update(accepted_at=1005, accepted_by='openai-n8n')
        return o, t

    def test_f3_every_branch_needs_positive_authority(self):
        o, t = self.setup()
        for a in (False, None, 'yes', 1):
            self.assertEqual(W.recover(t, o, [OA, CL], SPEC, a, 2000, True)['why'], 'NO_POSITIVE_RECOVERY_AUTHORITY')
        self.assertEqual(W.recover(t, W.Ownership(W.PersistentKV(tempfile.mkdtemp())), [CL], SPEC, False, 2000)['why'], 'NO_POSITIVE_RECOVERY_AUTHORITY')   # NO_CLAIM branch too
        self.assertEqual(o.owner_of('task256', 'CTX-SS')['owner'], 'openai-n8n')

    def test_f3_no_claim_never_reroutes(self):
        t = led().view('task256', 'CTX-SS')
        r = W.recover(t, own(), [CL], SPEC, True, 2000, True)
        self.assertFalse(r['recovered']); self.assertEqual(r['why'], 'NO_CLAIM_NOTHING_TO_RECOVER')

    def test_f3_claim_identity_must_match(self):
        o, t = self.setup(); t['worker'] = 'someone-else'
        self.assertEqual(W.recover(t, o, [CL], SPEC, True, 2000, True)['why'], 'CLAIM_IDENTITY_MISMATCH')

    def test_f4_no_alternate_keeps_owner(self):
        o, t = self.setup()
        r = W.recover(t, o, [OA], SPEC, True, 2000, True)
        self.assertEqual((r['recovered'], r['why']), (False, 'NO_ELIGIBLE_WORKER_HOLD_KEPT'))
        self.assertEqual(o.owner_of('task256', 'CTX-SS')['owner'], 'openai-n8n')             # never unowned

    def test_f4_atomic_transfer_with_fencing(self):
        o, t = self.setup()
        r = W.recover(t, o, [OA, CL], SPEC, True, 2000, owner_dead_proof=True)
        self.assertEqual((r['recovered'], r['reselected'], r['epoch']), (True, 'claude-native', 2))
        self.assertFalse(o.check_fence('task256', 'CTX-SS', 'openai-n8n', 1))              # old owner fenced out
        self.assertTrue(o.check_fence('task256', 'CTX-SS', 'claude-native', 2))
        self.assertEqual(o.transfer('task256', 'CTX-SS', 'openai-n8n', 'x', 1, True, True, 2001)['result'], 'REFUSED_NOT_OWNER')
        self.assertEqual(o.transfer('task256', 'CTX-SS', 'claude-native', 'x', 1, True, True, 2001)['result'], 'REFUSED_STALE_EPOCH')

    def test_f4_needs_dead_owner_proof_or_expired_lease(self):
        o, t = self.setup()
        self.assertEqual(W.recover(t, o, [OA, CL], SPEC, True, 50)['why'], 'REFUSED_OWNER_NOT_PROVEN_DEAD')      # lease to 101, no proof
        self.assertTrue(W.recover(t, o, [OA, CL], SPEC, True, 101)['recovered'])                                  # lease expired

    def test_accepted_task_not_recovered(self):
        o, t = self.setup(accepted=True)
        self.assertEqual(W.recover(t, o, [CL], SPEC, True, 2000, True)['why'], 'ALREADY_ACCEPTED')


class Persistence(unittest.TestCase):
    def test_ownership_survives_restart(self):
        d = tempfile.mkdtemp(); W.Ownership(W.PersistentKV(d)).claim('t', 'C', 'w1', 'r', H, 1)
        o2 = W.Ownership(W.PersistentKV(d))                                                    # new process-equivalent object
        self.assertEqual(o2.claim('t', 'C', 'w2', 'r', H, 2)['result'], 'REFUSED_DUPLICATE'); self.assertEqual(o2.owner_of('t', 'C')['owner'], 'w1')


def _proc(args):
    d, w, route = args
    return W.Ownership(W.PersistentKV(d)).claim('task256', 'CTX-SS', w, route, H, 1)['result']


class Concurrency(unittest.TestCase):
    def test_threads_exactly_one_claim(self):
        o, res = own(), []
        ts = [threading.Thread(target=lambda i=i: res.append(o.claim('task256', 'CTX-SS', 'w%d' % i, 'route-%d' % i, H, 1)['result'])) for i in range(16)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(res.count('CLAIMED'), 1); self.assertEqual(res.count('REFUSED_DUPLICATE'), 15)

    def test_processes_exactly_one_claim_across_routes(self):
        d = tempfile.mkdtemp(); ctx = multiprocessing.get_context('fork')
        with ctx.Pool(8) as p: res = p.map(_proc, [(d, 'w%d' % i, 'route-%d' % (i % 2)) for i in range(8)])
        self.assertEqual(res.count('CLAIMED'), 1); self.assertEqual(res.count('REFUSED_DUPLICATE'), 7)

    def test_concurrent_transfer_exactly_one_wins(self):
        o = own(); o.claim('t', 'C', 'w0', 'r', H, 1, lease_s=1); res = []
        ts = [threading.Thread(target=lambda i=i: res.append(o.transfer('t', 'C', 'w0', 'w%d' % (i + 1), 1, True, True, 10)['result'])) for i in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(res.count('TRANSFERRED'), 1); self.assertEqual(o.owner_of('t', 'C')['epoch'], 2)


class Chain(unittest.TestCase):
    def ev(self, **kw):
        e = [{'stage': s, 'sha256': H, 'by': 'openai-n8n'} for s in W.STAGES]
        return e

    def test_complete(self): self.assertTrue(W.verify_chain(self.ev(), H, owner='openai-n8n')['complete'])
    def test_missing(self): self.assertEqual(W.verify_chain([e for e in self.ev() if e['stage'] != 'CONSUMED'], H)['missing'], ['CONSUMED'])
    def test_hash_mismatch(self):
        e = self.ev(); e[3]['sha256'] = 'b' * 64; self.assertEqual(W.verify_chain(e, H)['hash_mismatch'], ['DELIVERED'])
    def test_duplicate_stage_rejected(self):
        e = self.ev() + [{'stage': 'RECEIPT', 'sha256': H, 'by': 'openai-n8n'}]
        r = W.verify_chain(e, H); self.assertFalse(r['complete']); self.assertEqual(r['duplicate_stages'], ['RECEIPT'])
    def test_unattributable_rejected(self):
        e = self.ev(); e[1].pop('by'); r = W.verify_chain(e, H); self.assertFalse(r['complete']); self.assertEqual(r['unattributable_stages'], ['RECEIPT'])
        e = self.ev(); e[2]['by'] = 'intruder'; self.assertEqual(W.verify_chain(e, H, owner='openai-n8n')['unattributable_stages'], ['CONSUMED'])
    def test_unknown_stage_rejected(self):
        self.assertEqual(W.verify_chain(self.ev() + [{'stage': 'MAGIC', 'sha256': H, 'by': 'x'}], H)['unknown_stages'], ['MAGIC'])
    def test_out_of_order(self):
        e = self.ev(); e[1], e[2] = e[2], e[1]; self.assertFalse(W.verify_chain(e, H)['in_order'])


class Measure(unittest.TestCase):
    def test_never_pooled_and_no_sla(self):
        m = W.measure([{'environment': 'openai-n8n', 'routed_at': 0, 'http_receipt_at': 1, 'claim_at': 2220, 'provider_exec_at': 2300},
                       {'environment': 'claude-native', 'routed_at': 0, 'http_receipt_at': 1, 'claim_at': 30, 'provider_exec_at': 90},
                       {'environment': 'openai-n8n', 'routed_at': 0, 'http_receipt_at': 1}])
        self.assertEqual(set(m), {'openai-n8n', 'claude-native'}); self.assertEqual(m['openai-n8n']['unclaimed'], 1)
        self.assertEqual(m['openai-n8n']['within_60s']['n_claimed_within_60s'], 0); self.assertTrue(all(not v['sla_asserted'] for v in m.values()))


class ServiceIdentity(unittest.TestCase):
    def test_v19_v20_never_merged(self):
        r = W.service_identity('GV-GOV-004', {'id': 40, 'method': 'D002-CGE', 'method_id': 23}, {'id': 35})
        self.assertEqual((r['v19']['id'], r['v20']['id'], r['merged'], r['id_equal']), (40, 35, False, False))
        self.assertEqual(r['v19']['method'], 'D002-CGE'); self.assertEqual(r['v20']['method'], 'UNRESOLVED_IN_V20')
        r = W.service_identity('SC-09', {'id': 55, 'method': 'D002-RULE', 'method_id': 11}, {'id': 40})
        self.assertEqual((r['v19']['id'], r['v20']['id']), (55, 40))                              # V20 id 40 is SC-09, V19 id 40 is GV-GOV-004: ids never interchanged
        self.assertEqual(W.service_identity('X', None, {'id': 1})['v19']['state'], 'NOT_READ')


if __name__ == '__main__':
    unittest.main()
