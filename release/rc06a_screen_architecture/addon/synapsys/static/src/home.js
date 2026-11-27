import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Component, onWillStart, onWillDestroy, proxy, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class SynapsysHome extends Component {
    static template = "synapsys.Home";
    setup() {
        this.state = proxy({ html: "" });
        onWillStart(async () => {
            this.state.html = markup(await rpc("/synapsys/home/data", {}));
        });
    }
}
registry.category("actions").add("synapsys_home", SynapsysHome);

export class SynapsysArchitectureMap extends Component {
    static template = "synapsys.ArchMap";
    setup() {
        this.state = proxy({ html: "" });
        this.lm = useService("synapsys_lens_mode");
        this.cur = { id: null, trail: "" };
        const off = this.lm.subscribe(() => this.load(this.cur.id, this.cur.trail));
        onWillDestroy(off);
        onWillStart(async () => {
            await this.load(null, "");
        });
    }
    async load(objectId, trail) {
        this.cur = { id: objectId, trail: trail };
        this.state.html = markup(await rpc("/synapsys/architecture/map/object", {
            object_id: objectId, trail: trail, mode: this.lm.mode, ov: this.lm.overrides }));
    }
    onClick(ev) {
        const ov = ev.target.closest("[data-ovel]");
        if (ov) {
            ev.preventDefault();
            this.lm.setOverride(ov.dataset.ovel, ov.dataset.ovmode);
            return;
        }
        const a = ev.target.closest("[data-obj]");
        if (!a) {
            return;
        }
        ev.preventDefault();
        this.load(a.dataset.obj, a.dataset.trail || "");
    }
    setMode(m) {
        this.lm.setMode(m);
    }
}
registry.category("actions").add("synapsys_architecture_map", SynapsysArchitectureMap);

export class SynapsysLenses extends Component {
    static template = "synapsys.Lenses";
    setup() {
        this.state = proxy({ html: "" });
        this.lm = useService("synapsys_lens_mode");
        this.cur = { level: 1, group: "", sec: "", scaffold: false };
        const off = this.lm.subscribe(() => this.load(this.cur.level, this.cur.group, this.cur.sec, this.cur.scaffold));
        onWillDestroy(off);
        onWillStart(async () => {
            await this.load(1, "", "");
        });
    }
    async load(level, group, sec, scaffold = false) {
        this.cur = { level: level, group: group, sec: sec, scaffold: scaffold };
        if (scaffold) {
            this.state.html = markup(await rpc("/synapsys/scaffold/view", { depth: this.lm.mode }));
            return;
        }
        this.state.html = markup(await rpc("/synapsys/lenses/data", {
            level: level, group: group, sec: sec, mode: this.lm.mode, ov: this.lm.overrides }));
    }
    setMode(m) {
        this.lm.setMode(m);
    }
    onClick(ev) {
        const ov = ev.target.closest("[data-ovel]");
        if (ov) {
            ev.preventDefault();
            this.lm.setOverride(ov.dataset.ovel, ov.dataset.ovmode);
            return;
        }
        const sc = ev.target.closest("[data-scaffold]");
        if (sc) {
            ev.preventDefault();
            this.load(1, "", "", true);
            return;
        }
        const a = ev.target.closest("[data-lv]");
        if (!a) {
            return;
        }
        ev.preventDefault();
        this.load(parseInt(a.dataset.lv, 10), a.dataset.g || "", a.dataset.s || "");
    }
}
registry.category("actions").add("synapsys_lenses", SynapsysLenses);
