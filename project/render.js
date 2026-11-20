const { chromium } = require('playwright'); const fs=require('fs');
const TL=JSON.parse(fs.readFileSync(process.env.TLF||'timeline.json')); const map=JSON.parse(fs.readFileSync('map.json')); const meta=JSON.parse(fs.readFileSync('shots/meta.json'));
const seg=Object.fromEntries(TL.edl.map(e=>[e.id,e.out]));
const chapters=TL.chapters?null:[
 {t0:seg.S1[0],t1:seg.S1[1],n:'01',label:'Pelaburan'},
 {t0:seg.S2[0],t1:TL.ev.map.t0-0.5,n:'02',label:'Tenaga kerja'},
 {t0:seg.S3[0],t1:TL.ev.jobs.t0-0.5,n:'03',label:'Unjuran pekerjaan'},
 {t0:seg.S5[0],t1:seg.S7[1],n:'04',label:'Ukuran kejayaan'},
];
const data={...TL,map,meta,chapters:TL.chapters||chapters};
(async()=>{
  const mode=process.argv[2]; const out=process.argv[3];
  fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:+(process.env.VW||1920),height:+(process.env.VH||1080)},deviceScaleFactor:1});
  await p.goto('file://'+__dirname+'/'+(process.env.PAGE||'overlay.html'),{waitUntil:'networkidle'});
  await p.evaluate(async d=>{await document.fonts.ready; init(d);}, data);
  await p.waitForTimeout(500);
  let times;
  if(mode==='test') times=process.argv.slice(4).map(Number);
  else { const n=Math.round(TL.total*TL.fps); const a=+(process.argv[4]||0), z=+(process.argv[5]||n); times=[]; for(let i=a;i<z;i++) times.push(i); }
  for(const x of times){
    const t= mode==='test'? x : x/TL.fps;
    await p.evaluate(t=>render(t),t);
    const name= mode==='test'? `t_${t.toFixed(2)}.png` : `f_${String(x).padStart(5,'0')}.png`;
    await p.screenshot({path:`${out}/${name}`,omitBackground:true});
  }
  await b.close();
})();
