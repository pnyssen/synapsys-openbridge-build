/*__SHA256_PRELUDE__*/
const reads=$input.all();const meta=$('Fan Out Sources').all();const pkts=$('Pending Only').all();
const MAXS=60000, MAXT=200000;
const out=[];
for(const pk of pkts){
 const P=pk.json;const checks=[];let total=0;let bodies='';let ok=true;
 for(let i=0;i<meta.length;i++){ if(meta[i].json.packet_path!==P.packet_path)continue;
  // v1.1 SOURCE-INTEGRITY FIX: digest is computed over the raw received bytes (binary property), before any decoding. Text is decoded only afterwards, for the prompt.
  const r=reads[i]||{json:{}};const hdr=(r.json||{}).headers||{};const stRaw=(r.json||{}).statusCode;const st=stRaw===undefined?null:Number(stRaw);
  const ct=String(hdr['content-type']||'');const cl=(hdr['content-length']!==undefined&&hdr['content-length']!==null&&hdr['content-length']!=='')?Number(hdr['content-length']):null;
  let buf=null;try{buf=await this.helpers.getBinaryDataBuffer(i,'data')}catch(e){buf=null}
  let got='READ_FAILED',bytes=0,cls='',txt='';
  if(buf&&buf.length>0&&(st===null||st===200)){got=sha256Bytes(buf);bytes=buf.length;txt=new TextDecoder('utf-8').decode(buf);}
  else{cls=(st!==null&&st!==200)?'HTTP_'+st:(buf&&buf.length===0?'EMPTY_BODY':'NO_BINARY_BODY');}
  const match=got===meta[i].json.src_sha;
  if(!match&&got!=='READ_FAILED'){
   cls='RAW_BYTES_DIFFER';
   if(cl!==null&&cl!==bytes)cls='LENGTH_MISMATCH_CONTENT_LENGTH_'+cl+'_RECEIVED_'+bytes;
   else{try{const compact=sha256Bytes(new TextEncoder().encode(JSON.stringify(JSON.parse(txt))));if(compact===meta[i].json.src_sha)cls='PINNED_DIGEST_IS_OF_COMPACT_JSON_NOT_RAW_BYTES';}catch(e){}}
  }
  if(!match)ok=false;checks.push({path:meta[i].json.src_path,expected:meta[i].json.src_sha,observed:got,match,bytes,status:st===null?'UNREPORTED':st,content_type:ct,mismatch_class:cls});
  let t=txt.length>MAXS?txt.slice(0,MAXS)+'\n[TRUNCATED at '+MAXS+' chars]':txt; if(total+t.length>MAXT){t='[OMITTED: total size cap]';} total+=t.length;
  bodies+='\n\n===== SOURCE '+meta[i].json.src_path+' (sha256 '+got+', '+(match?'MATCH':'MISMATCH')+') =====\n'+t;}
 const pkt=P.packet;
 const prompt=['You are the SynapSys domain lane '+pkt.lane+'. Your role, charter extract and outcome measures are in the FIRST source (your lane profile); the SECOND source is the core profile (Stewardship D000, Governance D001, Methods D002) you work within. The work below was produced by other lanes (mostly Anthropic Claude). Your output is a domain view only: NON_AUTHORISING_DOMAIN_VIEW. You cannot approve, release, promote value or change anything.',
 'Rules: use only the hash-verified sources supplied; never invent evidence; where evidence is missing say INSUFFICIENT_EVIDENCE. Separate evidenced, inferred and claimed. Triangulate: read each finding from the Steward, Collaborator and Client perspectives. Stay inside your domain authority; name any matter belonging to another domain instead of deciding it.',
 'Packet id: '+pkt.id,'Packet path: '+P.packet_path+' (sha256 '+P.packet_sha256+')','Goal: '+(pkt.goal||''),'Context: '+(pkt.context||''),
 'Tests:',...(Array.isArray(pkt.tests)?pkt.tests:[]).map((t,i)=>'  '+(i+1)+'. '+t),
 'Output, for each question: Outcome (the measurable outcome your domain needs, with measure and target); Situation (what the sources show); Complication (why it is a problem now); Critical question; Answer and proposed solution (with conditions, owner and closure test); Evidence cited; Dissent or open items. Then any matter outside the questions. End with exactly one final line: position: SUPPORT or position: SUPPORT_WITH_CONDITIONS or position: OBJECT or position: INSUFFICIENT_EVIDENCE. No other line may begin with position:.',
 bodies].join('\n');
 out.push({json:{lane:pkt.lane,packet_path:P.packet_path,packet_sha256:P.packet_sha256,packet_id:pkt.id,expected_return:P.expected_return,return_name:P.return_name,source_checks:checks,sources_ok:ok,prompt}});
}
return out;
