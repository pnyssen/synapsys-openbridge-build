import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Component, onWillStart, proxy, markup } from "@odoo/owl";
import { initialState, nextState, controlFrom } from "./master_nav";

// OWL replaces the rendered content asynchronously after state.html changes, so focusing straight away would focus the node that is about to be thrown away.
// Wait for the first DOM patch under the component root (with a short fallback when nothing changes), then focus the new content region.
function focusContentWhenPatched(root) {
    return new Promise((resolve) => {
        let timer = null;
        const done = () => {
            observer.disconnect();
            clearTimeout(timer);
            const main = root && root.querySelector("#sm-main");
            if (main) {
                main.focus({ preventScroll: true });
            }
            resolve();
        };
        const observer = new MutationObserver(done);
        observer.observe(root, { childList: true, subtree: true });
        timer = setTimeout(done, 750);
    });
}

// Master Architecture client action (UNRELEASED candidate; not in the manifest assets, no menu points at it).
// Server-rendered, escaped HTML only. This component holds navigation state and nothing else: no record is read or written here,
// and no right is decided here (the server applies the real account's rights on every request).
export class SynapsysMasterArchitecture extends Component {
    static template = "synapsys.MasterArchitecture";
    setup() {
        this.state = proxy({ html: "", error: "", nav: initialState() });
        onWillStart(async () => {
            await this.load();
        });
    }
    async load() {
        const n = this.state.nav;
        const r = await rpc("/synapsys/architecture/master/page", {
            section: n.section, perspective: n.perspective, depth: n.depth, actor: n.actor, drill: n.drill, ov: n.ov,
        });
        if (r && r.html) {
            this.state.error = "";
            this.state.html = markup(r.html);
        } else {
            this.state.error = (r && (r.error || r.state)) || "NOT_LOADED";
        }
    }
    async onClick(ev) {
        const next = nextState(this.state.nav, controlFrom(ev.target));
        if (!next) {
            return;
        }
        ev.preventDefault();
        const root = ev.currentTarget;      // captured before any await: currentTarget is cleared once dispatch ends. OWL components have no `this.el`.
        this.state.nav = next;
        await this.load();
        await focusContentWhenPatched(root);
    }
}
registry.category("actions").add("synapsys_master_architecture", SynapsysMasterArchitecture);
