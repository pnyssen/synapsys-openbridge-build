# synapsys-matrix-engine

Thin event-driven control plane for the MMM3CCC 3x3 control architecture.
One state source, one reducer, one prioritisation function, one Mesh
validator, one pattern registry, one renderer, one receipt writer. Pure
functions only -- no network, no filesystem, no wall-clock read, no Odoo or
N8N import (enforced by a static AST test, not just a comment).

- `matrix_engine.py` -- the engine.
- `tests/test_matrix_engine.py` -- 17 tests: reducer correctness (including
  rejection of out-of-order events), prioritisation ordering, mesh gating,
  pattern-registry MECE shape, renderer purity, receipt recomputability,
  and the no-Odoo/no-N8N boundary.

Run: `python3 -m pytest candidate-skills/synapsys-matrix-engine/tests/ -v`

`PATTERN_REGISTRY`'s nine verbs are a direct restatement of the MMM3CCC
board's own names/descriptions/use-cases already filed to Working Memory
this session -- this module executes against that content, it does not
invent it. HTML from `render()` is presentation only: no `<script>`, no
branching logic beyond formatting.

No Odoo or N8N mutation happens anywhere in this module, for any state
transition -- not gated by a runtime check, but absent: no client, no
import, no credential.
