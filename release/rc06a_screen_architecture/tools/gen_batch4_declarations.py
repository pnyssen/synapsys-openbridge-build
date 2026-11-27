"""Generates addon/synapsys/data/screen_declarations_batch4.json (RC06e batch 4: nine action screens, menu type, sourced from document rows).
Build aid, not part of the addon. Each screen: answer = its own A row; Made of = its plane row (P1 for A1 to A3, P2 for A4 to A6, P3 for A7 to A9);
trust table = its A row, its P row, C1, C2, C3. Two open questions on every screen: the fixed contract text about the definition, and C2.
usage: python3 gen_batch4_declarations.py [sources.json] > out.json"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "addon", "synapsys", "data", "screen_sources_batch4.json"), encoding="utf-8"))
ROWS = {r["id"]: r for r in SRC["rows"]}
HOLD = "noun-to-verb governance waits on the Architecture tab"  # carried from batches 1 to 3; the batch 4 contract only says verbs HOLD
DEFINITION = "Definition: UNSOURCED. No project document states what this action means."  # fixed contract text (the contract's own quotation)
ACTIONS = ["ORIENT", "CANONICALISE", "STRUCTURE", "ASSURE", "NAVIGATE", "COMPOSE", "ACTIVATE", "TRANSFORM", "PROJECT"]
screens = []
for i, name in enumerate(ACTIONS):
    a, p = "A%d" % (i + 1), "P%d" % (i // 3 + 1)
    label = ROWS[a]["display"].split(" (")[0]  # the action's name is the first word of its own A row
    assert ROWS[a]["display"].upper().startswith(name), (a, name)
    claims = [[a], [p], ["C1"], ["C2"], ["C3"]]
    screens.append({
        "id": "SCR.ACTION.%s" % name, "screen_type": "menu", "title": label,
        "answer": {"from": "doc", "row": a}, "trust_claim": "c." + a,
        "movement": {"verbs": [], "hold_reason": HOLD},
        "made_of": {"heading": None, "rows": [p], "note": None},
        "peers": None,
        "claims": [{"id": "c." + g[0], "type": "doc", "rows": g} for g in claims],
        "open": [{"id": "o.%s.1" % name, "kind": "unsourced", "claim": "c." + a, "rows": [], "text": DEFINITION, "tail": None},
                 {"id": "o.%s.2" % name, "kind": "decision", "claim": "c.C2", "rows": ["C2"], "tail": None}]})
doc = {"schema": "synapsys.screen.declaration/1",
       "status": "SOURCE CANDIDATE, NON_AUTHORISING. RC06e batch 4: nine action screens (menu type) sourced from document rows. Where each will sit in a menu is NOT decided. Not released to the registry (registry 0.3.5 is unchanged).",
       "slots": {"enable": ["header", "answer", "trust", "movement"], "enhance": ["made_of", "peers"], "enrich": ["trust_table", "open_questions", "technical"]},
       "sources": "screen_sources_batch4.json",
       "contract_text": [DEFINITION],
       "screens": screens}
print(json.dumps(doc, indent=2, ensure_ascii=False))
