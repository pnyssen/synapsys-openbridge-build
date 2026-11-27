"""Generates addon/synapsys/data/screen_declarations_batch3.json (RC06d batch 3: seven menu screens sourced from project documents).
Build aid, not part of the addon. Every claim is bound to rows of data/screen_sources_batch3.json; the generator refuses a row that does not
exist. Which rows each screen uses comes from the contract's "Per screen" list; nothing else is added.
usage: python3 gen_batch3_declarations.py [sources.json] > out.json"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "addon", "synapsys", "data", "screen_sources_batch3.json"), encoding="utf-8"))
ROWS = {r["id"]: r for r in SRC["rows"]}
HOLD = "noun-to-verb governance waits on the Architecture tab"  # carried from the earlier batches; the batch 3 contract only says verbs HOLD

# (id, title, answer row, [claim row groups, first = the trust claim], made-of rows, made-of heading, record note, [open entries])
# open entry: (kind, claim row it hangs on, [rows], tail)   kinds: decision, proposal, conflict
SCREENS = [
    ("SCR.STRATEGIES.MENU", "Strategies", "S9", [["S9"], ["S10"], ["S12"], ["S11"]], ["S12"], "Nine strategies by group", "Records: none",
     [("decision", "S11", ["S11"], None)]),
    ("SCR.NAVIGATOR_PROGRESS.MENU", "Navigator Progress", "S1", [["S1"], ["S2"], ["S3"], ["S13"]], ["S2", "S3"], None, None,
     [("proposal", "S13", ["S13"], None)]),
    ("SCR.NAVIGATOR_INBOX.MENU", "Navigator Inbox", "S4", [["S4"], ["S5"], ["S13"]], ["S5"], None, None,
     [("proposal", "S13", ["S13"], None)]),
    ("SCR.NAVIGATOR_LEARNING.MENU", "Navigator Learning", "S6", [["S6"], ["S4"], ["S7"], ["S13"]], ["S4"], None, None,
     [("conflict", "S7", ["S7", "S4", "S6"], "The live menu follows the later."), ("proposal", "S13", ["S13"], None)]),
    ("SCR.MESH_BENEFIT_ASSET_LINKS.MENU", "Mesh Benefit-Asset links", "S14", [["S14"], ["S15"]], ["S15"], None, "Records: none", []),
    ("SCR.MESH_DOOR_RECEIPTS.MENU", "Mesh Door receipts", "S16", [["S16"], ["S17"], ["S18"]], ["S17", "S18"], None, None, []),
    ("SCR.MESH_MEASURES.MENU", "Mesh Measures", "S19", [["S19"], ["S17"], ["S18"]], ["S17", "S18"], None, None, []),
]
screens = []
for sid, title, ans, claims, items, heading, note, opens in SCREENS:
    used = {r for g in claims for r in g} | set(items) | {ans}
    assert used <= set(ROWS), (sid, used - set(ROWS))
    assert claims[0][0] == ans, sid
    for g in claims:
        assert len({ROWS[r]["status_word"] for r in g}) == 1, (sid, g)
    s = {"id": sid, "screen_type": "menu", "title": title, "answer": {"from": "doc", "row": ans}, "trust_claim": "c." + claims[0][0],
         "movement": {"verbs": [], "hold_reason": HOLD},
         "made_of": {"heading": heading, "rows": items, "note": note},
         "peers": None,
         "claims": [{"id": "c." + g[0], "type": "doc", "rows": g} for g in claims],
         "open": [{"id": "o.%s.%d" % (sid.split(".")[1], i + 1), "kind": k, "claim": "c." + c, "rows": rs, "tail": t} for i, (k, c, rs, t) in enumerate(opens)]}
    for o in s["open"]:
        assert o["claim"][2:] in {g[0] for g in claims}
    screens.append(s)
doc = {"schema": "synapsys.screen.declaration/1",
       "status": "SOURCE CANDIDATE, NON_AUTHORISING. RC06d batch 3: seven menu screens sourced from project documents (no registry element exists for them). Not released to the registry (registry 0.3.5 is unchanged).",
       "slots": {"enable": ["header", "answer", "trust", "movement"], "enhance": ["made_of", "peers"], "enrich": ["trust_table", "open_questions", "technical"]},
       "sources": "screen_sources_batch3.json",
       "contract_text": ["Records: none", "The live menu follows the later.", "Nine strategies by group"],
       "screens": screens}
print(json.dumps(doc, indent=2, ensure_ascii=False))
