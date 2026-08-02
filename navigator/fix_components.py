"""Reconcile NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html into dist.

Two corrections, both root-caused:
- Working Memory link depth (05_AI_RETURNS_HASHED is a sibling of the
  Obsidian vault root: five ups from COMPONENTS, not four).
- RC12: pre-execution D007 language (static rows + embedded JSON literal)
  reconciled to the executed, receipted state; build fails if any stale
  marker survives.
"""
import pathlib

import model

HERE = pathlib.Path(__file__).parent
SRC = HERE / "mirror" / "CURRENT" / "COMPONENTS" / "NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html"
DST = (HERE / "dist" / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT" /
       "COMPONENTS" / "NAVIGATOR_PARALLEL_DELIVERY_CONTROL_v1.1.html")


def main():
    t = SRC.read_text(encoding="utf-8")
    bad = 'href="../../../../05_AI_RETURNS_HASHED/'
    assert bad in t
    t = t.replace(bad, 'href="../../../../../05_AI_RETURNS_HASHED/')
    t = model.reconcile_post_d007(t)
    for stale in model.STALE_PROJECTION_MARKERS:
        assert stale not in t, f"stale marker survives: {stale}"
    DST.write_text(t, encoding="utf-8")
    print(f"parallel delivery control reconciled: {len(t.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
