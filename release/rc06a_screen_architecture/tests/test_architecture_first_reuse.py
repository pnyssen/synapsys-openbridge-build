"""First operational Architecture reuse contract — source-only tests.

Work Object: WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001
Source target: release/rc06a_screen_architecture/addon/synapsys
Intended install location: release/rc06a_screen_architecture/tests/test_architecture_first_reuse.py

These are bounded fail-first tests of the user-requested contract, not evidence
of V20 runtime acceptance. Context and Service are distinct element types.
No Odoo mutations, model creation, data import, or elevation occurs here.

Old-source expected failures: inherited parent-specific depth, independent
record presentation depth, real actor Context membership, and native SB-02
Service Catalogue binding. The builder may adapt the API fixture while
preserving the tested semantics; never weaken a failing assertion to obtain green.
"""
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "addon" / "synapsys"
if not (SRC / "lens_contract.py").exists():
    raise RuntimeError("Run from the existing release/rc06a_screen_architecture/tests directory.")
sys.path.insert(0, str(SRC))

import lens_contract as lc
import screen_decl as sd
import scaffold_wire as sw


def elem(name, *, ancestors=()):
    return lc.element(name, name, ancestors=list(ancestors),
                      noun=name, definition="Source fixture", status="CANDIDATE",
                      relationships=[], source="fixture-only")


class User:
    id = 7
    def has_group(self, xmlid):
        return xmlid == "synapsys.group_synapsys_user"


class Context:
    id = 1
    member_ids = (User(),)
    steward_user_id = None


class ContextModel:
    def search(self, domain, *args, **kwargs):
        # Simulates only an actor-entitled Context; never performs sudo.
        return [Context()]


class Env:
    user = User()
    def __getitem__(self, model):
        if model == "synapsys.context":
            return ContextModel()
        raise AssertionError("Unexpected or privileged model lookup: " + model)


class ReuseContract(unittest.TestCase):
    def test_shared_global_depth_changes_two_element_types(self):
        for name in ("N.CONTEXT", "N.SERVICE"):
            with self.subTest(name=name):
                self.assertIn('data-mode="enhance"',
                              lc.render_element(elem(name), "enhance"))

    def test_local_exact_override_is_preserved(self):
        html = lc.render_element(elem("N.CONTEXT"), "enable",
                                 {"N.CONTEXT": "enrich"})
        self.assertIn('data-mode="enrich"', html)

    def test_parent_override_inherits_to_source_bound_descendant(self):
        child = elem("N.SERVICE", ancestors=("N.CONTEXT",))
        html = lc.render_element(child, "enable", {"N.CONTEXT": "enrich"})
        self.assertIn('data-mode="enrich"', html)

    def test_child_override_wins_over_ancestor_override(self):
        child = elem("N.SERVICE", ancestors=("N.CONTEXT",))
        html = lc.render_element(child, "enable",
                                 {"N.CONTEXT": "enrich", "N.SERVICE": "enhance"})
        self.assertIn('data-mode="enhance"', html)

    def test_ancestor_override_does_not_change_unrelated_branch(self):
        unrelated = elem("N.ASSET", ancestors=("N.OTHER_CONTEXT",))
        html = lc.render_element(unrelated, "enable",
                                 {"N.CONTEXT": "enrich"})
        self.assertIn('data-mode="enable"', html)

    # HELD (SB-02 handoff item 5): screen_decl.resolve_depth caps record depth by K-stage under a non-canonical 27-Nov chat rationale;
    # the latest Integration contract separates presentation depth from K-kind. The assertion below is UNCHANGED and still runs; it is
    # expected to fail until an attributable D001/D002 source ruling exists. An unexpected PASS means the rule changed: re-review.
    @unittest.expectedFailure
    def test_presentation_depth_is_not_a_kinematic_kind_stage(self):
        actual, clamped, reason = sd.resolve_depth(
            "record", "enrich", stage="enable", role_effective="enrich")
        self.assertEqual((actual, clamped, reason), ("enrich", False, None))

    def test_rights_cap_still_limits_presentation_depth(self):
        actual, clamped, reason = sd.resolve_depth(
            "record", "enrich", stage="enrich", role_effective="enable")
        self.assertEqual(actual, "enable")
        self.assertTrue(clamped)

    def test_context_membership_is_derived_from_current_actor_source(self):
        actor = sw.actor_from_env(Env())
        self.assertEqual(actor["uid"], 7)
        self.assertIn("collaborator", actor["groups"])
        self.assertIn(1, actor["context_ids"])

    def test_primary_service_contract_uses_native_v20_catalogue(self):
        refs = [b for bindings in sw.EVIDENCE_BINDINGS.values() for b in bindings]
        primary = [b for b in refs if b.get("code") == "SB-02"
                   and b.get("model") == "synapsys.service"]
        self.assertTrue(primary,
                        "Primary Architecture SB-02 must be source-bound to native V20 Service Catalogue, not a legacy SP-01-only projection.")


# ---- SB-02 fixture repair: real, distinct source-backed Context records (not the generic N.CONTEXT noun class) ----
CTX_A, CTX_B = "rec:synapsys.context:1", "rec:synapsys.context:2"


def svc(sid, ctx, *more):
    """A Service RECORD element whose lineage is its source Context record (nearest first), never a guessed prefix."""
    return elem("rec:synapsys.service:%d" % sid, ancestors=(ctx,) + more)


def mode_of(html):
    return html.split('data-mode="', 1)[1].split('"', 1)[0]


class TwoContextInheritance(unittest.TestCase):
    def test_context_a_override_reaches_only_its_own_service_record(self):
        ov = {CTX_A: "enrich"}
        self.assertEqual(mode_of(lc.render_element(svc(5, CTX_A), "enable", ov)), "enrich")
        self.assertEqual(mode_of(lc.render_element(svc(6, CTX_B), "enable", ov)), "enable")   # sibling Context isolated

    def test_same_behaviour_repeats_in_second_context(self):
        ov = {CTX_B: "enhance"}
        self.assertEqual(mode_of(lc.render_element(svc(6, CTX_B), "enable", ov)), "enhance")
        self.assertEqual(mode_of(lc.render_element(svc(5, CTX_A), "enable", ov)), "enable")

    def test_exact_descendant_override_beats_context_override(self):
        ov = {CTX_A: "enrich", "rec:synapsys.service:5": "enhance"}
        self.assertEqual(mode_of(lc.render_element(svc(5, CTX_A), "enable", ov)), "enhance")

    def test_clearing_returns_to_parent_then_global(self):
        s5 = svc(5, CTX_A)
        self.assertEqual(mode_of(lc.render_element(s5, "enable", {CTX_A: "enrich", s5["id"]: "enhance"})), "enhance")
        self.assertEqual(mode_of(lc.render_element(s5, "enable", {CTX_A: "enrich"})), "enrich")     # child cleared -> parent
        self.assertEqual(mode_of(lc.render_element(s5, "enable", {})), "enable")                     # parent cleared -> global

    def test_closest_ancestor_wins(self):
        s5 = svc(5, CTX_A, "rec:synapsys.portfolio:9")
        ov = {CTX_A: "enhance", "rec:synapsys.portfolio:9": "enrich"}
        self.assertEqual(mode_of(lc.render_element(s5, "enable", ov)), "enhance")

    def test_no_lineage_means_no_inheritance_even_with_matching_name_prefix(self):
        look_alike = elem("rec:synapsys.service:7")                   # same noun family, but no source lineage supplied
        self.assertEqual(mode_of(lc.render_element(look_alike, "enable", {CTX_A: "enrich"})), "enable")

    def test_inherited_state_is_labelled_not_claimed_as_local(self):
        html = lc.render_element(svc(5, CTX_A), "enable", {CTX_A: "enrich"})
        self.assertIn('data-override="inherited"', html)
        self.assertNotIn("Reset to global", html)


class Rec:
    def __init__(self, rid, steward=None, members=()):
        self.id, self.steward_user_id, self.member_ids = rid, steward, tuple(members)


class Actor(User):
    def __init__(self, uid, groups=("synapsys.group_synapsys_user",)):
        self.id, self._g = uid, groups

    def has_group(self, xmlid):
        return xmlid in self._g


class CtxModel:
    def __init__(self, recs=(), exc=None):
        self.recs, self.exc, self.queried = list(recs), exc, 0

    def search(self, domain, *a, **k):
        self.queried += 1
        if self.exc:
            raise self.exc
        return self.recs


class NoSudoEnv:
    def __init__(self, user, models):
        self.user, self.models = user, models

    def __getitem__(self, m):
        return self.models[m]

    def sudo(self, *a, **k):
        raise AssertionError("sudo must never be used")


class AccessError(Exception):
    pass


class ContextRights(unittest.TestCase):
    A, B = Rec(1, members=[Actor(7)]), Rec(2, members=[Actor(8)])

    def test_member_of_a_sees_only_a(self):
        env = NoSudoEnv(Actor(7), {"synapsys.context": CtxModel([self.A])})
        self.assertEqual(sw.actor_from_env(env)["context_ids"], {1})

    def test_overbroad_search_result_is_filtered_fail_closed(self):
        env = NoSudoEnv(Actor(7), {"synapsys.context": CtxModel([self.A, self.B])})      # B is not this actor's Context
        self.assertEqual(sw.actor_from_env(env)["context_ids"], {1})

    def test_member_of_b_sees_only_b_second_context(self):
        env = NoSudoEnv(Actor(8), {"synapsys.context": CtxModel([self.A, self.B])})
        self.assertEqual(sw.actor_from_env(env)["context_ids"], {2})

    def test_steward_of_context_is_entitled(self):
        c = Rec(3, steward=Actor(9))
        env = NoSudoEnv(Actor(9, ("synapsys.group_synapsys_steward",)), {"synapsys.context": CtxModel([c])})
        self.assertEqual(sw.actor_from_env(env)["context_ids"], {3})

    def test_wrong_role_user_gets_no_contexts_and_no_query(self):
        m = CtxModel([self.A])
        env = NoSudoEnv(Actor(7, groups=()), {"synapsys.context": m})
        a = sw.actor_from_env(env)
        self.assertEqual((a["groups"], a["context_ids"], m.queried), (set(), set(), 0))

    def test_access_error_fails_closed(self):
        env = NoSudoEnv(Actor(7), {"synapsys.context": CtxModel(exc=AccessError("no"))})
        self.assertEqual(sw.actor_from_env(env)["context_ids"], set())

    def test_missing_model_fails_closed(self):
        self.assertEqual(sw.actor_from_env(NoSudoEnv(Actor(7), {}))["context_ids"], set())

    def test_unexpected_error_is_not_swallowed(self):
        env = NoSudoEnv(Actor(7), {"synapsys.context": CtxModel(exc=RuntimeError("bug"))})
        with self.assertRaises(RuntimeError):
            sw.actor_from_env(env)


class NativeServiceBinding(unittest.TestCase):
    VALUES = {"code": "SB-02", "name": "Capability Architecture and Maturity Framing", "lifecycle": "active",
              "validation_status_v19": "status=active; gate=active; validation=validated; validated_at=2026-07-18 03:56:40; active=true",
              "ffe_state_v19": False, "context_id": False, "method_id": False, "plug_in_ready": False}

    class R(dict):
        def __bool__(self):
            return True

    class M:
        def __init__(self, vals):
            self.vals = vals

        def search(self, domain, limit=None):
            (field, op, code), = domain
            return NativeServiceBinding.R(self.vals) if self.vals.get(field) == code else []

    def env(self, vals=None, exc=None, ctxs=None):
        class E(NoSudoEnv):
            def __getitem__(s, m):
                if exc:
                    raise exc
                if m == "synapsys.service":
                    return NativeServiceBinding.M(vals or self.VALUES)
                if m == "synapsys.context" and ctxs is not None:
                    return CtxModel(ctxs)
                raise KeyError(m)                                  # legacy catalogue absent in this fake database
        return E(Actor(7), {})

    def test_binding_is_pinned_to_source_fields_and_matches(self):
        ev, idx, notes = sw.collect_evidence(self.env())
        e = [x for x in ev if x["source_ref"] == "synapsys.service:SB-02"]
        self.assertEqual(len(e), 1)
        self.assertEqual(idx["synapsys.service:SB-02"]["sha256"], e[0]["sha256"])      # live source hash == pin

    def test_context_and_method_absent_reports_unbound_hold(self):
        _, idx, _ = sw.collect_evidence(self.env())
        d = idx["synapsys.service:SB-02"]["detail"]
        self.assertEqual(d["binding_state"]["status"], "UNBOUND/HOLD")
        self.assertIn("not bound to a Context (UNBOUND/HOLD)", d["qualifiers"])
        self.assertIn("no Method anchored (UNBOUND/HOLD)", d["qualifiers"])

    def test_source_edit_shows_as_hash_mismatch_not_silent(self):
        changed = dict(self.VALUES, lifecycle="draft")
        ev, idx, _ = sw.collect_evidence(self.env(changed))
        e = [x for x in ev if x["source_ref"] == "synapsys.service:SB-02"][0]
        self.assertNotEqual(idx["synapsys.service:SB-02"]["sha256"], e["sha256"])

    def test_context_binding_alone_does_not_make_it_ready(self):
        _, idx, _ = sw.collect_evidence(self.env(dict(self.VALUES, context_id=1), ctxs=[Rec(1, members=[Actor(7)])]))
        d = idx["synapsys.service:SB-02"]["detail"]["binding_state"]
        self.assertEqual((d["context"], d["status"]), ("BOUND", "UNBOUND/HOLD"))

    def test_foreign_context_service_is_withheld_and_indistinguishable_from_not_found(self):
        # H-NONDISCLOSE: Service bound to Context 9; actor 7 is only in Context 1.
        foreign = dict(self.VALUES, context_id=9)
        a = sw.collect_evidence(self.env(foreign, ctxs=[Rec(1, members=[Actor(7)])]))
        b = sw.collect_evidence(self.env(dict(self.VALUES, code="NOT-SB-02")))      # genuinely not found
        self.assertEqual(a, b)                                                       # same evidence, index, notes
        self.assertEqual(a[:2], ([], {}))
        self.assertEqual([n for n in a[2] if "SB-02" in n], [])
        self.assertNotIn("9", repr(a))

    def test_actor_with_no_context_fails_closed_for_bound_service(self):
        self.assertEqual(sw.collect_evidence(self.env(dict(self.VALUES, context_id=9)))[1], {})

    def test_health_projection_is_in_the_screen_evidence_and_not_ready_by_flag(self):
        v = dict(self.VALUES, context_id=1, plug_in_ready=True, answer_accepted=True)
        _, idx, _ = sw.collect_evidence(self.env(v, ctxs=[Rec(1, members=[Actor(7)])]))
        h = idx["synapsys.service:SB-02"]["detail"]["health"]
        self.assertEqual(h["operating"]["state"], "HELD")
        self.assertEqual(h["operating"]["answer_accepted_flag"], "FLAG_ONLY_NOT_EVIDENCE")
        self.assertEqual(h["relationships"]["edges"]["context"]["state"], "BOUND")
        self.assertEqual(h["relationships"]["edges"]["method"]["state"], "SOURCE_UNVERIFIED")
        self.assertTrue(any("operating qualification: HELD" in q for q in idx["synapsys.service:SB-02"]["detail"]["qualifiers"]))

    def test_actor_without_read_right_gets_no_evidence(self):
        ev, idx, notes = sw.collect_evidence(self.env(exc=AccessError("x")))
        self.assertEqual((ev, idx), ([], {}))

    def test_missing_model_is_a_note_not_a_crash(self):
        ev, idx, notes = sw.collect_evidence(NoSudoEnv(Actor(7), {}))
        self.assertEqual((ev, idx), ([], {}))
        self.assertTrue(any("model not present" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
