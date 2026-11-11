/* Shared state, constants and helpers. D/el/meta are filled in by main.js after data/dash.json loads. */
let D,el,meta;
const $=s=>document.querySelector(s);
const TABS=[['over','Overview'],['prof','Player profile'],['cmp','Compare'],['rr','Rajasthan Royals lens'],['how','Method and limits']];
const state={role:'bat',pid:null,a:null,b:null};
const L=r=>r==='bat'?'Batters':'Bowlers';
const col=r=>r==='bat'?'var(--pink)':'var(--blue)';

const elig=r=>el[r].filter(p=>p.eligible).sort((a,b)=>b.prs-a.prs);
const f=(x,n=2)=>x==null?'–':(+x).toFixed(n);
