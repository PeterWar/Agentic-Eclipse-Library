#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/stack2.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle, sys
from scipy import ndimage
from scipy.spatial import cKDTree
OFF=pickle.load(open("offsets2.pkl","rb"))['off']
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
REF='DSC06993'
# 1. fresh peak lists with the DC-blind filter, sub-pixel
PK={}
for n,e in EXP.items():
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy")
    s=np.where(Dn>0,N/np.sqrt(np.maximum(Dn,1e-30)),0.0).astype(np.float32)
    lm=(s>4.5)&(s==ndimage.maximum_filter(s,9))
    ys,xs=np.nonzero(lm)
    fx=np.zeros(len(xs)); fy=np.zeros(len(xs))
    a=s[ys,xs-1]; b=s[ys,xs]; c=s[ys,xs+1]; d=a-2*b+c; fx=np.where(d!=0,0.5*(a-c)/np.where(d!=0,d,1),0)
    a=s[ys-1,xs]; c=s[ys+1,xs]; d=a-2*b+c; fy=np.where(d!=0,0.5*(a-c)/np.where(d!=0,d,1),0)
    PK[n]=dict(x=xs+np.clip(fx,-1,1),y=ys+np.clip(fy,-1,1),snr=b)
    print(n,len(xs)); del N,Dn,s
pickle.dump(PK,open("peaks3.pkl","wb"))
# 2. refine offsets
NEW={REF:(0.0,0.0)}
for n in EXP:
    if n==REF: continue
    o=list(OFF[n])
    for it in range(4):
        t=cKDTree(np.c_[PK[n]['x']-o[0],PK[n]['y']-o[1]])
        d,i=t.query(np.c_[PK[REF]['x'],PK[REF]['y']],distance_upper_bound=3.0 if it==0 else 1.5)
        ok=np.isfinite(d); ia=np.nonzero(ok)[0]; ib=i[ok]
        dx=PK[n]['x'][ib]-PK[REF]['x'][ia]; dy=PK[n]['y'][ib]-PK[REF]['y'][ia]
        o=[float(np.median(dx)),float(np.median(dy))]
    NEW[n]=tuple(o)
    print(f"  {n}: dx={o[0]:+9.3f} dy={o[1]:+9.3f} n={ok.sum()} rms=({np.std(dx):.2f},{np.std(dy):.2f})")
pickle.dump({'off':NEW},open("offsets3.pkl","wb"))
# 3. stack
NUM=None
for n,e in EXP.items():
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy"); dx,dy=NEW[n]
    if abs(dx)+abs(dy)>0:
        N=ndimage.shift(N,(-dy,-dx),order=1,mode='constant',cval=0.0)
        Dn=ndimage.shift(Dn,(-dy,-dx),order=1,mode='constant',cval=0.0)
    if NUM is None: NUM=np.zeros_like(N); DEN=np.zeros_like(Dn); COV=np.zeros_like(Dn)
    NUM+=N*e; DEN+=Dn*(e*e); COV+=(Dn>0)*e
    del N,Dn
SNR=np.where(DEN>0,NUM/np.sqrt(np.maximum(DEN,1e-30)),0.0).astype(np.float32)
FLX=np.where(DEN>0,NUM/np.maximum(DEN,1e-30),0.0).astype(np.float32)
np.save("SNR.npy",SNR); np.save("FLX.npy",FLX); np.save("DEN.npy",DEN.astype(np.float32)); np.save("COV.npy",COV.astype(np.float32))
m=DEN>0; q=np.percentile(SNR[m],[15.87,50,84.13])
print(f"\nSTACK: SNR med={q[1]:+.3f} sd=({q[1]-q[0]:.3f},{q[2]-q[1]:.3f}) max={SNR[m].max():.0f}")
deep=COV>24.5
print(f"deep area {deep.sum()/1e6:.1f} Mpx ; 1-sigma peak amplitude = {1/np.sqrt(np.median(DEN[deep])):.3f} ADU/s")
