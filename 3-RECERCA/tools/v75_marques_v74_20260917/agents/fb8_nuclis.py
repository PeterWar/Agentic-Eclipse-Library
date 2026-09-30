"""fb8: quin nucli de PSF (corona HDR ⊗ K) reprodueix el contrast marca/flancs de la taca al RAW normalitzat, sense perdre l'ajust global."""
import json, numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import gaussian_filter
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
RS=456.0; N=3000; c0=(1499.88,1500.41); OX,OY=501,502
yy,xx=np.mgrid[0:N,0:N]; rr3=np.hypot(xx-c0[0],yy-c0[1])
C=np.load(OLD+'/corona_hdr_3000.npy').astype(np.float64); C[rr3<RS]=0; C=np.nan_to_num(C); C[rr3>=1480]=0
def a_roi(A): return A[OY:OY+2000,OX:OX+2000]
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360; sec5=(az//5).astype(int)
disc=rr<RS-8
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for k in range(0,int(RS)+step,step):
        m=mask&(rr>=k)&(rr<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
M=np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64); Mv=np.isfinite(M); Mz=gaussian_filter(np.nan_to_num(np.where(Mv,M-1,0)),6)
L62d=np.load(S4+'/roi74p_L62.npz'); L62=np.dstack([L62d['c0'],L62d['c1'],L62d['c2']]).astype(np.float64).mean(-1); v62=L62d['c-1']>30000
LROC_az=ring_norm(gaussian_filter(L62,6),v62&disc); fit_mask=Mv&(rr>40)&(rr<400)&np.isfinite(LROC_az)
MK=np.load(S4+'/marques74_masks.npz'); m6=MK['m6']; e6=MK['ent_m6']
def contrast(A): return float(np.median(A[m6])-np.median(A[e6]))
raw_c=contrast(Mz); lroc_c=contrast(LROC_az)
# contrast del RAW normalitzat (azimutal pur) marca−flancs, i el que hi pot posar l'albedo (B·LROC)
print('contrast marca−flancs (mediana, unitats relatives): RAW_norm σ6 %.4f · LROC_az %.4f'%(raw_c,lroc_c))
dd=np.hypot(*np.mgrid[-N//2:N//2,-N//2:N//2])
def kern_pow(d0,q): K=1/(1+(dd/d0)**q); return K/K.sum()
def kern_gauss(s): K=np.exp(-dd**2/(2*s*s)); return K/K.sum()
res=[]
def prova(nom,K):
    G=a_roi(fftconvolve(C,K,mode='same')); Gaz=ring_norm(G,disc); Gz=np.nan_to_num(Gaz)
    Xf=np.stack([Gz[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); y=Mz[fit_mask]; coef,*_=np.linalg.lstsq(Xf,y,rcond=None); r2=1-np.var(y-Xf@coef)/np.var(y)
    mod=coef[0]*Gz; c_mod=contrast(mod); c_res=contrast(Mz-mod-coef[1]*np.nan_to_num(LROC_az))
    row=dict(nucli=nom,A=float(coef[0]),B=float(coef[1]),R2=float(r2),contrast_model=c_mod,contrast_residu=c_res,fraccio=c_mod/raw_c); res.append(row)
    print(f"{nom:22s} A={coef[0]:+.4f} B={coef[1]:+.4f} R²={r2:.3f} | contrast model {c_mod:+.4f} residu {c_res:+.4f} (fracció {c_mod/raw_c:.2f})",flush=True); return Gz
Gs={}
for d0 in (30,100,160,250):
    for q in (1.5,3.0,6.0):
        Gs[f'pow{d0}_{q}']=prova(f'pow d0={d0} q={q}',kern_pow(d0,q))
for s in (60,120,200):
    Gs[f'gauss{s}']=prova(f'gauss σ={s}',kern_gauss(s))
# dos nuclis: el millor global (pow30 q1.5) + cada compacte
base=Gs['pow30_1.5']; y=Mz[fit_mask]; two=[]
for k,G2 in Gs.items():
    if k=='pow30_1.5': continue
    Xf=np.stack([base[fit_mask],G2[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); coef,*_=np.linalg.lstsq(Xf,y,rcond=None); r2=1-np.var(y-Xf@coef)/np.var(y)
    mod=coef[0]*base+coef[1]*G2; c_mod=contrast(mod); c_res=contrast(Mz-mod-coef[2]*np.nan_to_num(LROC_az))
    two.append(dict(segon=k,A1=float(coef[0]),A2=float(coef[1]),B=float(coef[2]),R2=float(r2),contrast_model=c_mod,contrast_residu=c_res,fraccio=c_mod/raw_c))
    print(f"dos nuclis pow30q1.5 + {k:12s}: A1={coef[0]:+.4f} A2={coef[1]:+.4f} R²={r2:.3f} | contrast model {c_mod:+.4f} residu {c_res:+.4f} (fracció {c_mod/raw_c:.2f})",flush=True)
# control: la corona girada 90° amb el nucli que millor reprodueixi el contrast
best=max(res,key=lambda r:r['fraccio']); print('millor fracció:',best['nucli'])
json.dump(dict(contrast_raw=raw_c,contrast_lroc=lroc_c,un_nucli=res,dos_nuclis=two),open(S4+'/fb8_nuclis.json','w'),indent=1)
np.savez_compressed(S4+'/fb8_Gaz.npz',**{k:v.astype(np.float32) for k,v in Gs.items()}); print('fet')
