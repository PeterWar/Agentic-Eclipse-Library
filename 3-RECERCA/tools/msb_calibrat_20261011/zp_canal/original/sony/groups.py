#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/groups.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
OFF=pickle.load(open("offsets6.pkl","rb"))['off']
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
A=['DSC06984','DSC06985','DSC06987']; C=['DSC06991','DSC06993','DSC06996','DSC06999']
def stack(sub):
    NUM=None
    for n in sub:
        N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy"); dx,dy=OFF[n]
        if abs(dx)+abs(dy)>0:
            N=ndimage.shift(N,(-dy,-dx),order=1,mode='constant',cval=0.)
            Dn=ndimage.shift(Dn,(-dy,-dx),order=1,mode='constant',cval=0.)
        if NUM is None: NUM=np.zeros_like(N); DEN=np.zeros_like(Dn)
        NUM+=N*EXP[n]; DEN+=Dn*EXP[n]**2; del N,Dn
    return np.where(DEN>0,NUM/np.sqrt(np.maximum(DEN,1e-30)),0).astype(np.float32)
SA=stack(A); SC=stack(C)
np.save("SA.npy",SA); np.save("SC.npy",SC)
h,w=SA.shape; yy,xx=np.mgrid[0:h,0:w]; R=np.hypot(xx-CX,yy-CY)/RSUN; del xx,yy
def peaks(S,thr=5.0):
    lm=(S>thr)&(S==ndimage.maximum_filter(S,13))&(R>3.0)
    ys,xs=np.nonzero(lm)
    a=S[ys,xs-1];b=S[ys,xs];c=S[ys,xs+1];d=a-2*b+c; fx=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    a=S[ys-1,xs];c=S[ys+1,xs];d=a-2*b+c; fy=np.where(d!=0,.5*(a-c)/np.where(d!=0,d,1),0)
    return np.c_[xs+np.clip(fx,-1,1),ys+np.clip(fy,-1,1)],b
PA,sa=peaks(SA); PC,sc=peaks(SC)
print(f"group A stack (11 s): {len(PA)} outer peaks >5 sigma")
print(f"group C stack (13 s): {len(PC)} outer peaks >5 sigma")
t=cKDTree(PC); d,i=t.query(PA,distance_upper_bound=16.0)
ok=np.isfinite(d); print(f"pairs within 16 px: {ok.sum()}")
u=PA[ok]; v=PC[i[ok]]
c0=np.array([w/2,h/2])
for name,deg in [("affine",1),("quadratic",2)]:
    U=(u-c0)/1000.; 
    cols=[np.ones(len(U)),U[:,0],U[:,1]]
    if deg==2: cols+=[U[:,0]**2,U[:,1]**2,U[:,0]*U[:,1]]
    M=np.array(cols).T
    sol,*_=np.linalg.lstsq(M,v-u,rcond=None)
    pred=u+M@sol; res=pred-v
    rms=np.sqrt((res**2).sum(1).mean())
    # robust: drop worst 15%
    q=np.sqrt((res**2).sum(1)); keep=q<np.percentile(q,85)
    sol,*_=np.linalg.lstsq(M[keep],(v-u)[keep],rcond=None)
    res2=(u+M@sol-v)[keep]; rms2=np.sqrt((res2**2).sum(1).mean())
    print(f"  {name}: rms={rms:.2f} px (all)  {rms2:.2f} px (robust, n={keep.sum()})")
    if deg==2: np.save("warpAC.npy",sol); np.save("warp_c0.npy",c0)
tr=np.median(v-u,axis=0); print(f"  pure translation: rms={np.sqrt(((v-u-tr)**2).sum(1).mean()):.2f} px  (dx={tr[0]:.2f},dy={tr[1]:.2f})")
np.save("pairs_u.npy",u); np.save("pairs_v.npy",v)
