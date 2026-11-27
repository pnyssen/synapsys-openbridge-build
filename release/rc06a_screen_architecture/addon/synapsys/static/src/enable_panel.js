import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Component, proxy, markup, onWillDestroy } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";

// Read-only page head for a bound menu's native view (RC06g panel; RC06h: lens template with the shared Depth tabs).
// It never replaces or edits the native view, action, menu or any record. It asks ONE read-only route about the window action now on screen
// (by action id) at the shared presentation depth (the same Depth control as the Context page) and shows what the route returns, or nothing:
// a refusal, an error or an action that is not bound leaves no panel and no tabs. It writes nothing and derives no id from a label.
const MODES = ["enable", "enhance", "enrich"];

export class SynapsysEnablePanel extends Component {
    static template = "synapsys.EnablePanel";
    setup() {
        this.state = proxy({ html: "", key: null });
        this.action = useService("action");
        this.lm = useService("synapsys_lens_mode");
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.refresh());
        const off = this.lm.subscribe(() => this.refresh());
        onWillDestroy(off);
        this.refresh();
    }
    get modes() {
        return MODES;
    }
    setMode(m) {
        this.lm.setMode(m);
    }
    currentActionId() {
        const ctrl = this.action && this.action.currentController;
        const act = ctrl && ctrl.action;
        return act && act.type === "ir.actions.act_window" && Number.isInteger(act.id) ? act.id : null;
    }
    async refresh() {
        const id = this.currentActionId();
        const mode = MODES.includes(this.lm.mode) ? this.lm.mode : "enable";
        const key = id === null ? null : id + "|" + mode;
        if (key === this.state.key) {
            return;
        }
        this.state.key = key;
        this.state.html = "";
        if (id === null) {
            return;
        }
        try {
            const res = await rpc("/synapsys/menu/enable", { action_id: id, depth: mode });
            if (this.state.key === key && res && res.result === "OK" && typeof res.html === "string") {
                this.state.html = markup(res.html);
            }
        } catch (e) {
            this.state.html = "";
        }
    }
}
registry.category("main_components").add("synapsys_enable_panel", { Component: SynapsysEnablePanel });
