import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Component, proxy, markup } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";

// Read-only Enable panel for a bound menu's native view (RC06g). It never replaces or edits the native view, action, menu or any record.
// It asks ONE read-only route about the window action now on screen (by action id) and shows what the route returns, or nothing at all:
// a refusal, an error or an action that is not bound leaves no panel and no trace. It writes nothing and derives no id from a label.
export class SynapsysEnablePanel extends Component {
    static template = "synapsys.EnablePanel";
    setup() {
        this.state = proxy({ html: "", actionId: null });
        this.action = useService("action");
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.refresh());
        this.refresh();
    }
    currentActionId() {
        const ctrl = this.action && this.action.currentController;
        const act = ctrl && ctrl.action;
        return act && act.type === "ir.actions.act_window" && Number.isInteger(act.id) ? act.id : null;
    }
    async refresh() {
        const id = this.currentActionId();
        if (id === this.state.actionId) {
            return;
        }
        this.state.actionId = id;
        this.state.html = "";
        if (id === null) {
            return;
        }
        try {
            const res = await rpc("/synapsys/menu/enable", { action_id: id });
            if (this.state.actionId === id && res && res.result === "OK" && typeof res.html === "string") {
                this.state.html = markup(res.html);
            }
        } catch (e) {
            this.state.html = "";
        }
    }
}
registry.category("main_components").add("synapsys_enable_panel", { Component: SynapsysEnablePanel });
