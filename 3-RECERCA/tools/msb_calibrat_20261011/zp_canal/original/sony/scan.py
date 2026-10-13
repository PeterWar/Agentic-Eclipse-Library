#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/scan.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle
from scipy import ndimage
master=np.load("master_xy.npy").astype(int); msnr=np.load("master_snr.npy")
OFF=pickle.load(open("offsets5.pkl","rb"))['off']
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
sel=np.argsort(-msnr)[:60]; M=master[sel]
W=40
NEW={}
for n in EXP:
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy")
    S=np.where(Dn>0,N/np.sqrt(np.maximum(Dn,1e-30)),0.0); del N,Dn
    h,w=S.shape; dx0,dy0=OFF[n]
    grid=np.zeros((2*W+1,2*W+1))
    for a in range(-W,W+1):
        for b in range(-W,W+1):
            X=np.round(M[:,0]+dx0+b).astype(int); Y=np.round(M[:,1]+dy0+a).astype(int)
            k=(X>2)&(X<w-3)&(Y>2)&(Y<h-3)
            grid[a+W,b+W]=np.clip(S[Y[k],X[k]],-3,None).sum()
    i,j=np.unravel_index(np.argmax(grid),grid.shape)
    bg=np.median(grid); sd=np.std(grid)
    NEW[n]=(dx0+(j-W),dy0+(i-W))
    print(f"  {n} {EXP[n]:4.1f}s: best shift=({j-W:+3d},{i-W:+3d}) -> dx={NEW[n][0]:+9.2f} dy={NEW[n][1]:+9.2f}   "
          f"peak={grid[i,j]:7.1f} median={bg:6.1f} sd={sd:5.1f}  significance={(grid[i,j]-bg)/sd:5.1f}")
    del S
pickle.dump({'off':NEW},open("offsets6.pkl","wb"))
