"""Offline fakes and loaders for the RC06a tests. No Odoo, no network, no writes. Loads the addon modules by path."""
import hashlib, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.abspath(os.path.join(HERE, "..", "addon", "synapsys"))
FIXTURE = os.environ.get("SYN_REG_FIXTURE") or os.path.abspath(os.path.join(HERE, "..", "..", "rc05_scaffold_lens", "fixtures", "mesh_registry_v0_3.json"))
REG_SHA = "7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423"


def load(name):
    if ADDON not in sys.path:
        sys.path.insert(0, ADDON)
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(ADDON, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


sl = load("scaffold_lens")
sd = load("screen_decl")
sr = load("screen_render")
sw = load("scaffold_wire")
sv = load("scaffold_view")

RAW = open(FIXTURE, "rb").read()
REG = json.loads(RAW)
SHA = hashlib.sha256(RAW).hexdigest()
assert SHA == REG_SHA, "registry fixture is not registry 0.3.5"


class AccessError(Exception):
    pass


class Rec:
    def __init__(s, body=None, sha=None, version="0.3.5", state="candidate"):
        s.body = body if body is not None else RAW.decode("utf-8"); s.sha = sha or SHA; s.version = version; s.state = state

    def __bool__(s):
        return True


class Model:
    def __init__(s, rec, log):
        s.rec, s.log = rec, log

    def search(s, domain, order=None, limit=None):
        s.log.append(("search", tuple(map(tuple, domain)), order, limit))
        return s.rec

    def sudo(s):
        raise AssertionError("sudo must never be called")


SP01 = {"x_service_code": "SP-01", "x_service_name": "Strategic Planning & Context Establishment", "x_service_status": "active",
        "x_lifecycle_gate": "active", "x_validation_status": False, "x_source_document": False, "x_source_version": False,
        "x_primary_governing_domain": "D001", "x_processability_state": "structured"}


class CatRec(dict):
    def __bool__(s):
        return True

    def __getitem__(s, k):
        return dict.get(s, k, False)


class CatModel:
    def __init__(s, log, vals=None, ra=False, missing=False):
        s.log, s.vals, s.ra, s.missing = log, vals if vals is not None else dict(SP01), ra, missing

    def search(s, domain, limit=None):
        s.log.append(("search_cat", tuple(map(tuple, domain)), limit))
        if s.ra:
            raise AccessError("no catalogue read")
        return [] if s.missing else CatRec(s.vals)


class User:
    def __init__(s, groups):
        s.id = 7; s.g = set(groups)

    def has_group(s, x):
        return x in s.g


class Row(dict):
    """A fake record: field access by key; a many2one is a Row too (has .id)."""
    def __init__(s, id, **vals):
        dict.__init__(s, id=id, **vals); s.id = id

    def __bool__(s):
        return True


class RecModel:
    """Fake model holding Row records. Counts every call; any write-like call fails the test."""
    def __init__(s, rows, log, name, ra=False):
        s.rows, s.log, s.name, s.ra = rows, log, name, ra

    def search(s, domain, limit=None):
        s.log.append(("search_rec", s.name, tuple(map(tuple, domain)), limit))
        if s.ra:
            raise AccessError("no record read")
        for r in s.rows:
            if all(r.get(f) == v for f, op, v in domain):
                return r
        return []

    def sudo(s):
        raise AssertionError("sudo must never be called")

    def create(s, *a, **k):
        raise AssertionError("no writes")

    write = unlink = create


STEW, COLL = "synapsys.group_synapsys_steward", "synapsys.group_synapsys_user"


class Env:
    def __init__(s, groups, records=None, rec=None, cat=None, ra_models=()):
        s.user = User(groups); s.log = []
        s.m = Model(rec if rec is not None else Rec(), s.log)
        s.cat = cat if cat is not None else CatModel(s.log)
        s.records = records or {}
        s.ra_models = set(ra_models)

    def __getitem__(s, k):
        if k == "synapsys.mesh.registry":
            return s.m
        if k == "x_service_catalogue":
            return s.cat
        assert k in s.records or k in s.ra_models, k
        return RecModel(s.records.get(k, []), s.log, k, ra=k in s.ra_models)

    def sudo(s):
        raise AssertionError("env.sudo must never be called")
