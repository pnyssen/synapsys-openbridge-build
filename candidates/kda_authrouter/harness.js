// Offline harness: runs an n8n Code-node body with shimmed $input / $() against fixtures. No network, no n8n, no writes.
const fs = require('fs');
function runNode(codePath, payload, lookup, nowIso) {
  const wired = /candidate/.test(codePath);   // candidate is wired Webhook -> Lookup -> Validate: $input is the LOOKUP output
  const code = fs.readFileSync(codePath, 'utf8');
  const input = { first: () => ({ json: wired ? (lookup || {}) : { body: payload } }) };
  const dollar = (name) => name === 'Authority Packet In' ? ({ first: () => ({ json: { body: payload } }) }) : ({ first: () => { if (lookup === null) throw new Error('no lookup output'); return { json: lookup }; }, all: () => (Array.isArray(lookup && lookup.__all) ? lookup.__all.map(j => ({ json: j })) : [{ json: lookup }]) });
  const RealDate = Date;
  class FixedDate extends RealDate { constructor(...a) { super(...(a.length ? a : [nowIso])); } static now() { return new RealDate(nowIso).getTime(); } }
  const fn = new Function('$input', '$', 'Date', code);
  return fn(input, dollar, FixedDate)[0].json;
}
module.exports = { runNode };
if (require.main === module) {
  const [codePath, payloadPath, lookupPath, now] = process.argv.slice(2);
  const out = runNode(codePath, JSON.parse(fs.readFileSync(payloadPath)), lookupPath === '-' ? null : JSON.parse(fs.readFileSync(lookupPath)), now || '2026-11-29T00:00:00Z');
  console.log(JSON.stringify(out));
}
