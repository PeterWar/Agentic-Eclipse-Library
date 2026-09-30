"""B7: WOW bilateral 56 amb la màscara oberta per Pere: (1) biaix de contorn corregit amb TOT el suport fora del forat (abans la seva màscara hi era 0 i no es va mesurar), (2) dins del disc el ràster passa al nivell local (mediana per sector a d 4–12, suau en θ), amb transició a d ∈ [−2, 4]: el filtre no actua on no té dada."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
CX,CY,RS=998.88,998.41,456.0
v=np.load(OLD+'/a9_vores.npz'); TH=v['TH']; r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap')
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1); d=rr-R_hole[ia]
D=np.arange(-6,49,0.5); SIG=24
def w_taper(dd): return np.where(dd<=22,1.0,np.where(dd>=32,0.0,0.5*(1+np.cos(np.pi*(dd-22)/10))))*(dd>=0)
def polar(F,Redge):
    xs=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D))
def smooth_th(P): return gaussian_filter1d(P,SIG,axis=0,mode='wrap')
rep={}
for lid in (56,55):
    dd=np.load(NEW+f'/roi71_L{lid}.npz'); F=dd['c0'].astype(np.float64)/65535   # gris
    P=polar(F,R_hole); P[:,D<0]=np.nan; S=smooth_th(np.where(np.isfinite(P),P,np.nanmean(P))); ref=np.nanmean(S[:,(D>=32)&(D<=48)],1); B=np.nan_to_num((S-ref[:,None])*w_taper(D)[None,:])
    B0=np.nan_to_num((smooth_th(np.nan_to_num(polar(F,R_hole+170)))-np.nanmean(smooth_th(np.nan_to_num(polar(F,R_hole+170)))[:,(D>=32)&(D<=48)],1)[:,None])*w_taper(D)[None,:])
    inb=(d>=-6)&(d<=48); Bp=np.zeros_like(rr); Bp[inb]=map_coordinates(B,[az[inb]/0.25,(d[inb]+6)/0.5],order=1,mode='nearest'); F2=np.clip(F-Bp,0,1)
    # nivell local per sector a d 4–12 (després de corregir) i farcit del disc
    P2=polar(F2,R_hole); lvl=gaussian_filter1d(np.nanmedian(P2[:,(D>=4)&(D<=12)],1),40,mode='wrap'); lvl_pix=lvl[ia]
    t=np.clip((d+2)/6,0,1)   # 0 a d≤−2 (dins), 1 a d≥4
    F3=np.where(d<4,lvl_pix*(1-t)+F2*t,F2)
    rms=lambda Bm,a,b: float(np.sqrt(np.nanmean(Bm[:,(D>=a)&(D<=b)]**2)))
    P3=polar(F3,R_hole); P3[:,D<0]=np.nan; S3=smooth_th(np.where(np.isfinite(P3),P3,np.nanmean(P3))); B3=np.nan_to_num((S3-np.nanmean(S3[:,(D>=32)&(D<=48)],1)[:,None])*w_taper(D)[None,:])
    rep[lid]=dict(biaix_rms_d0_8=rms(B,0,8),biaix_max=float(np.abs(B).max()),control_nul_rms_d0_8=rms(B0,0,8),despres_rms_d0_8=rms(B3,0,8),nivell_dins_mitja=float(lvl.mean()),pixels_canviats=int((np.abs(F3-F)>1/65535).sum()))
    print(lid,rep[lid])
    out={k:dd[k] for k in dd.files}
    for c in ('c0','c1','c2'): out[c]=(F3*65535+.5).astype(np.uint16)
    np.savez_compressed(NEW+f'/roi72_L{lid}.npz',**out)
json.dump(rep,open(NEW+'/b7_wow.json','w'),indent=1)
