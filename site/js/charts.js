/* SVG chart builders (no external libraries). */
/* ---------- charts ---------- */
function barsSVG(rows,opts={}){ // rows:[label,value,detail]
 const W=640,H=Math.max(160,rows.length*0+opts.h||200),m={l:46,r:10,t:14,b:44};const n=rows.length;if(!n)return '<p class="muted">No data.</p>';
 const vs=rows.map(r=>r[1]),mx=Math.max(.5,...vs.map(Math.abs)),y0=H-m.b,ph=H-m.t-m.b;const sc=v=>m.t+ph/2-(v/mx)*(ph/2);
 const bw=Math.min(22,(W-m.l-m.r)/n*.7),step=(W-m.l-m.r)/n;
 let s=`<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${opts.label||'chart'}">`;
 [-mx,-mx/2,0,mx/2,mx].forEach(t=>{s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${sc(t)}" y2="${sc(t)}" stroke="var(--grid)"/><text x="${m.l-6}" y="${sc(t)+4}" text-anchor="end">${t.toFixed(1)}</text>`});
 s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${sc(0)}" y2="${sc(0)}" stroke="var(--muted)"/>`;
 rows.forEach((r,i)=>{const x=m.l+step*i+step/2-bw/2,v=r[1],y=sc(Math.max(v,0)),h=Math.abs(sc(v)-sc(0));
  s+=`<rect x="${x}" y="${y}" width="${bw}" height="${Math.max(h,1)}" rx="3" fill="${v>=0?opts.c||'var(--pink)':'var(--muted)'}"><title>${r[2]||r[0]}: ${v.toFixed(2)}</title></rect>`;
  if(n<=24||i%Math.ceil(n/24)===0)s+=`<text x="${x+bw/2}" y="${H-m.b+14}" text-anchor="middle" transform="rotate(-40 ${x+bw/2} ${H-m.b+14})" style="font-size:9px">${r[0]}</text>`});
 return s+`<text x="12" y="${H/2}" transform="rotate(-90 12 ${H/2})" text-anchor="middle">${opts.y||''}</text></svg>`}
function dumbbell(items,c){ // [label, pressure, ordinary, fmt]
 const W=640,rh=34,H=items.length*rh+30;let s=`<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Pressure versus ordinary">`;
 items.forEach((it,i)=>{const [lab,p,o,dp,hi]=it;const mx=Math.max(p,o)*1.25,x=v=>150+(v/mx)*(W-190),y=i*rh+22;
  s+=`<text x="0" y="${y+4}" class="t">${lab}</text><line x1="${x(0)}" x2="${W-30}" y1="${y}" y2="${y}" stroke="var(--grid)"/><line x1="${x(p)}" x2="${x(o)}" y1="${y}" y2="${y}" stroke="var(--muted)" stroke-width="2"/><circle cx="${x(o)}" cy="${y}" r="6" fill="var(--muted)"><title>Ordinary: ${o}</title></circle><circle cx="${x(p)}" cy="${y}" r="6" fill="${c}" stroke="var(--surface)" stroke-width="2"><title>Pressure: ${p}</title></circle><text x="${Math.max(x(p),x(o))+10}" y="${y+4}">${p} vs ${o}</text>`});
 return s+'</svg><div class="leg"><span><i style="background:'+c+'"></i>Under pressure</span><span><i style="background:var(--muted)"></i>Ordinary balls</span></div>'}
