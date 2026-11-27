import { registry } from "@web/core/registry";

// One shared presentation mode (enable, enhance, enrich) for every SynapSys screen.
// Presentation state only: it never touches a record, kind, approval, evidence or right.
const MODES = ["enable", "enhance", "enrich"];
const KEY = "synapsys.lens.mode";

export const lensModeService = {
    start() {
        let mode = "enable";
        try {
            const saved = window.localStorage.getItem(KEY);
            if (MODES.includes(saved)) {
                mode = saved;
            }
        } catch (e) {
            // storage unavailable: keep the in-memory default
        }
        const subs = new Set();
        const state = { mode, overrides: {} };
        return {
            get mode() {
                return state.mode;
            },
            get overrides() {
                return Object.entries(state.overrides).map(([k, v]) => k + "@" + v).join(";");
            },
            setMode(m) {
                if (!MODES.includes(m) || m === state.mode) {
                    return;
                }
                state.mode = m;
                try {
                    window.localStorage.setItem(KEY, m);
                } catch (e) {
                    // not persisted; still applies in this session
                }
                subs.forEach((f) => f());
            },
            setOverride(id, m) {
                if (MODES.includes(m)) {
                    state.overrides[id] = m;
                } else {
                    delete state.overrides[id];
                }
                subs.forEach((f) => f());
            },
            subscribe(f) {
                subs.add(f);
                return () => subs.delete(f);
            },
        };
    },
};
registry.category("services").add("synapsys_lens_mode", lensModeService);
