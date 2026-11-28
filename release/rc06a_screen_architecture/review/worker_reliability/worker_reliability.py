"""KDA worker reliability adapter (source-only candidate; not installed; no network, no Odoo, no N8N, no writes).

Implements the Steward-adopted requirements (KDA_WORKER_RELIABILITY_STEWARD_REQUIREMENTS_20261128_RC00, sha256 596848a5...8e3b) as PURE logic
that an environment-native adapter (n8n for ChatGPT/OpenAI, Claude-native for Claude) calls with its own clock and its own observations.
It adds no Service, Method, queue or doctrine: GV-GOV-004/D002-CGE and SC-09/D002-RULE stay the governing contracts. It claims no SLA.
"""
import hashlib

ACCEPT_S, PROGRESS_S = 60, 300
STAGES = ('PUBLISHED', 'RECEIPT', 'CONSUMED', 'DELIVERED', 'CONTROLLER_ACCEPTED', 'ASSURED')
UNKNOWN = 'UNKNOWN'


# ------------------------------------------------------------------------------------------ 1. worker selection (no default executor)
def select_worker(task, workers):
    """Pick by capability, authority, availability, then measured latency. No worker => (None, reasons); never a default."""
    reasons, ok = {}, []
    for w in workers:
        why = []
        if not set(task['needs']) <= set(w.get('capabilities', ())): why.append('CAPABILITY')
        if task['right'] not in w.get('rights', ()): why.append('AUTHORITY')
        if not w.get('available'): why.append('UNAVAILABLE')
        if task.get('exclude') and w['id'] in task['exclude']: why.append('EXCLUDED_AFTER_FAILURE')
        (reasons.__setitem__(w['id'], why) if why else ok.append(w))
    if not ok:
        return None, reasons
    lat = lambda w: (w.get('measured_claim_p50_s') is None, w.get('measured_claim_p50_s') or 0, w['id'])   # unmeasured ranks after measured
    best = sorted(ok, key=lat)[0]
    return best, reasons


# ------------------------------------------------------------------------------------------ 2. atomic claim + idempotency
class ClaimStore:
    """Compare-and-set ownership. A real environment must back this with its own atomic primitive (e.g. SharePoint create-with-fail,
    Postgres unique key); this class is the contract and the offline reference. One owner per idempotency key, ever."""
    def __init__(self):
        self.owner, self.log = {}, []

    def claim(self, key, worker, at):
        cur = self.owner.get(key)
        if cur is None:
            self.owner[key] = {'worker': worker, 'at': at}; self.log.append(('CLAIMED', key, worker, at)); return 'CLAIMED'
        if cur['worker'] == worker:
            return 'IDEMPOTENT_REPLAY'                                   # same worker re-asserting: no second execution
        self.log.append(('REFUSED_DUPLICATE', key, worker, at)); return 'REFUSED_DUPLICATE'

    def release_for_recovery(self, key, worker, authority_ok):
        if not authority_ok: return 'REFUSED_NO_AUTHORITY'
        if self.owner.get(key, {}).get('worker') != worker: return 'REFUSED_NOT_OWNER'
        del self.owner[key]; self.log.append(('RELEASED', key, worker, None)); return 'RELEASED'


def idempotency_key(task_id, route, payload_sha256):
    return hashlib.sha256(('%s|%s|%s' % (task_id, route, payload_sha256)).encode()).hexdigest()


# ------------------------------------------------------------------------------------------ 3. timers, diagnosis, escalation
def evaluate(task, now):
    """task: id, worker, environment, route, routed_at (epoch s), accepted_at, progress_at, blocker, observed (dict of runtime evidence).
    Returns the single required action at `now`. Pure."""
    t0 = task['routed_at']
    if task.get('accepted_at') is None:
        if now - t0 < ACCEPT_S: return {'action': 'WAIT', 'deadline_s': ACCEPT_S, 'remaining_s': ACCEPT_S - (now - t0)}
        return {'action': 'DIAGNOSE_AND_ESCALATE', 'reason': 'NO_ATTRIBUTABLE_ACCEPTANCE_WITHIN_60S', 'receipt': escalation_receipt(task, now)}
    if task.get('accepted_by') != task['worker']:
        return {'action': 'DIAGNOSE_AND_ESCALATE', 'reason': 'ACCEPTANCE_NOT_ATTRIBUTABLE_TO_ROUTED_WORKER', 'receipt': escalation_receipt(task, now)}
    if task.get('progress_at') is None and task.get('blocker') is None:
        if now - task['accepted_at'] < PROGRESS_S: return {'action': 'WAIT', 'deadline_s': PROGRESS_S, 'remaining_s': PROGRESS_S - (now - task['accepted_at'])}
        return {'action': 'ESCALATE_BLOCKER', 'reason': 'NO_PROGRESS_OR_PRECISE_BLOCKER_WITHIN_5MIN', 'receipt': escalation_receipt(task, now)}
    return {'action': 'OK'}


def diagnose(task):
    """Mechanism is named only when observed evidence establishes it; otherwise UNKNOWN. Never asserted from absence."""
    o = task.get('observed') or {}
    if o.get('http_status') in (401, 403): return {'mechanism': 'AUTH_REFUSED', 'basis': 'observed http_status %s' % o['http_status'], 'established': True}
    if o.get('http_status') is None and not o: return {'mechanism': UNKNOWN, 'basis': 'no runtime evidence observed', 'established': False}
    if o.get('execution_id') and not o.get('worker_claim'): return {'mechanism': UNKNOWN, 'basis': 'HTTP/execution observed, no worker claim; cause not observable', 'established': False}
    return {'mechanism': UNKNOWN, 'basis': 'insufficient evidence', 'established': False}


def escalation_receipt(task, now):
    d = diagnose(task)
    return {'task': task['id'], 'worker': task['worker'], 'environment': task['environment'], 'route': task['route'], 'routed_at': task['routed_at'],
            'acceptance_deadline': task['routed_at'] + ACCEPT_S, 'now': now, 'elapsed_s': now - task['routed_at'],
            'observed_runtime_evidence': task.get('observed') or {}, 'failure_mechanism': d['mechanism'], 'mechanism_established': d['established'],
            'mechanism_basis': d['basis'], 'recovery_attempted': task.get('recovery_attempted') or [], 'remaining_blocker': task.get('blocker') or d['basis'],
            'responsible_owner': task.get('owner') or 'D007 (route/credential) on Steward word', 'next_executable_action': next_action(task, d)}


def next_action(task, d):
    if d['mechanism'] == 'AUTH_REFUSED': return 'Steward/D007: fix auth profile; no retry on the same route until changed'
    if task.get('alternate_route') and task.get('alternate_authorised'): return 'reroute to %s within existing authority' % task['alternate_route']
    return 'diagnose with a non-mutating probe; if no alternate authorised route, hold for owner'


def recover(task, store, workers, key, now):
    """Automatic recovery within existing authority only: release the dead claim (if the routed worker never accepted), exclude it, reselect."""
    if task.get('accepted_at') is not None: return {'recovered': False, 'why': 'ALREADY_ACCEPTED'}
    rel = store.release_for_recovery(key, task['worker'], authority_ok=task.get('may_recover', False)) if key in store.owner else 'NO_CLAIM'
    if rel == 'REFUSED_NO_AUTHORITY': return {'recovered': False, 'why': rel}
    w, why = select_worker(dict(task['spec'], exclude=(task['worker'],)), workers)
    if w is None: return {'recovered': False, 'why': 'NO_ELIGIBLE_WORKER', 'reasons': why}
    return {'recovered': True, 'reselected': w['id'], 'claim': store.claim(key, w['id'], now)}


# ------------------------------------------------------------------------------------------ 4. delivery chain
def verify_chain(events, expected_sha256):
    """Every stage present, in order, each carrying the expected hash. A missing stage or a hash mismatch is a defect, not a pass."""
    seen = [e['stage'] for e in events]
    missing = [s for s in STAGES if s not in seen]
    bad = [e['stage'] for e in events if e.get('sha256') != expected_sha256]
    order_ok = [s for s in seen if s in STAGES] == sorted((s for s in seen if s in STAGES), key=STAGES.index)
    return {'complete': not missing and not bad and order_ok, 'missing': missing, 'hash_mismatch': bad, 'in_order': order_ok}


# ------------------------------------------------------------------------------------------ 5. per-environment measurement
def measure(samples):
    """samples: list of {environment, routed_at, http_receipt_at, claim_at, provider_exec_at}. Environments are NEVER pooled; the three
    latencies stay separate; no SLA is asserted (sla_asserted is always False)."""
    out = {}
    for s in samples:
        e = out.setdefault(s['environment'], {'n': 0, 'http_receipt_s': [], 'claim_s': [], 'provider_exec_s': [], 'unclaimed': 0})
        e['n'] += 1
        for k, f in (('http_receipt_s', 'http_receipt_at'), ('claim_s', 'claim_at'), ('provider_exec_s', 'provider_exec_at')):
            if s.get(f) is not None: e[k].append(s[f] - s['routed_at'])
        if s.get('claim_at') is None: e['unclaimed'] += 1
    for e in out.values():
        for k in ('http_receipt_s', 'claim_s', 'provider_exec_s'):
            v = sorted(e[k]); e[k] = {'n': len(v), 'values': v, 'max': v[-1] if v else None}
        e['sla_asserted'] = False
        e['within_60s'] = {'n_claimed_within_60s': sum(1 for x in e['claim_s']['values'] if x <= ACCEPT_S), 'of': e['n']}
    return out
