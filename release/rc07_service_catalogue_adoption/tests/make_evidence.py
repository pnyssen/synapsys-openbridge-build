"""Writes the evidence files: the dry-run diff on a fake database seeded with every reference record (what a dev dry-run would look like if all links resolve),
and the offline plan report (no database; relations not checked). Fixture data only; nothing here touches Odoo."""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import test_service_catalogue_load as T
L = T.L
out = os.path.join(HERE, "..", "evidence"); os.makedirs(out, exist_ok=True)
e = T.seeded(); buf = io.StringIO()
res = L.run(e, extract=T.EXTRACT, out=buf)
open(os.path.join(out, "dry_run_fake_db_20261127.txt"), "w").write("FAKE DATABASE (every Context, Domain, Method, Canon and Pattern the extract names is seeded); not dev\n" + buf.getvalue())
rep = dict(res["report"], extract_sha256=res["extract_sha256"], mode="DRY-RUN on a fake database; counts: %s" % res["counts"])
json.dump(rep, open(os.path.join(out, "dry_run_report_fake_db_20261127.json"), "w"), indent=1, sort_keys=True)
e2 = T.seeded(skip=("context", "method", "canon", "pattern", "domain")); r2 = L.run(e2, extract=T.EXTRACT, out=io.StringIO())
json.dump({"mode": "DRY-RUN on a fake database with NO reference records: every relation unresolved", "counts": r2["counts"], "unresolved_by_field": {k: sum(1 for u in r2["report"]["unresolved_relations"] if u["field"] == k) for k in ("context_id", "domain_id", "method_id", "canon_ids", "pattern_ids")}}, open(os.path.join(out, "dry_run_unresolved_scenario_20261127.json"), "w"), indent=1, sort_keys=True)
print("evidence written", res["counts"])
