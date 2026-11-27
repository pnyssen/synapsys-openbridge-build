// READ-ONLY DOM probe for Odoo 20 (paste into the browser Console on the dev page for Services, action 297, signed in as Steward).
// Writes nothing, calls no route, changes no style. It reports how the web client's containers are arranged, so the RC06h placement
// assumption (.o_web_client is a flex column and the panel or its container is a direct child) can be confirmed or refuted without installing RC06h.
// Works on RC06g (installed) because RC06g already mounts .syn-enable-panel as a main component.
(() => {
  const cs = (e) => { const c = getComputedStyle(e), r = e.getBoundingClientRect(); return {
    tag: e.tagName.toLowerCase(), id: e.id || null, cls: String(e.className).slice(0, 90), display: c.display, flexDir: c.flexDirection,
    position: c.position, order: c.order, overflowY: c.overflowY, top: Math.round(r.top), h: Math.round(r.height), w: Math.round(r.width) }; };
  const panel = document.querySelector('.syn-enable-panel');
  const out = { when: new Date().toISOString(), url: location.pathname + location.hash, vw: innerWidth, bodyClass: document.body.className.slice(0, 120),
    hasPanel: !!panel, panelChain: [], webClient: null, webClientChildren: [], actionManager: null, hasHas: CSS.supports('selector(:has(*))') };
  for (let e = panel; e && e !== document.documentElement; e = e.parentElement) out.panelChain.push(cs(e));
  const wc = document.querySelector('.o_web_client');
  if (wc) { out.webClient = cs(wc); out.webClientChildren = [...wc.children].map(cs); }
  const am = document.querySelector('.o_action_manager');
  if (am) { out.actionManager = cs(am); out.actionManagerParent = cs(am.parentElement); }
  out.verdict = !panel ? 'NO_PANEL (open a bound menu such as Services first)'
    : !wc ? 'NO_.o_web_client (placement assumption refuted: class not present)'
    : ([...wc.children].some((c) => c === panel || c.contains(panel)) && out.webClient.display === 'flex' && out.webClient.flexDir === 'column')
      ? 'ASSUMPTION_HOLDS (panel inside a direct child of a flex-column .o_web_client)'
      : 'ASSUMPTION_REFUTED_OR_PARTIAL (see panelChain and webClientChildren)';
  console.log(JSON.stringify(out, null, 1));
  return out.verdict;
})();
