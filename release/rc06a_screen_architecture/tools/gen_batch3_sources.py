"""Builds addon/synapsys/data/screen_sources_batch3.json from the source table of BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D
(sha256 85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c). The rows are parsed from the contract text, never retyped.
usage: python3 gen_batch3_sources.py CONTRACT.md [OVERRIDES.json] > out.json    (build aid, not part of the addon)
RC06f: an optional overrides file changes the note of named rows only (the table text is never edited): {"rows": {"S12": {"status_note": "..."}}}.
The file records the contract that authorises it. The row's earlier status is kept in previous_status so nothing is lost."""
import hashlib, json, re, sys

raw = open(sys.argv[1], "rb").read()
assert hashlib.sha256(raw).hexdigest() == "85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c", "not the batch 3 contract"
lines = raw.decode("utf-8").split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("## Source table")) + 1
rows, prev_file = [], None
for l in lines[start:]:
    if l.startswith("## "):
        break
    m = re.match(r"^(S\d+) \| (.*?) \| (.*?) \| (.*?) \| (.*)$", l)
    if not m:
        continue
    rid, f, when, status, rest = m.groups()
    f = prev_file if f == "same" else f
    prev_file = f
    rows.append({"id": rid, "file": f, "when": when, "status": status, "field": rest})
assert [r["id"] for r in rows] == ["S%d" % i for i in range(1, 20)], [r["id"] for r in rows]


# Short names for the source chips (authored, one per source file string in the table; each row's chip is this name plus the row's "when").
SHORT = {
    "claude/rulings-ledger-addendum-2026-11-19-2240-architecture-nouns-verbs-separate.md": "Ledger addendum (nouns, verbs)",
    "claude/rulings-ledger-addendum-2026-11-19-1334-strategy-groups-live-build-adapt.md": "Ledger addendum (strategy groups)",
    "claude/navigator-screen-and-strategy-lens-v0.1-2026-11-20.md": "Navigator screen v0.1",
    "claude/navigator-screen-and-strategy-lens-v0.1-2026-11-20.md section 3 table": "Navigator screen v0.1 s3",
    "claude/kinematic-domain-overlays-live-build-adapt-v0.1-2026-11-20.md section 4": "Domain overlays v0.1 s4",
    "claude/library-sorting-framework-and-critical-questions-v0.1-2026-11-14.md s3": "Library sorting v0.1 s3",
    "claude/mesh-registry-door-87866af-2026-11-20.patch.txt (commit message)": "Door patch (commit message)",
    "claude/mesh-architecture-persisted-in-odoo-and-door-bound-v0.1-2026-11-20.md": "Mesh architecture v0.1",
    "claude/v20-architecture-menu-map-and-integration-routine-v0.1-2026-11-22.md section 3": "Menu map v0.1 s3",
    "claude/mesh-registry-door-87866af-2026-11-20.patch.txt (model description)": "Door patch (model)",
}


def quoted(field):
    """The first double-quoted string of the field, or None when the table field is not a quotation (S12, S13)."""
    m = re.match(r'^"(.*?)"(?:\s+\(.*\))?$', field)
    return m.group(1) if m else None


for r in rows:
    q = quoted(r["field"])
    r["quote"] = q if q is not None else r["field"]  # exact copy of the table field; for S12 and S13 the field is a description, not a quotation
    r["is_quotation"] = q is not None
    r["status_word"] = r["status"].split(" (")[0].split(" ")[0]
    r["status_note"] = r["status"][len(r["status_word"]):].strip().strip("()") or None
    r["source_name"] = SHORT[r["file"]]
by_id = {r["id"]: r for r in rows}
# Display text: what a screen may show. Only mechanical edits, each stated: S10 markdown asterisks stripped (the contract says so);
# S12 and S13 lose their last sentence, which is an instruction to the builder ("Show names only..." and "Show as OPEN...").
for r in rows:
    r["display"] = r["quote"]
by_id["S10"]["display"] = by_id["S10"]["quote"].replace("*", "")
by_id["S12"]["display"], by_id["S12"]["builder_instruction"] = by_id["S12"]["quote"].rsplit(" Show names only", 1)[0], "Show names only" + by_id["S12"]["quote"].rsplit(" Show names only", 1)[1]
by_id["S13"]["display"], by_id["S13"]["builder_instruction"] = by_id["S13"]["quote"].rsplit(" Show as OPEN", 1)[0], "Show as OPEN" + by_id["S13"]["quote"].rsplit(" Show as OPEN", 1)[1]
if len(sys.argv) > 2:
    ov = json.load(open(sys.argv[2], encoding="utf-8"))
    for rid, ch in ov["rows"].items():
        assert set(ch) == {"status_note"}, "only the note may be overridden"
        r = by_id[rid]
        r["previous_status"] = r["status"]
        r["status_note"] = ch["status_note"]
        r["status"] = "%s (%s)" % (r["status_word"], ch["status_note"])
doc = {"schema": "synapsys.screen.sources/1",
       "origin": "Source table of BUILD_CONTRACT_ENABLE_DOC_SOURCED_SCREENS_BATCH3_RC06D_20261127_v1.md (sha256 85d9e13712bafa656e542ac564d0f9b877d57373c3508325e29941cf621b4b9c), copied by the chat lane from the project documents named in each row. The builder could not read those documents; D009 or the Navigator should re-check the quotes against them.",
       "rows": rows}
print(json.dumps(doc, indent=2, ensure_ascii=False))
