import json,re,html as H
P=json.load(open('/tmp/cf/pages.json'))
def shell(inner, tabs=True):
    t=''.join('<button class="btn btn-sm %s" data-mode="%s">%s</button>'%('btn-primary' if m=='enable' else 'btn-outline-secondary',m,m) for m in('enable','enhance','enrich'))
    return ('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><style>'
    'body{margin:0;font:14px sans-serif}.o_web_client{display:flex;flex-direction:column;height:100vh}.nav{height:46px;background:#714b67;color:#fff;flex:none}'
    '.btn{font-size:13px;padding:2px 8px;border:1px solid #888;border-radius:4px;background:#fff}.btn-primary{background:#714b67;color:#fff}'
    '.o_action_manager{flex:1 1 auto;overflow:auto}.o_view_nocontent{position:absolute;top:30%%;left:0;right:0;text-align:center}.lst{height:300px}'
    '</style><div class="o_web_client"><div class="nav">nav</div>'
    '<div class="o-main"><div class="syn-enable-panel border-bottom bg-view"><div class="syn-modebar" style="display:flex;gap:6px;padding:8px 16px;border-bottom:1px solid #e4e7eb;background:#fff"><span>Depth</span>%s</div>%s</div></div>'
    '<div class="o_action_manager"><div class="lst"><div class="o_view_nocontent">No records</div></div></div></div>')%(t,inner)
for k,v in P.items():
    open('/tmp/cf/out/'+k.replace('|','_').replace('.','_')+'.html','w').write(shell(v['html']))
