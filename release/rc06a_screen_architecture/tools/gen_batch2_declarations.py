"""Generates addon/synapsys/data/screen_declarations_batch2.json (RC06c batch 2: 12 PROPOSAL and OPEN noun screens).

Build aid, not part of the addon. Every source chip is authored here as (name, date, quote); the generator REFUSES to write a chip
whose quote is not in the registry element's definition_source, and refuses a date that is not in the quote's own text or in the
text of the same citation (a date is never inferred or inherited). A noun's "made of" relationship is the registry relationship (H.*)
in which that noun is the named subject of a REQUIRED role (role label equals the noun label); where there is none, made_of is null
and the screen says so. Peers are not declared (the registry gives no peer list for these nouns).
usage: python3 gen_batch2_declarations.py [registry.json] > out.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "rc05_scaffold_lens", "fixtures", "mesh_registry_v0_3.json")
REG = json.load(open(REGP, encoding="utf-8"))
EL = {e["id"]: e for e in REG["elements"]}
PI, TB, DD, LD = "Project instr. v2.2.2", "Task brief", "design_d", "Ledger"

# noun id -> [(chip name, date as written in the registry text or None, quote that must occur in definition_source)]
CHIPS = {
    "N.PURPOSE": [("design_d.json Context->Purpose", None, "design_d.json Context->Purpose"), ("design_d.json Purpose->Strategy", "16 Nov 23:32", "Purpose->Strategy (alignment, src L 16 Nov 23:32"), (LD, "20 Nov 06:27", "ledger 20 Nov 06:27")],
    "N.CAPABILITY": [(PI, None, "project instructions v2.2.2"), ("design_d.json", None, "design_d.json Programme->Capability"), ("pack.md OV-02", None, "pack.md OV-02")],
    "N.CHAIN": [(PI, None, "project instructions v2.2.2"), ("design_d.json", None, "design_d.json Benefit->Chain"), ("Registry PART Chain/Stage", None, "registry PART N.CHAIN/STAGE"), ("lens.json Value-chain lens", "20 Nov 05:5x", "lens.json Value-chain lens (ruled 20 Nov 05:5x)")],
    "N.PARTNER": [("design_d.json", None, "design_d.json Partner->Context"), ("Registry PART Partner/Agreement", None, "registry PART N.PARTNER/AGREEMENT"), ("Ledger line 10", "19 Nov", "ledger 19 Nov line 10")],
    "N.METHOD": [("Project instr. v2.2.2 s5", None, "Project instructions v2.2.2 s5"), ("spec/content_spec.md", None, "spec/content_spec.md 'Registered way of working (P)'"), (DD, None, "design_d Service->Method"), ("lens.json Learning lens", None, "lens.json Learning lens includes Method"), ("Steward ruling", "21 Nov 08:54", "Steward ruling 21 Nov 08:54")],
    "N.WORK": [("Project instr. v2.2.2 s0", None, "Project instructions v2.2.2 s0"), (LD, "20 Nov 10:05", "ledger 20 Nov 10:05"), (LD, "07:35", "ledger 07:35 (My Work"), (DD, None, "design_d Work->Programme")],
    "N.PATTERN": [("Builder spec row", None, "Builder spec row (spec_rows.json"), (LD, "19 Nov 23:15", "ledger 19 Nov 23:15"), (DD, None, "design_d Asset->Pattern")],
    "N.SIGNAL": [("Builder spec row", None, "Builder spec row ('What enters and is sensed'"), (LD, "20 Nov 07:16", "ledger 20 Nov 07:16"), (LD, "10:05", "10:05 (Inbox"), (DD, None, "design_d Signal->Fractal"), ("Ruling on Signal types", "21 Nov 08:24", "ruled 21 Nov 08:24")],
    "N.CHANGE": [("Builder spec row", None, "Builder spec row ('Change request and release'"), (DD, None, "design_d Change->Canonical"), ("Project instr. s8", None, "project instructions s8")],
    "N.MARKET": [("Builder spec row", None, "Builder spec row ('Markets sensed and captured"), (DD, None, "design_d Offering->Market"), (LD, "07:35", "ledger 07:35 (Playing to Win"), (LD, "10:33", "10:33 (Markets is a KDB face")],
    "N.INDUSTRY": [("pack.md OV-05", None, "pack.md OV-05 (builder proposal)"), ("design_d.json", None, "design_d.json Chain->Industry"), ("Registry PART Industry/Dataset", None, "registry PART N.INDUSTRY/DATASET"), (LD, "20 Nov 10:36", "ledger 20 Nov 10:36")],
    "N.PRODUCT": [(LD, "19 Nov 23:05", "Ledger 19 Nov 23:05"), ("Ledger Open list", None, "ledger Open list"), ("spec/content_spec.md", None, "spec/content_spec.md DEFINE"), ("pack.md OV-02", None, "pack.md OV-02")],
}
ORDER = ["N.PURPOSE", "N.CAPABILITY", "N.CHAIN", "N.PARTNER", "N.METHOD", "N.WORK", "N.PATTERN", "N.SIGNAL", "N.CHANGE", "N.MARKET", "N.INDUSTRY", "N.PRODUCT"]
STATUS = {"N.INDUSTRY": "OPEN", "N.PRODUCT": "OPEN"}  # everything else in this batch is PROPOSAL; asserted against the registry below
assert sorted(ORDER) == sorted(CHIPS)


AMBIGUOUS = {}
VERB_BINDING = {}


def own_relationship(noun):
    """The H.* relationship in which this noun is the named subject of a REQUIRED role, else None (must be unique)."""
    label = EL[noun]["label"].lower()
    hits = []
    for c in REG["clusters"]:
        rel = next((ref for role, ref in c["members"] if role == "relationship"), None)
        if not rel:
            continue
        if any((EL.get(ref) or {}).get("cls") == "V" for role, ref in c["members"]):  # binds verbs: verb binding is its own gate
            if any(role != "relationship" and ref == noun for role, ref in c["members"]):
                VERB_BINDING[noun] = rel
            continue
        for role, ref in c["members"]:
            r = EL.get(role) or {}
            if role != "relationship" and ref == noun and r.get("required") and str(r.get("label", "")).rstrip("+") == label:
                hits.append(rel)
    hits = sorted(set(hits))
    if len(hits) > 1:  # ambiguous: the registry names this noun the subject of more than one relationship; none is chosen here
        AMBIGUOUS[noun] = hits
        return None
    return hits[0] if hits else None


screens = []
for noun in ORDER:
    e = EL[noun]
    assert e["cls"] == "N" and e.get("status") == STATUS.get(noun, "PROPOSAL") and e.get("definition") and e.get("definition_source"), (noun, e.get("status"))
    src = e["definition_source"]
    for name, date, quote in CHIPS[noun]:
        assert quote in src, (noun, quote)
        assert date is None or date in src, (noun, date)
    rel = own_relationship(noun)
    noun_name = e["label"]
    s = {
        "id": "SCR.%s.NOUN" % noun[2:], "noun": noun, "screen_type": "noun", "title": noun_name,
        "answer": {"from": "element.definition"}, "trust_claim": "meaning",
        "movement": {"verbs": [], "hold_reason": "noun-to-verb governance waits on the Architecture tab"},
        "made_of": ({"relationship": rel, "heading": "What the %s is made of" % noun_name, "role_names": {}} if rel else None),
        "peers": None,
        "claims": [{"id": "meaning", "type": "element", "noun": noun, "label": "%s meaning" % noun_name, "qualifier_from": "element.kind",
                    "sources": [{"name": n, "date": d, "quote": q} for n, d, q in CHIPS[noun]]}],
    }
    screens.append(s)

doc = {"schema": "synapsys.screen.declaration/1",
       "status": "SOURCE CANDIDATE, NON_AUTHORISING. RC06c batch 2: noun screens for the 10 PROPOSAL and 2 OPEN nouns. Not released to the registry (registry 0.3.5 is unchanged).",
       "slots": {"enable": ["header", "answer", "trust", "movement"], "enhance": ["made_of", "peers"], "enrich": ["trust_table", "open_questions", "technical"]},
       "screens": screens}
print(json.dumps(doc, indent=2, ensure_ascii=False))
if AMBIGUOUS or VERB_BINDING:
    print("made_of left null. ambiguous: %s; relationship binds verbs: %s" % (AMBIGUOUS, VERB_BINDING), file=sys.stderr)
