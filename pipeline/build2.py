import pandas as pd, numpy as np, re, warnings, pickle
warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
import os
S=os.environ.get("WORK_DIR","build")
A=os.environ.get("RAW_DIR","../data_raw")
b=pd.read_csv(f"{S}/ball_by_ball.csv",low_memory=False)
m=pd.read_csv(f"{A}/matches.csv")
comp=pd.read_csv(f"{A}/competitions.csv")
m=m.merge(comp[['comp_id','comp_name','match_format']],on='comp_id')
# keep decided matches with 2 regular innings
ok=m[m.win_team_id.notna()].match_id
b=b[b.match_id.isin(ok)&(b.innings<=2)].copy()
inns=b.groupby('match_id').innings.nunique(); b=b[b.match_id.isin(inns[inns==2].index)]
b=b.merge(m[['match_id','win_team_id','first_inn_revised_overs','second_inn_revised_overs','revised_target','match_format','comp_name','match_date','stage','knock_out','home_team_id','away_team_id']],on='match_id')
b=b.sort_values(['match_id','innings','innings_ball_num']).reset_index(drop=True)
et=b.extras_type.fillna('none')
b['et']=et
b['legal']=(~et.isin(['wide','Overstep'])).astype(int)
ex=np.select([et=='wide',et=='Overstep',et.isin(['legbyes','byes']),et=='Penalty',et=='other'],[1+b.extras_2_runs,1+b.extras_2_runs,1.5,5,1],0)
b['ex_run']=ex; b['tot']=b.runs+ex
b['wk_ball']=b.is_wicket.astype(int)
g=b.groupby(['match_id','innings'])
b['R']=g.tot.cumsum()-b.tot; b['W']=g.wk_ball.cumsum()-b.wk_ball; b['L']=g.legal.cumsum()-b.legal
tot1=b[b.innings==1].groupby('match_id').tot.sum()
b['T']=np.where(b.innings==1,b.first_inn_revised_overs.fillna(20)*6,b.second_inn_revised_overs.fillna(20)*6)
T2=b[b.innings==2].groupby('match_id')['T'].first(); b['T2']=b.match_id.map(T2)
b['Tg']=np.where(b.revised_target.notna(),b.revised_target,b.match_id.map(tot1)+1)
b['ipl']=(b.match_format=='T20').astype(int)
b['fold']=(b.match_id*2654435761 % 2**32 // 7)%5
b['bat_wins']=(b.win_team_id==b.batting_team_id).astype(int)
print(len(b),b.match_id.nunique())
FE1=['bl','R','W','ipl','crr']; FE2=['bl','need','W','rrr','ipl','T']
def f1(R,W,L,T,ipl): bl=np.maximum(T-L,0); return np.c_[bl,R,W,ipl,R*6/(L+6)]
def f2(R,W,L,T,Tg,ipl): bl=np.maximum(T-L,1); need=Tg-R; return np.c_[bl,need,W,need/bl*6,ipl,T]
# train
M1={};M2={}
d1=b[(b.innings==1)&(b.legal==1)]; d2=b[(b.innings==2)&(b.legal==1)]
X1=f1(d1.R.values,d1.W.values,d1.L.values,d1['T'].values,d1.ipl.values); y1=d1.bat_wins.values
X2=f2(d2.R.values,d2.W.values,d2.L.values,d2['T'].values,d2.Tg.values,d2.ipl.values); y2=d2.bat_wins.values
mc1=[1,1,-1,0,1]; mc2=[1,-1,-1,-1,0,0]
for k in range(5):
    t1=(d1.fold!=k).values; t2=(d2.fold!=k).values
    M1[k]=HGB(max_depth=4,learning_rate=0.05,max_iter=150,min_samples_leaf=400,l2_regularization=5,monotonic_cst=mc1,random_state=0).fit(X1[t1],y1[t1])
    M2[k]=HGB(max_depth=5,learning_rate=0.05,max_iter=200,min_samples_leaf=300,l2_regularization=5,monotonic_cst=mc2,random_state=0).fit(X2[t2],y2[t2])
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
p1=np.zeros(len(d1));p2=np.zeros(len(d2))
for k in range(5):
    s=(d1.fold==k).values; p1[s]=M1[k].predict_proba(X1[s])[:,1]
    s=(d2.fold==k).values; p2[s]=M2[k].predict_proba(X2[s])[:,1]
cal={}
for nm_,p,y in [('inn1',p1,y1),('inn2',p2,y2)]:
    cal[nm_]=dict(auc=roc_auc_score(y,p),brier=brier_score_loss(y,p),base_brier=brier_score_loss(y,np.full(len(y),y.mean())),ll=log_loss(y,p))
    print(nm_,cal[nm_])
# calibration table inn2
q=pd.DataFrame({'p':p2,'y':y2}); q['bin']=pd.cut(q.p,[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]); print(q.groupby('bin').agg(n=('y','size'),pred=('p','mean'),act=('y','mean')))
q=pd.DataFrame({'p':p1,'y':y1}); q['bin']=pd.cut(q.p,[0,.2,.35,.5,.65,.8,1.0]); print(q.groupby('bin').agg(n=('y','size'),pred=('p','mean'),act=('y','mean')))
pickle.dump(cal,open('cal.pkl','wb'))
fold=b.fold.values; inn=b.innings.values; ipl=b.ipl.values
def wp(R,W,L,T,Tg,T2):
    R=np.asarray(R,float);W=np.asarray(W);L=np.asarray(L);out=np.zeros(len(b))
    i2=inn==2; i1=~i2
    # innings 2
    need=Tg-R; bl=T-L
    win=i2&(need<=0); lose=i2&(need>0)&((W>=10)|(bl<=0)); live2=i2&~win&~lose
    out[win]=1; out[lose]=0
    for k in range(5):
        s=live2&(fold==k)
        if s.any(): out[s]=M2[k].predict_proba(f2(R[s],W[s],L[s],T[s],Tg[s],ipl[s]))[:,1]
    # innings 1
    term=i1&((W>=10)|(L>=T)); live1=i1&~term
    for k in range(5):
        s=live1&(fold==k)
        if s.any(): out[s]=M1[k].predict_proba(f1(R[s],W[s],L[s],T[s],ipl[s]))[:,1]
        s=term&(fold==k)
        if s.any():
            z=np.zeros(s.sum()); out[s]=1-M2[k].predict_proba(f2(R[s]*0+0,z.astype(int),(L[s]*0),T2[s],R[s]+1,ipl[s]))[:,1]
    return out
R=b.R.values;W=b.W.values;L=b.L.values;T=b['T'].values;Tg=b.Tg.values;T2v=b.T2.values;lg=b.legal.values
wp0=wp(R,W,L,T,Tg,T2v); b['wp0']=wp0
# outcome distribution table
b['phase']=np.where(b.overid<=6,0,np.where(b.overid<=15,1,2)); b['wb']=np.where(b.W<=2,0,np.where(b.W<=5,1,2))
lb=b[b.legal==1]
outs=[0,1,2,3,4,6]
tab={}
for (i,ph,wb),gg in lb.groupby(['innings','phase','wb']):
    pw=gg.is_wicket.mean(); nw=gg[~gg.is_wicket]; pr=nw.tot.round().clip(0,6).value_counts(normalize=True)
    pr=pr.reindex(range(7)).fillna(0); pr[5]=0; pr[6]+=0
    # map 5->4? (5 rare): fold into 4 and 6 equally
    pr[4]+=pr[5]/2; pr[6]+=pr[5]/2
    pr=pr.drop(5); pr=pr/pr.sum()*(1-pw); tab[(i,ph,wb)]=(pr.values,pw)
probs=np.zeros((len(b),7)); 
for idx,((i,ph,wb)) in enumerate(zip(b.innings,b.phase,b.wb)): pass
key=list(zip(b.innings,b.phase,b.wb))
P=np.array([np.r_[tab[k][0],tab[k][1]] for k in pd.unique(pd.Series(key))]); kmap={k:i for i,k in enumerate(pd.unique(pd.Series(key)))}
ki=np.array([kmap[k] for k in key]); probs=P[ki]
runs_o=[0,1,2,3,4,6]
ev=np.zeros((len(b),7))
for j in range(7):
    if j<6: ev[:,j]=wp(R+runs_o[j],W,L+1,T,Tg,T2v)
    else: ev[:,j]=wp(R,W+1,L+1,T,Tg,T2v)
b['li_raw']=(probs*np.abs(ev-wp0[:,None])).sum(1)
b.loc[b.legal==0,'li_raw']=np.nan
# actual after-states
isw=b.is_wicket.values; dis=b.dismissed_player_id.values; dt=b.dismissal_type.fillna('').values
bowl_cred=isw&np.isin(dt,['Caught','Bowled','LBW','Stump','Hit Wicket'])
bat_out=isw&(dis==b.striker_id.values)&(dt!='Retire Out')
Lp=L+lg
full=wp(R+b.tot.values,W+isw.astype(int),Lp,T,Tg,T2v)
bowl=wp(R+b.runs.values+np.where(np.isin(b.et,['wide','Overstep']),b.ex_run.values,0),W+bowl_cred.astype(int),Lp,T,Tg,T2v)
bat=wp(R+b.runs.values,W+bat_out.astype(int),Lp,T,Tg,T2v)
b['wp_full']=full
b['d_bat']=bat-wp0     # batting-side WP change attributable to striker
b['d_bowl']=-(bowl-wp0)  # fielding-side WP change attributable to bowler
b['bowl_cred']=bowl_cred; b['bat_out']=bat_out
b.to_pickle('balls.pkl'); pickle.dump(tab,open('tab.pkl','wb'))
print(b[['wp0','li_raw','d_bat','d_bowl']].describe())
