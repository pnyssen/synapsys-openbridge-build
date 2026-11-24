/*__SHA256_PRELUDE__*/
const BASE='/sites/SynapSys/Shared Documents/SynapSys-Control/11_WORKING_MEMORY/';const SP='https://synapsysgroup.sharepoint.com/sites/SynapSys/_api/web/';const fileUrl=(p)=>SP+"GetFileByServerRelativeUrl('"+encodeURI(BASE+p)+"')";
const out=[];const reads=$input.all();
for(let i=0;i<reads.length;i++){
 // v1.1 SOURCE-INTEGRITY FIX: packet bytes arrive as a binary property (responseFormat=file); the digest is over the raw received bytes, never over a parsed/re-serialised string.
 const st=(reads[i].json||{}).statusCode;if(st!==undefined&&Number(st)!==200)continue;
 let buf;try{buf=await this.helpers.getBinaryDataBuffer(i,'data')}catch(e){continue}
 if(!buf||!buf.length)continue;
 const meta=$('Packet Paths').itemMatching(i).json;
 const pkSha=sha256Bytes(buf);
 let p;try{p=JSON.parse(new TextDecoder('utf-8').decode(buf))}catch(e){continue}
 if(!p||p.route!=='lane_v1')continue;
 const lane=String(p.lane||'');if(!['D001','D008','D011'].includes(lane))continue;
 const er=String(p.expected_return||'');
 const em=er.match(/^MESH_QUEUE\/RETURNS\/RETURN_(D0\d\d)_[A-Z0-9_]+(_v\d+)?\.md$/);if(!em||em[1]!==lane)continue;
 if(meta.caller_packet_sha256&&meta.caller_packet_sha256!==pkSha)continue;
 const srcs=Array.isArray(p.sources)?p.sources:[];
 if(srcs.length<2||srcs.length>8)continue;
 if(!/^MESH_QUEUE\/KIT\/LANES\/D0\d\d_LANE_PROFILE_v\d+\.md$/.test(String(srcs[0].path))||!String(srcs[0].path).includes(lane+'_LANE_PROFILE'))continue;
 if(!/^MESH_QUEUE\/KIT\/LANES\/CORE_D000_D001_D002_PROFILE_v\d+\.md$/.test(String(srcs[1].path)))continue;
 if(!srcs.every(s=>s&&/^[A-Za-z0-9_\/.\-]+$/.test(String(s.path||''))&&/^[a-f0-9]{64}$/.test(String(s.sha256||''))&&!String(s.path).includes('..')))continue;
 out.push({json:{lane,packet_path:meta.packet_path,packet_sha256:pkSha,packet_bytes:buf.length,packet:p,expected_return:er,return_name:er.split('/').pop(),return_check_url:fileUrl(er)+'?$select=Name'}});
}
return out;
