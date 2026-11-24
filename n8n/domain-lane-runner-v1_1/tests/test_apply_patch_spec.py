import json, subprocess, sys, tempfile, pathlib, copy
root = pathlib.Path(__file__).resolve().parent.parent
OLD = json.load(open(root/'NODE_PATCH_SPEC_v1_1.json'))['node_code_replacements'][0]['find']
def wf(ver='85db4098-1679-4e04-afd1-9374b6f0af8b', active=True, anchor=OLD):
    resp={"fullResponse":False,"neverError":True,"outputPropertyName":"raw","responseFormat":"text"}
    n=lambda name,p:{"name":name,"parameters":p}
    return {"id":"pnCEHhZWIDaRfrLe","versionId":ver,"active":active,"nodes":[
      n("Read Packet",{"options":{"response":{"response":dict(resp)}}}), n("Read Source",{"options":{"response":{"response":dict(resp,outputPropertyName="body_text")}}}),
      n("Gate Packets",{"jsCode":"old"}), n("Assemble Prompt",{"jsCode":"old"}), n("Build Return",{"jsCode":"x ... "+anchor+" ... y"})]}
def run(w):
    d=pathlib.Path(tempfile.mkdtemp()); (d/'w.json').write_text(json.dumps(w))
    r=subprocess.run([sys.executable,str(root/'apply_patch_spec.py'),str(d/'w.json'),str(root/'NODE_PATCH_SPEC_v1_1.json'),str(d/'o.json')],capture_output=True,text=True)
    return r.returncode, (json.load(open(d/'o.json')) if r.returncode==0 else None), r.stderr
res=[]
rc,o,_=run(wf()); nm={x['name']:x for x in o['nodes']}
res.append(('A1 apply on matching version exits 0',rc==0))
res.append(('A2 both HTTP nodes -> responseFormat=file, outputPropertyName=data, fullResponse',all(nm[k]['parameters']['options']['response']['response']=={"fullResponse":True,"neverError":True,"outputPropertyName":"data","responseFormat":"file"} for k in('Read Packet','Read Source'))))
res.append(('A3 Gate/Assemble code replaced and contain sha256Bytes + getBinaryDataBuffer',all('sha256Bytes' in nm[k]['parameters']['jsCode'] and 'getBinaryDataBuffer' in nm[k]['parameters']['jsCode'] for k in('Gate Packets','Assemble Prompt'))))
res.append(('A4 Build Return anchor replaced once; old text gone',OLD not in nm['Build Return']['parameters']['jsCode'] and 'mismatch_class' in nm['Build Return']['parameters']['jsCode']))
res.append(('A5 NEG drifted versionId refused (exit 3)',run(wf(ver='deadbeef'))[0]==3))
res.append(('A6 NEG inactive workflow refused (exit 3)',run(wf(active=False))[0]==3))
res.append(('A7 NEG anchor missing refused (exit 3)',run(wf(anchor='nothing'))[0]==3))
res.append(('A8 NEG anchor duplicated refused (exit 3)',run(wf(anchor=OLD+' '+OLD))[0]==3))
ok=all(v for _,v in res)
for k,v in res: print(('PASS ' if v else 'FAIL ')+k)
print('SUMMARY','pass=%d fail=%d'%(sum(v for _,v in res),sum(not v for _,v in res)))
sys.exit(0 if ok else 1)
