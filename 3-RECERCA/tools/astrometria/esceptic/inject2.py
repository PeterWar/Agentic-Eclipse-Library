#!/usr/bin/env python3
"""Injeccio CORREGIDA (x2) i soroll real de la fotometria COMBINADA de 7 fotogrames,
replicant exactament la combinacio de zp.py (pes = temps d'exposicio).

Origen: rescat estrelles_placa_flats_16-08/skeptic2/inject2.py (sessio ea55df18, 16-08-2026).
Promogut a research/tools/astrometria/esceptic/: nomes canvien les rutes (comu) i
l'import de phot2 (ara des de ../xmatch/). Cap constant, llavor ni llindar tocat.

Entrades: 7 ARW (comu.DADES_300MM); comu.work('sony')/{masterdark_{1,2,8}s.npy, bkg_<nom>.npy,
offsets6.pkl}; comu.work('xmatch')/{final_solution.json, final_match_sony.csv, cogf_sony.npz}.
Sortida: comu.work('esceptic')/noise.npy (5 floats, soroll 1 sigma per banda) + stdout.
Cost: ~10 min (7 ARW de 170 MB, 90 posicions x 5 bandes x 3 mesures per fotograma).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
# phot_stamp i SONY_EXP son els del pipeline promogut (research/tools/astrometria/xmatch/phot2.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'xmatch'))
import numpy as np, rawpy, pandas as pd, pickle, json
from scipy import ndimage as ndi
try:
    from phot2 import phot_stamp, SONY_EXP
except ImportError as ex:
    raise SystemExit(f"inject2.py necessita xmatch/phot2.py (phot_stamp, SONY_EXP): {ex}")

SD = comu.work('sony')
D = comu.DADES_300MM
XD = comu.work('xmatch')
OUTD = comu.work('esceptic')
sol=json.load(open(XD/'final_solution.json'))['sony_radial']
off=pickle.load(open(SD/'offsets6.pkl','rb'))['off']
tab=pd.read_csv(XD/'final_match_sony.csv')
cog=np.load(XD/'cogf_sony.npz'); CORR=cog['ref'][5]/np.nanmedian(cog['ref'][13:18])
RSUN=947.07/sol['scale']; rng=np.random.default_rng(11)
sig=3.74/2.3548
BANDS=[(1.6,2.6),(2.6,4),(4,6),(6,9),(9,14)]
NP=90
# posicions comunes a tots els fotogrames (coords del sistema de referencia)
def band(lo,hi,n,W,H):
    out=[]; g=0
    while len(out)<n and g<40000:
        g+=1
        th=rng.uniform(0,2*np.pi); rr=rng.uniform(lo,hi)*RSUN
        x,y=sol['sun_x']+rr*np.cos(th),sol['sun_y']+rr*np.sin(th)
        if not(200<x<W-200 and 200<y<H-200): continue
        if np.min(np.hypot(tab.x.values-x,tab.y.values-y))<60: continue
        out.append((x,y))
    return np.array(out)
POS={}
FR={}
for name,e in SONY_EXP.items():
    with rawpy.imread(str(D/(name+'.ARW'))) as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    md=np.load(SD/f'masterdark_{int(e)}s.npy'); bkg=np.load(SD/f'bkg_{name}.npy')
    res=raw-md-bkg
    valid=((col==1)|(col==3))&(raw<15600)&(~ndi.binary_dilation(raw>=15600,iterations=6))
    H,W=res.shape
    if not POS:
        for lo,hi in BANDS: POS[(lo,hi)]=band(lo,hi,NP,W,H)
    dx,dy=off[name]
    FR[name]=dict(exp=e)
    for b,P in POS.items():
        E=np.full(len(P),np.nan); I4=np.full(len(P),np.nan); I12=np.full(len(P),np.nan)
        for i,(x,y) in enumerate(P):
            o=phot_stamp(res,valid,x+dx,y+dy,recenter=False)
            if o is not None: E[i]=o[0][5]*2.0/e
            xi,yi=int(round(x+dx)),int(round(y+dy)); Pp=50
            if not(Pp<xi<W-Pp and Pp<yi<H-Pp): continue
            Y,Xg=np.mgrid[-Pp:Pp+1,-Pp:Pp+1]
            sub=res[yi-Pp:yi+Pp+1,xi-Pp:xi+Pp+1].copy()
            for k,Finj in enumerate((400.,1200.)):
                amp=(Finj*e)/(2*np.pi*sig**2)
                res[yi-Pp:yi+Pp+1,xi-Pp:xi+Pp+1]=sub+amp*np.exp(
                    -((Xg-(x+dx-xi))**2+(Y-(y+dy-yi))**2)/(2*sig**2))
                o2=phot_stamp(res,valid,x+dx,y+dy)
                if o2 is not None:
                    v=o2[0][5]*2.0/e/CORR
                    if k==0: I4[i]=v
                    else: I12[i]=v
            res[yi-Pp:yi+Pp+1,xi-Pp:xi+Pp+1]=sub
        FR[name][b]=(E,I4,I12)
    print('fet',name); sys.stdout.flush()
    del raw,res,valid,bkg,md

print('\n=== SONY: soroll REAL de la fotometria COMBINADA (7 fotogrames, 24 s) ===')
print(f'{"banda R/Rsol":>13s} {"n":>4s} {"biaix (ADU/s)":>14s} {"SOROLL 1sigma":>14s} {"SNR d\'una V=7,7":>16s}')
NOISE={}
for b in BANDS:
    Es=np.array([FR[n][b][0] for n in FR]); w=np.array([FR[n]['exp'] for n in FR])[:,None]
    C=np.nansum(Es*w,0)/np.nansum(np.where(np.isfinite(Es),w,0),0)
    C=C[np.isfinite(C)]
    md=np.median(C); sd=1.4826*np.median(np.abs(C-md)); NOISE[b]=sd
    print(f'{b[0]:5.1f}-{b[1]:5.1f} {len(C):4d} {md:14.1f} {sd:14.1f} {350/sd:16.1f}')
print('\n=== INJECCIO: flux recuperat / flux injectat (1,0 = sense biaix) ===')
print(f'{"banda":>13s} {"F=400":>22s} {"F=1200":>22s}')
for b in BANDS:
    o=[]
    for k in (1,2):
        Es=np.array([FR[n][b][k] for n in FR]); w=np.array([FR[n]['exp'] for n in FR])[:,None]
        C=np.nansum(Es*w,0)/np.nansum(np.where(np.isfinite(Es),w,0),0)
        C=C[np.isfinite(C)]/(400. if k==1 else 1200.)
        md=np.median(C) if len(C) else np.nan
        o.append(f'{md:.3f}+-{(1.4826*np.median(np.abs(C-md)) if len(C) else np.nan):.3f} (n={len(C)})')
    print(f'{b[0]:5.1f}-{b[1]:5.1f} {o[0]:>22s} {o[1]:>22s}')
np.save(OUTD/'noise.npy',np.array([NOISE[b] for b in BANDS]))
print('desat', OUTD/'noise.npy')
