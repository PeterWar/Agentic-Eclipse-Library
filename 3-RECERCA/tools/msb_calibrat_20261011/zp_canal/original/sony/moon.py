#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/moon.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import rawpy, numpy as np, pickle
from scipy import ndimage, optimize
D=str(comu.DADES_300MM)+"/"
OFF=pickle.load(open("offsets2.pkl","rb"))['off']
out={}
for n in ['DSC06993','DSC06987','DSC06996','DSC06991']:
    with rawpy.imread(D+n+".ARW") as r: v=r.raw_image_visible.astype(np.float32)
    sat=(v>=16380)
    fill=ndimage.binary_fill_holes(ndimage.binary_closing(sat,np.ones((9,9))))
    hole=fill&~sat
    lab,nl=ndimage.label(hole); sz=np.bincount(lab.ravel()); sz[0]=0
    m=(lab==sz.argmax())
    ys,xs=np.nonzero(m)
    cx,cy=xs.mean(),ys.mean(); area=m.sum(); rad=np.sqrt(area/np.pi)
    # refine by fitting circle to the hole boundary
    edge=m&~ndimage.binary_erosion(m)
    ey,ex=np.nonzero(edge)
    def f(p):
        return np.sqrt((ex-p[0])**2+(ey-p[1])**2)-p[2]
    p,_=optimize.leastsq(f,[cx,cy,rad])
    rr=np.abs(f(p)); keep=rr<np.percentile(rr,85)
    def f2(q): return np.sqrt((ex[keep]-q[0])**2+(ey[keep]-q[1])**2)-q[2]
    p,_=optimize.leastsq(f2,p)
    gx,gy=p[0]-OFF[n][0],p[1]-OFF[n][1]
    print(f"{n}: lunar disc centre sensor=({p[0]:.1f},{p[1]:.1f}) R={p[2]:.1f} px = {p[2]*2*3.234/60:.2f}' diam ; in ref grid=({gx:.1f},{gy:.1f})")
    out[n]=(p[0],p[1],p[2],gx,gy)
pickle.dump(out,open("moon.pkl","wb"))
