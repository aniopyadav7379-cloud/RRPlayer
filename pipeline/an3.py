import pandas as pd, numpy as np, pickle, warnings, scipy.sparse as sp
warnings.filterwarnings('ignore')
import os
S=os.environ.get("WORK_DIR","build")
A=os.environ.get("RAW_DIR","../data_raw")
b=pd.read_pickle('balls.pkl')
# ---------- pressure definition
b['li']=b.groupby(['match_id','innings']).li_raw.transform(lambda s:s.bfill().ffill())
last1=(b.innings==1)&(b.L+b.legal>=b['T'])
b.loc[last1,'li']=np.nan
b['li']=b.groupby(['match_id','innings']).li.transform(lambda s:s.ffill().bfill())
b['phase']=np.where(b.overid<=6,'Powerplay (1-6)',np.where(b.overid<=15,'Middle (7-15)','Death (16-20)'))
b['li_n']=b.li/b.groupby('innings').li.transform('mean')
thr2=b[b.innings==2].li.quantile(.75)
thr1=b[b.innings==1].groupby('phase').li.quantile(.75)
b['thr']=np.where(b.innings==2,thr2,b.phase.map(thr1))
b['press']=b.li>=b.thr
thr2h=b[b.innings==2].li.quantile(.90); thr1h=b[b.innings==1].groupby('phase').li.quantile(.90)
b['press_hi']=b.li>=np.where(b.innings==2,thr2h,b.phase.map(thr1h))
# validation table
lb=b[b.legal==1]
def sm(d): return pd.Series({'balls':len(d),'mean |ΔWP| per ball':d.d_bat.abs().mean(),'runs/ball':d.tot.mean(),'dot %':100*(d.runs==0).mean(),'boundary %':100*(d.is_four|d.is_six).mean(),'wicket %':100*d.is_wicket.mean(),'wickets lost (avg)':d.W.mean(),'balls left (avg)':(d['T']-d.L).mean()})
val=lb.groupby(['innings','press']).apply(sm).round(3).reset_index(); val.to_csv('out_pressure_validation.csv',index=False); print(val.to_string())
# within-phase comparison
vp=lb.groupby(['innings','phase','press']).apply(sm).round(3).reset_index(); vp.to_csv('out_pressure_validation_phase.csv',index=False)
c=lb[lb.innings==2]; c=c.assign(rrr=(c.Tg-c.R)/(c['T']-c.L)*6); print(c.groupby('press')[['rrr']].median(), (c.groupby('press').wp0.apply(lambda s:((s>.2)&(s<.8)).mean())))
b['press_i']=b.groupby(['innings']).press.transform('mean')
# alt rule-based definition
need=b.Tg-b.R; bl=(b['T']-b.L).clip(lower=1); rrr=need/bl*6
alt2=(b.overid>=15)&(b.wp0.between(.2,.8)) | (b.overid.between(7,14)&(b.W>=5)&(b.wp0.between(.2,.8)))
alt1=((b.W>=3)&(b.overid<=10))|((b.W>=5)&(b.overid<=16))|(b.overid>=17)
b['press_alt']=np.where(b.innings==2,alt2,alt1)
b['press_chase_only']=b.press&(b.innings==2)
# opposition weights
assoc={272,283,311,312,313,282,24,26,89,315,3886}; ateam={222,341,3093,3674,4444}
def wt(r):
    s=set(r)
    return 0.5 if s&assoc else (0.75 if s&ateam else 1.0)
mw=b.groupby('match_id').apply(lambda g:wt(set(g.batting_team_id)|set(g.bowling_team_id)))
b['w']=b.match_id.map(mw)
b['npv_bat']=(b.d_bat/b.li.clip(lower=.003)).clip(-6,6); b['npv_bowl']=(b.d_bowl/b.li.clip(lower=.003)).clip(-6,6)
print("winsor:",(b.d_bat/b.li.clip(lower=.003)).abs().gt(6).mean())
b.to_pickle('balls2.pkl'); pickle.dump(dict(thr2=thr2,thr1=thr1.to_dict(),thr2h=thr2h,thr1h=thr1h.to_dict()),open('thr.pkl','wb'))
print(b.groupby('innings').press.mean(), b.groupby(['innings','phase']).press.mean().round(3))
print(mw.value_counts())
