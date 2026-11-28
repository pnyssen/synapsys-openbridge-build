"""The ONE declared overlay of the read-only Context->Strategy->Service slice on the RC06 tree. The historical file-level guards (rc06f/g/h manifests)
stay strict about everything else: they call strip() so that exactly these additions, and exactly one import line, are discounted - nothing more."""
import hashlib, os
SLICE_ADDED = {"arch_graph.py", "arch_slice.py", "controllers/arch_slice.py", "data/arch_slice_acceptance.json"}
SLICE_IMPORT_LINE = "from . import arch_slice\n"
CTRL_INIT = "controllers/__init__.py"
# Wave 1 row-scope hotfix parity overlay (declared; installed-dev hotfix brought into source). strip() discounts it ONLY while each file still has exactly
# the installed-hotfix bytes, mapping it back to its pre-hotfix hash; any other edit to these files is still caught by the historical guards.
ROWSCOPE_ADDED = {"tests/test_context_row_scope.py"}
ROWSCOPE_CHANGED = {  # relpath: (installed hotfix sha256, pre-hotfix sha256)
    "security/ir.access.csv": ("937eb38846cc3cf42d9338e23bcec07741589de37b8270b1f24304794d74be2a", "2da94277b2601f5c1af8f95b255c152eda5db720b4d061897ac577195d0d50f8"),
    "models/work.py": ("12ce345d340ee5894d1553be277c48a3dbd3b18ed9369966c78b7264789e1afa", "c44628751187be429e1087965199250e8460def0502dd46db56c593989489589"),
    "tests/__init__.py": ("9831a3d9233db89423d338f7b139386154ab98cec7860f616337bea6944555ff", "e306074a66839477ddfbb4b5d79d0c10ca4ca02eebfb575ef94df2bd2bae0350"),
}

ROWSCOPE_CHANGED.update({  # SB-02 source correction (declared): shared lens inheritance + own-rights actor Context ids + native SB-02 binding; same rule as above
    "lens_contract.py": ("e5fca4b7f0c360f2dfb404e876d73f44d16d0c063d3c3da6f5a542874393b89f", "c101592a687bfefcb55f0c94b1eb12826ef6edf1d3ecc69e0e662aa873d91600"),
    "scaffold_wire.py": ("0e59d17cda618c2f0463f25bfad07c2711061403451efa2676ef3767533257ce", "f6a64c5012c66ca38547479fa8e9e91753a6e89198efd7a30f7f041c353347a5"),
})

def _sha(b): return hashlib.sha256(b).hexdigest()

def strip(now, addon_dir):
    """Return a copy of {relpath: sha256} with the declared overlay removed and controllers/__init__.py restored to its pre-slice bytes."""
    out = {k: v for k, v in now.items() if k not in SLICE_ADDED and k not in ROWSCOPE_ADDED}
    for k, (hot, pre) in ROWSCOPE_CHANGED.items():
        if out.get(k) == hot:
            out[k] = pre
    p = os.path.join(addon_dir, CTRL_INIT)
    raw = open(p, "rb").read().decode("utf-8")
    if raw.endswith(SLICE_IMPORT_LINE) and raw.count(SLICE_IMPORT_LINE) == 1:
        out[CTRL_INIT] = _sha(raw[: -len(SLICE_IMPORT_LINE)].encode("utf-8"))
    return out
