"""Derive the addon's slice acceptance subset from the existing 61-row ALL61 matrix. Deterministic; reads two files; writes one file; no Odoo."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
MATRIX = os.path.join(ROOT, "review", "all61", "ALL61_MENU_IMPLEMENTATION_QA_MATRIX_20261128_v1.json")
OUT = os.path.join(ROOT, "addon", "synapsys", "data", "arch_slice_acceptance.json")
MODELS = ("synapsys.context", "synapsys.strategy", "synapsys.service")
KEEP = ("menu_id", "action_id", "path", "model", "status", "record_state", "definition_state", "perspective", "disposition", "status_reason")
def build():
    raw = open(MATRIX, "rb").read(); m = json.loads(raw)
    rows = [{k: r.get(k) for k in KEEP} for r in m["rows"] if r.get("model") in MODELS and r.get("action_id") is not None]
    return {"schema": "synapsys.arch.slice.acceptance.v1", "matrix_sha256": hashlib.sha256(raw).hexdigest(), "row_count_source": len(m["rows"]),
            "rows": sorted(rows, key=lambda r: r["menu_id"])}
if __name__ == "__main__":
    out = build(); open(OUT, "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n"); print(len(out["rows"]), "rows ->", OUT)
