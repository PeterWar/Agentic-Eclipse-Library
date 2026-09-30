#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/mf3.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import rawpy, numpy as np, pickle, sys
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from scipy import ndimage
D=str(comu.DADES_300MM)+"/"
GAIN=3.323; SG=1.3; HW=7
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
t=np.arange(-HW,HW+1)
p1=np.exp(-t*t/(2*SG*SG))          # separable Gaussian factor
p2=p1*p1
one=np.ones_like(t,dtype=float)
def sep(a,kx,ky):
    return ndimage.convolve1d(ndimage.convolve1d(a,ky.astype(np.float32),axis=0,mode='constant'),
                              kx.astype(np.float32),axis=1,mode='constant')
def green_interp(sig,col):
    g=((col==1)|(col==3))
    G=np.where(g,sig,0.0).astype(np.float32); W=g.astype(np.float32)
    s=np.zeros_like(G); n=np.zeros_like(W)
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        s+=np.roll(np.roll(G,dy,0),dx,1); n+=np.roll(np.roll(W,dy,0),dx,1)
    return np.where(g,sig,s/np.maximum(n,1)).astype(np.float32), g
for name,exp in EXP.items():
    md=np.load(f"masterdark_{int(exp)}s.npy")
    with rawpy.imread(D+name+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    sig=raw-md; Gi,g=green_interp(sig,col)
    bkg=Background2D(Gi,(32,32),filter_size=(3,3),sigma_clip=SigmaClip(sigma=3.0),
                     bkg_estimator=MedianBackground(),exclude_percentile=30.0).background
    res=(sig-bkg).astype(np.float32); var=(np.maximum(bkg,1.0)/GAIN).astype(np.float32)
    valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    w=np.where(valid,1.0/var,0.0).astype(np.float32); wd=(w*np.where(valid,res,0.0)).astype(np.float32)
    Sw   = sep(w ,one,one); Swp = sep(w ,p1,p1); Swpp= sep(w ,p2,p2)
    Swd  = sep(wd,one,one); Swpd= sep(wd,p1,p1)
    det  = Sw*Swpp - Swp*Swp
    NUM  = (Sw*Swpd - Swp*Swd)          # numerator of A
    DEN  = det                          # A = NUM/DEN ; Var(A)=Sw/DEN
    snr  = np.where(det>0, NUM/np.sqrt(np.maximum(Sw*det,1e-30)), 0.0).astype(np.float32)
    # store so that a stack can be built:  A = NUM/DEN, Var = Sw/DEN  -> weight = DEN/Sw
    np.save(f"N_{name}.npy",(NUM/np.maximum(Sw,1e-30)).astype(np.float32))   # NUM' with Var(A)=1/DEN'
    np.save(f"D_{name}.npy",(det/np.maximum(Sw,1e-30)).astype(np.float32))
    np.save(f"bkg_{name}.npy",bkg)
    m=valid
    q=np.percentile(snr[m],[15.87,50,84.13])
    print(f"{name} {exp}s  SNR med={q[1]:+.3f} sd=({q[1]-q[0]:.3f},{q[2]-q[1]:.3f}) max={snr[m].max():.0f} "
          f"peaks>5={(((snr>5)&(snr==ndimage.maximum_filter(snr,11)))&m).sum()}")
    sys.stdout.flush()
    del raw,sig,Gi,bkg,res,var,valid,w,wd,Sw,Swp,Swpp,Swd,Swpd,det,NUM,DEN,snr
