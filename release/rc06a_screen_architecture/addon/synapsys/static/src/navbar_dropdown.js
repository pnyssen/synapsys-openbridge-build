import { patch } from "@web/core/utils/patch";
import { Dropdown } from "@web/core/dropdown/dropdown";

// Odoo 20 opens every dropdown as a bottom sheet on touch devices (iPad included).
// Inside the SynapSys app the menus must drop down like on desktop.
patch(Dropdown.prototype, {
    get isBottomSheet() {
        const app = this.env.services?.menu?.getCurrentApp?.();
        if (app && (app.name === "SynapSys" || (app.xmlid || "").startsWith("synapsys"))) {
            return false;
        }
        return super.isBottomSheet;
    },
});
