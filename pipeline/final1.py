exec(open('an4c.py').read().split("res={}")[0])
rng=np.random.default_rng(11)
matches=np.sort(b.match_id.unique()); M=len(matches); midx={m:i for i,m in enumerate(matches)}
OUT={}
for role in ['bat','bowl']:
    u,ids,a,el,sc,v=run(role)
    base=pd.DataFrame({'pid':ids,'name':[NAME[i] for i in ids],'press_balls':a['cp'],'press_inn':a['ninn'],'eff_press_balls':a['Np'],**{k:sc[k] for k in ['level','cons','ret','base','prior','comp','prs']},'eligible':el})
    mi=u.match_id.map(midx).values; E=np.where(el)[0]
    ranks=[]
    for r in range(500):
        c=np.bincount(rng.integers(0,M,M),minlength=M).astype(float)
        _,a2=agg(u,cw=c[mi]); s2=score(a2,*v,el,role=role); ranks.append(pd.Series(s2['comp'])[E].rank(ascending=False).values)
    ranks=np.array(ranks)
    base.loc[el,'rank_lo']=np.percentile(ranks,5,0); base.loc[el,'rank_hi']=np.percentile(ranks,95,0); base.loc[el,'p_top10']=(ranks<=10).mean(0)
    # split-half, 20 random match splits
    ia=pd.Series(range(len(ids)),index=ids)
    def aligned(uu):
        ids_u,aa_=agg(uu); out_={k:np.zeros(len(ids)) for k in aa_}; pos=ia[ids_u].values
        for k in aa_: out_[k][pos]=aa_[k]
        return out_
    rels={k:[] for k in ['level','cons','ret','comp']}; top10ov=[]
    for r in range(30):
        sel=rng.random(M)<.5; hv=sel[mi]
        s1=score(aligned(u[hv]),*v,el,role=role);s2=score(aligned(u[~hv]),*v,el,role=role)
        for k in rels: rels[k].append(np.corrcoef(s1[k][el],s2[k][el])[0,1])
        t1=set(np.argsort(-s1['comp'][el])[:10]);t2=set(np.argsort(-s2['comp'][el])[:10]); top10ov.append(len(t1&t2))
    rel={k:float(np.mean(x)) for k,x in rels.items()}; rel['top10_overlap_halves']=float(np.mean(top10ov))
    # robustness
    ser=pd.Series(sc['comp'],index=ids); T0=set(ser[el].nlargest(10).index); rob=[]
    for nmx,flag,uw in [('Chase-only pressure','press_chase_only',True),('Top-10% leverage only','press_hi',True),('Rule-based pressure (alternative definition)','press_alt',True),('No opposition weighting','press',False)]:
        u3,ids3,a3,_,s3,_=run(role,flag,uw,elig_ids=ids[el]); s3c=pd.Series(s3['comp'],index=ids3).reindex(ids)
        rob.append(dict(variant=nmx,spearman=float(spearmanr(ser[el],s3c[el]).correlation),top10_overlap=len(T0&set(s3c[el].nlargest(10).index))))
    # alt weights
    for nmx,w_ in [('Equal weights (1/3 each)',dict(level=1/3,cons=1/3,ret=1/3)),('Level only',dict(level=1,cons=0,ret=0))]:
        s3=score(a,*v,el,wts=w_,role=role); s3c=pd.Series(s3['comp'],index=ids)
        rob.append(dict(variant=nmx,spearman=float(spearmanr(ser[el],s3c[el]).correlation),top10_overlap=len(T0&set(s3c[el].nlargest(10).index))))
    print(role,rel); print(pd.DataFrame(rob).round(3).to_string())
    OUT[role]=dict(base=base,rel=rel,rob=rob,u=u,ids=ids,a=a,el=el,v=v,sc=sc)
pickle.dump(OUT,open('out_final.pkl','wb'))
for role in ['bat','bowl']:
    d=OUT[role]['base']; print(d[d.eligible].sort_values('prs',ascending=False).head(15)[['name','press_balls','press_inn','level','cons','ret','prs','rank_lo','rank_hi','p_top10']].round(3).to_string())
pickle.dump(NAME,open('name.pkl','wb'))
