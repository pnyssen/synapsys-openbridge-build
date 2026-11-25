// Offline harness for Domain Lane Runner v1.1 source-integrity fix.
// Runs the exact node code (src/*.js with the SHA prelude inlined) against a minimal n8n mock.
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)); const root=path.join(here,'..');
const prelude=fs.readFileSync(path.join(root,'src/sha256_bytes.js'),'utf8');
const build=(f)=>fs.readFileSync(path.join(root,'src',f),'utf8').replace('/*__SHA256_PRELUDE__*/',prelude);
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const sha=(b)=>crypto.createHash('sha256').update(b).digest('hex');
const V=(n)=>fs.readFileSync(path.join(here,'vectors',n));
const ALIAS=V('real_alias_gvtec001_candidate_c553.json.bin'), STATE=V('real_current_state.json.bin'), SV56=V('real_state_v56_alias_d2de.json.bin');
let pass=0,fail=0; const log=[];
function check(id,desc,cond,detail=''){ (cond?pass++:fail++); const l=`${cond?'PASS':'FAIL'} ${id} ${desc}${detail?' :: '+detail:''}`; log.push(l); console.log(l); }

// ---- n8n mock helpers
function run(code,{inputs,named,thisObj}){ // inputs: [{json,binary(Buffer)|null}]
  const bin=inputs.map(i=>i.bin);
  const helpers={getBinaryDataBuffer:async(i,k)=>{ if(k!=='data'||bin[i]==null) throw new Error('no binary'); return Buffer.from(bin[i]); }};
  const $input={all:()=>inputs.map(i=>({json:i.json}))};
  const $=(name)=>({all:()=>named[name],itemMatching:(i)=>named[name][i]});
  return new AsyncFunction('$input','$',code).call({helpers},$input,$);
}
// Original (v1) transport replay: HTTP node text mode + JSON sniffing => compacted string; original hash = sha256(utf8(string)).
function originalTransport(bytes){ const s=Buffer.from(bytes).toString('utf8'); try{return JSON.stringify(JSON.parse(s));}catch(e){return s;} }
const originalHash=(str)=>sha(Buffer.from(str,'utf8')); // identical in effect to v1 sha256Hex(str)

// ---- T05 sha256Bytes vs node:crypto
const shaFn=new Function(prelude+';return sha256Bytes;')();
let allOK=true; const lens=[0,1,2,55,56,57,63,64,65,119,120,121,127,128,129,1000,4095,4096,65535,65536,1048576];
for(const L of lens){ const b=crypto.randomBytes(L); if(shaFn(new Uint8Array(b))!==sha(b)){allOK=false;check('T05','sha256Bytes length '+L,false);} }
const all=Buffer.from([...Array(256).keys()]); if(shaFn(new Uint8Array(all))!==sha(all))allOK=false;
check('T05','sha256Bytes == node:crypto on '+lens.length+' lengths (0..1 MiB, block boundaries) and all-256-byte vector',allOK);
check('T05b','sha256Bytes rejects non-bytes input (string)',(()=>{try{shaFn('abc');return false}catch(e){return /NOT_BYTES/.test(e.message)}})());

// ---- fixtures for Assemble Prompt
const LANE='MESH_QUEUE/KIT/LANES/D001_LANE_PROFILE_v1.md';
function srcCase(items){ // items: [{path,expected,bytes,status,headers}]
  const pkt={id:'T',lane:'D001',goal:'g',context:'c',tests:['t1']};
  const named={ 'Fan Out Sources':items.map((s,idx)=>({json:{packet_path:'MESH_QUEUE/INBOX/PKT-T.json',idx,src_path:s.path,src_sha:s.expected}})),
                'Pending Only':[{json:{packet:pkt,packet_path:'MESH_QUEUE/INBOX/PKT-T.json',packet_sha256:'p'.repeat(64),expected_return:'x',return_name:'r.md',lane:'D001'}}]};
  const inputs=items.map(s=>({json:{statusCode:s.status??200,headers:s.headers??{}},bin:s.bytes}));
  return {named,inputs};
}
const assemble=build('assemble_prompt.js'); const gate=build('gate_packets.js');
async function A(items){ const c=srcCase(items); const r=await run(assemble,{inputs:c.inputs,named:c.named}); return r[0].json; }

// ---- T01 ORIGINAL FAILURE replay (recorded execution 430528: alias expected c553.. observed bc454ae0..)
const tx=originalTransport(ALIAS);
check('T01','ORIGINAL v1 transport+hash reproduces the recorded false mismatch on the real alias (observed bc454ae0..., expected c553c4f9...)',
  originalHash(tx)==='bc454ae0c41e023e9cd754fcf672d7146e16c8bb03b471fda62f5f3fd0e9a609' && originalHash(tx)!==sha(ALIAS),
  'observed='+originalHash(tx).slice(0,16)+' raw='+sha(ALIAS).slice(0,16)+' compactBytes='+Buffer.byteLength(tx)+' rawBytes='+ALIAS.length);
const txtAlias=originalTransport(ALIAS); // .txt alias: same bytes, same sniffing
check('T01b','ORIGINAL v1 ".txt alias" workaround fails identically (name/extension irrelevant)',originalHash(txtAlias)===originalHash(tx));

// ---- T02 corrected path, real alias; T03 second real traversal; T04 repeat/idempotence
const hdr=(b)=>({'content-type':'application/json','content-length':String(b.length)});
const r1=await A([{path:'a.json',expected:sha(ALIAS),bytes:ALIAS,headers:hdr(ALIAS)}]);
check('T02','v1.1 real alias (10,846 B) raw-byte digest == pinned c553c4f9...; sources_ok',r1.sources_ok===true&&r1.source_checks[0].observed==='c553c4f99968cd15adbccd2eaf7197f0db36b8914cd5b9fa44a442b7fa540e7e'&&r1.source_checks[0].bytes===10846);
const r2=await A([{path:'state.json',expected:'049eda7c92eb7c672b0fdd6d1237a25f1022452d026fe42abde513f1bfbe2b7e',bytes:STATE,headers:hdr(STATE)}]);
check('T03','v1.1 SECOND equivalent real JSON traversal (CURRENT_STATE.json, 1,025 B) == 049eda7c...; sources_ok',r2.sources_ok===true&&r2.source_checks[0].bytes===1025);
const r2t=await A([{path:'state.txt',expected:sha(STATE),bytes:STATE,headers:{'content-type':'text/plain','content-length':'1025'}}]);
check('T03b','v1.1 same bytes under .txt / text/plain still MATCH (digest independent of name and MIME)',r2t.sources_ok===true);
const r3=await A([{path:'a.json',expected:sha(ALIAS),bytes:ALIAS,headers:hdr(ALIAS)},{path:'s.json',expected:sha(STATE),bytes:STATE,headers:hdr(STATE)}]);
const r4=await A([{path:'a.json',expected:sha(ALIAS),bytes:ALIAS,headers:hdr(ALIAS)},{path:'s.json',expected:sha(STATE),bytes:STATE,headers:hdr(STATE)}]);
check('T04','repeat traversal (two sources, run twice): identical checks, no state carried',r3.sources_ok&&r4.sources_ok&&JSON.stringify(r3.source_checks)===JSON.stringify(r4.source_checks)&&r3.prompt===r4.prompt);
check('T04b','prompt carries the RAW text (pretty-printed, not compacted)',r1.prompt.includes('"acceptance": "One true')&&r1.prompt.includes('\n  "acceptance"'));


// ---- T05c LATENT DEFECT in v1 hash routine: padding block count wrong when len % 64 == 55
{ const origSrc=prelude.replace('(((l+8)>>6)+1)<<6','(((l+9)>>6)+1)<<6'); const origFn=new Function(origSrc+';return sha256Bytes;')();
  const badLens=[],fixBad=[]; for(let L=0;L<=700;L++){const b=crypto.randomBytes(L);const h=sha(b); if(origFn(new Uint8Array(b))!==h)badLens.push(L); if(shaFn(new Uint8Array(b))!==h)fixBad.push(L);}
  check('T05c','ORIGINAL v1 padding formula (l+9) reproduced as wrong exactly at len%64==55 (lens '+badLens.join(',')+')',badLens.length>0&&badLens.every(L=>L%64===55)&&badLens.length===Math.floor((700-55)/64)+1);
  check('T05d','v1.1 formula (l+8) correct for every length 0..700',fixBad.length===0);
  const f55=Buffer.alloc(119,0x61); const asm=await A([{path:'f.md',expected:sha(f55),bytes:f55,headers:{'content-length':'119'}}]);
  check('T05e','v1.1 end-to-end: a 119-byte source (len%64==55) now MATCHES; v1 hash of the same bytes would not',asm.sources_ok===true&&origFn(new Uint8Array(f55))!==sha(f55)); }


// ---- T16 SECOND RECORDED FAILURE (execution 430528): STATE_v56 alias, expected d2de2edb.., observed b0972b18..
check('T16a','ORIGINAL v1 transport+hash on the real STATE_v56 alias reproduces the recorded false mismatch b0972b18... (falsifiable prediction of the root cause)',
  originalHash(originalTransport(SV56))==='b0972b187cf9de90745e2f184d562991798fe2fc69f3284d07bee4f4c93accf4'&&sha(SV56)==='d2de2edbaece0f780ea603a5acf6dc21b54c56cb5bb589c1f01118dc9c09b269');
{ const r=await A([{path:'s.json',expected:'d2de2edbaece0f780ea603a5acf6dc21b54c56cb5bb589c1f01118dc9c09b269',bytes:SV56,headers:hdr(SV56)}]);
  check('T16b','v1.1 real STATE_v56 alias (16,545 B) raw-byte digest == d2de2edb...; sources_ok',r.sources_ok===true&&r.source_checks[0].bytes===16545); }

// ---- negatives (must fail closed)
const tam=Buffer.from(ALIAS); tam[100]^=0x01;
const n1=await A([{path:'a.json',expected:sha(ALIAS),bytes:tam,headers:hdr(ALIAS)}]);
check('T07','NEG single-bit tamper, same length => MISMATCH, sources_ok=false, class RAW_BYTES_DIFFER',n1.sources_ok===false&&n1.source_checks[0].match===false&&n1.source_checks[0].mismatch_class==='RAW_BYTES_DIFFER');
const tr=ALIAS.subarray(0,5000);
const n2=await A([{path:'a.json',expected:sha(ALIAS),bytes:tr,headers:hdr(ALIAS)}]);
check('T08','NEG truncated transfer vs Content-Length => fail closed, class LENGTH_MISMATCH',n2.sources_ok===false&&/^LENGTH_MISMATCH_CONTENT_LENGTH_10846_RECEIVED_5000$/.test(n2.source_checks[0].mismatch_class));
const n3=await A([{path:'a.json',expected:sha(ALIAS),bytes:Buffer.from('{"error":"not found"}'),status:404,headers:{}}]);
check('T09','NEG HTTP 404 error body => READ_FAILED, class HTTP_404, never hashed as the source',n3.sources_ok===false&&n3.source_checks[0].observed==='READ_FAILED'&&n3.source_checks[0].mismatch_class==='HTTP_404');
const n4=await A([{path:'a.json',expected:sha(ALIAS),bytes:Buffer.alloc(0),headers:{}}]);
check('T10','NEG empty body => READ_FAILED / EMPTY_BODY',n4.sources_ok===false&&n4.source_checks[0].mismatch_class==='EMPTY_BODY');
const n4b=await A([{path:'a.json',expected:sha(ALIAS),bytes:null,headers:{}}]);
check('T10b','NEG no binary property at all => READ_FAILED / NO_BINARY_BODY',n4b.sources_ok===false&&n4b.source_checks[0].mismatch_class==='NO_BINARY_BODY');
const compactDigest=originalHash(tx);
const n5=await A([{path:'a.json',expected:compactDigest,bytes:ALIAS,headers:hdr(ALIAS)}]);
check('T11','NEG pinned digest is of COMPACT JSON, raw bytes differ => still FAIL (digest not silently redefined) but classified PINNED_DIGEST_IS_OF_COMPACT_JSON_NOT_RAW_BYTES',n5.sources_ok===false&&n5.source_checks[0].mismatch_class==='PINNED_DIGEST_IS_OF_COMPACT_JSON_NOT_RAW_BYTES');
// exotic bytes
const exotic=Buffer.concat([Buffer.from([0xEF,0xBB,0xBF]),Buffer.from('{"k":"é—✓","n":1}\r\n'),Buffer.from([0xFF,0xFE,0x00])]);
const n6=await A([{path:'x.bin',expected:sha(exotic),bytes:exotic,headers:hdr(exotic)}]);
check('T06','BOM + CRLF + non-ASCII + invalid UTF-8 bytes: digest over raw bytes == node:crypto',n6.sources_ok===true&&n6.source_checks[0].observed===sha(exotic));
const mixed=await A([{path:'a.json',expected:sha(ALIAS),bytes:ALIAS,headers:hdr(ALIAS)},{path:'b.json',expected:sha(ALIAS),bytes:tam,headers:hdr(ALIAS)}]);
check('T07b','NEG one bad source among good ones => sources_ok=false for the packet (provider gate closed)',mixed.sources_ok===false&&mixed.source_checks[0].match===true&&mixed.source_checks[1].match===false);

// ---- Gate Packets (packet digest over raw bytes)
function pkt(o={}){ return Buffer.from(JSON.stringify({id:'PKT-1',route:'lane_v1',lane:'D001',goal:'g',expected_return:'MESH_QUEUE/RETURNS/RETURN_D001_X_V1.md',
  sources:[{path:'MESH_QUEUE/KIT/LANES/D001_LANE_PROFILE_v1.md',sha256:'a'.repeat(64)},{path:'MESH_QUEUE/KIT/LANES/CORE_D000_D001_D002_PROFILE_v1.md',sha256:'b'.repeat(64)}],...o},null,2)+'\n'); }
async function G(bytes,callerSha,status){ const named={'Packet Paths':[{json:{packet_path:'MESH_QUEUE/INBOX/PKT-1.json',caller_packet_sha256:callerSha||null}}]}; return run(gate,{inputs:[{json:{statusCode:status??200,headers:{}},bin:bytes}],named}); }
const P=pkt(); const g1=await G(P); 
check('T12','Gate: pretty-printed packet accepted; packet_sha256 is the RAW-byte digest, not the compact one',g1.length===1&&g1[0].json.packet_sha256===sha(P)&&g1[0].json.packet_sha256!==originalHash(originalTransport(P)));
check('T12b','Gate: caller-supplied raw digest accepted when equal',(await G(P,sha(P))).length===1);
check('T12c','NEG Gate: caller-supplied COMPACT digest (the v1 behaviour) now rejected',(await G(P,originalHash(originalTransport(P)))).length===0);
check('T12d','NEG Gate: wrong caller digest rejected',(await G(P,'0'.repeat(64))).length===0);
check('T13','NEG Gate: non-JSON body skipped; HTTP 500 skipped; empty skipped',(await G(Buffer.from('<html>'))).length===0&&(await G(P,null,500)).length===0&&(await G(Buffer.alloc(0))).length===0);
check('T14','NEG Gate: wrong lane / bad return name / profile path outside KIT rejected',(await G(pkt({lane:'D009'}))).length===0&&(await G(pkt({expected_return:'MESH_QUEUE/RETURNS/RETURN_D008_X.md'}))).length===0&&(await G(pkt({sources:[{path:'../x.md',sha256:'a'.repeat(64)},{path:'MESH_QUEUE/KIT/LANES/CORE_D000_D001_D002_PROFILE_v1.md',sha256:'b'.repeat(64)}]}))).length===0);

// ---- Build Return check-line patch
const spec=JSON.parse(fs.readFileSync(path.join(root,'NODE_PATCH_SPEC_v1_1.json'),'utf8'));
const op=spec.node_code_replacements.find(r=>r.node==='Build Return');
const mk=(s)=>new Function('c','return '+s.replace(/^.*?\.map\(c=>/,'').replace(/\),\s*$/,'').replace(/\)$/,''));
check('T15','Build Return replacement text present exactly once and differs from original',!!op&&op.expect_count===1&&op.find!==op.replace);

console.log(`\nSUMMARY pass=${pass} fail=${fail}`);
fs.writeFileSync(path.join(here,'TEST_LOG.txt'),log.join('\n')+`\nSUMMARY pass=${pass} fail=${fail}\n`);
process.exit(fail?1:0);
