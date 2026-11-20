const topo=require('world-atlas/countries-50m.json'); const {feature}=require('topojson-client');
const fs=require('fs');
const fc=feature(topo,topo.objects.countries);
const B={lon0:99.4,lon1:104.8,lat0:0.95,lat1:6.9}; const W=900;
const k=Math.cos(3.9*Math.PI/180); const sx=W/((B.lon1-B.lon0)*k); const H=(B.lat1-B.lat0)*sx;
const P=([lon,lat])=>[((lon-B.lon0)*k*sx).toFixed(1),((B.lat1-lat)*sx).toFixed(1)];
const out={W,H:+H.toFixed(1),paths:{}, pts:{}};
for (const f of fc.features){ const n=f.properties.name; if(!['Malaysia','Thailand','Indonesia','Singapore'].includes(n)) continue;
  const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates; let d='';
  for (const poly of polys){ for (const ring of poly){ if(!ring.some(([lo,la])=>lo>B.lon0-3&&lo<B.lon1+3&&la>B.lat0-3&&la<B.lat1+3)) continue; d+='M'+ring.map(P).map(p=>p.join(',')).join('L')+'Z'; } }
  out.paths[n]=d; }
// approximate locations (state level for planned campuses)
const pts={elmina:[101.50,3.19], selangor:[101.43,3.33], ns:[101.94,2.72], kl:[101.69,3.14]};
for (const [k2,v] of Object.entries(pts)) out.pts[k2]=P(v).map(Number);
fs.writeFileSync('map.json',JSON.stringify(out)); console.log(out.W,out.H,Object.keys(out.paths).map(k=>k+':'+out.paths[k].length), out.pts);
