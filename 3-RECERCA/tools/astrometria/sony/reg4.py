#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/reg4.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np, pickle
from scipy.spatial import cKDTree
PK=pickle.load(open("peaks3.pkl","rb")); OFF0=pickle.load(open("offsets3.pkl","rb"))['off']
moon=pickle.load(open("moon.pkl","rb"))
RSUN=293.0; REF='DSC06993'
CX,CY=moon[REF][0],moon[REF][1]
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
# keep only peaks far from the Sun/Moon: pure star field
KEEP={}
for n in PK:
    dx,dy=OFF0[n]; cx,cy=CX+dx,CY+dy
    r=np.hypot(PK[n]['x']-cx,PK[n]['y']-cy)/RSUN
    k=r>3.0
    KEEP[n]=dict(x=PK[n]['x'][k],y=PK[n]['y'][k],snr=PK[n]['snr'][k])
    print(f"{n}: {k.sum():4d} outer peaks of {len(r)}")
NEW={REF:(0.0,0.0)}; STAT={}
for n in EXP:
    if n==REF: continue
    o=list(OFF0[n])
    for it,tol in enumerate([16.0,6.0,3.0,2.0]):
        t=cKDTree(np.c_[KEEP[n]['x']-o[0],KEEP[n]['y']-o[1]])
        d,i=t.query(np.c_[KEEP[REF]['x'],KEEP[REF]['y']],distance_upper_bound=tol)
        ok=np.isfinite(d); ia=np.nonzero(ok)[0]; ib=i[ok]
        if ok.sum()<3: break
        dx=KEEP[n]['x'][ib]-KEEP[REF]['x'][ia]; dy=KEEP[n]['y'][ib]-KEEP[REF]['y'][ia]
        o=[float(np.median(dx)),float(np.median(dy))]
    NEW[n]=tuple(o); STAT[n]=(ok.sum(),np.std(dx),np.std(dy))
    print(f"  {n}: dx={o[0]:+9.3f} dy={o[1]:+9.3f}  (was {OFF0[n][0]:+8.2f},{OFF0[n][1]:+8.2f})  "
          f"shift={o[0]-OFF0[n][0]:+6.2f},{o[1]-OFF0[n][1]:+6.2f}  n={ok.sum()} rms=({np.std(dx):.2f},{np.std(dy):.2f})")
pickle.dump({'off':NEW},open("offsets4.pkl","wb"))
# lunar motion relative to the star field
print("\nlunar disc centre in the STAR frame (ref grid):")
tt=[('DSC06987',29.0),('DSC06991',57.5),('DSC06993',62.0),('DSC06996',77.0)]
for n,t in tt:
    if n in moon:
        gx=moon[n][0]-NEW[n][0]; gy=moon[n][1]-NEW[n][1]
        print(f"  {n} (t~C2+{t:4.1f}s): ({gx:7.1f},{gy:7.1f})")
