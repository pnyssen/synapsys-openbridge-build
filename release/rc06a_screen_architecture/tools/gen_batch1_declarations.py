"""Generates addon/synapsys/data/screen_declarations_batch1.json (RC06b batch 1: 15 RULED noun screens).

Build aid, not part of the addon. Every source chip is authored here as (name, date, quote); the generator REFUSES to write a chip
whose quote is not in the registry element's definition_source, and refuses a date that is not in the quote's own text or in the
text of the same citation (a date is never inferred or inherited). A noun's "made of" relationship is the registry relationship (H.*)
in which that noun is the named subject of a REQUIRED role (role label equals the noun label); where there is none, made_of is null
and the screen says so. Peers are not declared (the registry gives no peer list for these nouns).
usage: python3 gen_batch1_declarations.py [registry.json] > out.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "rc05_scaffold_lens", "fixtures", "mesh_registry_v0_3.json")
REG = json.load(open(REGP, encoding="utf-8"))
EL = {e["id"]: e for e in REG["elements"]}
PI, TB, DD, LD = "Project instr. v2.2.2", "Task brief", "design_d", "Ledger"

# noun id -> [(chip name, date as written in the registry text or None, quote that must occur in definition_source)]
CHIPS = {
    "N.STRATEGY": [(LD, "20 Nov 06:27", "ledger 20 Nov 06:27"), (LD, "20 Nov 07:33", "20 Nov 07:33 (Live"), (LD, "20 Nov 07:29", "20 Nov 07:29 (Strategies")],
    "N.PORTFOLIO": [(PI, None, "project instructions v2.2.2"), ("pack.md OV-04", None, "pack.md OV-04"), ("design_d.json", None, "design_d.json Portfolio"), (LD, "20 Nov 07:13", "ledger 20 Nov 07:13")],
    "N.OFFERING": [("design_d.json", None, "design_d.json Offering->Context"), (LD, "19 Nov 23:05", "ledger 19 Nov 23:05"), ("Registry PART Offering/Platform", None, "registry PART N.OFFERING/PLATFORM"), ("Registry H.OFR", None, "registry H.OFR")],
    "N.SHAPE": [(LD, "19 Nov 23:05", "ledger 19 Nov 23:05"), (LD, "20 Nov 07:21", "20 Nov 07:21 (Shape is"), (LD, "20 Nov 06:49", "20 Nov 06:49 (kinematic"), (TB, None, "task brief (Shape governs")],
    "N.DOMAIN": [(LD, "19 Nov 23:15", "ledger 19 Nov 23:15"), (LD, "20 Nov ~11:00", "20 Nov ~11:00 (the seats"), (LD, "20 Nov 11:14", "20 Nov 11:14 (domain"), ("Registry class D", None, "registry class D (12 elements)")],
    "N.CANONICAL": [(LD, "19 Nov 23:15", "ledger 19 Nov 23:15"), (LD, "19 Nov 23:05", "19 Nov 23:05 (Rule covered"), ("Registry PART Canonical/Rule", None, "registry PART N.CANONICAL/RULE"), ("design_d.json", None, "design_d.json Canonical->*")],
    "N.PROGRAMME": [(PI, None, "Project instructions v2.2.2"), (LD, "19 Nov 23:15", "ledger 19 Nov 23:15"), (DD, None, "design_d Programme->Benefit")],
    "N.PROJECT": [(PI, None, "Project instructions v2.2.2"), (TB, None, "task brief ruled facts"), (DD, None, "design_d Project->Outcome"), ("Steward ruling", "21 Nov 08:54", "Steward ruling 21 Nov 08:54")],
    "N.SERVICE": [(PI, None, "Project instructions v2.2.2"), (DD, None, "design_d Service->Benefit"), (LD, "20 Nov 07:06", "ledger 20 Nov 07:06"), (LD, "10:51", "10:51 (KDA seats")],
    "N.WORKFLOW": [(LD, "19 Nov 23:15", "Ledger 19 Nov 23:15"), (LD, "20 Nov 07:35", "ledger 20 Nov 07:35"), ("Ledger Parts", None, "ledger Parts (Gate in Workflow)"), (DD, None, "design_d Workflow->Service"), ("Steward ruling", "21 Nov 08:54", "Steward ruling 21 Nov 08:54")],
    "N.OUTCOME": [(PI, None, "Project instructions v2.2.2"), (LD, "19 Nov 23:25", "ledger 19 Nov 23:25"), (LD, "20 Nov 07:13", "20 Nov 07:13 (polarity"), (LD, "20 Nov 06:10", "20 Nov 06:10 (Outcomes"), (DD, None, "design_d Project->Outcome"), ("Registry H.OUT", None, "registry H.OUT"), ("Steward ruling", "21 Nov 08:54", "Steward ruling 21 Nov 08:54")],
    "N.BENEFIT": [(PI, None, "Project instructions v2.2.2"), (LD, "20 Nov 07:13", "ledger 20 Nov 07:13"), (LD, "19 Nov 23:25", "ledger 19 Nov 23:25"), ("Registry H.BEN", None, "registry H.BEN")],
    "N.ASSET": [("Project core definition", None, "Project core definition"), (LD, "20 Nov 07:13", "ledger 20 Nov 07:13"), (LD, "19 Nov ~23:25", "19 Nov ~23:25 (two-sided"), (DD, None, "design_d Benefit->Asset")],
    "N.FRACTAL": [("Project instr. s3", None, "Project instructions s3"), (LD, "20 Nov 07:06", "ledger 20 Nov 07:06"), (LD, "07:10", "07:10 (Expressed"), (LD, "07:16", "07:16 (every element")],
    "N.MESH": [(LD, "20 Nov 06:27", "Ledger 20 Nov 06:27"), ("Design D", None, "Design D (Mesh covers"), (LD, "06:40", "06:40 (one Mesh design"), (LD, "06:49", "06:49 (own Service")],
}
ORDER = ["N.STRATEGY", "N.PORTFOLIO", "N.OFFERING", "N.SHAPE", "N.DOMAIN", "N.CANONICAL", "N.PROGRAMME", "N.PROJECT", "N.SERVICE", "N.WORKFLOW", "N.OUTCOME", "N.BENEFIT", "N.ASSET", "N.FRACTAL", "N.MESH"]
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
    assert e["cls"] == "N" and e.get("status") == "RULED" and e.get("definition") and e.get("definition_source"), noun
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
    if noun == "N.MESH":
        s["serves"] = ["Registry", "Elements", "Clusters", "Verbs"]
        s["serves_note"] = "One declaration shared by the Registry, Elements, Clusters and Verbs screens. Verbs stay empty: HOLD, not bound. No menu binding or route is made here."
    screens.append(s)

doc = {"schema": "synapsys.screen.declaration/1",
       "status": "SOURCE CANDIDATE, NON_AUTHORISING. RC06b batch 1: noun screens for the 15 RULED nouns. Not released to the registry (registry 0.3.5 is unchanged).",
       "slots": {"enable": ["header", "answer", "trust", "movement"], "enhance": ["made_of", "peers"], "enrich": ["trust_table", "open_questions", "technical"]},
       "screens": screens}
print(json.dumps(doc, indent=2, ensure_ascii=False))
if AMBIGUOUS or VERB_BINDING:
    print("made_of left null. ambiguous: %s; relationship binds verbs: %s" % (AMBIGUOUS, VERB_BINDING), file=sys.stderr)
