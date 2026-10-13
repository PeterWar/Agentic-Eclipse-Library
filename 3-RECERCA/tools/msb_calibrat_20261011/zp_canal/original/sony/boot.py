#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/boot.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle
from scipy import ndimage
from scipy.spatial import cKDTree
OFF=pickle.load(open("offsets4.pkl","rb"))['off']
moon=pickle.load(open("moon.pkl","rb")); RSUN=293.0
CX,CY=moon['DSC06993'][0],moon['DSC06993'][1]
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
core=['DSC06987','DSC06991','DSC06993','DSC06996','DSC06999']
def build(sub,off):
    NUM=None
    for n in sub:
        N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy"); dx,dy=off[n]
        if abs(dx)+abs(dy)>0:
            N=ndimage.shift(N,(-dy,-dx),order=1,mode='constant',cval=0.0)
            Dn=ndimage.shift(Dn,(-dy,-dx),order=1,mode='constant',cval=0.0)
        if NUM is None: NUM=np.zeros_like(N); DEN=np.zeros_like(Dn)
        NUM+=N*EXP[n]; DEN+=Dn*EXP[n]**2; del N,Dn
    return np.where(DEN>0,NUM/np.sqrt(np.maximum(DEN,1e-30)),0).astype(np.float32)
S=build(core,OFF)
h,w=S.shape; yy,xx=np.mgrid[0:h,0:w]; R=np.hypot(xx-CX,yy-CY)/RSUN; del xx,yy
lm=(S>5.0)&(S==ndimage.maximum_filter(S,13))&(R>3.0)
ys,xs=np.nonzero(lm)
print(f"master star list from the 5 well-registered frames: {len(xs)} sources at R>3 Rsun, SNR>5")
master=np.c_[xs,ys]; np.save("master_xy.npy",master); np.save("master_snr.npy",S[ys,xs])
# re-register every frame against this list
NEW={}
for n in EXP:
    P=pickle.load(open("peaks3.pkl","rb"))[n]
    o=list(OFF[n]); best=None
    for tol in (25.0,8.0,3.0,2.0):
        t=cKDTree(np.c_[P['x']-o[0],P['y']-o[1]])
        d,i=t.query(master.astype(float),distance_upper_bound=tol)
        ok=np.isfinite(d)
        if ok.sum()<3: break
        dx=P['x'][i[ok]]-master[ok,0]; dy=P['y'][i[ok]]-master[ok,1]
        o=[float(np.median(dx)),float(np.median(dy))]; best=(ok.sum(),np.std(dx),np.std(dy))
    NEW[n]=tuple(o)
    if best is None:
        # PROMOCIO: a l'original aquest print petava (TypeError) quan un fotograma (DSC06988) no arribava a 3 aparellaments
        # a la primera tolerancia; master_xy/master_snr ja son escrits i offsets5.pkl el sobreescriu boot2.py, o sigui
        # que el resultat de la cadena no canvia. Nomes s'evita l'aturada.
        print(f"  {n} {EXP[n]:4.1f}s: dx={o[0]:+9.3f} dy={o[1]:+9.3f}  n= <3 (sense aparellament; es conserva l'offset previ)")
        continue
    print(f"  {n} {EXP[n]:4.1f}s: dx={o[0]:+9.3f} dy={o[1]:+9.3f}  n={best[0]:3d} rms=({best[1]:.2f},{best[2]:.2f})  "
          f"delta vs prev=({o[0]-OFF[n][0]:+.2f},{o[1]-OFF[n][1]:+.2f})")
pickle.dump({'off':NEW},open("offsets5.pkl","wb"))
