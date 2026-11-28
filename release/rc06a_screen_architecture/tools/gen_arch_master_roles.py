"""Generate data/arch_master_roles.json: the EXISTING role definitions, read from the installed security source (no group is created or changed).
Inputs: addon/synapsys/security/synapsys_security.xml (groups, implied groups) and security/ir.access.csv (per-model operations and row rules).
Deterministic. Run: python3 tools/gen_arch_master_roles.py [--check]"""
import csv, hashlib, json, os, sys
import xml.etree.ElementTree as ET
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SEC = os.path.join(ROOT, "addon", "synapsys", "security")
OUT = os.path.join(ROOT, "addon", "synapsys", "data", "arch_master_roles.json")

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def build():
    xml_p, csv_p = os.path.join(SEC, "synapsys_security.xml"), os.path.join(SEC, "ir.access.csv")
    groups = {}
    for rec in ET.parse(xml_p).getroot().iter("record"):
        if rec.get("model") != "res.groups":
            continue
        f = {x.get("name"): x for x in rec.findall("field")}
        implied = [e.split("ref('")[1].split("')")[0] for e in [(f["implied_ids"].get("eval") or "")] if "ref('" in e] if "implied_ids" in f else []
        groups["synapsys." + rec.get("id")] = {"display_name": f["name"].text, "comment": (f.get("comment").text if f.get("comment") is not None else None),
                                                "implies": [i if "." in i else "synapsys." + i for i in implied]}
    access = {}
    for row in csv.DictReader(open(csv_p, encoding="utf-8")):
        model, grp, op, dom = row["model_id"], row["group_id/id"], row["operation"], (row.get("domain") or "").strip()
        access.setdefault(model, {})[grp] = {"operations": op, "row_scoped": bool(dom), "row_rule": dom[:240] if dom else None}
    return {"schema": "synapsys.arch.master.roles.v1", "authority": "read from installed security source; creates and changes nothing",
            "source_pins": {"security_xml_sha256": sha(xml_p), "ir_access_csv_sha256": sha(csv_p)},
            "groups": dict(sorted(groups.items())), "client_group": None,
            "client_note": "no Client group, privilege or access row exists in the installed security source",
            "access": {m: dict(sorted(a.items())) for m, a in sorted(access.items())}}

def render(d): return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

if __name__ == "__main__":
    text = render(build())
    if "--check" in sys.argv:
        sys.exit(0 if os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text else 1)
    open(OUT, "w", encoding="utf-8").write(text); print(OUT, len(text.encode()), hashlib.sha256(text.encode()).hexdigest())
