#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/refine.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle
from scipy import ndimage
P=pickle.load(open("peaks2.pkl","rb")); names=sorted(P.keys())
prev=pickle.load(open("offsets.pkl","rb")); OFF0=prev['off']; CORE=prev['core']
REF='DSC06993'
def match(a,b,off,tol):
    xa,ya=P[a]['x'],P[a]['y']; xb,yb=P[b]['x']-off[0],P[b]['y']-off[1]
    from scipy.spatial import cKDTree
    t=cKDTree(np.c_[xb,yb]); d,i=t.query(np.c_[xa,ya],distance_upper_bound=tol)
    ok=np.isfinite(d)
    return np.nonzero(ok)[0], i[ok], d[ok]
OFF={}
for n in names:
    if n==REF: OFF[n]=(0.0,0.0); continue
    o=list(OFF0[n])
    for it in range(4):
        ia,ib,d=match(REF,n,o,3.0 if it==0 else 1.8)
        dx=P[n]['x'][ib]-P[REF]['x'][ia]; dy=P[n]['y'][ib]-P[REF]['y'][ia]
        w=np.minimum(P[REF]['snr'][ia],P[n]['snr'][ib])
        o=[float(np.median(dx)),float(np.median(dy))]
    sx=np.std(dx-np.median(dx)); sy=np.std(dy-np.median(dy))
    OFF[n]=tuple(o)
    print(f"{n:10s} exp={P[n]['exp']:4.1f}s  dx={o[0]:+9.3f} dy={o[1]:+9.3f}  n_match={len(ia):4d}  rms=({sx:.2f},{sy:.2f}) px")
OFF[REF]=(0.0,0.0)
pickle.dump({'off':OFF,'core':CORE},open("offsets2.pkl","wb"))
# solar centre in reference frame coordinates
print("\nsaturated-core centroid mapped into the DSC06993 grid:")
for n in names:
    print(f"  {n}: ({CORE[n][0]-OFF[n][0]:7.1f},{CORE[n][1]-OFF[n][1]:7.1f})")
