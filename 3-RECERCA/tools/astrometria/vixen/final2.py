#!/usr/bin/env python3
"""Fotometria d'obertura (r=5, anell 9–14, APC=1.031) sobre la pila i sobre cada fotograma desplaçat; recompte de fotogrames amb S/N>3 → final.json.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/final2.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); cap constant,
llindar ni ordre de fotogrames tocat.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, json, warnings; warnings.filterwarnings('ignore')
cand=np.load('cand.npy'); moons=np.load('moons.npy')
FF=np.load('stack_flux.npy'); SG=np.load('stack_sig.npy')
SH=json.load(open('shifts_start.json'))
FR=[('572A2978',1.0),('572A2979',2.0),('572A2980',2.0),('572A2981',2.0),
    ('572A2982',10.3),('572A2983',10.3),('572A2984',10.3),('572A2996',1.0)]
B=14
yy,xx=np.mgrid[-B:B+1,-B:B+1]; rr=np.hypot(xx,yy)
ANN=(rr>9)&(rr<=B); AP=rr<=5.0
def phot_at(img,sig,x,y):
    x0,y0=int(round(x)),int(round(y))
    if x0<B+2 or y0<B+2 or x0>=img.shape[1]-B-2 or y0>=img.shape[0]-B-2: return np.nan,np.nan
    sub=img[y0-B:y0+B+1,x0-B:x0+B+1].astype(np.float64)
    ss=sig[y0-B:y0+B+1,x0-B:x0+B+1].astype(np.float64)
    bg=np.nanmedian(sub[ANN])
    if not np.isfinite(bg): return np.nan,np.nan
    v=np.isfinite(sub)&AP
    if v.sum()<AP.sum()*0.7: return np.nan,np.nan
    F=np.nansum(sub[v]-bg)*AP.sum()/v.sum()
    n=np.nanmedian(ss[ANN])*np.sqrt(AP.sum())
    return F,F/max(n,1e-9)
res={}; sg={}
for f,exp in FR:
    res[f]=np.load('res_%s.npy'%f); sg[f]=np.load('sig_%s.npy'%f)
APC=1.031  # r=5 -> total, from growth curve (1709/1764 inverse)
out=[]
print('%3s %8s %8s %8s %7s %6s %11s %8s  %s'%('id','x_px','y_px','r_px','r_Rm','r_deg','flux ADU/s','SNR','per-frame SNR  [1s 2s 2s 2s 10.3s 10.3s 10.3s 1s]'))
for i,(x,y,pk,sa,sb) in enumerate(cand):
    r=np.hypot(x-moons[4][0],y-moons[4][1])
    F,S=phot_at(FF,SG,x,y); F*=APC
    per=[]
    for f,exp in FR:
        dt,dx,dy=SH[f]
        pf,ps=phot_at(res[f],sg[f],x+dx,y+dy)
        per.append((pf/exp*APC if pf==pf else np.nan, ps))
    ns=[p[1] for p in per]
    nfr=sum(1 for v in ns if v==v and v>3)
    nlong=sum(1 for v in ns[4:7] if v==v and v>3)
    out.append(dict(id=i,x=float(x),y=float(y),r=float(r),flux=float(F),snr=float(S),nfr=nfr,nlong=nlong,
                    per_snr=[None if v!=v else round(float(v),1) for v in ns],
                    per_flux=[None if p[0]!=p[0] else round(float(p[0]),1) for p in per]))
    print('%3d %8.2f %8.2f %8.0f %7.2f %6.2f %11.1f %8.1f  %s   n>3s=%d (long %d)'%(
        i,x,y,r,r/451.0,r*2.158/3600,F,S,' '.join('%5.1f'%v if v==v else '   na' for v in ns),nfr,nlong))
json.dump(out,open('final.json','w'),indent=0)
