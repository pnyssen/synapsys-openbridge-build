const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for(const w of[390,1024]){const pg=await b.newPage({viewport:{width:w,height:900},deviceScaleFactor:1});await pg.goto('file:///tmp/cf/specimen.html');
const m=await pg.evaluate(()=>({overflowX:document.documentElement.scrollWidth>innerWidth,minBtn:Math.min(...[...document.querySelectorAll('button')].map(e=>e.getBoundingClientRect().height)),recTop:Math.round(document.querySelector('.rec').getBoundingClientRect().top),h:document.documentElement.scrollHeight}));
console.log(w,JSON.stringify(m));await pg.screenshot({path:'/tmp/cf/out/specimen_'+w+'.png',fullPage:true});}
await b.close()})();
