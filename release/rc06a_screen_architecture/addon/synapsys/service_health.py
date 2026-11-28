"""Service Health: three INDEPENDENT projections over the existing native Service record (source-only candidate; not installed).

Pure functions. No Odoo import, no sudo, no write, no SQL, no new model, no Service, no Method. Plain values in, plain values out.

1. structural_slots()      the existing 15-slot count and the historical `plug_in_ready` flag, UNCHANGED in meaning (D001/D002 own any change).
2. relationship_coverage() per-edge typed states for Context / Method / Canon / Pattern. Never derived from a zero structural gap.
3. operating_qualification() verdict from attributable, authorised, independently attested receipts ONLY. A Boolean flag such as
   `answer_accepted`, an install, a hash, a passing test or 15/15 slots is NOT evidence and can never produce a verified state.

Relationship states are exactly BOUND, MISSING_REQUIRED, NOT_APPLICABLE, SOURCE_UNVERIFIED, INACCESSIBLE_REDACTED. A relationship is
"required" or "not applicable" only if the caller supplies a ruling; with no ruling an unbound edge is SOURCE_UNVERIFIED (never invented).
A bound edge that points at a Context the actor is not entitled to is INACCESSIBLE_REDACTED and carries no id, name or count.
"""

SLOT_FIELDS = ('name', 'kind_proposed', 'perspective', 'method_id', 'canon_ids', 'owner_name', 'entry_point', 'approval_category',
               'execution_outcome_schema', 'return_acceptance_schema', 'sla_value', 'benefit_ids', 'asset_ids',
               'observation_learning_contract', 'obligations', 'context_id')

# The fields the compute MUST depend on. Slot 9 reads BOTH execution_outcome_schema and return_acceptance_schema.
HEALTH_DEPENDS = ('context_id', 'kind_proposed', 'perspective', 'method_id', 'canon_ids', 'owner_name', 'entry_point',
                  'approval_category', 'execution_outcome_schema', 'return_acceptance_schema', 'sla_value', 'benefit_ids',
                  'asset_ids', 'observation_learning_contract', 'obligations', 'name')

STATES = ('BOUND', 'MISSING_REQUIRED', 'NOT_APPLICABLE', 'SOURCE_UNVERIFIED', 'INACCESSIBLE_REDACTED')
EDGES = (('context', 'context_id', 'many2one'), ('method', 'method_id', 'many2one'),
         ('canon', 'canon_ids', 'many2many'), ('pattern', 'pattern_ids', 'many2many'))
RULINGS = ('REQUIRED', 'NOT_APPLICABLE')          # anything else (or absent) means: no source ruling exists

OPERATING_REQUIRED = ('authorised_invocation', 'registered_method_applicability', 'attributable_expected_return',
                      'recovery_tested', 'independent_assurance', 'human_outcome_acceptance', 'second_cycle')


# ---------------------------------------------------------------------------------------------------------------- 1. structure
def structural_slots(v):
    """Identical to the historical SynapsysService._compute_health formula. Returns (slots_filled, plug_in_ready, slots)."""
    slots = [v.get('name'),
             v.get('context_id') and v.get('kind_proposed'),
             v.get('perspective'),
             v.get('method_id') or v.get('canon_ids'),
             v.get('owner_name'),
             v.get('entry_point'),
             v.get('approval_category'),
             True,
             v.get('execution_outcome_schema') or v.get('return_acceptance_schema'),
             v.get('sla_value'),
             v.get('benefit_ids'),
             v.get('asset_ids'),
             v.get('observation_learning_contract'),
             v.get('obligations'),
             True]
    filled = sum(1 for s in slots if s)
    return filled, filled == 15, [bool(s) for s in slots]


# ---------------------------------------------------------------------------------------------------------------- 2. relationships
def _ids(x):
    if x is None or x is False:
        return []
    if isinstance(x, (list, tuple, set, frozenset)):
        return [getattr(i, 'id', i) for i in x]
    return [getattr(x, 'id', x)]


def relationship_coverage(values, actor_context_ids=None, rulings=None, method_context_id=None):
    """Typed per-edge coverage. `actor_context_ids` is the set of Contexts the ACTOR is entitled to (own ORM rights); None means the
    caller could not establish entitlement, in which case a bound Context is INACCESSIBLE_REDACTED (fail closed)."""
    rulings = rulings or {}
    out = {}
    for edge, fld, card in EDGES:
        ids = _ids(values.get(fld))
        ruling = rulings.get(edge) if rulings.get(edge) in RULINGS else None
        state = None
        if ids:
            foreign = False
            if edge == 'context':
                foreign = actor_context_ids is None or any(i not in actor_context_ids for i in ids)
            elif edge == 'method' and method_context_id not in (None, False):
                foreign = actor_context_ids is None or method_context_id not in actor_context_ids
            state = 'INACCESSIBLE_REDACTED' if foreign else 'BOUND'
        elif ruling == 'NOT_APPLICABLE':
            state = 'NOT_APPLICABLE'
        elif ruling == 'REQUIRED':
            state = 'MISSING_REQUIRED'
        else:
            state = 'SOURCE_UNVERIFIED'
        out[edge] = {'field': fld, 'cardinality': card, 'state': state, 'ruling': ruling or 'NONE_IN_SOURCE'}
        if state == 'BOUND':
            out[edge]['count'] = len(ids)             # only for an entitled, bound edge; never for a redacted one
    states = [e['state'] for e in out.values()]
    if 'MISSING_REQUIRED' in states:
        summary = 'INCOMPLETE'
    elif 'SOURCE_UNVERIFIED' in states or 'INACCESSIBLE_REDACTED' in states:
        summary = 'HOLD'
    else:
        summary = 'COMPLETE_FOR_RULED_EDGES'
    return {'edges': out, 'summary': summary}


# ---------------------------------------------------------------------------------------------------------------- 3. operating
def _receipt_ok(r):
    return isinstance(r, dict) and bool(r.get('by')) and r.get('authorised') is True and r.get('attributable') is True


def operating_qualification(evidence=None, answer_accepted_flag=None):
    """HELD when any required item has no authorised, attributable receipt. NOT_VERIFIED when every item has one but not all are
    independently attested. VERIFIED only when every receipt is also attested by someone other than the producer."""
    evidence = evidence or {}
    present, missing, unattested = [], [], []
    for item in OPERATING_REQUIRED:
        r = evidence.get(item)
        if not _receipt_ok(r):
            missing.append(item)
            continue
        present.append(item)
        if r.get('attested') is not True or r.get('by') == r.get('produced_by'):
            unattested.append(item)
    if missing:
        state = 'HELD'
    elif unattested:
        state = 'NOT_VERIFIED'
    else:
        state = 'VERIFIED'
    return {'state': state, 'present': present, 'missing': missing, 'unattested': unattested,
            'answer_accepted_flag': 'FLAG_ONLY_NOT_EVIDENCE' if answer_accepted_flag is not None else 'NOT_SUPPLIED',
            'note': 'structural slots, plug_in_ready, install, hash and test passes are not operating evidence'}


def project(values, actor_context_ids=None, rulings=None, method_context_id=None, evidence=None, answer_accepted_flag=None):
    filled, ready, _ = structural_slots(values)
    return {'structural': {'slots_filled': filled, 'plug_in_ready': ready, 'meaning': 'historical structural flag; not an operating verdict'},
            'relationships': relationship_coverage(values, actor_context_ids, rulings, method_context_id),
            'operating': operating_qualification(evidence, answer_accepted_flag)}


# ---------------------------------------------------------------------------------------------------------------- actor rights
def _rid(x):
    return getattr(x, 'id', x)


def _is_access_error(exc):
    return exc.__class__.__name__ == 'AccessError'


def _entitled(rec, uid):
    """Belt and braces on top of the record rule: the Context must name this user as steward or member in the record itself."""
    if _rid(getattr(rec, 'steward_user_id', None)) == uid:
        return True
    return uid in [_rid(m) for m in (getattr(rec, 'member_ids', None) or ())]


def actor_context_ids(env, uid):
    """Context ids this actor may act in, from the native ORM with the CALLER'S OWN rights (no sudo). Fail closed: no access,
    no model, or no membership means no Context ids, never a guess."""
    try:
        recs = env['synapsys.context'].search(['|', ('steward_user_id', '=', uid), ('member_ids', 'in', uid)])
        return set(_rid(r) for r in recs if _entitled(r, uid))
    except KeyError:
        return set()
    except Exception as exc:  # noqa: BLE001
        if _is_access_error(exc) or exc.__class__.__name__ == 'MissingError':
            return set()
        raise
