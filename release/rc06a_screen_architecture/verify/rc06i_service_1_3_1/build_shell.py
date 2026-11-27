"""MOCK SHELL shaped by the DOM probe on dev (RETURN_COWORK_DOM_PROBE_RC06G_DEV_SERVICES_20261127_v1.md, sha256 f69e3c93...): body.o_web_client is a
viewport-height flex column; children in order: header.o_navbar (46 px), div.o_action_manager (flexible, overflow-y hidden), div.o-main-components-container
(block) holding the panel. The panel wrapper and any client-side markup come from THAT version's own enable_panel.xml, expanded here for the one template
the file contains. This is structural evidence only: it is not Odoo and not proof of correct placement."""
import html, re, sys

NATIVE = ('<div class="o_action o_list_view" data-native-view="1"><div class="o_control_panel"><b>Services</b> <button class="btn btn-sm">New</button></div>'
          '<table class="o_list_table"><thead><tr><th>Name</th><th>Status</th></tr></thead></table><div class="o_view_nocontent">No records</div></div>')
CSS = ('html{height:100%}body.o_web_client{margin:0;display:flex;flex-direction:column;height:100%;font:14px/1.5 system-ui,sans-serif;color:#212529}'
       'header.o_navbar{height:46px;flex:0 0 auto;background:#714b67;color:#fff;display:flex;align-items:center;padding:0 12px}'
       '.o_action_manager{flex:1 1 auto;overflow-y:hidden;min-height:0;position:relative;display:flex;flex-direction:column}'
       '.o_action{flex:1 1 auto;min-height:0;overflow:hidden}.o_control_panel{padding:8px 16px;border-bottom:1px solid #dee2e6}'
       '.o_list_table{width:100%;border-collapse:collapse}.o_list_table th{text-align:left;padding:4px 16px;border-bottom:1px solid #dee2e6}'
       '.o_view_nocontent{padding:60px 16px;text-align:center;color:#6c757d}'
       '.o-main-components-container{display:block}.bg-view{background:#fff}.border-bottom{border-bottom:1px solid #dee2e6}'
       '.btn{font:inherit;font-size:12.25px;padding:3px 8px;border:1px solid #6c757d;border-radius:4px;background:#fff;color:#212529}'
       '.btn-primary{background:#714b67;color:#fff;border-color:#714b67}.btn-outline-secondary{background:#fff}')


def panel(xml, inner):
    m = re.search(r'<div t-if="this\.state\.html" class="([^"]*)"', xml)
    cls = m.group(1) if m else "syn-enable-panel"
    modebar = ""
    if "syn-modebar" in xml:  # RC06g/RC06h keep a modebar in the client template: expand its one t-foreach as the client would (enable pressed)
        btns = "".join('<button type="button" class="btn btn-sm %s" data-mode="%s" aria-pressed="%s">%s</button>' % (
            "btn-primary" if d == "enable" else "btn-outline-secondary", d, "true" if d == "enable" else "false", d) for d in ("enable", "enhance", "enrich"))
        sty = re.search(r'class="syn-modebar"[^>]*style="([^"]*)"', xml)
        modebar = '<div class="syn-modebar" role="group" aria-label="Presentation depth" style="%s"><span style="font-size:13px;color:#52606d;align-self:center">Depth</span>%s</div>' % (
            sty.group(1) if sty else "", btns)
    return '<div class="%s">%s%s</div>' % (cls, modebar, inner)


def shell(xml, inner):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MOCK SHELL</title><style>%s</style></head>'
            '<body class="o_web_client"><header class="o_navbar">MOCK SHELL (not Odoo)</header><div class="o_action_manager">%s</div>'
            '<div class="o-main-components-container">%s</div><svg width="0" height="0"></svg></body></html>') % (CSS, NATIVE, panel(xml, inner))


if __name__ == "__main__":
    import json
    pages = json.load(open(sys.argv[1])); xml = open(sys.argv[2]).read(); outdir = sys.argv[3]
    for k, v in pages.items():
        open("%s/%s.html" % (outdir, k.replace("|", "_")), "w").write(shell(xml, v["html"] if v["result"] == "OK" else ""))
