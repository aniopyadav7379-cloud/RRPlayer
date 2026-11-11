import pandas as pd, numpy as np, pickle, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
PINK='#E6007E'; BLUE='#254AA5'; GR='#6b7280'
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9ca3af','axes.grid':True,'grid.color':'#e5e7eb','grid.linewidth':.6,'axes.axisbelow':True})
T=pickle.load(open('tables.pkl','rb')); v=pd.read_csv('out_pressure_validation.csv'); vp=pd.read_csv('out_pressure_validation_phase.csv')
# 1 validation
fig,ax=plt.subplots(1,2,figsize=(9,3.6),dpi=200)
lab=['1st innings','2nd innings (chase)']; x=np.arange(2)
for j,(p,c,nm) in enumerate([(False,GR,'Ordinary'),(True,PINK,'Pressure')]):
    y=[v[(v.innings==i)&(v.press==p)]['mean |ΔWP| per ball'].iloc[0]*100 for i in (1,2)]
    r=ax[0].bar(x+(j-.5)*.38,y,.34,color=c,label=nm)
    for xx,yy in zip(x+(j-.5)*.38,y): ax[0].text(xx,yy+.07,f'{yy:.2f}',ha='center',fontsize=8)
ax[0].set_xticks(x);ax[0].set_xticklabels(lab);ax[0].set_ylabel('Mean win-probability swing per ball (pp)');ax[0].set_title('Pressure balls carry 3–5× the swing',fontsize=10,loc='left');ax[0].legend(frameon=False,fontsize=8)
y=[29.0,79.2]; ax[1].bar([0,1],y,.5,color=[GR,PINK])
for i,yy in enumerate(y): ax[1].text(i,yy+1.5,f'{yy:.0f}%',ha='center',fontsize=9)
ax[1].set_xticks([0,1]);ax[1].set_xticklabels(['Ordinary','Pressure']);ax[1].set_ylabel('% of chase balls with win prob. 20–80%');ax[1].set_title('Pressure balls are genuinely close contests',fontsize=10,loc='left');ax[1].set_ylim(0,95)
plt.tight_layout();plt.savefig('figs/validation.png');plt.close()
# 2 calibration
pred=[.033,.148,.249,.350,.450,.552,.650,.753,.852,.965]; act=[.035,.165,.274,.359,.451,.554,.660,.729,.807,.961]
fig,ax=plt.subplots(figsize=(4.2,3.8),dpi=200); ax.plot([0,1],[0,1],color=GR,ls='--',lw=1,label='Perfect calibration');ax.plot(pred,act,'o-',color=BLUE,lw=2,ms=5,label='Chase model (out-of-sample)')
ax.set_xlabel('Predicted win probability');ax.set_ylabel('Observed win frequency');ax.legend(frameon=False,fontsize=8);ax.set_title('Win-probability model calibration (chase)',fontsize=10,loc='left')
plt.tight_layout();plt.savefig('figs/calib.png');plt.close()
# 3/4 top10
for role,col,title in [('bat',PINK,'Top-10 batters under pressure'),('bowl',BLUE,'Top-10 bowlers under pressure')]:
    t=T[role]; t=t[t.eligible].sort_values('prs',ascending=False).head(10)[::-1]
    fig,ax=plt.subplots(figsize=(8,4.4),dpi=200)
    ax.barh(t.name,t.prs,color=col,height=.62)
    for yy,(p,lo,hi,p10) in enumerate(zip(t.prs,t.rank_lo,t.rank_hi,t.p_top10)): ax.text(p+.5,yy,f'{p:.1f}   (90% rank band {int(lo)}–{int(hi)}; P(top-10)={p10:.0%})',va='center',fontsize=7.5,color='#374151')
    ax.set_xlim(50,max(t.prs)+30);ax.set_xlabel('Pressure Reliability Score (50 = average eligible player; 10 = 1 SD)');ax.set_title(title,fontsize=11,loc='left');ax.grid(axis='y',visible=False)
    plt.tight_layout();plt.savefig(f'figs/top10_{role}.png');plt.close()
# 5 scatter
for role,col in [('bat',PINK),('bowl',BLUE)]:
    t=T[role]; e=t[t.eligible]
    fig,ax=plt.subplots(figsize=(6.2,4.4),dpi=200)
    ax.scatter(e.base,e.level,s=e.press_balls/6,color=col,alpha=.45,edgecolor='white',lw=.5)
    top=e.sort_values('prs',ascending=False).head(10)
    ax.scatter(top.base,top.level,s=top.press_balls/6,color=col,edgecolor='black',lw=.8)
    for r in top.itertuples(): ax.annotate(r.name.split()[-1],(r.base,r.level),fontsize=7,xytext=(3,3),textcoords='offset points')
    ax.axhline(0,color=GR,lw=.8);ax.axvline(0,color=GR,lw=.8)
    ax.set_xlabel('Usual (ordinary-situation) level, shrunk');ax.set_ylabel('Pressure level, shrunk (win-prob. swing units/ball)')
    ax.set_title(('Batters' if role=='bat' else 'Bowlers')+': usual level vs pressure level (bubble = pressure balls)',fontsize=9,loc='left')
    plt.tight_layout();plt.savefig(f'figs/scatter_{role}.png');plt.close()
for role in ['bat','bowl']:
    t=T[role]; print(role); print(t[t.eligible].head(10)[['name','team','press_balls','press_inn','prs','level','cons','ret','rank_lo','rank_hi','p_top10']].round(3).to_string())
