"""Row-scope source parity (Wave 1). Offline only; no Odoo, no network, no writes.
Proves: (1) branch source equals the installed dev hotfix byte-for-byte (hashes read read-only from the host 28 Nov 2026);
(2) original failure: the baseline CSV leaves Collaborator rows for Context/Purpose/Strategy/Asset unscoped, so a non-member
sees foreign Context data - this test FAILS on that baseline and PASSES on the corrected CSV; (3) the corrected domains keep an
entitled member and a Steward able to read and do not over-restrict; (4) the change adds no Model, Method or Service wiring.
CANNOT show: real ir.rule/ir.model.access evaluation, role tests, 390/1024 UX, restore. Those need the gated dev run (D009)."""
import ast, csv, hashlib, io, os, re, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(HERE, "..", "addon", "synapsys")
BASELINE = os.path.join(HERE, "fixtures", "ROWSCOPE_BASELINE_ir.access.csv_8ecd95d")
INSTALLED = {  # sha256 read-only from /opt/odoo20/addons/synapsys on srv1536619, 28 Nov 2026
    "security/ir.access.csv": "937eb38846cc3cf42d9338e23bcec07741589de37b8270b1f24304794d74be2a",
    "models/work.py": "12ce345d340ee5894d1553be277c48a3dbd3b18ed9369966c78b7264789e1afa",
    "tests/__init__.py": "9831a3d9233db89423d338f7b139386154ab98cec7860f616337bea6944555ff",
    "tests/test_context_row_scope.py": "595e73837363b3c5ef3df7dd718bcd7d82475c68ca1f5654dc73d40621f9a609",
}
BASELINE_SHA = "2da94277b2601f5c1af8f95b255c152eda5db720b4d061897ac577195d0d50f8"
SCOPED = ["synapsys.context", "synapsys.purpose", "synapsys.strategy", "synapsys.asset"]
USER = "synapsys.group_synapsys_user"
STEWARD = "synapsys.group_synapsys_steward"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def rows(path):
    return list(csv.DictReader(io.open(path, newline="", encoding="utf-8")))


def collab(rs, model):
    return [r for r in rs if r["model_id"] == model and r["group_id/id"] == USER]


def unscoped_collaborator_models(path):
    """Models whose Collaborator row has no domain (the original defect)."""
    rs = rows(path)
    return [m for m in SCOPED if any(not r["domain"].strip() for r in collab(rs, m))]


def walk(rec, dotted):
    vals = [rec]
    for part in dotted.split("."):
        nxt = []
        for v in vals:
            x = v.get(part) if isinstance(v, dict) else None
            nxt.extend(x if isinstance(x, list) else [x])
        vals = [n for n in nxt if n is not None]
    return vals


def allowed(domain_text, rec, uid):
    """Tiny evaluator for the ['|', (path,op,user.id), ...] domains used in this CSV."""
    if not domain_text.strip():
        return True
    toks = ast.parse(domain_text.replace("user.id", str(uid)), mode="eval").body
    items = [ast.literal_eval(ast.unparse(e)) for e in toks.elts]
    assert items.count("|") == len(items) - 1 - items.count("|"), "unsupported domain shape"
    terms = [t for t in items if t != "|"]
    ok = []
    for path, op, val in terms:
        got = walk(rec, path)
        ok.append(any(g == val for g in got) if op == "=" else any(g == val for g in got) if op == "in" else False)
    return any(ok)


# fixture: own Context (member 7), foreign Context (steward 9), foreign Asset-style record
CTX_OWN = {"steward_user_id": 3, "member_ids": [7]}
CTX_FOREIGN = {"steward_user_id": 9, "member_ids": [8]}
REC = {
    "synapsys.context": (CTX_OWN, CTX_FOREIGN),
    "synapsys.strategy": ({"context_id": CTX_OWN}, {"context_id": CTX_FOREIGN}),
    "synapsys.asset": ({"context_id": CTX_OWN}, {"context_id": CTX_FOREIGN}),
    "synapsys.purpose": ({"context_ids": [CTX_OWN]}, {"context_ids": [CTX_FOREIGN]}),
}


class RowScopeParity(unittest.TestCase):
    csv_path = os.path.join(ADDON, "security", "ir.access.csv")

    def test_branch_source_equals_installed_hotfix(self):
        for rel, want in INSTALLED.items():
            self.assertEqual(sha(os.path.join(ADDON, rel)), want, rel)

    def test_baseline_fixture_is_the_original_branch_file(self):
        self.assertEqual(sha(BASELINE), BASELINE_SHA)

    def test_original_failure_baseline_is_unscoped(self):
        self.assertEqual(unscoped_collaborator_models(BASELINE), SCOPED)  # defect reproduced on the original source

    def test_corrected_source_scopes_every_collaborator_row(self):
        self.assertEqual(unscoped_collaborator_models(self.csv_path), [])

    def test_formerly_unscoped_access_is_now_denied_for_non_member(self):
        rs = rows(self.csv_path)
        for m in SCOPED:
            own, foreign = REC[m]
            dom = collab(rs, m)[0]["domain"]
            self.assertFalse(allowed(dom, foreign, 7), m + " foreign must be denied to collaborator 7")
            base = collab(rows(BASELINE), m)[0]["domain"]
            self.assertTrue(allowed(base, foreign, 7), m + " baseline leaked foreign record (original failure)")

    def test_entitled_member_and_steward_of_context_not_over_restricted(self):
        rs = rows(self.csv_path)
        for m in SCOPED:
            own, _ = REC[m]
            dom = collab(rs, m)[0]["domain"]
            self.assertTrue(allowed(dom, own, 7), m + " member")
            self.assertTrue(allowed(dom, own, 3), m + " steward of the Context")

    def test_steward_group_rows_stay_unscoped_full_access(self):
        rs = rows(self.csv_path)
        for m in SCOPED:
            st = [r for r in rs if r["model_id"] == m and r["group_id/id"] == STEWARD]
            self.assertTrue(st and all(not r["domain"].strip() and r["operation"] == "crud" for r in st), m)

    def test_only_the_four_collaborator_rows_changed(self):
        a, b = {r["id"]: r for r in rows(BASELINE)}, {r["id"]: r for r in rows(self.csv_path)}
        self.assertEqual(set(a), set(b))
        changed = sorted(i for i in a if a[i] != b[i])
        self.assertEqual(changed, sorted("access_synapsys_%s_user" % m.split(".")[1] for m in SCOPED))
        for i in changed:  # same model, group and operation: only name + domain differ
            for k in ("model_id", "group_id/id", "operation"):
                self.assertEqual(a[i][k], b[i][k])

    def test_purpose_context_ids_is_inverse_only_no_new_model_or_method(self):
        src = open(os.path.join(ADDON, "models", "work.py"), encoding="utf-8").read()
        m = re.search(r"class SynapsysPurposeScope\(models\.Model\):\n(.*?)\n\n\nclass ", src, re.S)
        self.assertTrue(m)
        body = m.group(1)
        self.assertIn("_inherit = 'synapsys.purpose'", body)
        self.assertNotIn("_name", body)
        self.assertNotIn("def ", body)
        self.assertIn("fields.One2many('synapsys.context', 'purpose_id'", body)


if __name__ == "__main__":
    unittest.main()
