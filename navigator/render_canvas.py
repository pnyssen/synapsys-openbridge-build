"""Render an Obsidian .canvas JSON file to a browser-safe SVG projection.

The output is a self-contained HTML page (inline SVG, no scripts required
for viewing, no external requests) that works from file://, local HTTP and
SharePoint, and is explicitly labelled as a projection of the authoritative
.canvas source.
"""
import html
import json
import re

_COLOR = {
    "1": ("#fdecea", "#c0392b"), "2": ("#fff4d8", "#b9770e"),
    "3": ("#fff9c4", "#9a7d0a"), "4": ("#eaf6ed", "#1e8449"),
    "5": ("#e8f8f5", "#148f77"), "6": ("#eaf2fb", "#2471a3"),
}
_DEFAULT = ("#eef3f6", "#5d6d7e")


def _node_colors(node):
    c = node.get("color", "")
    if c in _COLOR:
        return _COLOR[c]
    if isinstance(c, str) and c.startswith("#"):
        return (c + "22" if len(c) == 7 else c, c)
    return _DEFAULT


def _wrap(text, width=34):
    out = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        # strip simple markdown decoration for the SVG projection
        para = re.sub(r"[#*`>]+", "", para).strip()
        while len(para) > width:
            cut = para.rfind(" ", 0, width)
            cut = cut if cut > 0 else width
            out.append(para[:cut])
            para = para[cut:].strip()
        if para:
            out.append(para)
    return out


def render_svg(canvas_json):
    data = json.loads(canvas_json)
    nodes = [n for n in data.get("nodes", []) if n.get("type") in ("text", "group", "file", "link")]
    edges = data.get("edges", [])
    if not nodes:
        return "<p>Empty canvas.</p>"

    minx = min(n["x"] for n in nodes) - 60
    miny = min(n["y"] for n in nodes) - 60
    maxx = max(n["x"] + n.get("width", 200) for n in nodes) + 60
    maxy = max(n["y"] + n.get("height", 80) for n in nodes) + 60
    w, h = maxx - minx, maxy - miny

    byid = {n["id"]: n for n in nodes}
    parts = []
    parts.append(
        f'<svg viewBox="{minx} {miny} {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Canvas projection" '
        f'style="width:100%;height:auto;background:#fbfdfe;border:1px solid #cbd8de;border-radius:10px">')
    parts.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
                 'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                 '<path d="M 0 0 L 10 5 L 0 10 z" fill="#7f8c8d"/></marker></defs>')

    # edges under nodes
    for e in edges:
        a, b = byid.get(e.get("fromNode")), byid.get(e.get("toNode"))
        if not a or not b:
            continue
        ax = a["x"] + a.get("width", 200) / 2
        ay = a["y"] + a.get("height", 80) / 2
        bx = b["x"] + b.get("width", 200) / 2
        by = b["y"] + b.get("height", 80) / 2
        parts.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" '
                     f'stroke="#7f8c8d" stroke-width="2" marker-end="url(#arr)" opacity="0.75"/>')
        lbl = e.get("label")
        if lbl:
            mx, my = (ax + bx) / 2, (ay + by) / 2
            esc = html.escape(lbl)
            parts.append(f'<text x="{mx}" y="{my - 6}" font-size="13" text-anchor="middle" '
                         f'fill="#34495e" font-family="Arial" paint-order="stroke" '
                         f'stroke="#fbfdfe" stroke-width="4">{esc}</text>')

    groups = [n for n in nodes if n.get("type") == "group"]
    plain = [n for n in nodes if n.get("type") != "group"]

    for n in groups + plain:
        x, y = n["x"], n["y"]
        nw, nh = n.get("width", 200), n.get("height", 80)
        fill, stroke = _node_colors(n)
        is_group = n.get("type") == "group"
        opacity_attr = 'fill-opacity="0.35" ' if is_group else ""
        parts.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="10" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="{2 if is_group else 1.5}" '
                     f'{opacity_attr}/>')
        label = n.get("label") or n.get("text") or n.get("file") or n.get("url") or ""
        approx_chars = max(12, int(nw / 8.2))
        lines = _wrap(label, approx_chars)
        max_lines = max(1, int((nh - 16) / 17))
        shown = lines[:max_lines]
        if len(lines) > max_lines and shown:
            shown[-1] = shown[-1][:approx_chars - 1] + "…"
        ty = y + 22 if is_group else y + (nh - len(shown) * 17) / 2 + 14
        weight = "bold" if (is_group or n.get("text", "").startswith("#")) else "normal"
        for i, line in enumerate(shown):
            esc = html.escape(line)
            parts.append(f'<text x="{x + nw / 2}" y="{ty + i * 17}" font-size="13.5" '
                         f'text-anchor="middle" fill="#1b2b34" font-family="Arial" '
                         f'font-weight="{weight}">{esc}</text>')
    parts.append("</svg>")
    return "".join(parts)
