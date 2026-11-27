"""RC07 offline tests for the Service Catalogue loader (contract section 5, tests 1 to 10, plus the cases that protect them). In-memory fake ORM; no Odoo, no network.
What this cannot show: the real ORM (required fields, access rules, guards, onchange, mail), the real V20 reference data (Contexts, Methods, Canon, Patterns, Domains), the
Service screen and counts after a load, and a real backup and restore. Those are the dev fast path (separate, Steward word)."""
import ast, collections, copy, hashlib, io, json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "loader")); sys.path.insert(0, HERE)
import service_catalogue_load as L
from fake_orm import FakeEnv

# The extract is business data and is NOT committed (it is filed in Working Memory, sha256 87bdc258...). Put it at fixtures/ or point SYN_V19_EXTRACT at it; without it
# every test here is SKIPPED, never passed.
EXTRACT = os.environ.get("SYN_V19_EXTRACT") or os.path.abspath(os.path.join(HERE, "..", "fixtures", "V19_SERVICE_CATALOGUE_EXTRACT_20261127.json"))
LOADER = os.path.abspath(os.path.join(HERE, "..", "loader", "service_catalogue_load.py"))
if not os.path.exists(EXTRACT):
    raise unittest.SkipTest("V19 extract not present at %s: the loader tests were NOT run" % EXTRACT)
DOC, SHA = L.load_extract(EXTRACT)
ROWS = DOC["rows"]
HELD_NAMES = {3, 14}
RULINGS = {"3": "Human-AI Orientation and Navigation (HAION)", "14": "Relationship, Partner & Collaborative Ecosystem Orchestration"}


def seeded(skip=()):
    """A fake database holding every Context, Domain, Method, Canon and Pattern the extract refers to (unless skipped), each found by its v19 id or code."""
    e = FakeEnv()
    ids = collections.defaultdict(dict)
    for r in ROWS:
        if r["x_context_id"] and "context" not in skip:
            ids["context"].setdefault(r["x_context_id"][0], r["x_context_id"][1])
        if r["x_primary_governing_domain"] and "domain" not in skip:
            ids["domain"].setdefault(r["x_primary_governing_domain"], None)
        if r["x_method_id"] and "method" not in skip:
            ids["method"].setdefault(r["x_method_id"][0], None)
        if "canon" not in skip:
            for c in r["x_canonical_library_ids"]:
                ids["canon"].setdefault(c, None)
        if "pattern" not in skip:
            for c in r["x_pattern_ids"]:
                ids["pattern"].setdefault(c, None)
    for v, code in ids["context"].items():
        e.seed("synapsys.context", code=code, v19_id=v)
    for code in ids["domain"]:
        e.seed("synapsys.domain", code=code)
    for v in ids["method"]:
        e.seed("synapsys.method", v19_id=v, code="M%d" % v)
    for v in ids["canon"]:
        e.seed("synapsys.canon", v19_id=v)
    for v in ids["pattern"]:
        e.seed("synapsys.pattern", v19_id=v, code="P%d" % v)
    return e


def run(env, apply=False, rulings=None):
    buf = io.StringIO()
    return L.run(env, extract=EXTRACT, apply=apply, name_rulings=rulings, out=buf), buf.getvalue()


def services(env):
    return env.data["synapsys.service"]


class T1_Extract(unittest.TestCase):
    def test_extract_hash_49_rows_34_live_15_archived_and_a_wrong_hash_is_refused(self):
        self.assertEqual(hashlib.sha256(open(EXTRACT, "rb").read()).hexdigest(), L.EXTRACT_SHA256)
        self.assertEqual(len(ROWS), 49); self.assertEqual(sum(1 for r in ROWS if r["x_active"] is True), 34); self.assertEqual(sum(1 for r in ROWS if r["x_active"] is False), 15)
        self.assertEqual(len(ROWS[0]), 85)
        with self.assertRaises(ValueError):
            L.load_extract(EXTRACT, "0" * 64)

    def test_every_extract_field_is_either_mapped_or_in_the_unmapped_list_and_never_both(self):
        allf = set(ROWS[0])
        self.assertEqual((len(L.MAPPED), len(L.UNMAPPED)), (45, 40))
        self.assertEqual(set(L.MAPPED) | set(L.UNMAPPED), allf)
        self.assertEqual(set(L.MAPPED) & set(L.UNMAPPED), set())
        plan = L.build_plan(DOC, L.NoLookup())
        self.assertEqual((plan["report"]["coverage"]["neither"], plan["report"]["coverage"]["overlap"], plan["report"]["coverage"]["absent_from_extract"]), ([], [], []))


class T2_DryRunApplyIdempotent(unittest.TestCase):
    def test_dry_run_is_the_default_and_writes_nothing(self):
        import inspect
        self.assertFalse(inspect.signature(L.run).parameters["apply"].default)
        e = seeded(); res, out = run(e)
        self.assertEqual(e.writes(), []); self.assertEqual(res["mode"], "DRY-RUN"); self.assertIn("DRY-RUN: nothing was written", out)
        self.assertEqual(res["counts"], {"CREATE": 47, "HOLD_NAME": 2})
        self.assertEqual(len(services(e)), 0); self.assertEqual(len(e.data["synapsys.service.standard"]), 0)

    def test_apply_creates_the_rows_and_a_second_apply_changes_nothing(self):
        e = seeded(); res, _ = run(e, apply=True)
        self.assertEqual(res["writes"], {"created": 47, "updated": 0, "standard": 1}); self.assertEqual(len(services(e)), 47)
        n = len(e.log); res2, out2 = run(e, apply=True)
        self.assertEqual(res2["writes"], {"created": 0, "updated": 0, "standard": 0}); self.assertEqual(len(e.log), n)  # not one write call
        self.assertEqual(res2["counts"], {"UNCHANGED": 47, "HOLD_NAME": 2}); self.assertEqual(res2["standard"], "UNCHANGED")

    def test_held_names_are_not_loaded_until_the_steward_rules_and_then_the_load_completes_idempotently(self):
        e = seeded(); run(e, apply=True)
        have = {r["v19_id"] for r in services(e).values()}
        self.assertEqual({r["id"] for r in ROWS} - have, HELD_NAMES)
        res, _ = run(e, apply=True, rulings=RULINGS)
        self.assertEqual(res["writes"], {"created": 2, "updated": 0, "standard": 0}); self.assertEqual(len(services(e)), 49)
        n = len(e.log); run(e, apply=True, rulings=RULINGS); self.assertEqual(len(e.log), n)
        self.assertEqual({r["code"]: r["name"] for r in services(e).values()}["SC-03"], RULINGS["3"])

    def test_every_v19_code_appears_once_and_the_v19_id_set_equals_the_extract_set(self):
        e = seeded(); run(e, apply=True, rulings=RULINGS)
        rows = list(services(e).values())
        self.assertEqual(sorted(r["v19_id"] for r in rows), sorted(r["id"] for r in ROWS))
        self.assertEqual(sorted(r["code"] for r in rows), sorted(r["x_service_code"] for r in ROWS))
        self.assertEqual(len({r["code"] for r in rows}), 49)
        plan = L.build_plan(DOC, L.NoLookup())  # and at plan level, before any ruling
        self.assertEqual(sorted(p["v19_id"] for p in plan["rows"]), sorted(r["id"] for r in ROWS))

    def test_a_managed_field_changed_by_hand_is_shown_as_an_update_and_restored_but_unmanaged_fields_are_left_alone(self):
        e = seeded(); run(e, apply=True)
        rid = [i for i, r in services(e).items() if r["code"] == "SC-01"][0]
        services(e)[rid]["description"] = "edited"; services(e)[rid]["perspective"] = "internal"; services(e)[rid]["kind_proposed"] = "K-6"
        res, out = run(e)
        self.assertEqual(res["counts"].get("UPDATE"), 1); self.assertIn("description", out)
        run(e, apply=True)
        self.assertNotEqual(services(e)[rid]["description"], "edited")
        self.assertEqual((services(e)[rid]["perspective"], services(e)[rid]["kind_proposed"]), ("internal", "K-6"))  # never touched

    def test_an_unmarked_row_with_a_matching_v19_id_is_a_conflict_and_is_never_touched(self):
        e = seeded(); i = e.seed("synapsys.service", code="X", name="hand made", v19_id=1)
        res, _ = run(e, apply=True)
        self.assertEqual(res["counts"].get("CONFLICT_UNMARKED"), 1); self.assertEqual(services(e)[i], {"code": "X", "name": "hand made", "v19_id": 1})
        self.assertEqual(len(services(e)), 1 + 46)


class T3_Relations(unittest.TestCase):
    def test_unresolvable_context_method_canon_pattern_domain_become_a_recorded_gap_and_no_record_is_invented(self):
        e = seeded(skip=("context", "method", "canon", "pattern", "domain"))
        before = {m: len(e.data[m]) for m in ("synapsys.context", "synapsys.method", "synapsys.canon", "synapsys.pattern", "synapsys.domain")}
        res, _ = run(e, apply=True)
        self.assertEqual({m: len(e.data[m]) for m in before}, before)  # no stub parent created
        for r in services(e).values():
            for f in ("context_id", "method_id", "domain_id"):
                self.assertFalse(r.get(f)); 
            self.assertFalse(r.get("canon_ids")); self.assertFalse(r.get("pattern_ids"))
        un = res["report"]["unresolved_relations"]
        kinds = collections.Counter(u["field"] for u in un)
        self.assertEqual(kinds["context_id"], 19 - 0)  # every row that has a context
        self.assertTrue(all(k in kinds for k in ("method_id", "canon_ids", "pattern_ids", "domain_id")))
        self.assertTrue(all(u["why"] == "not found" for u in un))
        self.assertTrue(any(r.get("pattern_codes") for r in services(e).values()))  # the raw v19 pattern ids survive in the field built for them

    def test_resolved_relations_are_linked_by_v19_id_or_code(self):
        e = seeded(); run(e, apply=True)
        ctx = {r["v19_id"]: i for i, r in e.data["synapsys.context"].items()}
        r1 = [r for r in services(e).values() if r["v19_id"] == 1][0]
        self.assertEqual(r1["context_id"], ctx[1])
        self.assertEqual(sorted(r1["canon_ids"]), sorted(i for i, r in e.data["synapsys.canon"].items() if r["v19_id"] in ROWS[0]["x_canonical_library_ids"]))
        dom = {r["code"]: i for i, r in e.data["synapsys.domain"].items()}
        self.assertEqual(r1["domain_id"], dom[ROWS[0]["x_primary_governing_domain"]])

    def test_an_ambiguous_match_is_not_guessed(self):
        e = seeded(); e.seed("synapsys.method", v19_id=1, code="DUP")  # two methods carry v19 id 1
        res, _ = run(e, apply=True)
        self.assertTrue(any(u["field"] == "method_id" and u["why"] == "ambiguous" for u in res["report"]["unresolved_relations"]))
        self.assertTrue(all(not r.get("method_id") for r in services(e).values() if r["v19_id"] == 1))

    def test_context_found_by_code_only_and_a_v19_id_that_disagrees_with_the_code_is_ambiguous(self):
        e = seeded(); e.seed("synapsys.context", code="CTX-SS", v19_id=999)  # same code, another v19 id
        res, _ = run(e)
        self.assertTrue(any(u["field"] == "context_id" and u["why"] == "ambiguous" for u in res["report"]["unresolved_relations"]))


class T4_Standard(unittest.TestCase):
    def setUp(self):
        self.e = seeded(); self.res, _ = run(self.e, apply=True, rulings=RULINGS)
        self.std = list(self.e.data["synapsys.service.standard"].values())
        self.rows = {r["v19_id"]: r for r in services(self.e).values()}

    def test_one_standard_holding_the_four_shared_paragraphs_and_the_expected_row_counts(self):
        self.assertEqual(len(self.std), 1)
        paras = json.loads(self.std[0]["paragraphs"]); self.assertEqual(len(paras), 4)
        pf = self.res["report"]["standard"]["per_field"]
        self.assertEqual({k: v["top_count"] for k, v in pf.items()}, {"authority_gate_schema": 15, "adaptability_envelope": 30, "observation_learning_contract": 15, "provider_fallback_policy": 29})
        self.assertEqual({k: v["linked_rows"] for k, v in pf.items()}, {"authority_gate_schema": 15, "adaptability_envelope": 30, "observation_learning_contract": 15, "provider_fallback_policy": 29})

    def test_rows_with_the_shared_text_link_to_the_standard_and_store_no_own_copy(self):
        paras = json.loads(self.std[0]["paragraphs"])
        src = {"authority_gate_schema": "x_authority_gate_schema", "adaptability_envelope": "x_adaptability_envelope", "observation_learning_contract": "x_observation_learning_contract"}
        for r in ROWS:
            live = self.rows[r["id"]]
            refs = json.loads(live.get("standard_refs") or "{}")
            for dst, s in src.items():
                if r[s] and r[s] in paras:
                    self.assertEqual(paras[refs[dst][0]], r[s], (r["id"], dst))
                    self.assertFalse(live.get(dst), (r["id"], dst))  # no own copy
                    self.assertTrue(live.get("standard_id"))
                elif r[s]:
                    self.assertEqual(live.get(dst), r[s], (r["id"], dst))  # differing text stays as the row's own override
                    self.assertNotIn(dst, refs)

    def test_differing_provider_fallback_text_has_no_field_and_is_reported_held_not_dropped_silently(self):
        held = self.res["report"]["standard"]["provider_fallback_overrides_held"]
        self.assertEqual(held, 47 - 29)
        for r in services(self.e).values():
            self.assertNotIn("provider_fallback_policy", r)  # no such field is invented on synapsys.service

    def test_source_hashes_record_the_sha256_of_each_v19_text(self):
        r = self.rows[1]; h = json.loads(r["source_hash"])
        self.assertEqual(h["description"], hashlib.sha256(ROWS[0]["x_description"].encode()).hexdigest())
        self.assertEqual(h["authority_gate_schema"], hashlib.sha256(ROWS[0]["x_authority_gate_schema"].encode()).hexdigest())

    def test_a_standard_field_below_the_threshold_is_not_made_a_paragraph(self):
        plan = L.build_plan(DOC, L.NoLookup(), min_shared=31)
        self.assertEqual(len(plan["standard"]["paragraphs"]), 0)
        self.assertTrue(all(not p["values"]["standard_refs"] for p in plan["rows"]))


class T5_LifecycleAndPerspective(unittest.TestCase):
    def test_lifecycle_counts_active_29_draft_3_candidate_1_retired_16_flagged_proposed(self):
        plan = L.build_plan(DOC, L.NoLookup())
        lc = plan["report"]["lifecycle_counts"]
        self.assertEqual(lc["counts"], {"active": 29, "draft": 3, "candidate": 1, "retired": 16}); self.assertTrue(lc["proposed"])
        e = seeded(); run(e, apply=True, rulings=RULINGS)
        self.assertEqual(dict(collections.Counter(r["lifecycle"] for r in services(e).values())), {"active": 29, "draft": 3, "candidate": 1, "retired": 16})

    def test_all_15_archived_rows_are_loaded_as_retired_and_the_original_status_is_kept_as_history(self):
        e = seeded(); run(e, apply=True, rulings=RULINGS)
        rows = {r["v19_id"]: r for r in services(e).values()}
        arch = [r for r in ROWS if r["x_active"] is False]
        self.assertEqual(len(arch), 15)
        for r in arch:
            self.assertEqual(rows[r["id"]]["lifecycle"], "retired")
            self.assertIn("status=%s" % r["x_service_status"], rows[r["id"]]["validation_status_v19"]); self.assertIn("active=false", rows[r["id"]]["validation_status_v19"])
        self.assertIn("validation=validated", rows[1]["validation_status_v19"])
        self.assertTrue(all(r["lifecycle"] != "plug_in_ready" for r in rows.values()))

    def test_perspective_is_empty_on_every_row_and_the_source_values_are_counted_not_mapped(self):
        e = seeded(); run(e, apply=True, rulings=RULINGS)
        for r in services(e).values():
            self.assertNotIn("perspective", r)
        plan = L.build_plan(DOC, L.NoLookup()); pc = plan["report"]["perspective_source_counts"]
        self.assertEqual(pc["x_service_class"], {"(empty)": 20, "offering": 16, "internal": 9, "membrane": 4})
        self.assertEqual(pc["x_offering_layer"], {"C": 35, "B": 8, "A": 6}); self.assertEqual(pc["x_service_role"], {"(empty)": 25, "service": 24})

    def test_proof_states_and_protected_fields_are_never_written_to_a_live_field(self):
        e = seeded(); run(e, apply=True, rulings=RULINGS)
        written = set()
        for _op, model, _ids, vals in e.writes("synapsys.service"):
            written |= set(vals)
        self.assertEqual(written & set(L.PROTECTED_NEVER_WRITTEN), set())
        self.assertEqual(written - set(L.MANAGED), set())  # only the managed list is ever written
        for f in ("ppv", "kind", "observed", "answer_accepted", "benefit_ids", "asset_ids", "slots_filled", "plug_in_ready"):
            self.assertNotIn(f, written)
        # sentinel test: put a unique marker into every proof-state field and every other unmapped field of a copy of the extract; none may reach a written value
        doc = copy.deepcopy(DOC)
        for r in doc["rows"]:
            for f in L.UNMAPPED:
                if f not in ("x_company_id", "create_date", "write_date") and not L.empty(r[f]):
                    r[f] = "SENTINEL_%s_%d" % (f, r["id"])
        e2 = seeded(); plan = L.build_plan(doc, L.OdooBackend(e2), RULINGS)
        for p in plan["rows"]:
            self.assertNotIn("SENTINEL_", json.dumps(p["values"], default=str), p["code"])
        for f in ("x_service_ppv_entry", "x_service_ppv_ceiling", "x_productisation_status", "x_processability_state", "x_fpv_acceptance"):
            self.assertEqual(sum(1 for r in doc["rows"] if "SENTINEL_" in str(r[f])), sum(1 for r in ROWS if not L.empty(r[f])))  # the sentinels really were in the input


class T6_Unmapped(unittest.TestCase):
    CONTRACT_COUNTS = {"x_service_ppv_entry": 40, "x_service_ppv_ceiling": 39, "x_productisation_status": 46, "x_processability_state": 30, "x_fpv_acceptance": 0,
                       "x_itil_service_description": 3, "x_itil_utility": 21, "x_itil_warranty": 22, "x_itil_service_level_target": 1, "x_itil_support_model": 4, "x_itil_service_owner_role": 29,
                       "x_warranty_commitment_type": 1, "x_warranty_commitment_text": 1, "x_ai_capability_requirements": 32, "x_human_role_requirements": 31,
                       "x_deterministic_tech_requirements": 31, "x_operator_trace": 41, "x_operations_pattern": 35, "x_default_workflow_phase": 19, "x_named_consumer": 4, "x_gsa_role": 2,
                       "x_cost_risk_transfer": 1, "x_fallback_flag": 1, "x_collab_ai_access_mode": 28, "x_collab_ai_allowed_intents": 19, "x_collab_ai_scope": 28, "x_client_contact_visible": 16,
                       "x_channel_ids": 0, "x_context_binding_required": 15, "x_context_binding_notes": 40, "x_haion_summary": 18, "x_source_document": 25, "x_source_version": 24,
                       "x_dim_trigger_linkage": 2, "x_producible_lens_ids": 6, "x_prerequisite_edge_ids": 1, "x_requires_edge_ids": 1, "x_company_id": 49, "create_date": 49, "write_date": 49}

    def test_the_report_lists_exactly_the_40_fields_with_the_contracts_counts(self):
        rep = L.build_plan(DOC, L.NoLookup())["report"]["unmapped_fields"]
        self.assertEqual(len(rep), 40)
        self.assertEqual({x["field"]: x["filled"] for x in rep}, self.CONTRACT_COUNTS)
        self.assertEqual(sum(1 for x in rep if x["group"] == "Authority/proof states (PPV)"), 5)

    def test_held_mapped_fields_are_reported_separately_and_nothing_is_dropped_silently(self):
        rep = L.build_plan(DOC, L.NoLookup())["report"]
        held = {x["field"]: x for x in rep["held_mapped"]}
        self.assertEqual(held["x_itil_csi_log"]["filled"], 13)
        self.assertEqual((held["x_steward_contact_id"]["owner_empty_and_contact_present"], held["x_steward_contact_id"]["differs_from_owner"]), (0, 0))
        for f in L.PERSPECTIVE_SOURCES:
            self.assertIn(f, held)
        self.assertEqual({x["field"] for x in rep["unmapped_fields"]} & set(held), set())


class T7_Rollback(unittest.TestCase):
    def test_rollback_removes_only_rows_and_the_standard_the_loader_created(self):
        e = seeded()
        pre = e.seed("synapsys.service", code="PRE-1", name="pre-existing", v19_id=777)
        std_pre = e.seed("synapsys.service.standard", name="someone else's standard", paragraphs="[]")
        run(e, apply=True, rulings=RULINGS)
        self.assertEqual(len(services(e)), 1 + 49)
        res = L.rollback(env=e, out=io.StringIO())  # dry-run by default
        self.assertEqual((res["mode"], res["services"], res["standard"]), ("DRY-RUN", 49, True)); self.assertEqual(len(services(e)), 50)
        L.rollback(env=e, apply=True, out=io.StringIO())
        self.assertEqual(list(services(e)), [pre]); self.assertIn(std_pre, e.data["synapsys.service.standard"]); self.assertEqual(len(e.data["synapsys.service.standard"]), 1)
        self.assertEqual(len([i for i in e.data["ir.model.data"].values() if i["module"] == L.XML_MODULE]), 0)
        for m in ("synapsys.context", "synapsys.domain", "synapsys.method", "synapsys.canon", "synapsys.pattern"):
            self.assertTrue(e.data[m])  # reference data untouched

    def test_after_a_rollback_a_new_apply_reloads_cleanly(self):
        e = seeded(); run(e, apply=True); L.rollback(env=e, apply=True, out=io.StringIO())
        res, _ = run(e, apply=True)
        self.assertEqual(res["writes"]["created"], 47)

    def test_the_standard_survives_a_rollback_if_a_row_the_loader_did_not_create_still_uses_it(self):
        e = seeded(); run(e, apply=True)
        sid = [i for i in e.data["synapsys.service.standard"]][0]
        other = e.seed("synapsys.service", code="OTHER", name="other", standard_id=sid)
        L.rollback(env=e, apply=True, out=io.StringIO())
        self.assertIn(sid, e.data["synapsys.service.standard"]); self.assertIn(other, services(e))


class T8_StaticNoV19Write(unittest.TestCase):
    SRC = open(LOADER, encoding="utf-8").read()
    TREE = ast.parse(SRC)

    def test_the_loader_imports_nothing_that_can_reach_v19_or_the_network(self):
        mods = {a.name.split(".")[0] for n in ast.walk(self.TREE) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(self.TREE) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertEqual(mods, {"argparse", "collections", "hashlib", "json", "re", "sys"})
        for bad in ("xmlrpc", "odoorpc", "requests", "urllib", "socket", "http", "subprocess", "os", "shutil"):
            self.assertNotIn(bad, mods)

    def test_the_proof_state_and_other_unmapped_field_names_appear_in_code_only_in_the_unmapped_table(self):
        tbl = [n for n in ast.walk(self.TREE) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "UNMAPPED_GROUPS" for t in n.targets)][0]
        inside = {id(x) for x in ast.walk(tbl)}
        names = set(L.UNMAPPED)
        for n in ast.walk(self.TREE):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in names:
                self.assertIn(id(n), inside, "%s is referenced outside the unmapped table, line %d" % (n.value, n.lineno))

    def test_the_only_database_models_named_in_code_are_the_synapsys_ones_and_ir_model_data(self):
        doc = {id(n.body[0].value) for n in ast.walk(self.TREE) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
        models = set()
        for n in ast.walk(self.TREE):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc and ("." in n.value) and " " not in n.value and n.value != L.EXTRACT_SCHEMA and n.value.split(".")[0] in ("synapsys", "ir", "res", "x_service_catalogue"):
                models.add(n.value)
        self.assertEqual(models, {"synapsys.service", "synapsys.service.standard", "synapsys.context", "synapsys.method", "synapsys.canon", "synapsys.pattern", "synapsys.domain", "ir.model.data"})
        self.assertNotIn("x_service_catalogue", {c.value for n in ast.walk(self.TREE) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc for c in [n]})

    def test_create_write_unlink_appear_only_inside_the_backend_class_and_the_report_file_write(self):
        cls = [n for n in ast.walk(self.TREE) if isinstance(n, ast.ClassDef) and n.name == "OdooBackend"][0]
        inside = {id(x) for x in ast.walk(cls)}
        for n in ast.walk(self.TREE):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("create", "write", "unlink"):
                if isinstance(n.func.value, ast.Name) and n.func.value.id in ("out", "w"):
                    continue  # writing text to the output stream, not to a database
                self.assertIn(id(n), inside, "%s() outside OdooBackend at line %d" % (n.func.attr, n.lineno))
        opens = [n for n in ast.walk(self.TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"]
        modes = [ast.literal_eval(n.args[1]) if len(n.args) > 1 else "r" for n in opens]
        self.assertEqual(sorted(modes), ["r", "r", "rb", "w"])  # reads the extract and a ruling file; the one write is the optional offline report

    def test_the_fake_database_cannot_reach_a_v19_model_so_a_v19_write_would_fail_loudly(self):
        with self.assertRaises(KeyError):
            seeded()["x_service_catalogue"]
        e = seeded(); run(e, apply=True)
        self.assertEqual({m for _o, m, _i, _v in e.log}, {"synapsys.service", "synapsys.service.standard", "ir.model.data"})

    def test_the_command_line_has_no_apply_switch_and_needs_no_database(self):
        self.assertNotIn("--apply", self.SRC.split("def main")[1].split("a = ap.parse_args")[0])
        self.assertEqual(L.main(["--extract", EXTRACT, "--no-lookup"]), 0)


class T9_FieldValues(unittest.TestCase):
    def setUp(self):
        self.e = seeded(); run(self.e, apply=True, rulings=RULINGS); self.rows = {r["v19_id"]: r for r in services(self.e).values()}

    def test_names_codes_descriptions_and_the_equality_rule(self):
        by = {r["id"]: r for r in ROWS}
        for vid, live in self.rows.items():
            self.assertEqual(live["code"], by[vid]["x_service_code"])
            self.assertEqual(live.get("description"), by[vid]["x_description"] or None) if by[vid]["x_description"] else self.assertFalse(live.get("description"))
        self.assertEqual(self.rows[1]["name"], "Governance and Operating Model Enablement")
        self.assertEqual(self.rows[43]["name"], "Benefits Realisation as a Service")  # V19 x_name had a dash
        for vid in (18, 34, 35):
            self.assertFalse(self.rows[vid]["name"].startswith(self.rows[vid]["code"]))  # the duplicated code prefix is removed once
        notes = {(n["v19_id"]) for n in L.build_plan(DOC, L.NoLookup())["report"]["name_notes"] if "leading code" in n["note"]}
        self.assertEqual(notes, {18, 34, 35})
        holds = L.build_plan(DOC, L.NoLookup())["report"]["name_holds"]
        self.assertEqual({h["v19_id"] for h in holds}, HELD_NAMES)

    def test_owner_escalation_sla_door_and_approval_values(self):
        by = {r["id"]: r for r in ROWS}
        n = 0
        for vid, live in self.rows.items():
            r = by[vid]
            self.assertEqual(live.get("owner_name"), r["x_service_owner_id"][1] if r["x_service_owner_id"] else None)
            self.assertEqual(live.get("escalation"), r["x_escalation_group_id"][1] if r["x_escalation_group_id"] else None)
            self.assertFalse(live.get("delivery_lead"))
            self.assertEqual(live.get("entry_point"), r["x_entry_point"] or None)
            if r["x_sla_metric_text"]:
                self.assertTrue(live["sla_text"].startswith(r["x_sla_metric_text"])); n += 1
            if r["x_sla_metric_value"]:
                self.assertEqual(live["sla_value"], r["x_sla_metric_value"])
            if r["x_authority_reference"]:
                self.assertTrue(live["approval_category"].startswith(r["x_authority_reference"]))
            if r["x_service_activation_requires_decision"] is True:
                self.assertIn("activation_requires_decision", live["approval_category"])
        self.assertEqual(n, 33)

    def test_a_filled_x_ffe_state_is_kept_as_history_and_slots_8_11_12_14_15_are_not_written(self):
        self.assertEqual(sum(1 for r in self.rows.values() if r.get("ffe_state_v19")), 4)
        for r in self.rows.values():
            for f in ("programme_ids", "benefit_ids", "asset_ids", "obligations", "slots_filled", "plug_in_ready", "rhythm_tier", "kind_proposed"):
                self.assertNotIn(f, r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
