"""KDA worker reliability adapter v2 (source-only candidate; not installed; no network, no Odoo, no N8N, no writes outside a caller-given state dir).

Pure logic for environment-native adapters (n8n for ChatGPT/OpenAI, Claude-native). Adds no Service, Method, queue or doctrine; GV-GOV-004/D002-CGE and
SC-09/D002-RULE stay governing. Claims no SLA (sla_asserted is always False). Corrects review RC01 F1-F5 against base commit c570366e.
"""
import hashlib, json, os, tempfile
try:
    import fcntl
except ImportError:                                             # non-POSIX: persistence refuses rather than pretending to be atomic
    fcntl = None

ACCEPT_S, PROGRESS_S = 60, 300                                  # BOTH anchored to successful routing (routed_at), never to acceptance
STAGES = ('PUBLISHED', 'RECEIPT', 'CONSUMED', 'DELIVERED', 'CONTROLLER_ACCEPTED', 'ASSURED')
UNKNOWN = 'UNKNOWN'


# ------------------------------------------------------------------------------------------ 1. worker selection (no default executor)
def select_worker(task, workers):
    reasons, ok = {}, []
    for w in workers:
        why = []
        if not set(task['needs']) <= set(w.get('capabilities', ())): why.append('CAPABILITY')
        if task['right'] not in w.get('rights', ()): why.append('AUTHORITY')
        if not w.get('available'): why.append('UNAVAILABLE')
        if w['id'] in (task.get('exclude') or ()): why.append('EXCLUDED_AFTER_FAILURE')
        if why: reasons[w['id']] = why
        else: ok.append(w)
    if not ok: return None, reasons
    return sorted(ok, key=lambda w: (w.get('measured_claim_p50_s') is None, w.get('measured_claim_p50_s') or 0, w['id']))[0], reasons


# ------------------------------------------------------------------------------------------ 2. persistent atomic store (CAS + fencing)
class PersistentKV:
    """One JSON file per key under `root`, guarded by an exclusive flock on a lock file: create-if-absent and compare-and-swap are atomic across
    threads AND processes, and survive restart. This is the offline reference for the contract a live adapter must meet with its own primitive
    (e.g. SharePoint create-with-fail / ETag, Postgres unique key). It is NOT evidence that any live primitive behaves this way."""
    def __init__(self, root):
        if fcntl is None: raise RuntimeError('no atomic lock primitive on this platform')
        self.root = root; os.makedirs(root, exist_ok=True); self.lockp = os.path.join(root, '.lock')

    def _p(self, key): return os.path.join(self.root, key + '.json')

    def atomic(self, fn):
        fd = os.open(self.lockp, os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            return fn(self)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)

    def get(self, key):
        try:
            with open(self._p(key), encoding='utf-8') as f: return json.load(f)
        except FileNotFoundError: return None

    def put(self, key, val):                                     # caller holds the lock; write-then-rename so a crash never leaves a torn record
        fd, tmp = tempfile.mkstemp(dir=self.root); 
        with os.fdopen(fd, 'w', encoding='utf-8') as f: json.dump(val, f, sort_keys=True); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, self._p(key))


def task_key(task_id, context_id):
    """STABLE identity across ALL routes: task + Context only. Route and payload are metadata, never part of the key (F5)."""
    if not task_id or not context_id: raise ValueError('task_id and context_id are required')
    return hashlib.sha256(('%s|%s' % (task_id, context_id)).encode()).hexdigest()


class Ownership:
    """One persistent owner per task_key. Every owner change bumps a fencing epoch; writes must present the current epoch."""
    def __init__(self, kv): self.kv = kv

    def claim(self, task_id, context_id, worker, route, payload_sha256, now, lease_s=900):
        k = task_key(task_id, context_id)
        def f(kv):
            cur = kv.get(k)
            if cur is None:
                kv.put(k, {'task_id': task_id, 'context_id': context_id, 'owner': worker, 'epoch': 1, 'payload_sha256': payload_sha256,
                           'routes': [route], 'claimed_at': now, 'lease_expires_at': now + lease_s})
                return {'result': 'CLAIMED', 'epoch': 1}
            if cur['payload_sha256'] != payload_sha256: return {'result': 'REFUSED_PAYLOAD_CONFLICT', 'epoch': cur['epoch']}
            if cur['owner'] != worker: return {'result': 'REFUSED_DUPLICATE', 'epoch': cur['epoch']}
            if route not in cur['routes']: cur['routes'].append(route); kv.put(k, cur)
            return {'result': 'IDEMPOTENT_REPLAY', 'epoch': cur['epoch']}
        return self.kv.atomic(f)

    def transfer(self, task_id, context_id, from_worker, to_worker, expected_epoch, authority, owner_dead_proof, now, lease_s=900):
        """ONE atomic compare-and-swap. Needs positive authority, the current owner and epoch, and proof the owner is dead
        (lease expired OR explicit proof). A replacement must already have been selected by the caller; this never leaves the task unowned."""
        if authority is not True: return {'result': 'REFUSED_NO_AUTHORITY'}
        k = task_key(task_id, context_id)
        def f(kv):
            cur = kv.get(k)
            if cur is None: return {'result': 'REFUSED_NO_CLAIM'}
            if cur['owner'] != from_worker: return {'result': 'REFUSED_NOT_OWNER'}
            if cur['epoch'] != expected_epoch: return {'result': 'REFUSED_STALE_EPOCH', 'epoch': cur['epoch']}
            if not (owner_dead_proof is True or now >= cur['lease_expires_at']): return {'result': 'REFUSED_OWNER_NOT_PROVEN_DEAD'}
            cur.update(owner=to_worker, epoch=cur['epoch'] + 1, claimed_at=now, lease_expires_at=now + lease_s); kv.put(k, cur)
            return {'result': 'TRANSFERRED', 'epoch': cur['epoch']}
        return self.kv.atomic(f)

    def check_fence(self, task_id, context_id, worker, epoch):
        cur = self.kv.get(task_key(task_id, context_id))
        return bool(cur and cur['owner'] == worker and cur['epoch'] == epoch)

    def owner_of(self, task_id, context_id): return self.kv.get(task_key(task_id, context_id))


# ------------------------------------------------------------------------------------------ 3. immutable measurement ledger
class Ledger:
    """Append-only, first-write-wins. routed_at (successful routing) and accepted_at can never be changed or back-dated."""
    def __init__(self): self.rec = {}

    def route(self, task_id, context_id, worker, environment, route, routed_at, payload_sha256):
        k = (task_id, context_id)
        if k in self.rec: return 'REFUSED_ALREADY_ROUTED'
        self.rec[k] = {'task': task_id, 'context': context_id, 'worker': worker, 'environment': environment, 'route': route,
                       'routed_at': routed_at, 'payload_sha256': payload_sha256, 'accepted_at': None, 'accepted_by': None,
                       'progress_at': None, 'blocker': None, 'observed': {}}
        return 'ROUTED'

    def accept(self, task_id, context_id, by, at):
        r = self.rec.get((task_id, context_id))
        if r is None: return 'REFUSED_NOT_ROUTED'
        if r['accepted_at'] is not None: return 'REFUSED_ALREADY_ACCEPTED'
        if at < r['routed_at']: return 'REFUSED_BEFORE_ROUTING'
        r['accepted_at'], r['accepted_by'] = at, by; return 'ACCEPTED'

    def progress(self, task_id, context_id, at, blocker=None):
        r = self.rec[(task_id, context_id)]
        if r['progress_at'] is None and blocker is None: r['progress_at'] = at
        if blocker and r['blocker'] is None: r['blocker'] = blocker
        return r

    def view(self, task_id, context_id): return dict(self.rec[(task_id, context_id)])


# ------------------------------------------------------------------------------------------ 4. timers, diagnosis, escalation
def breaches(t, now):
    b = []
    if t['accepted_at'] is None:
        if now - t['routed_at'] >= ACCEPT_S: b.append('NO_ACCEPTANCE_WITHIN_60S')
    else:
        if t['accepted_at'] - t['routed_at'] > ACCEPT_S: b.append('LATE_ACCEPTANCE')              # F1: judged on the immutable delta, even after the claim
        if t['accepted_by'] != t['worker']: b.append('ACCEPTANCE_NOT_ATTRIBUTABLE')
    if t['progress_at'] is None and t['blocker'] is None and now - t['routed_at'] >= PROGRESS_S:
        b.append('NO_PROGRESS_OR_BLOCKER_WITHIN_5MIN_OF_ROUTING')                                 # F2: anchored to routing
    return b


def evaluate(t, now):
    b = breaches(t, now)
    if not b:
        if t['accepted_at'] is None: return {'action': 'WAIT', 'breaches': [], 'remaining_s': ACCEPT_S - (now - t['routed_at'])}
        if t['progress_at'] is None and t['blocker'] is None: return {'action': 'WAIT', 'breaches': [], 'remaining_s': PROGRESS_S - (now - t['routed_at'])}
        return {'action': 'OK', 'breaches': [], 'sla_asserted': False}
    pri = ('ACCEPTANCE_NOT_ATTRIBUTABLE', 'NO_PROGRESS_OR_BLOCKER_WITHIN_5MIN_OF_ROUTING', 'NO_ACCEPTANCE_WITHIN_60S', 'LATE_ACCEPTANCE')
    first = next(x for x in pri if x in b)
    return {'action': {'NO_PROGRESS_OR_BLOCKER_WITHIN_5MIN_OF_ROUTING': 'ESCALATE_BLOCKER'}.get(first, 'DIAGNOSE_AND_ESCALATE'),
            'reason': first, 'breaches': b, 'sla_asserted': False, 'receipt': escalation_receipt(t, now, b)}


def diagnose(t):
    o = t.get('observed') or {}
    if o.get('http_status') in (401, 403): return {'mechanism': 'AUTH_REFUSED', 'basis': 'observed http_status %s' % o['http_status'], 'established': True}
    if not o: return {'mechanism': UNKNOWN, 'basis': 'no runtime evidence observed', 'established': False}
    if o.get('execution_id') and not o.get('worker_claim'): return {'mechanism': UNKNOWN, 'basis': 'HTTP/execution observed, no worker claim; cause not observable', 'established': False}
    return {'mechanism': UNKNOWN, 'basis': 'insufficient evidence', 'established': False}


def escalation_receipt(t, now, b=None):
    d = diagnose(t)
    return {'task': t['task'], 'context': t['context'], 'worker': t['worker'], 'environment': t['environment'], 'route': t['route'], 'routed_at': t['routed_at'],
            'accepted_at': t['accepted_at'], 'acceptance_deadline': t['routed_at'] + ACCEPT_S, 'progress_deadline': t['routed_at'] + PROGRESS_S, 'now': now,
            'elapsed_s': now - t['routed_at'], 'breaches': b or breaches(t, now), 'observed_runtime_evidence': t.get('observed') or {},
            'failure_mechanism': d['mechanism'], 'mechanism_established': d['established'], 'mechanism_basis': d['basis'],
            'recovery_attempted': t.get('recovery_attempted') or [], 'remaining_blocker': t.get('blocker') or d['basis'],
            'responsible_owner': t.get('owner') or 'D007 worker-controller (route/credential) on Steward word',
            'next_executable_action': 'Steward/D007: fix auth profile; no retry on the same route until changed' if d['mechanism'] == 'AUTH_REFUSED'
            else 'non-mutating diagnosis of the existing route; reroute only with positive recovery authority and an eligible replacement'}


# ------------------------------------------------------------------------------------------ 5. recovery (positive authority on EVERY branch)
def recover(t, ownership, workers, spec, authority, now, owner_dead_proof=False, lease_s=900):
    if authority is not True: return {'recovered': False, 'why': 'NO_POSITIVE_RECOVERY_AUTHORITY'}          # F3: first, before any branch
    cur = ownership.owner_of(t['task'], t['context'])
    if cur is None: return {'recovered': False, 'why': 'NO_CLAIM_NOTHING_TO_RECOVER'}                       # F3: NO_CLAIM never permits a reroute
    if cur['owner'] != t['worker']: return {'recovered': False, 'why': 'CLAIM_IDENTITY_MISMATCH'}
    if t.get('accepted_at') is not None: return {'recovered': False, 'why': 'ALREADY_ACCEPTED'}
    w, why = select_worker(dict(spec, exclude=tuple(spec.get('exclude') or ()) + (t['worker'],)), workers)     # F4: replacement chosen BEFORE touching ownership
    if w is None: return {'recovered': False, 'why': 'NO_ELIGIBLE_WORKER_HOLD_KEPT', 'reasons': why, 'owner_unchanged': cur['owner']}
    r = ownership.transfer(t['task'], t['context'], t['worker'], w['id'], cur['epoch'], authority, owner_dead_proof, now, lease_s)
    return dict(recovered=r['result'] == 'TRANSFERRED', why=r['result'], reselected=w['id'] if r['result'] == 'TRANSFERRED' else None, epoch=r.get('epoch'))


# ------------------------------------------------------------------------------------------ 6. delivery chain
def verify_chain(events, expected_sha256, owner=None):
    seen, dup, unattr, unknown, bad = [], [], [], [], []
    for e in events:
        s = e.get('stage')
        if s not in STAGES: unknown.append(s); continue
        if s in seen: dup.append(s)
        seen.append(s)
        if not e.get('by') or (owner and s in ('RECEIPT', 'CONSUMED', 'DELIVERED') and e.get('by') != owner): unattr.append(s)
        if e.get('sha256') != expected_sha256: bad.append(s)
    first = [s for i, s in enumerate(seen) if s not in seen[:i]]
    missing = [s for s in STAGES if s not in seen]
    in_order = first == sorted(first, key=STAGES.index)
    return {'complete': not (missing or bad or dup or unattr or unknown) and in_order, 'missing': missing, 'hash_mismatch': bad,
            'duplicate_stages': dup, 'unattributable_stages': unattr, 'unknown_stages': unknown, 'in_order': in_order}


# ------------------------------------------------------------------------------------------ 7. per-environment measurement
def measure(samples):
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


# ------------------------------------------------------------------------------------------ 8. V19 / V20 Service identity (no merge, no registry change)
def service_identity(code, v19=None, v20=None):
    """Same code, DIFFERENT registries. Never merged; ids are never interchanged; an unresolved Method link stays UNRESOLVED."""
    def side(x, env):
        if x is None: return {'environment': env, 'state': 'NOT_READ'}
        return {'environment': env, 'state': 'READ', 'id': x['id'], 'method': x.get('method') or 'UNRESOLVED_IN_%s' % env, 'method_id': x.get('method_id')}
    return {'code': code, 'v19': side(v19, 'V19'), 'v20': side(v20, 'V20'), 'merged': False, 'id_equal': None if not (v19 and v20) else v19['id'] == v20['id'],
            'rule': 'identity = (environment, id); code is a label only; neither registry is changed by this module'}
