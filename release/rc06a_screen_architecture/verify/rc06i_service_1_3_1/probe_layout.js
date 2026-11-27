// Real-browser layout probe (Playwright, Chromium) over the MOCK SHELL pages. usage: node probe_layout.js DIR OUT.json [shotsdir]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const dir = process.argv[2], outFile = process.argv[3], shots = process.argv[4];
const VIEWPORTS = [[390, 844], [1024, 854]];
function measure() {
  const top = (e) => e ? e.getBoundingClientRect().top + window.scrollY : null;
  const bot = (e) => e ? e.getBoundingClientRect().bottom + window.scrollY : null;
  const q = (s) => document.querySelector(s), qa = (s) => [...document.querySelectorAll(s)];
  const panel = q('.syn-enable-panel'), page = q('.syn-sc');
  const scope = panel || document.body;
  const rec = q('[data-slot=records]'), nat = q('[data-native-view]'), am = q('.o_action_manager');
  const own = (e) => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const controls = qa('[data-control=detail], .syn-modebar');
  const ctl = controls[0];
  const btns = ctl ? [...ctl.querySelectorAll('button')] : [];
  const scrollCont = scope === document.body ? [] : [scope, ...scope.querySelectorAll('*')].filter(e => { const o = getComputedStyle(e).overflowY; return o === 'auto' || o === 'scroll' || (o === 'hidden' && e.scrollHeight > e.clientHeight + 1 && !e.closest('svg')); });
  const cells = scope === document.body ? [] : [...scope.querySelectorAll('.tt td, .tt th')];
  const trunc = [...scope.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); return (cs.textOverflow === 'ellipsis') || (e.children.length === 0 && e.textContent.trim() && cs.overflowX !== 'visible' && e.scrollWidth > e.clientWidth + 1); }).map(e => e.textContent.trim().slice(0, 40));
  const sourceCells = [...scope.querySelectorAll('.tt tbody tr')].map(r => r.children[2]).filter(Boolean);
  const sourceVisible = sourceCells.filter(c => { const r = c.getBoundingClientRect(); const cs = getComputedStyle(c); return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0 && r.right <= window.innerWidth + 1; }).length;
  const tgt = [...scope.querySelectorAll('button, summary, a[href], input, select')].map(e => { const r = e.getBoundingClientRect(); return { t: e.textContent.trim().slice(0, 20), w: Math.round(r.width), h: Math.round(r.height) }; });
  const sv = q('.syn-sv'); const fonts = {};
  if (sv) [sv, ...sv.querySelectorAll('*')].filter(own).forEach(e => { const f = getComputedStyle(e).fontSize; fonts[f] = (fonts[f] || 0) + 1; });
  const reach = Math.max(0, ...[...scope.querySelectorAll('*')].map(bot)) - document.scrollingElement.scrollHeight;
  return {
    docScrollW: document.documentElement.scrollWidth, vw: innerWidth, vh: innerHeight, docH: document.scrollingElement.scrollHeight,
    tops: { header: top(q('[data-slot=header]')), answer: top(q('[data-slot=answer]')), apertures: top(q('[data-band=apertures]')), value: top(q('[data-band=value]')), records: top(rec), native: top(nat) },
    recordsBottom: bot(rec), panelBottom: panel ? bot(panel) : null, panelHeight: panel ? panel.getBoundingClientRect().height : null,
    nativeTop: top(nat), nativeHeight: am ? am.getBoundingClientRect().height : null, gapRecordsToNative: rec && nat ? top(nat) - bot(rec) : null,
    controlCount: controls.length, controlInAnswerBand: !!(ctl && ctl.closest('[data-band=answer]')),
    controlGroupLabelled: !!(ctl && ctl.getAttribute('role') === 'group' && ctl.getAttribute('aria-label')),
    controlAllPressedAttr: btns.length === 3 && btns.every(b => b.hasAttribute('aria-pressed')),
    pressed: btns.filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim().toLowerCase()),
    targets: tgt, smallTargets: tgt.filter(t => t.h < 44 || t.w < 44),
    scrollContainers: scrollCont.length, truncated: trunc, ellipsisCells: trunc.length,
    cells: cells.length, sourceRows: sourceCells.length, sourceVisible,
    apertures: qa('[data-aperture]').map(e => e.dataset.aperture), valueBand: !!q('[data-band=value]'), fonts,
    unreachablePx: Math.round(reach),
  };
}
(async () => {
  const b = await chromium.launch(); const res = [];
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.html')).sort()) {
    for (const [w, h] of VIEWPORTS) {
      const pg = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
      await pg.goto('file://' + path.resolve(dir, f));
      const m = await pg.evaluate(measure);
      // keyboard: Tab until focus lands inside the depth control (max 40), then read the focus indicator
      let kb = { reached: false, outline: null };
      if (m.controlCount) {
        for (let i = 0; i < 40 && !kb.reached; i++) {
          await pg.keyboard.press('Tab');
          kb = await pg.evaluate(() => { const a = document.activeElement; const ok = !!(a && a.closest && a.closest('[data-control=detail], .syn-modebar')); const cs = ok ? getComputedStyle(a) : null; return { reached: ok, outline: ok ? { style: cs.outlineStyle, width: cs.outlineWidth } : null }; });
        }
      }
      m.keyboard = kb;
      res.push({ file: f.replace('.html', ''), w, h, m });
      if (shots && /^(service|measures)_(enable|enrich)/.test(f)) await pg.screenshot({ path: path.join(shots, f.replace('.html', '') + '_' + w + '.png'), fullPage: true });
      await pg.close();
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(res, null, 1)); await b.close();
})();
