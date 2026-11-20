const { chromium } = require('playwright');
const fs=require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
  await p.goto(process.argv[2], { waitUntil: 'networkidle', timeout: 60000 });
  await p.addStyleTag({content: 'img[alt^="Google Announces"]{display:none!important} .social, [class*="share"]{visibility:hidden!important}'});
  await p.waitForTimeout(800);
  const phraseRects = async (phrases) => p.evaluate((phrases) => {
    const res={};
    const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    const nodes=[]; let n; while(n=w.nextNode()) nodes.push(n);
    for (const ph of phrases) {
      for (const node of nodes) { const i=node.textContent.indexOf(ph); if(i>=0){ const r=document.createRange(); r.setStart(node,i); r.setEnd(node,i+ph.length);
          res[ph]=[...r.getClientRects()].map(c=>({x:c.x,y:c.y+scrollY,w:c.width,h:c.height})); break; } }
      if(!res[ph]) res[ph]=null;
    }
    return res; }, phrases);
  const elRect = async (needle) => p.evaluate((needle)=>{ for (const el of document.querySelectorAll('p,li')) if (el.innerText && el.innerText.includes(needle)) { const r=el.getBoundingClientRect(); return {x:r.x,y:r.y+scrollY,w:r.width,h:r.height}; } }, needle);
  const crops = {
    headline: { from:'Google Announces Digital Infrastructure Expansion', to:null, phrases:['US$15 Billion Malaysia Investment','November 4, 2026'] },
    jobs: { from:'The construction phase of Google', to:'Once operational, the facilities', phrases:['support more than 37,000 local jobs per year','more than 9,000 local jobs per year','wages averaging 45% above the national median','contractor roles with local suppliers and workers at the shops, restaurants, and amenities patronized by these employees and their families','data center technicians, mechanical engineers, electrical engineers, logistics operations managers'] },
    suppliers: { from:'domestic supply chain of more than 80', to:null, phrases:['domestic supply chain of more than 80 Malaysian entities','construction and civil engineering; network infrastructure; power and cooling system components; and services like logistics'] },
    dci: { from:'Data Center Institutes', to:null, phrases:['Data Center Institutes (DCIs)','train and place local Technical and Vocational Education and Training (TVET) jobseekers'] },
  };
  const meta={};
  for (const [k,c] of Object.entries(crops)) {
    let r;
    if (k==='headline') r={x:0,y:0,w:1280,h:660};
    else { const a=await elRect(c.from); const z=c.to? await elRect(c.to):a; const y0=a.y-28, y1=z.y+z.h+28; r={x:a.x-40,y:y0,w:a.w+80,h:y1-y0}; }
    await p.screenshot({ path:`shots/${k}.png`, clip:{x:r.x,y:r.y,width:r.w,height:r.h}, fullPage:true });
    const pr=await phraseRects(c.phrases);
    for (const ph in pr) if (pr[ph]) pr[ph]=pr[ph].map(q=>({x:q.x-r.x,y:q.y-r.y,w:q.w,h:q.h}));
    meta[k]={clip:r,phrases:pr};
  }
  fs.writeFileSync('shots/meta.json',JSON.stringify(meta,null,1));
  console.log(JSON.stringify(meta,null,0).slice(0,3000));
  await b.close();
})();
