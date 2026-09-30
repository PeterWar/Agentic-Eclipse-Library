#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/imgs.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import rawpy, numpy as np, pickle
from scipy import ndimage
D=str(comu.DADES_300MM)+"/"; GAIN=3.323
OFF=pickle.load(open("offsets6.pkl","rb"))['off']
EXP={'DSC06984':2.,'DSC06985':1.,'DSC06987':8.,'DSC06991':1.,'DSC06993':8.,'DSC06996':2.,'DSC06999':2.}
G={'A':['DSC06984','DSC06985','DSC06987'],'C':['DSC06991','DSC06993','DSC06996','DSC06999']}
SI=0.6; t=np.arange(-2,3); k=np.exp(-t*t/(2*SI*SI))
def sep(a,kk): return ndimage.convolve1d(ndimage.convolve1d(a,kk.astype(np.float32),0,mode='constant'),kk.astype(np.float32),1,mode='constant')
for g,sub in G.items():
    ACC=None
    for n in sub:
        e=EXP[n]; md=np.load(f"masterdark_{int(e)}s.npy"); bkg=np.load(f"bkg_{n}.npy")
        with rawpy.imread(D+n+".ARW") as r:
            raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
        gm=((col==1)|(col==3)); res=(raw-md-bkg).astype(np.float32)
        valid=gm&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
        valid[:40]=valid[-40:]=False; valid[:,:40]=valid[:,-40:]=False
        v=valid.astype(np.float32); cw=sep(v,k)
        I=sep(np.where(valid,res,0.).astype(np.float32),k)/np.maximum(cw,1e-6)/e
        W=(cw>0.05).astype(np.float32)*(e*e/(np.median(bkg[valid])/GAIN))
        dx,dy=OFF[n]
        if abs(dx)+abs(dy)>0:
            I=ndimage.shift(I,(-dy,-dx),order=1,mode='constant',cval=0.); W=ndimage.shift(W,(-dy,-dx),order=1,mode='constant',cval=0.)
        if ACC is None: ACC=np.zeros_like(I); WT=np.zeros_like(W)
        ACC+=I*W; WT+=W; del raw,res,valid,v,I,W,bkg,cw
    np.save(f"IMG{g}.npy",np.where(WT>0,ACC/np.maximum(WT,1e-20),0).astype(np.float32))
    print("built IMG",g)
