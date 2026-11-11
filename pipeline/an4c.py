import os
A=os.environ.get("RAW_DIR","../data_raw")
import pandas as pd, numpy as np, pickle, json, warnings
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
b=pd.read_pickle('balls2.pkl')
mp=pd.read_csv(A+"/competition_team_player_mapping.csv")
# ---- names
nm=pd.concat([b[['striker_id','striker_name']].set_axis(['id','n'],axis=1),b[['bowler_id','bowler_name']].set_axis(['id','n'],axis=1)]).drop_duplicates('id')
dupn=nm.n[nm.n.duplicated(keep=False)]; nm['name']=np.where(nm.n.isin(dupn),nm.n+' #'+nm.id.astype(str),nm.n); NAME=nm.set_index('id').name.to_dict()
b['mord']=b.match_id.map(b.groupby('match_id').match_date.first().rank(method='first'))
b['date']=pd.to_datetime(b.match_date)
W_BAT=dict(level=.7,cons=.2,ret=.1)
TAU2={'bat':0.0088,'bowl':0.0042}
ELIG={'bat':dict(balls=150,inn=12),'bowl':dict(balls=150,inn=12)}
def units(role,flag,useW=True):
    if role=='bat': df=b[b.et!='wide']; pid='striker_id'; v='npv_bat'; d='d_bat'
    else: df=b; pid='bowler_id'; v='npv_bowl'; d='d_bowl'
    df=df.assign(_p=df[flag].astype(bool),_w=df.w if useW else 1.0)
    df=df.assign(_pw=df._w*df._p, _ow=df._w*(~df._p), _pv=df._w*df._p*df[v], _ov=df._w*(~df._p)*df[v], _pd=df._p*df[d], _pc=df._p.astype(int))
    u=df.groupby([pid,'match_id','innings']).agg(Np=('_pw','sum'),Sp=('_pv','sum'),No=('_ow','sum'),So=('_ov','sum'),cp=('_pc','sum'),dp=('_pd','sum'),mord=('mord','first')).reset_index().rename(columns={pid:'pid'})
    return u
def eb(S,N,mask,floor=1e-4):
    mu=S[mask].sum()/N[mask].sum()
    m_=np.where(N>0,S/np.maximum(N,1e-9),mu)
    return m_,mu
def shrink(S,N,var_ball,mask):
    mu=S[mask].sum()/N[mask].sum(); mean=S/np.maximum(N,1e-9)
    mk=mask&(N>=30)
    tau2=max(np.var(mean[mk])-np.mean(var_ball/N[mk]),1e-4)
    k=var_ball/tau2
    return (S+k*mu)/(N+k),k
def agg(u,cw=None):
    pid=u.pid.values; ids,inv=np.unique(pid,return_inverse=True)
    w=np.ones(len(u)) if cw is None else cw
    f=lambda x:np.bincount(inv,weights=w*x,minlength=len(ids))
    succ=((u.cp.values>=6)&(u.dp.values>=0)).astype(float); el=(u.cp.values>=6).astype(float)
    return ids,dict(Np=f(u.Np.values),Sp=f(u.Sp.values),No=f(u.No.values),So=f(u.So.values),cp=f(u.cp.values),ninn=f(el),succ=f(succ),npu=f((u.cp.values>0).astype(float)))
def score(a,vp,vo,elig,K=8,wts=None,role='bat'):
    wts=wts or W_BAT
    Np,Sp,No,So=a['Np'],a['Sp'],a['No'],a['So']
    allm=np.ones(len(Np),bool)
    base,ko=shrink(So,No,vo,allm)
    # hierarchical prior: pressure mean ~ a + b*baseline
    mean_p=Sp/np.maximum(Np,1e-9); ok=(Np>=30)
    Xd=np.c_[np.ones(ok.sum()),base[ok]]; w=Np[ok]/(1+Np[ok]/200.)
    beta=np.linalg.lstsq(Xd*np.sqrt(w)[:,None],mean_p[ok]*np.sqrt(w),rcond=None)[0]
    prior=beta[0]+beta[1]*base
    resid=mean_p[ok]-prior[ok]
    tau2=TAU2[role]; k=vp/tau2
    lev=(Sp+k*prior)/(Np+k)
    ret=lev-prior
    p0=a['succ'][allm].sum()/max(a['ninn'][allm].sum(),1)
    cons=(a['succ']+K*p0)/(a['ninn']+K)
    z=lambda x:(x-x[elig].mean())/x[elig].std()
    comp=wts['level']*z(lev)+wts['cons']*z(cons)+wts['ret']*z(ret)
    comp=(comp-comp[elig].mean())/comp[elig].std()
    return dict(level=lev,cons=cons,ret=ret,base=base,prior=prior,comp=comp,prs=50+10*comp,beta1=beta[1],tau2=tau2)
def var_ball(role,flag,useW=True):
    v='npv_bat' if role=='bat' else 'npv_bowl'; df=b[b.et!='wide'] if role=='bat' else b
    return df[df[flag]][v].var(), df[~df[flag]][v].var()
def run(role,flag='press',useW=True,elig_ids=None):
    u=units(role,flag,useW); ids,a=agg(u); vp,vo=var_ball(role,flag)
    el=(a['cp']>=ELIG[role]['balls'])&(a['ninn']>=ELIG[role]['inn']) if elig_ids is None else np.isin(ids,elig_ids)
    return u,ids,a,el,score(a,vp,vo,el,role=role),(vp,vo)
res={}
for role in ['bat','bowl']:
    u,ids,a,el,sc,v=run(role)
    df=pd.DataFrame({'pid':ids,'name':[NAME[i] for i in ids],'press_balls':a['cp'],'press_inn':a['ninn'],'eff_press_balls':a['Np'],**{k:sc[k] for k in sc},'eligible':el})
    res[role]=(u,df,a,v,ids)
    print(role,"eligible",el.sum(),"of",len(ids),"| var",v)
    print(df[df.eligible].sort_values('prs',ascending=False).head(15)[['name','press_balls','press_inn','level','cons','ret','prs']].round(3).to_string())
pickle.dump(res,open('res.pkl','wb')); pickle.dump(NAME,open('name.pkl','wb'))
