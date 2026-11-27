import copy
import unittest
from wave1_binder_candidate import dry_run, NoWriteRights

SRC = {
 "contexts": [{"id":1,"code":"CTX-SS","purpose_id":4},{"id":9,"code":"CTX-BASIN","purpose_id":7}],
 "purposes": [{"id":4,"code":"PRP-ENT-001"},{"id":7,"code":None}],
 "strategies": [{"id":10,"code":"STR-SS-001","context_id":1,"purpose_id":4}],
 "assets": [{"id":366,"context_id":1},{"id":373,"context_id":1},{"id":374,"context_id":1},{"id":367,"context_id":9}]
}
V20 = {
 "contexts":[{"id":1001,"v19_id":1,"code":"CTX-SS","purpose_id":2004,"kind":"K-4","kind_ruling":"ATTESTED_TEST_FIXTURE","kind_proposed":"K-12"}],
 "purposes":[{"id":2004,"code":"PRP-ENT-001"}],
 "strategies":[{"id":3010,"v19_id":10,"code":"STR-SS-001","context_id":1001,"purpose_id":2004}],
 "assets":[{"id":4366,"v19_id":366,"context_id":1001},{"id":4373,"v19_id":373,"context_id":1001},{"id":4374,"v19_id":374,"context_id":1001}],
 "mode_verbs":{"K-4":[{"id":6},{"id":7},{"id":15},{"id":25},{"id":14,"human_only":True}]}}
ACT={"allowed_contexts":["CTX-SS"],"visible":{"context":[1001],"purpose":[2004],"strategy":[3010],"asset":[4366,4373,4374]}}

def run(src=SRC,v20=V20,act=ACT,noun="N.CONTEXT",**kwargs):
    return dry_run(noun,"CTX-SS",act,src,v20,**kwargs)

class T(unittest.TestCase):
    def test_valid_source_only_membership(self):
        r=run(); self.assertEqual(r["state"],"SOURCE_BOUND_FIXTURE")
        self.assertEqual((r["data"]["source_strategy_count"],r["data"]["context_asset_count"]),(1,3))
        self.assertEqual(r["simulation"],{"CREATE":0,"UPDATE":0,"HOLD":0,"NO_CHANGE":6})
    def test_explicit_context_purpose_fk(self):
        v=copy.deepcopy(V20);v["contexts"][0]["purpose_id"]=None
        self.assertEqual(run(v20=v)["reason"],"CONTEXT_PURPOSE_FK_MISMATCH")
    def test_foreign_actor_denied_no_metadata(self):
        a=copy.deepcopy(ACT);a["allowed_contexts"]=["CTX-BASIN"]
        r=run(act=a);self.assertEqual(r["state"],"DENIED_REDACTED")
        self.assertIsNone(r["data"]);self.assertEqual(r["relationships"],[])
    def test_actor_record_rule_denied(self):
        a=copy.deepcopy(ACT);a["visible"]["context"]=[]
        self.assertEqual(run(act=a)["state"],"DENIED_REDACTED")
    def test_missing_context_holds(self):
        v=copy.deepcopy(V20);v["contexts"]=[]
        self.assertEqual(run(v20=v)["reason"],"MISSING_OR_DUPLICATE_TARGET_CONTEXT")
    def test_duplicate_context_holds(self):
        v=copy.deepcopy(V20);v["contexts"].append(copy.deepcopy(v["contexts"][0]))
        self.assertEqual(run(v20=v)["reason"],"MISSING_OR_DUPLICATE_TARGET_CONTEXT")
    def test_duplicate_purpose_code_holds(self):
        v=copy.deepcopy(V20);v["purposes"].append({"id":2005,"code":"PRP-ENT-001"})
        self.assertEqual(run(v20=v)["reason"],"PURPOSE_TARGET_CODE_AMBIGUOUS_OR_MISSING")
    def test_unverified_purpose_code_holds(self):
        s=copy.deepcopy(SRC);s["purposes"][0]["code"]=None
        self.assertEqual(run(src=s)["reason"],"PURPOSE_SOURCE_IDENTITY_UNRESOLVED")
    def test_missing_or_unruled_kind_holds(self):
        for kind,ruling in [(None,None),("K-4",None),("K-99","TEXT")]:
            v=copy.deepcopy(V20);v["contexts"][0].update({"kind":kind,"kind_ruling":ruling})
            self.assertEqual(run(v20=v)["reason"],"K_KIND_NOT_RULED")
    def test_kind_not_inferred_from_proposal(self):
        self.assertEqual(run()["data"]["context_kind"],"K-4")
        self.assertEqual(run()["data"]["cut_b"],"Enable")
    def test_human_only_filtered_execution_denied(self):
        r=run();self.assertEqual(r["data"]["eligible_verbs"],[6,7,15,25])
        self.assertNotIn(14,r["data"]["eligible_verbs"])
        self.assertFalse(r["data"]["execution_authorised"])
    def test_strategy_context_mismatch_holds(self):
        v=copy.deepcopy(V20);v["strategies"][0]["context_id"]=999
        self.assertEqual(run(v20=v)["reason"],"STRATEGY_CONTEXT_OR_PURPOSE_MISMATCH")
    def test_source_strategy_purpose_mismatch_holds(self):
        s=copy.deepcopy(SRC);s["strategies"][0]["purpose_id"]=7
        self.assertEqual(run(src=s)["reason"],"STRATEGY_SOURCE_PURPOSE_MISMATCH")
    def test_no_strategy_asset_causality(self):
        r=run();self.assertFalse(any(e["from"]=="Strategy" and e["to"]=="Asset" for e in r["relationships"]))
        self.assertEqual(r["data"]["strategy_asset_causality"],"NOT_PROVEN")
    def test_foreign_asset367_denied(self):
        r=run(requested_asset=367);self.assertEqual(r["state"],"DENIED_REDACTED")
        self.assertIsNone(r["data"]);self.assertEqual(r["relationships"],[])
    def test_asset_context_mismatch_holds(self):
        v=copy.deepcopy(V20);v["assets"][1]["context_id"]=1009
        self.assertEqual(run(v20=v)["reason"],"ASSET_CONTEXT_MISMATCH")
    def test_duplicate_strategy_target_holds(self):
        v=copy.deepcopy(V20);v["strategies"].append(copy.deepcopy(v["strategies"][0]))
        self.assertEqual(run(v20=v)["reason"],"STRATEGY_IDENTITY_MISSING_OR_DUPLICATE")
    def test_service_view_reuses_contract_no_staged_service(self):
        a=run();b=run(noun="N.SERVICE")
        self.assertEqual(a["contract"],b["contract"])
        self.assertEqual(b["state"],"UNSOURCED_HELD")
        self.assertEqual(b["relationships"],[])
    def test_duplicate_source_asset_holds(self):
        s=copy.deepcopy(SRC);s["assets"].append(copy.deepcopy(s["assets"][0]))
        self.assertEqual(run(src=s)["reason"],"DUPLICATE_SOURCE_PROVENANCE")
    def test_duplicate_source_strategy_holds(self):
        s=copy.deepcopy(SRC);s["strategies"].append(copy.deepcopy(s["strategies"][0]))
        self.assertEqual(run(src=s)["reason"],"DUPLICATE_SOURCE_PROVENANCE")
    def test_owner_authority_not_inferred_from_fixture(self):
        r=run();self.assertEqual(r["data"]["owner_authority"],"UNATTESTED_HELD")
        self.assertEqual(r["data"]["actor_entitlement"],"ASSUMED_IN_FIXTURE_NOT_RUNTIME_PROVEN")
    def test_no_source_or_target_mutation(self):
        a,b,c=copy.deepcopy(SRC),copy.deepcopy(V20),copy.deepcopy(ACT)
        run();self.assertEqual((SRC,V20,ACT),(a,b,c))
    def test_duplicate_crosswalk_source_holds(self):
        s=copy.deepcopy(SRC);s["contexts"].append(copy.deepcopy(s["contexts"][0]))
        self.assertEqual(run(src=s)["reason"],"DUPLICATE_SOURCE_PROVENANCE")
    def test_legacy_false_positive_fixed(self):
        # Previous binder emitted BOUND for only a V20 Context fixture, no Purpose/Strategy/Asset.
        v={"contexts":V20["contexts"],"purposes":[],"strategies":[],"assets":[],"mode_verbs":V20["mode_verbs"]}
        self.assertEqual(run(v20=v)["state"],"UNSOURCED_HELD")
    def test_idempotent_twice_zero_writes(self):
        a,b=run(),run()
        self.assertEqual(a["dry_run_sha256"],b["dry_run_sha256"])
        self.assertEqual(a["writes"],b["writes"])
        self.assertEqual(a["simulation"],b["simulation"])
    def test_no_write_path_even_when_rights_claimed(self):
        with self.assertRaises(NoWriteRights):run(write=True)

if __name__=="__main__":unittest.main(verbosity=2)
