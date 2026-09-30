"""B5: model 2D del vel millorat (dos nuclis + dipol de cel), ajustat al disc RAW normalitzat; component azimutal; coeficient a la capa lunar per anell amb LROC de covariable i k(r) pel criteri de l'anticorrelació; capa 30 v72."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.signal import fftconvolve
from scipy.ndimage import gaussian_filter
RS=456.0; N=3000; c0=(1499.88,1500.41); OX,OY=501,502
yy,xx=np.mgrid[0:N,0:N]; rr=np.hypot(xx-c0[0],yy-c0[1])
C=np.load(OLD+'/corona_hdr_3000.npy').astype(np.float64); C[rr<RS]=0; C=np.nan_to_num(C); C[rr>=1480]=0
def a_roi(A): return A[OY:OY+2000,OX:OX+2000]
Y2,X2=np.mgrid[0:2000,0:2000]; rr2=np.hypot(X2-998.88,Y2-998.41); az2=np.rad2deg(np.arctan2(-(Y2-998.41),X2-998.88))%360
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for k in range(0,int(RS)+step,step):
        m=mask&(rr2>=k)&(rr2<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
M=np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64); Mv=np.isfinite(M); Mz=gaussian_filter(np.nan_to_num(np.where(Mv,M-1,0)),6)
rgb62,_=carrega(62); L62=rgb62.mean(-1); v62=np.load(NEW+'/roi71_L62.npz')['c-1']>30000; LROC_az=ring_norm(gaussian_filter(L62,6),v62&(rr2<RS-8))
disc=rr2<RS-8; fit_mask=Mv&(rr2>40)&(rr2<400)&np.isfinite(LROC_az)
def kern(d0,q):
    d=np.hypot(*np.mgrid[-N//2:N//2,-N//2:N//2]); K=1/(1+(d/d0)**q); return K/K.sum()
G1=a_roi(fftconvolve(C,kern(3,1.5),mode='same')); G2=a_roi(fftconvolve(C,kern(160,1.5),mode='same'))
# components azimutals (mitjana zero per anell) de cada terme + dipol (cosθ, sinθ escalats per r)
def az_comp(A):
    out=np.zeros_like(A)
    for k in range(0,int(RS)+4,4):
        m=disc&(rr2>=k)&(rr2<k+4)
        if m.sum()>10: out[m]=A[m]-A[m].mean()
    return out
g1=az_comp(G1/np.mean(G1[disc])); g2=az_comp(G2/np.mean(G2[disc])); dx=az_comp((X2-998.88)/RS); dy=az_comp((Y2-998.41)/RS)
X=np.stack([g1[fit_mask],g2[fit_mask],dx[fit_mask],dy[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); y=Mz[fit_mask]
coef,*_=np.linalg.lstsq(X,y,rcond=None); pred=X@coef; r2=1-np.var(y-pred)/np.var(y)
Xs=X[:,[0,1,2,3,5]]; cs,*_=np.linalg.lstsq(Xs,y,rcond=None); r2s=1-np.var(y-Xs@cs)/np.var(y)
Xc=np.stack([np.rot90(g1)[fit_mask],np.rot90(g2)[fit_mask],dx[fit_mask],dy[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); cc,*_=np.linalg.lstsq(Xc,y,rcond=None); r2c=1-np.var(y-Xc@cc)/np.var(y)
print('ajust RAW: coef g1 %.4f g2 %.4f dipol (%.4f,%.4f) LROC %.4f · R² %.3f (sense LROC %.3f; control nuclis girats 90°: %.3f)'%(coef[0],coef[1],coef[2],coef[3],coef[4],r2,r2s,r2c))
# vel azimutal total en unitats relatives del RAW (sense el terme LROC)
Gaz=coef[0]*g1+coef[1]*g2+coef[2]*dx+coef[3]*dy; Gaz=np.nan_to_num(Gaz)
np.save(NEW+'/vel_Gaz_v2.npy',Gaz.astype(np.float32))
# coeficient a la capa (V71 de Pere: capa 30 ja porta la correcció v1). Treballem sobre la capa ORIGINAL V69 (roi_L30.npz de l'OLD) per no acumular.
d69=np.load(OLD+'/roi_L30.npz'); rgb30=np.dstack([d69['c0'],d69['c1'],d69['c2']]).astype(np.float64)/65535; L30=rgb30.mean(-1); LAY=ring_norm(gaussian_filter(L30,6),disc)
sec=(az2//10).astype(int); parell=sec%2==0; bins=np.arange(20,RS-8,20)
def fit_c(m):
    Xl=np.stack([Gaz[m],LROC_az[m],np.ones(m.sum())],1); c,*_=np.linalg.lstsq(Xl,LAY[m],rcond=None); return c[0]
c_all=[]; k_fin=[]; obj=[]
for k in bins:
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY)&np.isfinite(LROC_az); c_all.append(fit_c(m))
    mp=m&parell; ms=m&~parell; c=max(fit_c(mp),0); tgt=np.corrcoef(LROC_az[ms],Gaz[ms])[0,1]
    ks=np.arange(0,2.01,0.1); cc=[np.corrcoef(ring_norm(gaussian_filter(L30/(1+kf*c*Gaz),6),disc)[ms],Gaz[ms])[0,1] for kf in ks]
    j=int(np.argmin(np.abs(np.array(cc)-tgt))); k_fin.append(ks[j]); obj.append((int(k),round(float(c),3),round(float(tgt),2),round(float(ks[j]),1)))
print('c per anell (tot):',np.round(c_all,3)); print('objectiu/k:',obj)
kf_s=gaussian_filter(np.clip(np.array(k_fin),0.6,1.6),1.0); c_s=gaussian_filter(np.clip(np.array(c_all),0,None),1.5)*kf_s
c_r=np.interp(rr2,bins+10,c_s); taper=np.clip((RS-8-rr2)/24,0,1); c_r=c_r*taper
corr=1.0/(1.0+c_r*Gaz); corr[rr2>=RS-8]=1.0
rgb_new=np.clip(rgb30*corr[...,None],0,1); Ln=rgb_new.mean(-1); LAYn=ring_norm(gaussian_filter(Ln,6),disc)
cl=[]
for k in bins:
    ms=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAYn)&np.isfinite(LROC_az)&~parell; cl.append(round(float(np.corrcoef(LAYn[ms],LROC_az[ms])[0,1]),2))
print('correlació capa~LROC (holdout) DESPRÉS:',cl)
# la taca 219.7 (marca de V71)
m7=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.03
yb,xb=np.nonzero(R7); rb=np.hypot(xb-998.88,yb-998.41); anell=(rr2>=rb.min()-10)&(rr2<=rb.max()+10)&(~R7)&disc
v71=np.load(OLD+'/roi_L30_v71.npz'); L71=np.dstack([v71['c0'],v71['c1'],v71['c2']]).astype(np.float64).mean(-1)/65535
for nom,LL in (('V69',L30),('V71 (v1)',L71),('v2',Ln)):
    Ls=gaussian_filter(LL,8); print(f'taca 219.7 {nom:9s}: mitjana {100*(1-LL[R7].mean()/LL[anell].mean()):+.1f} % sota l\'anell · mín σ8 {100*(1-Ls[R7].min()/LL[anell].mean()):+.1f} % · LROC diu {100*(1-L62[R7&v62].mean()/L62[anell&v62].mean()):+.1f} %')
print('factor: mín %.3f màx %.3f'%(corr.min(),corr.max()))
# retenció de bandes fines i color
for lo,hi in ((3,8),(8,32),(32,64)):
    b0=gaussian_filter(L30,lo)-gaussian_filter(L30,hi); b1=gaussian_filter(Ln,lo)-gaussian_filter(Ln,hi); m=rr2<RS-30; print(f'banda {lo}–{hi}: corr {np.corrcoef(b0[m],b1[m])[0,1]:.4f} amplitud ×{b1[m].std()/b0[m].std():.3f}')
out={k:v71[k] for k in v71.files}   # màscara de V71 (interior opac, vora de Pere intacta)
for c,key in enumerate(('c0','c1','c2')): out[key]=(rgb_new[...,c]*65535+.5).astype(np.uint16)
np.savez_compressed(NEW+'/roi72_L30.npz',**out); np.save(NEW+'/vel_corr_v2.npy',corr.astype(np.float32))
json.dump(dict(coef_raw=dict(g1=float(coef[0]),g2=float(coef[1]),dipol=[float(coef[2]),float(coef[3])],lroc=float(coef[4]),R2=float(r2),R2_sense_lroc=float(r2s),R2_control_girat=float(r2c)),c_per_anell=[float(x) for x in c_all],k_per_anell=[float(x) for x in kf_s],corr_lroc_holdout_despres=cl,factor=[float(corr.min()),float(corr.max())]),open(NEW+'/b5_vel2d_v2.json','w'),indent=1)
from PIL import Image
lin=lambda A: np.clip((A-np.percentile(A[disc],1))/(np.percentile(A[disc],99.5)-np.percentile(A[disc],1)),0,1)
pan=np.concatenate([lin(L30),lin(L71),lin(Ln),np.clip((L62-np.percentile(L62[v62&disc],1))/(np.percentile(L62[v62&disc],99.5)-np.percentile(L62[v62&disc],1)),0,1)*(v62&disc)],1)
Image.fromarray(np.uint8(pan*255)).save(NEW+'/v_B5_lluna_v69_v71_v72_lroc.png'); print('fet')
