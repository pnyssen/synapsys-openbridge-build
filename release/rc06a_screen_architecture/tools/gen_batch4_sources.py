"""Builds addon/synapsys/data/screen_sources_batch4.json from the source table of BUILD_CONTRACT_ENABLE_ACTION_SCREENS_BATCH4_RC06E
(sha256 743e92bb0eb588a3a28b4fddf6f0d52211e7485e6dcbbc10e7c4c5a7e481b9d6). Rows are parsed from the contract text, never retyped.
Table columns: id | file | when | status | note | quote. "same file s1" means the file string of row A1; "same" in the note column means A1's note.
usage: python3 gen_batch4_sources.py CONTRACT.md > out.json    (build aid, not part of the addon)"""
import hashlib, json, re, sys

raw = open(sys.argv[1], "rb").read()
assert hashlib.sha256(raw).hexdigest() == "743e92bb0eb588a3a28b4fddf6f0d52211e7485e6dcbbc10e7c4c5a7e481b9d6", "not the batch 4 contract"
lines = raw.decode("utf-8").split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("| id | file |")) + 2
rows = []
for l in lines[start:]:
    if not l.startswith("| "):
        break
    cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
    assert len(cells) == 6, l
    rows.append(dict(zip(("id", "file", "when", "status_word", "note", "quote"), cells)))
assert [r["id"] for r in rows] == ["A%d" % i for i in range(1, 10)] + ["P1", "P2", "P3", "C1", "C2", "C3"], [r["id"] for r in rows]
a1 = rows[0]
SHORT = {a1["file"]: "Mesh fit-to-shapes test v0.3 s1"}
for r in rows:
    if r["file"] == "same file s1":
        r["file"] = a1["file"]
    if r["note"] == "same":
        r["note"] = a1["note"]
    r["note"] = r["note"] or None
c2 = next(r for r in rows if r["id"] == "C2")
SHORT[c2["file"]] = "Toolkit verbs rules v0.1 s1"
for r in rows:
    r["source_name"] = SHORT[r["file"]]
    r["status"] = "%s (%s)" % (r["status_word"], r["note"]) if r["note"] else r["status_word"]
    r["status_note"] = r["note"]
    del r["note"]
    r["display"] = r["quote"]  # the table's quote is shown verbatim: no mechanical edit is needed for any row
    r["is_quotation"] = True
doc = {"schema": "synapsys.screen.sources/1",
       "origin": "Source table of BUILD_CONTRACT_ENABLE_ACTION_SCREENS_BATCH4_RC06E_20261127_v1.md (sha256 743e92bb0eb588a3a28b4fddf6f0d52211e7485e6dcbbc10e7c4c5a7e481b9d6), read from the project documents by the chat lane on 27 Nov. The builder could not read those documents; D009 or the Navigator should re-check the quotes against them.",
       "rows": rows}
print(json.dumps(doc, indent=2, ensure_ascii=False))
