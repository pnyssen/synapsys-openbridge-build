// Pure navigation rules for the Master Architecture page. No Odoo imports, so it runs in Node and in a plain browser page.
// The page is server-rendered; the only client logic is: which control was pressed, what navigation state follows, and whether the state is valid.
export const SECTIONS = ["overview", "value", "kinematics", "fractals", "perspectives", "effects", "mesh", "drill", "actors", "evidence", "holds"];
export const PERSPECTIVES = ["Form", "Flow", "Evolve"];
export const DEPTHS = ["enable", "enhance", "enrich"];
export const ACTORS = ["steward", "collaborator", "client"];
// The same grammar the server enforces (arch_master_drill._PATH). The server validates again; this only avoids sending an obviously invalid request.
export const DRILL_RE = /^(app|grp:\d{1,5}|scr:\d{1,5}|view:\d{1,5}|fld:\d{1,5}:[a-z][a-z0-9_]{0,48}|data:\d{1,5}:[a-z][a-z0-9_]{0,48}|rec:synapsys\.(?:outcome|benefit|asset):\d{1,10})$/;
const OV_ID_RE = /^[A-Za-z0-9._:-]{1,80}$/;
const OV_MAX = 50;

export function initialState() {
    return { section: "overview", perspective: "Form", depth: "enable", actor: "steward", drill: "app", ov: "" };
}

export function parseOv(text) {
    const m = new Map();
    for (const part of String(text || "").split(";").slice(0, OV_MAX)) {
        const i = part.lastIndexOf("@");
        const id = i > 0 ? part.slice(0, i) : "";
        const mode = i > 0 ? part.slice(i + 1) : "";
        if (id && DEPTHS.includes(mode) && OV_ID_RE.test(id)) { m.set(id, mode); }
    }
    return m;
}

export function composeOv(map) {
    return [...map.entries()].map(([k, v]) => k + "@" + v).join(";");
}

// Returns the NEXT state for a pressed control, or null when the target is not a navigation control or carries an invalid value.
// Rights are never decided here: the server validates every field again and applies the real account's rights.
export function nextState(state, ds) {
    if (!ds) {
        return null;
    }
    const s = Object.assign({}, state);
    let moved = false;
    if (ds.section !== undefined) {
        if (!SECTIONS.includes(ds.section)) { return null; }
        s.section = ds.section; moved = true;
    }
    if (ds.persp !== undefined) {
        if (!PERSPECTIVES.includes(ds.persp)) { return null; }
        s.perspective = ds.persp; moved = true;
        if (ds.section === undefined && state.section !== "perspectives" && state.section !== "overview") { s.section = "perspectives"; }
    }
    if (ds.depth !== undefined) {
        if (!DEPTHS.includes(ds.depth)) { return null; }
        s.depth = ds.depth; moved = true;
    }
    if (ds.actor !== undefined) {
        if (!ACTORS.includes(ds.actor)) { return null; }
        s.actor = ds.actor; moved = true;
    }
    if (ds.drill !== undefined) {
        if (!DRILL_RE.test(ds.drill)) { return null; }
        s.drill = ds.drill; s.section = "drill"; moved = true;
    }
    if (ds.ovel !== undefined) {
        if (!OV_ID_RE.test(ds.ovel) || (ds.ovmode !== "" && !DEPTHS.includes(ds.ovmode))) { return null; }
        const m = parseOv(state.ov);
        if (ds.ovmode === "") { m.delete(ds.ovel); } else { m.set(ds.ovel, ds.ovmode); }
        s.ov = composeOv(m); moved = true;
    }
    if (!moved) {
        return null;
    }
    return JSON.stringify(s) === JSON.stringify(state) ? null : s;
}

// Walk up from the event target to the nearest control that carries navigation data.
export function controlFrom(target) {
    let el = target;
    while (el && el.dataset !== undefined) {
        const d = el.dataset;
        if (d.section !== undefined || d.persp !== undefined || d.depth !== undefined || d.actor !== undefined || d.drill !== undefined || d.ovel !== undefined) {
            return d;
        }
        el = el.parentElement;
    }
    return null;
}
