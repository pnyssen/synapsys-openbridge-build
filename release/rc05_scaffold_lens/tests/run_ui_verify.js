// Runs verify/ui_verify_console.js under node with a fake fetch fed from fixtures. usage: node run_ui_verify.js fixtures.json script.js
const fs = require("fs"); const fx = JSON.parse(fs.readFileSync(process.argv[2], "utf8")); const src = fs.readFileSync(process.argv[3], "utf8");
const serve = (url, p) => {
  if (url === "/synapsys/lenses/data") return { result: fx["lens" + p.level] };
  if (url === "/synapsys/scaffold/view") return { result: fx["view_" + p.depth] };
  if (url === "/synapsys/scaffold/context") return { result: p.depth === "deep" ? fx.ctx_bad : fx.ctx_ok };
  return { error: { message: "no route " + url } };
};
global.fetch = async (url, o) => ({ json: async () => { const r = serve(url, JSON.parse(o.body).params); return { jsonrpc: "2.0", id: null, ...r }; } });
const logs = []; const origLog = console.log; console.log = (s) => logs.push(s);
new Function(src)(); setTimeout(() => { console.log = origLog; console.log(logs[logs.length - 1]); }, 300);
