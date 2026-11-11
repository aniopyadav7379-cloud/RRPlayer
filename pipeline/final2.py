import os
import pandas as pd, numpy as np, pickle, json, warnings
A=os.environ.get("RAW_DIR","../data_raw")
warnings.filterwarnings('ignore')
b=pd.read_pickle('balls2.pkl'); OUT=pickle.load(open('out_final.pkl','rb')); NAME=pickle.load(open('name.pkl','rb'))
teams=pd.read_csv(A+"/teams.csv").drop_duplicates('team_id').set_index('team_id').team_name.to_dict()
b['date']=pd.to_datetime(b.match_date); b['yr']=b.date.dt.year
b['opp_bat']=b.bowling_team_id.map(teams); b['opp_bowl']=b.batting_team_id.map(teams)
fb=b[b.et!='wide']
last_team={}
for col,df in [('striker_id',b.assign(t=b.batting_team_id)),('bowler_id',b.assign(t=b.bowling_team_id))]:
    x=df.sort_values('date').groupby(col).t.last(); 
    for k,v in x.items(): last_team.setdefault(k,v)
hand=b.groupby('striker_id').batting_type.agg(lambda s:s.mode()[0]); btype=b.groupby('bowler_id').pace_or_spin.agg(lambda s:s.mode()[0]); bstyle=b.groupby('bowler_id').bowling_type.agg(lambda s:s.mode()[0])
fmtshare=b.groupby('striker_id').ipl.mean()
def pct(s,v): return float((s<v).mean()*100)
data={'bat':[], 'bowl':[]}; tables={}
for role in ['bat','bowl']:
    O=OUT[role]; base=O['base'].copy(); ids=O['ids']
    if role=='bat':
        df=fb; pid='striker_id'; d='d_bat'; v='npv_bat'
        df=df.assign(runs_c=df.runs,out=df.bat_out.astype(int),bnd=(df.is_four|df.is_six).astype(int),dot=(df.runs==0).astype(int))
    else:
        df=b; pid='bowler_id'; d='d_bowl'; v='npv_bowl'
        df=df.assign(runs_c=df.runs+np.where(df.et.isin(['wide','Overstep']),df.ex_run,0),out=df.bowl_cred.astype(int),bnd=(df.is_four|df.is_six).astype(int),dot=((df.runs==0)&(df.ex_run==0)).astype(int))
    def desc(g):
        n=len(g); return pd.Series(dict(n=n,runs=g.runs_c.sum(),outs=g.out.sum(),dot=g['dot'].mean()*100,bnd=g['bnd'].mean()*100))
    P=df[df.press].groupby(pid).apply(desc); Oo=df[~df.press].groupby(pid).apply(desc)
    ch=df[df.press&(df.innings==2)].groupby(pid)[v].agg(['mean','size']); st=df[df.press&(df.innings==1)].groupby(pid)[v].agg(['mean','size'])
    yr=df[df.press].groupby([pid,'yr'])[v].agg(['mean','size']).reset_index()
    ph=df[df.press].groupby([pid,'phase'])[v].agg(['mean','size']).reset_index()
    unit=df[df.press].groupby([pid,'match_id','innings']).agg(date=('date','first'),opp=('opp_bat' if role=='bat' else 'opp_bowl','first'),n=('runs_c','size'),runs=('runs_c','sum'),outs=('out','sum'),dwp=(d,'sum'),fmt=('ipl','first')).reset_index()
    el=base[base.eligible]
    keep=base[(base.press_balls>=60)].pid.tolist()
    for _,r in base.iterrows():
        i=r.pid
        if i not in keep: continue
        p=P.loc[i] if i in P.index else None; o=Oo.loc[i] if i in Oo.index else None
        rec=dict(id=int(i),name=r['name'],team=teams.get(last_team.get(i),''),eligible=bool(r.eligible),pb=int(r.press_balls),pi=int(r.press_inn),
          level=round(r.level,4),cons=round(r.cons,3),ret=round(r.ret,4),base=round(r.base,4),prs=round(r.prs,1),
          lo=None if pd.isna(r.rank_lo) else int(r.rank_lo),hi=None if pd.isna(r.rank_hi) else int(r.rank_hi),p10=None if pd.isna(r.p_top10) else round(r.p_top10,2))
        if role=='bat': rec['style']=hand.get(i,'')+' bat'
        else: rec['style']=bstyle.get(i,'')+' ('+btype.get(i,'')+')'
        if p is not None and o is not None:
            if role=='bat':
                rec.update(p_sr=round(100*p.runs/p.n,1),o_sr=round(100*o.runs/o.n,1),p_out=round(100*p.outs/p.n,2),o_out=round(100*o.outs/o.n,2),p_dot=round(p['dot'],1),o_dot=round(o['dot'],1),p_bnd=round(p.bnd,1),o_bnd=round(o.bnd,1))
            else:
                rec.update(p_eco=round(6*p.runs/p.n,2),o_eco=round(6*o.runs/o.n,2),p_wk=round(100*p.outs/p.n,2),o_wk=round(100*o.outs/o.n,2),p_dot=round(p['dot'],1),o_dot=round(o['dot'],1),p_bnd=round(p.bnd,1),o_bnd=round(o.bnd,1))
        rec['chase']=[round(ch.loc[i,'mean'],3),int(ch.loc[i,'size'])] if i in ch.index else None
        rec['setting']=[round(st.loc[i,'mean'],3),int(st.loc[i,'size'])] if i in st.index else None
        rec['yr']=[[int(a),round(b_,3),int(c)] for a,b_,c in yr[yr[pid]==i][['yr','mean','size']].values]
        rec['ph']=[[a,round(b_,3),int(c)] for a,b_,c in ph[ph[pid]==i][['phase','mean','size']].values]
        uu=unit[unit[pid]==i].sort_values('date')
        rec['mm']=[[str(x.date.date()),x.opp,int(x.innings),int(x.n),int(x.runs),int(x.outs),round(x.dwp,3)] for x in uu.itertuples() if x.n>=3]
        data[role].append(rec)
    tab=base.sort_values('prs',ascending=False)
    tab=tab.assign(team=tab.pid.map(lambda i:teams.get(last_team.get(i),'')))
    tables[role]=tab
    tab[tab.eligible].drop(columns=['eligible','comp','eff_press_balls']).round(4).to_csv(f'ranking_{role}.csv',index=False)
    tab.round(4).to_csv(f'all_players_{role}.csv',index=False)
    print(role,len(data[role]),'profiles')
# RR squad IPL 2026
mp=pd.read_csv(A+"/competition_team_player_mapping.csv")
rr=mp[(mp.comp_id==3298)&(mp.team_id==3)]; print(len(rr)); 
rr_ids=set(rr.player_id)
for role in ['bat','bowl']:
    t=tables[role]; print(role,'RR'); print(t[t.pid.isin(rr_ids)].sort_values('prs',ascending=False)[['name','press_balls','eligible','level','prs']].head(12).round(3).to_string())
meta=dict(rr=[int(x) for x in rr_ids],rel={k:OUT[k]['rel'] for k in OUT},rob={k:OUT[k]['rob'] for k in OUT},
  nplayers=int(pd.concat([b.striker_id,b.bowler_id]).nunique()),nballs=int(len(b)),nmatches=int(b.match_id.nunique()),
  nipl=int(b[b.ipl==1].match_id.nunique()),nt20i=int(b[b.ipl==0].match_id.nunique()))
json.dump(dict(data=data,meta=meta),open('dash.json','w'))
pickle.dump(tables,open('tables.pkl','wb')); print(meta['nmatches'],meta['nipl'],meta['nt20i'],meta['nplayers'])
