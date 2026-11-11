/* Rule-based strengths and weaknesses from percentile ranks among rated players. */
function pct(arr,v){return arr.filter(x=>x<v).length/arr.length*100}
function insights(p,r){const E=elig(r),S=[],W=[];const pc=(k)=>pct(E.map(x=>x[k]),p[k]);
 const add=(c,s,w)=>{if(c>=70)S.push(s);else if(c<=30)W.push(w)};
 add(pc('level'),`Pressure level in the top ${Math.max(1,Math.round(100-pc('level')))}% of rated ${L(r).toLowerCase()} (${f(p.level,3)}).`,`Pressure level in the bottom ${Math.round(pc('level'))+1}% of rated ${L(r).toLowerCase()} (${f(p.level,3)}).`);
 add(pc('cons'),`Positive contribution in ${Math.round(p.cons*100)}% of pressure innings (consistency).`,`Net-positive in only ${Math.round(p.cons*100)}% of pressure innings (low consistency).`);
 add(pc('ret'),`Rises above their usual level under pressure (retention ${f(p.ret,3)}).`,`Falls below their usual level under pressure (retention ${f(p.ret,3)}).`);
 if(p.p_sr!=null){ if(r==='bat'){const d=p.p_sr-p.o_sr; if(d>8)S.push(`Strike rate holds up: ${p.p_sr} under pressure vs ${p.o_sr} otherwise.`); if(d<-8)W.push(`Strike rate drops under pressure: ${p.p_sr} vs ${p.o_sr}.`); if(p.p_out<p.o_out*.8)S.push(`Dismissed less often under pressure (${p.p_out}% vs ${p.o_out}% of balls).`); if(p.p_out>p.o_out*1.25)W.push(`Dismissed more often under pressure (${p.p_out}% vs ${p.o_out}% of balls).`);}}
 if(p.p_eco!=null){const d=p.p_eco-p.o_eco; if(d<0.3)S.push(`Economy ${p.p_eco} under pressure vs ${p.o_eco} otherwise.`); if(d>1.5)W.push(`Economy rises from ${p.o_eco} to ${p.p_eco} under pressure.`); if(p.p_wk>p.o_wk*1.2)S.push(`Takes wickets more often under pressure (${p.p_wk} vs ${p.o_wk} per 100 balls).`)}
 if(p.chase&&p.setting&&p.chase[1]>=40&&p.setting[1]>=40){ if(p.chase[0]-p.setting[0]>.15)S.push('Stronger in chases than when setting a total.'); if(p.setting[0]-p.chase[0]>.15)S.push('Stronger when setting a total than in chases.')}
 if(!p.eligible)W.push(`Small sample (${p.pb} pressure balls, ${p.pi} innings): treat as indicative only.`);
 return [S,W]}
