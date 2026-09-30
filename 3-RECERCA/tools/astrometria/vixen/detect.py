#!/usr/bin/env python3
"""Detecció sobre la pila S/N: DAOStarFinder (4.5, fwhm 3.5), retall de la franja lunar (r>1,16·451 px a tots els fotogrames via center_fit+shifts), presència a les dues mitges piles (>3σ), dedup 6 px → cand.npy (32), moons.npy.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/detect.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); cap constant,
llindar ni ordre de fotogrames tocat.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, json
from scipy import ndimage as ndi
from photutils.detection import DAOStarFinder
import warnings; warnings.filterwarnings('ignore')

snr=np.load('stack_snr.npy'); A=np.load('halfA_snr.npy'); B=np.load('halfB_snr.npy')
d=DAOStarFinder(threshold=4.5,fwhm=3.5,roundness_range=(-1.6,1.6),sharpness_range=(0.05,2.0),exclude_border=True)
tb=d(snr)
x=np.array(tb['x_centroid']); y=np.array(tb['y_centroid']); pk=np.array(tb['peak'])
print('raw candidates',len(x))
# --- moon centre in registered (star) coords, per frame time
cf=json.load(open('center_fit.json')); T0=cf['T0']; pxf=cf['px']; pyf=cf['py']
SH=json.load(open('shifts_start.json'))
FR=[('572A2978',1.0,73742.55),('572A2979',2.0,73744.45),('572A2980',2.0,73747.35),('572A2981',2.0,73750.26),
    ('572A2982',10.3,73753.41),('572A2983',10.3,73766.48),('572A2984',10.3,73779.88),('572A2996',1.0,73804.26)]
moons=[]
for f,exp,t in FR:
    tm=t+exp/2
    mx=np.polyval(pxf,tm-T0); my=np.polyval(pyf,tm-T0)
    dt,dx,dy=SH[f]
    moons.append((mx-dx,my-dy))
moons=np.array(moons)
RM=451.0
rmin=np.min([np.hypot(x-m[0],y-m[1]) for m in moons],axis=0)
keep=rmin>1.16*RM
print('after lunar-limb swath cut (r>1.16 Rmoon in every frame):',keep.sum())
x,y,pk=x[keep],y[keep],pk[keep]
def val(img,x,y,r=2):
    xi=np.round(x).astype(int); yi=np.round(y).astype(int)
    out=np.zeros(len(x))
    for k in range(len(x)):
        out[k]=img[max(0,yi[k]-r):yi[k]+r+1,max(0,xi[k]-r):xi[k]+r+1].max()
    return out
sa=val(A,x,y); sb=val(B,x,y)
good=(sa>3.0)&(sb>3.0)
print('present in BOTH independent half-stacks (>3 sigma):',good.sum())
x,y,pk,sa,sb=x[good],y[good],pk[good],sa[good],sb[good]
# deduplicate within 6 px keeping brightest
o=np.argsort(-pk); x,y,pk,sa,sb=x[o],y[o],pk[o],sa[o],sb[o]
sel=[]
for i in range(len(x)):
    if all(np.hypot(x[i]-x[j],y[i]-y[j])>6 for j in sel): sel.append(i)
sel=np.array(sel)
x,y,pk,sa,sb=x[sel],y[sel],pk[sel],sa[sel],sb[sel]
print('after dedup:',len(x))
np.save('cand.npy',np.vstack([x,y,pk,sa,sb]).T)
np.save('moons.npy',moons)
for i in range(min(len(x),80)):
    print('%3d x=%8.2f y=%8.2f  snr=%6.2f  A=%5.2f B=%5.2f  r_moon=%.0f'%(i,x[i],y[i],pk[i],sa[i],sb[i],
        np.hypot(x[i]-moons[4][0],y[i]-moons[4][1])))
