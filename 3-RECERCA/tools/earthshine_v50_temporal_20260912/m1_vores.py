"""M1: vores aparents al marc de la ROI lunar (1440 azimuts, mateix detector per a tot).
Detector: al llarg de cada raig des del centre lunar, nivell interior = mediana a [F4-10,F4-5],
exterior = mediana a [F4+8,F4+14]; vora = primer creuament del 50 %. Ajust de cercle robust
r(θ) = R + dx cosθ + dy sinθ amb retall a 2,5 σ (3 passades)."""
import json, numpy as np
from pathlib import Path
from scipy.ndimage import map_coordinates
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); OUT=ROOT/'output/earthshine_v50_temporal_20260912'
CX=699.568111973117; CY=699.6475341408573; N=1400
V=ROOT/'output/earthshine_v49_pere_reveal_20260912'; O=ROOT/'output/earthshine_v50_causal_20260912'
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False)
rr=np.arange(430,482,0.25)
def prof(img):
    x=CX+np.cos(th)[:,None]*rr[None,:]; y=CY+np.sin(th)[:,None]*rr[None,:]
    return map_coordinates(img.astype(np.float64),[y.ravel(),x.ravel()],order=1,mode='nearest').reshape(len(th),len(rr))
def edge(P,inner=(-10,-5),outer=(8,14),sign=+1):
    e=np.full(len(th),np.nan); lo=np.full(len(th),np.nan); hi=np.full(len(th),np.nan)
    for i in range(len(th)):
        p=P[i]; r0=f4[i]
        mi=(rr>=r0+inner[0])&(rr<r0+inner[1]); mo=(rr>=r0+outer[0])&(rr<r0+outer[1])
        a=np.median(p[mi]); b=np.median(p[mo]); lo[i]=a; hi[i]=b
        if abs(b-a)<1e-9: continue
        half=(a+b)/2; q=(p-half)*np.sign(b-a)
        k=np.where((q[:-1]<0)&(q[1:]>=0)&(rr[:-1]>=r0-8))[0]
        if len(k)==0: continue
        k=k[0]; e[i]=rr[k]+(rr[k+1]-rr[k])*(-q[k])/(q[k+1]-q[k])
    return e,lo,hi
def fit(e,excl=None):
    m=np.isfinite(e)
    if excl is not None: m&=~excl
    A=np.c_[np.ones(1440),np.cos(th),np.sin(th)]
    for _ in range(3):
        c,*_=np.linalg.lstsq(A[m],e[m],rcond=None); res=e-A@c; s=np.nanstd(res[m]); m&=np.abs(res)<2.5*s
    return dict(R=float(c[0]),dx=float(c[1]),dy=float(c[2]),rms=float(np.nanstd(res[m])),n=int(m.sum()))
G=lambda a:a[...,1]
res={}
# 0. F4 mateix
res['F4']=fit(f4)
# 1. forat de la base (sense font lunar)
sense=np.load(V/'A2_sense_font_lunar_RGB16.npy'); eS,loS,hiS=edge(prof(G(sense))); res['forat_sense_font_lunar']=fit(eS)
# 2. alfa de Pere (heretada)
am=np.load(V/'A0_inherited_mask_roi.npy'); eA,_,_=edge(prof(am),inner=(-10,-5),outer=(8,14)); res['alfa_Pere_50']=fit(eA)
# 3. capes solars L4 (rgb sense màscara) i el seu producte alpha*mask
shifts={'12':(-3,0),'11':(0,0),'10':(0,0),'09':(0,0)}
eL={}
for L in ('12','11','10','09'):
    z=np.load(O/f'L4_original_{L}.npz'); rgb=G(z['rgb']).astype(np.float64); am_=z['alpha'].astype(np.float64)*z['mask'].astype(np.float64)/65535
    sx,sy=shifts[L]
    if (sx,sy)!=(0,0): rgb=np.roll(np.roll(rgb,sx,axis=1),sy,axis=0); am_=np.roll(np.roll(am_,sx,axis=1),sy,axis=0)
    e,lo,hi=edge(prof(rgb),inner=(-8,-3),outer=(4,9)); eL[L]=e; res[f'capa{L}_lluna_rgb_shift{shifts[L]}']=fit(e)
    e2,_,_=edge(prof(am_),inner=(-8,-3),outer=(4,12)); res[f'capa{L}_alpha*mask_50']=fit(e2)
    # també sense el shift per 12
    if L=='12':
        e3,_,_=edge(prof(G(z['rgb']).astype(np.float64)),inner=(-8,-3),outer=(4,9)); res['capa12_lluna_rgb_sense_shift']=fit(e3)
# 4. Pere actual: on és el màxim de la franja i el mínim de la vall, per sector
pere=np.load(V/'A2_Pere_actual_RGB16.npy'); P=prof(G(pere))
sec=(np.arange(1440)//120)
fr=[]
for s in range(12):
    p=np.median(P[sec==s],axis=0); d=rr-np.median(f4[sec==s])
    w=(d>-8)&(d<8); i=np.argmax(p[w]); j=np.argmin(p[w][i:])+i
    fr.append(dict(sector=s,d_max_franja=float(d[w][i]),G_max=float(p[w][i]),d_min_vall=float(d[w][j]),G_min=float(p[w][j]),G_disc=float(np.median(p[(d>-20)&(d<-12)])),G_corona=float(np.median(p[(d>8)&(d<14)]))))
res['franja_i_vall_Pere_per_sector']=fr
# 5. vora del forat per sector relatiu a F4
res['forat_menys_F4_per_sector_12']=[float(np.nanmedian((eS-f4)[sec==s])) for s in range(12)]
res['alfa_menys_F4_per_sector_12']=[float(np.nanmedian((eA-f4)[sec==s])) for s in range(12)]
for L in eL: res[f'capa{L}_menys_F4_per_sector_12']=[float(np.nanmedian((eL[L]-f4)[sec==s])) for s in range(12)]
np.savez(OUT/'M1_vores.npz',theta=th,f4=f4,forat=eS,alfa=eA,**{f'capa{L}':eL[L] for L in eL})
(OUT/'M1_vores.json').write_text(json.dumps(res,indent=1,ensure_ascii=False))
for k,v in res.items():
    if isinstance(v,dict): print(f'{k:42s} R={v["R"]:.2f} dx={v["dx"]:+.2f} dy={v["dy"]:+.2f} rms={v["rms"]:.2f} n={v["n"]}')
    elif k.endswith('_12'): print(k, np.round(v,2).tolist())
for r in fr: print(r)
