"""A minimal in-memory ORM, just enough to run the loader's OdooBackend offline: search / browse / create / write / unlink on named models, many2one and many2many
fields, and a write log. It stands in for Odoo; it is not Odoo (what it cannot show is listed in the return)."""
import itertools

M2O = {'context_id': 'synapsys.context', 'domain_id': 'synapsys.domain', 'method_id': 'synapsys.method', 'standard_id': 'synapsys.service.standard'}
M2M_F = ('canon_ids', 'pattern_ids')


class RS(object):
    def __init__(self, env, model, ids):
        self.env, self._m, self.ids = env, model, list(ids)

    @property
    def id(self):
        return self.ids[0] if self.ids else False

    def __bool__(self):
        return bool(self.ids)

    def __len__(self):
        return len(self.ids)

    def __iter__(self):
        return (RS(self.env, self._m, [i]) for i in self.ids)

    def __getitem__(self, k):
        if isinstance(k, int):
            return RS(self.env, self._m, [self.ids[k]])
        row = self.env.data[self._m].get(self.ids[0], {}) if self.ids else {}
        if k in M2O:
            v = row.get(k)
            return RS(self.env, M2O[k], [v] if v else [])
        if k in M2M_F:
            return RS(self.env, {'canon_ids': 'synapsys.canon', 'pattern_ids': 'synapsys.pattern'}[k], row.get(k, []))
        if k == 'id':
            return self.id
        v = row.get(k, False)
        return v

    def __getattr__(self, k):
        if k in ('res_id', 'name', 'model', 'module', 'code', 'v19_id', 'paragraphs'):
            return self[k]
        raise AttributeError(k)

    def exists(self):
        return RS(self.env, self._m, [i for i in self.ids if i in self.env.data[self._m]])

    def browse(self, ids):
        return RS(self.env, self._m, [ids] if isinstance(ids, int) else list(ids))

    def search(self, domain, limit=None):
        out = []
        for i, row in sorted(self.env.data[self._m].items()):
            ok = True
            for f, op, v in domain:
                have = i if f == 'id' else row.get(f, False)
                ok = ok and ((have == v) if op == '=' else (have in v))
            if ok:
                out.append(i)
        return RS(self.env, self._m, out[:limit] if limit else out)

    def create(self, vals):
        if self._m == 'synapsys.service':
            assert vals.get('code') and vals.get('name'), 'code and name are required on synapsys.service'
        i = next(self.env.seq)
        row = {}
        for k, v in vals.items():
            row[k] = self.env._norm(k, v)
        self.env.data[self._m][i] = row
        self.env.log.append(('create', self._m, i, dict(vals)))
        return RS(self.env, self._m, [i])

    def write(self, vals):
        for i in self.ids:
            for k, v in vals.items():
                self.env.data[self._m][i][k] = self.env._norm(k, v)
        self.env.log.append(('write', self._m, tuple(self.ids), dict(vals)))
        return True

    def unlink(self):
        for i in self.ids:
            self.env.data[self._m].pop(i, None)
        self.env.log.append(('unlink', self._m, tuple(self.ids), {}))
        return True


class FakeEnv(object):
    MODELS = ('synapsys.service', 'synapsys.service.standard', 'synapsys.context', 'synapsys.domain', 'synapsys.method', 'synapsys.canon', 'synapsys.pattern', 'ir.model.data')

    def __init__(self):
        self.data = {m: {} for m in self.MODELS}
        self.seq = itertools.count(1000)
        self.log = []

    @staticmethod
    def _norm(k, v):
        if k in M2M_F:
            assert isinstance(v, list) and v and v[0][0] == 6, 'many2many writes use (6, 0, ids)'
            return sorted(v[0][2])
        return v

    def __getitem__(self, model):
        if model not in self.data:
            raise KeyError('model %r is not part of the loader\'s allowed surface' % model)  # x_service_catalogue (V19) or anything else is unreachable
        return RS(self, model, [])

    def seed(self, model, **vals):
        i = next(self.seq)
        self.data[model][i] = dict(vals)
        return i

    def writes(self, model=None):
        return [x for x in self.log if x[0] in ('create', 'write', 'unlink') and (model is None or x[1] == model)]
