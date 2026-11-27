const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const res=[];
for(const f of fs.readdirSync('/tmp/cf/out').filter(x=>x.endsWith('.html'))){
 for(const w of [390,1024]){
  const pg=await b.newPage({viewport:{width:w,height:800},deviceScaleFactor:1});
  await pg.goto('file:///tmp/cf/out/'+f);
  const m=await pg.evaluate(()=>{
   const r=e=>e?e.getBoundingClientRect():null;
   const panel=document.querySelector('.syn-enable-panel'),list=document.querySelector('.o_action_manager');
   const rec=document.querySelector('[data-slot=records]');
   const clipped=[...document.querySelectorAll('.syn-sc *')].filter(e=>e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).overflow!=='visible'&&e.children.length===0).map(e=>e.textContent.trim().slice(0,40));
   const hidden=[...document.querySelectorAll('.syn-sc .tt th,.syn-sc .tt td')].filter(e=>getComputedStyle(e).display==='none').length;
   return {docScrollW:document.documentElement.scrollWidth,vw:innerWidth,panelTop:r(panel).top,panelBottom:r(panel).bottom,listTop:r(list).top,
    panelAboveList:r(panel).bottom<=r(list).top+1,panelH:r(panel).height,recTop:rec?r(rec).top:null,clipped,hiddenTrustCells:hidden,
    panelScrolls:panel.scrollHeight>panel.clientHeight+1,btnMin:Math.min(...[...document.querySelectorAll('.btn')].map(e=>r(e).height))};});
  res.push({f,w,...m});
  if(f.includes('SERVICE_NOUN_enrich')||f.includes('SERVICE_NOUN_enable')||f.includes('MEASURES_MENU_enable')) await pg.screenshot({path:'/tmp/cf/out/'+f.replace('.html','')+'_'+w+'.png'});
  await pg.close();}}
fs.writeFileSync('/tmp/cf/out/metrics.json',JSON.stringify(res,null,1));
for(const r of res)console.log(r.f.padEnd(34),r.w,'overflowX',r.docScrollW>r.vw,'above',r.panelAboveList,'panelH',Math.round(r.panelH),'scrolls',r.panelScrolls,'clipped',r.clipped.length,'hiddenCells',r.hiddenTrustCells,'btnH',r.btnMin);
await b.close();})();
