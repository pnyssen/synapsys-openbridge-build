"""Screen declarations and the screen projection (RC06a, source-only candidate).

Pure functions: no Odoo, no writes, no sudo, no I/O except loading the declaration file by path.

A screen is DECLARED as data (data/screen_declarations.json) and PROJECTED here into one depth-limited model, which
screen_render.render_screen turns into HTML. No screen has its own slot code.

Rulings relied on (Steward, 27 Nov 2026, in chat; none is canon):
  1 stage sets the ceiling, you drill within it; stage is computed from the bound kind at render time and never stored
  2 two screen types: noun (full ladder, no stage) and record (ceiling from its kind)
  3 one question per depth   4 fixed frame   5 trust table   6 declared as data   7 frame first, verbs separately
  8 Stage and Depth are two separate labels.
Content is never invented: every claim reads from the registry element it is bound to, every source chip must quote text
the registry element actually holds (a chip whose quote is absent is dropped and noted), and a missing value says so.
"""
import hashlib
import json
import os

try:  # inside Odoo
    from . import scaffold_lens as sl
except ImportError:  # offline tests load modules by path
    import scaffold_lens as sl

DEPTHS = sl.DEPTHS  # ("enable", "enhance", "enrich")
NOT_BOUND = "not bound"
STAGE_BY_KIND = {"K-1": "enable", "K-3": "enable", "K-4": "enable", "K-6": "enhance", "K-8": "enhance", "K-12": "enrich"}
SCREEN_TYPES = ("noun", "record")
KNOWN_SLOTS = {
    "enable": ("header", "answer", "trust", "movement"),
    "enhance": ("made_of", "peers"),
    "enrich": ("trust_table", "open_questions", "technical"),
}
FRAME = KNOWN_SLOTS["enable"]
NOT_APPLICABLE = "Not applicable for this kind"
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "screen_declarations.json")
STEM_MAX = 60


# ---------------------------------------------------------------------------------------------------------- stage
def stage_for_kind(kind):
    """Pure. kind -> 'enable' | 'enhance' | 'enrich' | 'not bound'. Unknown or missing kind is NOT bound, never guessed."""
    k = kind.strip() if isinstance(kind, str) else None
    return STAGE_BY_KIND.get(k, NOT_BOUND)


def ceiling_for_stage(stage):
    """Deepest depth a record screen may show. An unbound stage is Enable depth only."""
    return stage if stage in DEPTHS else "enable"


def _ix(depth):
    return DEPTHS.index(depth)


def resolve_depth(screen_type, requested, stage=None, role_effective=None):
    """Returns (effective, clamped, reason). Noun screens never clamp for stage; role clamping still applies.

    role_effective is the depth the actor's role allows (already <= requested). A record screen then also applies the
    stage ceiling. depth_clamped is True whenever effective != requested, with the reason named."""
    if requested not in DEPTHS:
        raise ValueError("unknown depth %r" % (requested,))
    eff = role_effective if role_effective in DEPTHS else requested
    reason = "role" if eff != requested else None
    if screen_type == "record":
        ceil = ceiling_for_stage(stage)
        if _ix(ceil) < _ix(eff):
            eff, reason = ceil, "stage"
    return eff, eff != requested, reason


# ----------------------------------------------------------------------------------------------------- declaration
def declaration_sha(raw_bytes):
    return hashlib.sha256(raw_bytes).hexdigest()


def validate_screen(d):
    """Returns a list of error strings; empty means valid."""
    errs = []
    sid = d.get("id", "?")

    def bad(msg):
        errs.append("%s: %s" % (sid, msg))

    for k in ("id", "noun", "screen_type", "title", "answer", "trust_claim", "movement", "claims"):
        if k not in d:
            bad("missing %s" % k)
    if errs:
        return errs
    if d["screen_type"] not in SCREEN_TYPES:
        bad("screen_type must be noun or record")
    rec = d.get("record")
    if d["screen_type"] == "record":
        if not isinstance(rec, dict) or not rec.get("model") or not rec.get("name_field"):
            bad("a record screen must declare record.model and record.name_field")
        else:
            kd = rec.get("kind")
            if not isinstance(kd, dict) or (("field" in kd) == ("fixed" in kd)):
                bad("a record screen must declare record.kind as exactly one of field or fixed")
            elif "fixed" in kd and kd["fixed"] not in STAGE_BY_KIND:
                bad("record.kind.fixed %r is not a known kind" % (kd["fixed"],))
    elif rec is not None:
        bad("a noun screen has no record block and no stage")
    if d["answer"].get("from") != "element.definition":
        bad("answer.from must be element.definition (no invented text)")
    mv = d["movement"]
    if not isinstance(mv.get("verbs"), list):
        bad("movement.verbs must be a list (empty allowed)")
    else:
        for v in mv["verbs"]:
            if not (isinstance(v, dict) and v.get("verb") and v.get("source") and v.get("status") == "bound"):
                bad("a verb appears only where bound: verb, source and status 'bound' are required (no proposed or candidate verbs)")
    if not mv.get("verbs") and not mv.get("hold_reason"):
        bad("movement.hold_reason is required where no verb is bound")
    ids = []
    for c in d["claims"]:
        for k in ("id", "type", "noun", "label", "sources"):
            if k not in c:
                bad("claim missing %s" % k)
        ids.append(c.get("id"))
        if c.get("type") not in ("element", "peer"):
            bad("claim %s: type must be element or peer" % c.get("id"))
        for s in c.get("sources", []):
            if not (s.get("name") and s.get("quote")) or "date" not in s:
                bad("claim %s: a source needs name, date (null if the registry text holds none) and quote" % c.get("id"))
    if len(set(ids)) != len(ids):
        bad("duplicate claim ids")
    if d["trust_claim"] not in ids:
        bad("trust_claim %r is not a claim id" % (d["trust_claim"],))
    mo = d.get("made_of")
    if mo is not None and not (mo.get("relationship") and mo.get("heading") and isinstance(mo.get("role_names"), dict)):
        bad("made_of needs relationship, heading and role_names")
    pe = d.get("peers")
    if pe is not None:
        if not (pe.get("heading") and isinstance(pe.get("nouns"), list)) or len(pe["nouns"]) > 3:
            bad("peers needs heading and at most three nouns")
        else:
            peer_claims = {c["noun"] for c in d["claims"] if c.get("type") == "peer"}
            for n in pe["nouns"]:
                if n not in peer_claims:
                    bad("peer %s has no peer claim for the trust table" % n)
            for n in peer_claims - set(pe["nouns"]):
                bad("peer claim for %s is not in peers.nouns" % n)
    elif any(c.get("type") == "peer" for c in d["claims"]):
        bad("a peer claim needs a peers block")
    return errs


def load_declarations(path=None):
    """Returns ({id: screen}, meta). Raises ValueError listing every error; never returns a half-valid set."""
    p = path or DEFAULT_PATH
    with open(p, "rb") as fh:
        raw = fh.read()
    doc = json.loads(raw.decode("utf-8"))
    errs = []
    if doc.get("schema") != "synapsys.screen.declaration/1":
        errs.append("unknown schema %r" % (doc.get("schema"),))
    slots = doc.get("slots")
    if slots != {k: list(v) for k, v in KNOWN_SLOTS.items()}:
        errs.append("slots per depth must be exactly %s" % json.dumps(KNOWN_SLOTS))
    out = {}
    for s in doc.get("screens", []):
        errs.extend(validate_screen(s))
        out[s.get("id")] = s
    if errs:
        raise ValueError("; ".join(errs))
    return out, {"sha256": declaration_sha(raw), "slots": slots}


# --------------------------------------------------------------------------------------------------- projection
def stem_of(text):
    """One-line stem of an open question: up to the first ( : or ? and at most STEM_MAX chars. Returns (stem, truncated)."""
    t = " ".join(str(text).split())
    cut = len(t)
    for ch in ("(", ":", "?"):
        i = t.find(ch)
        if 0 < i < cut:
            cut = i
    s = t[:min(cut, STEM_MAX)].rstrip(" ,;")
    return s, len(s) < len(t)


def _chips(claim, element, notes):
    """Source chips for a claim. A chip whose quote is absent from the registry text is dropped and noted, never shown."""
    src = (element or {}).get("definition_source") or ""
    out = []
    for s in claim.get("sources", []):
        if s["quote"] in src:
            out.append({"name": s["name"], "date": s.get("date")})
        else:
            notes.append("%s: source chip %r not found in the registry text" % (claim["id"], s["name"]))
    return out


def _kind_of(decl, record):
    """Returns (kind_or_None, reason_or_None, neighbour_kind) for a record screen."""
    kd = decl["record"]["kind"]
    nb = (record or {}).get("neighbour_kind") or None
    if "fixed" in kd:
        return kd["fixed"], None, nb
    k = (record or {}).get("kind")
    if not k:
        return None, "this record has no resolved kind", nb
    if k not in STAGE_BY_KIND:
        return None, "kind %s is not one of K-1, K-3, K-4, K-6, K-8, K-12" % k, nb
    return k, None, nb


def _slots_for(depth):
    out = []
    for d in DEPTHS[:_ix(depth) + 1]:
        out.extend(KNOWN_SLOTS[d])
    return out


def project(decl, reg, requested_depth, actor, evidence, library_index, context_id="", role_max_depth=None, record=None):
    """Declaration + registry + actor -> depth-limited screen model (a dict). No I/O, no writes.

    Only content the actor is entitled to, at the effective depth, is put in the model (the same model is the JSON route
    output, so there is no hidden page data). Evidence passes the existing fail-closed filters in scaffold_lens."""
    if requested_depth not in DEPTHS:
        return {"result": "REFUSED", "reason": "UNKNOWN_DEPTH"}
    els = sl.index_registry(reg)
    noun = decl["noun"]
    if noun not in els:
        return {"result": "REFUSED", "reason": "UNKNOWN_NOUN"}
    role_eff = sl._effective_depth(actor or {}, requested_depth, role_max_depth)
    if role_eff is None:
        return {"result": "REFUSED", "reason": "NO_RECOGNISED_ROLE"}
    stype = decl["screen_type"]
    stage = stage_reason = neighbour = None
    kind = None
    if stype == "record":
        kind, stage_reason, neighbour = _kind_of(decl, record)
        stage = stage_for_kind(kind)
        if stage == NOT_BOUND and not stage_reason:
            stage_reason = "kind not bound"
    eff, clamped, clamp_reason = resolve_depth(stype, requested_depth, stage, role_eff)
    el = els[noun]
    notes = []
    claims = {c["id"]: c for c in decl["claims"]}
    chips = {cid: _chips(c, els.get(c["noun"]), notes) for cid, c in claims.items()}
    tc = claims[decl["trust_claim"]]
    mv = decl["movement"]
    out = {
        "result": "OK", "screen": decl["id"], "screen_type": stype, "noun": noun, "title": decl["title"],
        "label": el["label"], "status": el.get("status"), "definition": el.get("definition"),
        "registry_version": reg.get("version"),
        "stage": stage, "stage_reason": stage_reason, "stage_computed_not_stored": True,
        "depth_requested": requested_depth, "depth_effective": eff, "depth_clamped": clamped, "clamp_reason": clamp_reason,
        "context_id": context_id, "writes": 0,
        "slots": _slots_for(eff),
        "frame": {
            "header": {"noun": el["label"], "status": el.get("status"), "record_name": (record or {}).get("name") if stype == "record" else None,
                       "neighbour_kind": neighbour},
            "answer": el.get("definition"),
            "trust": {"status": el.get("status"), "source_count": len(chips[tc["id"]])},
            "movement": ({"state": "BOUND", "verbs": [v["verb"] for v in mv["verbs"]]} if mv["verbs"]
                         else {"state": "HOLD", "text": "verbs not yet bound", "reason": mv["hold_reason"], "verbs": []}),
        },
        "notes": notes,
    }
    if eff != requested_depth and clamp_reason == "stage":
        out["not_applicable"] = {"requested": requested_depth, "text": NOT_APPLICABLE if stage != NOT_BOUND else "Stage not bound: Enable depth only",
                                 "reason": stage_reason if stage == NOT_BOUND else "stage %s sets the ceiling" % stage}
    peers = []
    if _ix(eff) >= 1:
        mo = decl.get("made_of")
        roles = sl.roles_for(reg, els, mo["relationship"]) if mo else []
        enh = {"made_of": {"heading": mo["heading"], "relationship": mo["relationship"], "rows": [
            {"role_id": r["role_id"], "name": mo["role_names"].get(r["role_id"]) or _fallback_role(r), "required": r["required"],
             "many": r["many"], "bound_label": r["bound_label"], "bound_status": r["bound_status"], "cluster_id": r["cluster_id"]}
            for r in roles]} if mo else None}
        pd = decl.get("peers")
        if pd:
            for pn in pd["nouns"]:
                peers.append(sl._peer_block(els, pn, eff, actor, evidence, library_index, context_id))
            enh["peers"] = {"heading": pd["heading"], "rows": [
                {"id": p["id"], "label": p["label"], "status": p["status"], "operating_source": p.get("operating_source"),
                 "definition": p.get("definition")} for p in peers]}
        else:
            enh["peers"] = None
        out["enhance"] = enh
    if _ix(eff) >= 2:
        rows = []
        for c in decl["claims"]:
            e = els.get(c["noun"]) or {}
            row = {"id": c["id"], "label": c["label"], "chips": chips[c["id"]], "source_count": len(chips[c["id"]]),
                   "full_citation": e.get("definition_source"), "evidence": [], "rejected": []}
            oqs = list(e.get("open_questions") or [])
            if c["type"] == "element":
                row["status"] = e.get("status")
                row["qualifier"] = None
                if c.get("qualifier_from") == "element.kind":
                    k = e.get("kind")
                    row["qualifier"] = {"first": ("Kind: " + str(k).split(";")[0]) if k else None, "full": k}
            else:
                p = [x for x in peers if x["id"] == c["noun"]][0]
                row["registry_status"] = p.get("status")
                sourced = p.get("operating_source") == "SOURCED"
                row["status"] = "CATALOGUE RECORD FOUND" if sourced else "HOLD"
                quals = []
                for ev in p.get("evidence") or []:
                    quals.extend((ev.get("detail") or {}).get("qualifiers") or [])
                    row["evidence"].append({"label": ev.get("label"), "source_ref": ev.get("source_ref"), "sha256": ev.get("sha256")})
                    row["chips"] = [{"name": str(ev.get("label") or ev.get("source_ref")).split(" ")[0], "date": None, "evidence": True}] + row["chips"]
                    row["source_count"] += 1
                row["rejected"] = sorted(set(r.get("reason", "") for r in p.get("rejected_evidence") or []))
                row["qualifier"] = ({"first": quals[0], "full": quals} if quals else
                                    {"first": "No operating source: HOLD", "full": None} if not sourced else None)
            row["open"] = []
            for q in oqs:
                s, trunc = stem_of(q)
                row["open"].append({"text": q, "stem": s, "truncated": trunc})
            rows.append(row)
        out["enrich"] = {
            "rows": rows,
            "open_total": sum(len(r["open"]) for r in rows),
            "technical": {
                "registry_version": reg.get("version"), "relationship": (decl.get("made_of") or {}).get("relationship"),
                "cluster_id": (out["enhance"]["made_of"]["rows"][0]["cluster_id"] if out["enhance"]["made_of"] and out["enhance"]["made_of"]["rows"] else None),
                "evidence_sources": [{"source_ref": e["source_ref"], "sha256": e["sha256"]} for r in rows for e in r["evidence"]],
                "screen_id": decl["id"], "kind": kind,
            },
        }
    return out


def _fallback_role(r):
    t = str(r.get("role_label") or r.get("role_id") or "").replace("_", " ").replace("+", "").strip()
    return (t[:1].upper() + t[1:]) if t else "Role"
