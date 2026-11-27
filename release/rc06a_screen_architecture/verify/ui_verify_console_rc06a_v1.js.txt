// SynapSys RC06a UI verification (re-expression of the RC05e 31 checks, plus new checks for the screen architecture). READ-ONLY. Paste into the DevTools Console of the logged-in dev Odoo tab (as the Steward).
// It only POSTs to the two read-only /synapsys routes and prints ONE line of JSON (no cookies, tokens or passwords).
(async () => {
  const post = async (url, params) => {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params }) });
    const j = await r.json(); return j.error ? { error: j.error.message } : { result: j.result };
  };
  const text = (h) => String(h).replace(/<style>.*?<\/style>/gs, "").replace(/<[^>]+>/g, " ").replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ");
  const crumb = (h) => { const m = /<div class="cr">(.*?)<\/div>/s.exec(h); return m ? text(m[1]).trim() : null; };
  const count = (h, s) => String(h).split(s).length - 1;
  const checks = [];
  const add = (id, pass, detail) => checks.push({ id, pass: !!pass, detail: detail === undefined ? "" : String(detail).slice(0, 160) });
  const NOTE = "Depth applies when you open a lens or element.";
  try {
    const l1 = await post("/synapsys/lenses/data", { level: 1, group: "", sec: "", mode: "enable", ov: "" });
    const l2 = await post("/synapsys/lenses/data", { level: 2, group: "pattern", sec: "", mode: "enable", ov: "" });
    const l3 = await post("/synapsys/lenses/data", { level: 3, group: "pattern", sec: "e0", mode: "enhance", ov: "" });
    for (const [k, v] of [["L1", l1], ["L2", l2], ["L3", l3]]) add(k + "_loads", v.result, v.error);
    if (l1.result) {
      add("D16_level1_position_only", /^Level 1 of 3/.test(crumb(l1.result) || "") && !/Enable|Enhance|Enrich/.test(crumb(l1.result)), crumb(l1.result));
      add("D16_level1_note_once", count(l1.result, NOTE) === 1, count(l1.result, NOTE));
      add("scaffold_card_once_for_steward", count(l1.result, 'data-scaffold="1"') === 1, count(l1.result, 'data-scaffold="1"'));
      add("D13_card_inside_lens_wrapper", /<\/div><\/div>\s*$/.test(l1.result), "");
    }
    if (l2.result) {
      add("D16_level2_position_only", /^Level 2 of 3/.test(crumb(l2.result) || "") && !/Enable|Enhance|Enrich/.test(crumb(l2.result)), crumb(l2.result));
      add("D16_level2_note_once", count(l2.result, NOTE) === 1, count(l2.result, NOTE));
    }
    if (l3.result) {
      add("D16_level3_position_only", /^Level 3 of 3/.test(crumb(l3.result) || "") && !/Enable|Enhance|Enrich/.test(crumb(l3.result)), crumb(l3.result));
      add("D16_level3_no_list_note", count(l3.result, NOTE) === 0, count(l3.result, NOTE));
    }
    const en = await post("/synapsys/scaffold/view", { depth: "enable" });
    const eh = await post("/synapsys/scaffold/view", { depth: "enhance" });
    const er = await post("/synapsys/scaffold/view", { depth: "enrich" });
    for (const [k, v] of [["enable", en], ["enhance", eh], ["enrich", er]]) add("scaffold_" + k + "_loads", v.result, v.error);
    const slots = (h) => (String(h).match(/data-slot="(\w+)"/g) || []).map((x) => x.slice(11, -1));
    const slotHtml = (h, name) => { const m = new RegExp('<(?:div|p|details)[^>]*data-slot="' + name + '".*?(?=<(?:div|p|details)[^>]*data-slot="|<div class="cd" data-slot="not_applicable"|<p class="nt">)', "s").exec(h); return m ? m[0] : ""; };
    if (en.result) add("enable_headline_only", /Context/.test(text(en.result)) && !/What a Context is made of|Linked peers/.test(text(en.result)) && JSON.stringify(slots(en.result)) === '["header","answer","trust","movement"]', JSON.stringify(slots(en.result)));
    if (eh.result) {
      const t = text(eh.result), a = t.indexOf("What a Context is made of"), b = t.indexOf("Linked peers"), roles = a >= 0 && b > a ? t.slice(a, b) : "";
      add("enhance_roles_section_present", a >= 0 && b > a, "");
      add("enhance_plain_role_names", ["Rights holder", "Intersecting chains", "Portfolios", "Strategies", "The Context itself", "one or more"].every((s) => roles.includes(s)), "");
      add("enhance_no_registry_codes_in_roles", !/rights_holder|intersects\+|portfolio\+|strategy\+|H\.CTX|MC-|\bmany\b/.test(roles), "");
      const peers = text(slotHtml(eh.result, "peers"));
      add("enhance_service_record_found", /Service[^]*CATALOGUE RECORD FOUND/.test(peers), "");
      add("enhance_capability_hold", /Capability[^]*?NO OPERATING SOURCE: HOLD/.test(peers), "");
      add("enhance_no_technical_details", !/Technical details/.test(t), "");
    }
    if (er.result) {
      const raw = er.result, t = text(raw), main = t.slice(0, t.indexOf("Technical details") > 0 ? t.indexOf("Technical details") : t.length);
      const svc = text((/<tr data-claim="peer\.service">.*?<\/tr>/s.exec(raw) || [""])[0]);
      add("enrich_four_qualifiers", ["existence is not operation", "validation: none recorded", "no source document recorded", "not bound to a Context"].every((s) => svc.includes(s)), svc.slice(0, 80));
      add("enrich_evidence_names_SP01", /Evidence: SP-01 Strategic Planning & Context Establishment/.test(svc), "");
      add("enrich_hash_not_in_ordinary_copy", !/\([0-9a-f]{12}\)/.test(main), "");
      add("enrich_technical_details_present", /<details class="td"[^>]*><summary>Technical details<\/summary>/.test(raw), "");
      add("enrich_technical_details_content", /fingerprint 608938cd399e/.test(t) && /relationship H\.CTX, cluster MC-390147223f2d/.test(t), "");
      add("enrich_presentation_only_statement", /Presentation only: this view changes no data, kind, PPV, approval or right\./.test(t), "");
      add("no_script_or_handler_in_view", !/<script|\son[a-z]+=|javascript:/i.test(raw), "");
    }
    // NEW in RC06a (not mappings of an old check)
    const hs = { enable: en.result, enhance: eh.result, enrich: er.result };
    if (hs.enable && hs.enhance && hs.enrich) {
      const frameOk = Object.values(hs).every((h) => JSON.stringify(slots(h).filter((x) => ["header", "answer", "trust", "movement"].includes(x))) === '["header","answer","trust","movement"]');
      add("NEW_frame_order_same_at_all_depths", frameOk, "");
      const same = ["answer", "trust", "movement"].every((n) => slotHtml(hs.enable, n) === slotHtml(hs.enhance, n) && slotHtml(hs.enhance, n) === slotHtml(hs.enrich, n));
      add("NEW_frame_not_reworded_by_depth", same, "");
      add("NEW_stage_and_depth_are_two_labels", [["enable", "Enable"], ["enhance", "Enhance"], ["enrich", "Enrich"]].every(([k, v]) => (hs[k].match(/data-label="stage">([^<]*)</) || [])[1] === "Stage: none (a noun screen has no stage)" && (hs[k].match(/data-label="depth">([^<]*)</) || [])[1] === "Depth: " + v), "");
      add("NEW_one_trust_line_and_one_movement", Object.values(hs).every((h) => count(h, 'data-slot="trust"') === 1 && count(h, 'data-slot="movement"') === 1 && /HOLD[^]*verbs not yet bound/.test(text(slotHtml(h, "movement")))), "");
      const th = [...String(hs.enrich).matchAll(/<th>(.*?)<\/th>/g)].map((m) => m[1]);
      add("NEW_trust_table_has_four_columns", JSON.stringify(th) === '["Claim","Status","Source","Open question"]' && [...String(hs.enrich).matchAll(/<tr data-claim=.*?<\/tr>/gs)].every((m) => count(m[0], "<td>") === 4), JSON.stringify(th));
      const oq = text(slotHtml(hs.enrich, "open_questions"));
      add("NEW_open_questions_rolled_up_once", /Which domain is Context's home/.test(text(hs.enrich)) && count(text(hs.enrich), "Which domain is Context's home (D001") === 1 && /\(1 open\)/.test(oq), "");
    }
    const bad = await post("/synapsys/scaffold/context", { depth: "deep", context_id: "1" });
    add("bad_depth_refused", bad.result && bad.result.result === "REFUSED" && bad.result.reason === "UNKNOWN_DEPTH", JSON.stringify(bad.result || bad.error));
    const ctx = await post("/synapsys/scaffold/context", { depth: "enrich", context_id: "1" });
    add("route_read_only_writes_zero", ctx.result && ctx.result.writes === 0, ctx.result && ctx.result.writes);
    add("registry_fingerprint_is_pinned_0.3.5", ctx.result && ctx.result.registry_version === "0.3.5" && ctx.result.registry_sha === "7c31aa1de4c97e8e062c5ae9e2f907b4c67ea0949bf143235499c32b1a30f423", ctx.result && ctx.result.registry_sha);
    add("NEW_route_reports_the_declaration_fingerprint", ctx.result && /^[0-9a-f]{64}$/.test(ctx.result.declaration_sha || "") && ctx.result.screen === "SCR.CONTEXT.NOUN" && ctx.result.screen_type === "noun" && ctx.result.stage === null, ctx.result && ctx.result.screen);
  } catch (e) { add("script_error", false, e && e.message); }
  const failed = checks.filter((c) => !c.pass);
  console.log(JSON.stringify({ script: "ui_verify_console_rc06a_v1", checks: checks.length, passed: checks.length - failed.length, failed: failed.map((c) => c.id + (c.detail ? ": " + c.detail : "")), all: checks.map((c) => (c.pass ? "PASS " : "FAIL ") + c.id) }));
})();
