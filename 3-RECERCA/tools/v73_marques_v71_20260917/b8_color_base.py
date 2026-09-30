"""B8: anell verdós de la base (3): anivellament de color per sector (σθ 6°) a d ∈ [0, 40] px del forat (taper 32→44): B/G i R/G portats al nivell de d 40–70; G intacte (lluminància ≈ intacta); control nul a +170 px."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
CX,CY,RS=998.88,998.41,456.0
v=np.load(OLD+'/a9_vores.npz'); TH=v['TH']; r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap')
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1); d=rr-R_hole[ia]
D=np.arange(-4,81,0.5); SIG=24
def taper(dd): return np.where(dd<=32,1.0,np.where(dd>=44,0.0,0.5*(1+np.cos(np.pi*(dd-32)/12))))*np.clip((dd-1)/2,0,1)
def polar(F,Redge):
    xs=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D))
dd=np.load(NEW+'/roi71_L3.npz'); rgb=np.dstack([dd['c0'],dd['c1'],dd['c2']]).astype(np.float64)/65535; sup=(dd['c-1'].astype(np.float64)/65535)*(dd['c-2'].astype(np.float64)/65535)
Sp=polar(sup,R_hole)
def exces(ratio,Redge):
    P=polar(ratio,Redge); P=np.where(polar(sup,Redge)>=0.5,np.log(np.maximum(P,1e-4)),np.nan)
    # mediana circular en θ (±6° = ±24 mostres) per files de d
    Pe=np.concatenate([P[-24:],P,P[:24]],0); S=np.stack([np.nanmedian(Pe[i:i+49],0) for i in range(len(TH))],0)
    ref=np.nanmedian(S[:,(D>=40)&(D<=70)],1); E=np.clip(np.nan_to_num(S-ref[:,None]),-0.06,0.06)
    E=gaussian_filter1d(E,8,axis=0,mode='wrap')   # suau final
    return E*taper(D)[None,:]
out=rgb.copy(); rep={}
for c,nom in ((2,'B/G'),(0,'R/G')):
    ratio=rgb[...,c]/np.maximum(rgb[...,1],1e-4); E=exces(ratio,R_hole); E0=exces(ratio,R_hole+170)
    inb=(d>=-4)&(d<=80); Ep=np.zeros_like(rr); Ep[inb]=map_coordinates(E,[az[inb]/0.25,(d[inb]+4)/0.5],order=1,mode='nearest')
    out[...,c]=np.clip(rgb[...,c]*np.exp(-Ep),0,1)
    r2=exces(out[...,c]/np.maximum(out[...,1],1e-4),R_hole)
    rep[nom]=dict(exces_rms_d0_30=float(np.sqrt(np.mean(E[:,(D>=0)&(D<=30)]**2))),exces_max_pct=float(100*(np.exp(np.abs(E).max())-1)),control_nul_rms=float(np.sqrt(np.mean(E0[:,(D>=0)&(D<=30)]**2))),despres_rms=float(np.sqrt(np.mean(r2[:,(D>=0)&(D<=30)]**2))),pixels=int((np.abs(Ep)>0.002).sum()))
    print(nom,rep[nom])
L0=rgb.mean(-1); L1=out.mean(-1); print('lluminància: canvi màx %.2f %% (mitjana absoluta %.3f %%)'%(100*np.abs(L1/np.maximum(L0,1e-4)-1).max(),100*np.mean(np.abs(L1/np.maximum(L0,1e-4)-1))))
o={k:dd[k] for k in dd.files}
for c,key in enumerate(('c0','c1','c2')): o[key]=(out[...,c]*65535+.5).astype(np.uint16)
np.savez_compressed(NEW+'/roi72_L3.npz',**o); json.dump(rep,open(NEW+'/b8_color_base.json','w'),indent=1); print('fet')
