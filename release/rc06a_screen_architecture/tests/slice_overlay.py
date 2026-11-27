"""The ONE declared overlay of the read-only Context->Strategy->Service slice on the RC06 tree. The historical file-level guards (rc06f/g/h manifests)
stay strict about everything else: they call strip() so that exactly these additions, and exactly one import line, are discounted - nothing more."""
import hashlib, os
SLICE_ADDED = {"arch_graph.py", "arch_slice.py", "controllers/arch_slice.py", "data/arch_slice_acceptance.json"}
SLICE_IMPORT_LINE = "from . import arch_slice\n"
CTRL_INIT = "controllers/__init__.py"

def _sha(b): return hashlib.sha256(b).hexdigest()

def strip(now, addon_dir):
    """Return a copy of {relpath: sha256} with the declared overlay removed and controllers/__init__.py restored to its pre-slice bytes."""
    out = {k: v for k, v in now.items() if k not in SLICE_ADDED}
    p = os.path.join(addon_dir, CTRL_INIT)
    raw = open(p, "rb").read().decode("utf-8")
    if raw.endswith(SLICE_IMPORT_LINE) and raw.count(SLICE_IMPORT_LINE) == 1:
        out[CTRL_INIT] = _sha(raw[: -len(SLICE_IMPORT_LINE)].encode("utf-8"))
    return out
