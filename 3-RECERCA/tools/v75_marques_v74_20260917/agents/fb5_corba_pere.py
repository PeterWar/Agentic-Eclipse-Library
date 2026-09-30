"""fb5: RAW Vixen 10 s absolut al marc de la ROI (3 CR3), corba monòtona f: RAW→P (revelat de Pere reconstruït), residu, pendent local; perfils per sector del RAW absolut."""
import sys, json, numpy as np
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,OLD); import esceptic_comu as ec
from scipy.ndimage import gaussian_filter, median as ndmed
from scipy.optimize import isotonic_regression
CX,CY,RS=998.88,998.41,456.0
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360; sec=(az//5).astype(int)
ref=np.load(OLD+'/raw_disc_norm_2000.npy'); refv=np.isfinite(ref)&(rr<0.9*RS)
acc=[]; info=[]
for fr in ('572A2982','572A2983','572A2984'):
    d=ec.llegeix(fr); Lum=d['Y']; cx,cy,R,rms=ec.troba_lluna(Lum)
    best=None
    for phi in (11.0,-11.0):
        M=ec.cap_al_compost(Lum,cx,cy,R,phi); Mn=np.where(rr<0.95*RS,M,np.nan)
        # normalitza per anells per comparar amb la referència a26
        prof=np.array([np.nanmedian(Mn[(rr>=k)&(rr<k+2)]) for k in range(0,440,2)]); rad=np.interp(rr,np.arange(0,440,2)+1,prof); Nn=Mn/rad
        c=np.corrcoef(np.nan_to_num(Nn[refv]-1),ref[refv]-1)[0,1]
        if best is None or c>best[0]: best=(c,phi,M)
    print(fr,'centre',round(cx,2),round(cy,2),'R',round(R,2),'phi',best[1],'corr amb a26',round(best[0],3)); acc.append(best[2]); info.append(dict(frame=fr,cx=float(cx),cy=float(cy),R=float(R),phi=best[1],corr_a26=float(best[0])))
RAW=np.mean(acc,0); RAW[rr>=RS+30]=np.nan; np.save(S4+'/fb5_raw10s_abs_roi.npy',RAW.astype(np.float32))
P=np.load(S4+'/fb3_P_rec.npy').astype(np.float64); G69=np.load(OLD+'/roi_L30.npz')['c1'].astype(np.float64)
disc=(rr<430)&np.isfinite(RAW)
print('RAW disc: mediana %.1f p1 %.1f p99 %.1f (DN14−negre, mitjana 2×2)'%(np.median(RAW[disc]),*np.percentile(RAW[disc],[1,99])))
# corba f: RAW→P (suavitzant el RAW σ3 per treure el soroll fotònic abans de la regressió; P té textura pròpia)
RAWs=gaussian_filter(np.nan_to_num(RAW),3); Ps=gaussian_filter(P,3)
x=RAWs[disc]; y=Ps[disc]; o=np.argsort(x); xs=x[o]; ys=y[o]
nb=300; edges=np.quantile(xs,np.linspace(0,1,nb+1)); xc=np.array([xs[(xs>=a)&(xs<=b)].mean() for a,b in zip(edges[:-1],edges[1:])]); yc=np.array([np.median(ys[(xs>=a)&(xs<=b)]) for a,b in zip(edges[:-1],edges[1:])])
yi=isotonic_regression(yc).x
def f(v): return np.interp(v,xc,yi)
fR=f(RAWs); res=Ps-fR
r2=1-np.var(res[disc])/np.var(Ps[disc]); print('f monòtona: R² %.3f ; rms residu %.0f DN16 (σ3)'%(r2,np.std(res[disc])))
# pendent local de f: γ = dlnP/dlnRAW als nivells de la taca i del limbe
def gamma(v): 
    h=v*0.01; return (np.log(f(v+h))-np.log(f(v-h)))/(np.log(v+h)-np.log(v-h))
M=np.load(S4+'/marques74_masks.npz'); m6=M['m6']; e6=M['ent_m6']
lv_t=np.median(RAWs[m6]); lv_e=np.median(RAWs[e6]); lv_lim=np.median(RAWs[(rr>390)&(rr<410)]); lv_c=np.median(RAWs[rr<100])
print('nivell RAW: taca %.1f entorn %.1f centre %.1f r400 %.1f ; γ(taca) %.1f γ(entorn) %.1f γ(centre) %.1f γ(r400) %.1f'%(lv_t,lv_e,lv_c,lv_lim,gamma(lv_t),gamma(lv_e),gamma(lv_c),gamma(lv_lim)))
out=dict(frames=info,R2=float(r2),rms_residu=float(np.std(res[disc])),nivells_raw=dict(taca=float(lv_t),entorn=float(lv_e),centre=float(lv_c),r400=float(lv_lim)),gamma=dict(taca=float(gamma(lv_t)),entorn=float(gamma(lv_e)),centre=float(gamma(lv_c)),r400=float(gamma(lv_lim))),corba=dict(raw=[float(v) for v in xc[::10]],P=[float(v) for v in yi[::10]]))
# la taca: dins/entorn a RAW, f(RAW), P, residu, capa
def lnr(A): return float(np.log(np.median(A[m6])/np.median(A[e6])))
out['taca_ln_dins_entorn']=dict(RAW=lnr(RAWs),f_RAW=lnr(fR),P=lnr(Ps),capa_V69=lnr(G69),residu_DN16=float(np.median(res[m6])-np.median(res[e6])))
print('taca ln(dins/entorn): RAW %.4f · f(RAW) %.4f · P %.4f · capa V69 %.4f · residu (DN16) %.0f'%(lnr(RAWs),lnr(fR),lnr(Ps),lnr(G69),out['taca_ln_dins_entorn']['residu_DN16']))
# perfils per sector (mediana bins 2 px): RAW abs, f(RAW), P ; taca vs veïns
rb=np.arange(100,454,2); rc=rb[:-1]+1; NS=72
def perfils(A):
    ib=((rr-100)//2).astype(int); ok=(rr>=100)&(rr<452)&np.isfinite(A)
    lab=sec[ok]*len(rc)+ib[ok]; cnt=np.bincount(lab,minlength=NS*len(rc)); med=ndmed(A[ok],labels=lab,index=np.arange(NS*len(rc)))
    return np.where(cnt>=6,med,np.nan).reshape(NS,len(rc))
PR=perfils(np.where(np.isfinite(RAW),RAW,np.nan)); PF=perfils(fR); PP=perfils(P)
T=list(range(48,54)); VV=list(range(42,48))+list(range(54,60)); g=lambda A,i: np.nanmedian(A[i],0)
i200=np.argmin(np.abs(rc-201)); rows=[]
print(' r   RAW_t/RAW_t200 RAW_v/RAW_v200 | ln RAW t/v | f(RAW)_t/200 f_v/200 | ln f t/v | ln P t/v')
for i in range(0,len(rc),10):
    rt,rv=g(PR,T),g(PR,VV); ft,fv=g(PF,T),g(PF,VV); pt,pv=g(PP,T),g(PP,VV)
    row=dict(r=int(rc[i]),RAW_t_rel=round(float(rt[i]/rt[i200]),4),RAW_v_rel=round(float(rv[i]/rv[i200]),4),ln_RAW_tv=round(float(np.log(rt[i]/rv[i])),4),f_t_rel=round(float(ft[i]/ft[i200]),4),f_v_rel=round(float(fv[i]/fv[i200]),4),ln_f_tv=round(float(np.log(ft[i]/fv[i])),4),ln_P_tv=round(float(np.log(pt[i]/pv[i])),4))
    rows.append(row); print(f"{row['r']:4d}   {row['RAW_t_rel']:.4f}   {row['RAW_v_rel']:.4f}   | {row['ln_RAW_tv']:+.4f} | {row['f_t_rel']:.4f}  {row['f_v_rel']:.4f} | {row['ln_f_tv']:+.4f} | {row['ln_P_tv']:+.4f}")
out['perfils']=rows
np.savez_compressed(S4+'/fb5_perfils.npz',rc=rc,RAW=PR,fRAW=PF,P=PP); np.save(S4+'/fb5_fRAW.npy',fR.astype(np.float32)); np.save(S4+'/fb5_residu.npy',res.astype(np.float32))
json.dump(out,open(S4+'/fb5_corba_pere.json','w'),indent=1)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,3,figsize=(17,5))
ax[0].plot(xc,yi,'k'); ax[0].set_xlabel('RAW Vixen 10 s (DN14−negre)'); ax[0].set_ylabel('P revelat de Pere (DN16)'); ax[0].set_title('corba monòtona f (R² %.3f)'%r2); ax[0].axvline(lv_t,color='r',ls='--',label='nivell taca'); ax[0].axvline(lv_lim,color='b',ls='--',label='nivell r400'); ax[0].legend()
for A,nm,col in ((PR,'RAW',"m"),(PF,'f(RAW)','g'),(PP,'P','k')):
    ax[1].plot(rc,g(A,T)/g(A,T)[i200],col+'-',label=nm+' taca'); ax[1].plot(rc,g(A,VV)/g(A,VV)[i200],col+'--',label=nm+' veïns')
ax[1].set_ylim(0.85,1.6); ax[1].legend(fontsize=7); ax[1].set_title('perfil radial relatiu a r 200'); ax[1].set_xlabel('r (px)')
ax[2].plot(rc,np.log(g(PR,T)/g(PR,VV))*10,'m',label='10× ln RAW t/v'); ax[2].plot(rc,np.log(g(PF,T)/g(PF,VV)),'g',label='ln f(RAW) t/v'); ax[2].plot(rc,np.log(g(PP,T)/g(PP,VV)),'k',label='ln P t/v'); ax[2].axhline(0,color='gray'); ax[2].set_ylim(-0.3,0.1); ax[2].legend(fontsize=8); ax[2].set_xlabel('r (px)'); ax[2].set_title('taca / veïns')
plt.tight_layout(); plt.savefig(S4+'/v_fb5_corba_pere.png',dpi=110)
# vista: taca en RAW (norm σ4), f(RAW), P, residu — retall 700×700 al voltant de la marca, ×1
from PIL import Image
y0,x0=1157-230,828-230; sl=(slice(y0,y0+700),slice(x0,x0+700))
def st(A,lo,hi): return np.clip((A-lo)/(hi-lo),0,1)
rawn=gaussian_filter(np.nan_to_num(RAW),4)/np.nan_to_num(gaussian_filter(np.nan_to_num(RAW),40)+1e-6)
pan=np.concatenate([st(rawn[sl],0.97,1.03),st(fR[sl],6500,10500),st(Ps[sl],6500,10500),st(res[sl]+8500,6500,10500)],1)
Image.fromarray(np.uint8(pan*255)).save(S4+'/v_fb5_taca_raw_f_P_residu.png'); print('fet')
