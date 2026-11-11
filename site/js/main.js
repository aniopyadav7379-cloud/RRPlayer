function tabs(){const t=$('#tabs');t.innerHTML=TABS.map(([k,v])=>`<button role="tab" data-k="${k}" aria-selected="${k==='over'}">${v}</button>`).join('');
t.onclick=e=>{const k=e.target.dataset.k;if(!k)return;show(k)}}
function show(k){TABS.forEach(([x])=>{$('#s-'+x).hidden=x!==k});document.querySelectorAll('#tabs button').forEach(b=>b.setAttribute('aria-selected',b.dataset.k===k));render[k]();try{history.replaceState(null,'','#'+k)}catch(e){}}
function seg(id,val,opts,fn){return `<div class="seg" id="${id}">${opts.map(([k,v])=>`<button data-k="${k}" aria-pressed="${k===val}">${v}</button>`).join('')}</div>`}
function bindSeg(id,fn){$('#'+id).onclick=e=>{if(e.target.dataset.k)fn(e.target.dataset.k)}}

async function boot(){
  try{
    const res=await fetch('data/dash.json');
    if(!res.ok)throw new Error('HTTP '+res.status);
    D=await res.json();el=D.data;meta=D.meta;
  }catch(err){
    document.getElementById('s-over').innerHTML='<div class="note">Could not load <code>data/dash.json</code> ('+err.message+'). Serve this folder over HTTP (for example <code>python3 -m http.server</code>); opening index.html directly from disk blocks the data request.</div>';
    return;
  }
  tabs();
  const h=(location.hash||'').slice(1);
  show(TABS.some(t=>t[0]===h)?h:'over');
}
boot();
