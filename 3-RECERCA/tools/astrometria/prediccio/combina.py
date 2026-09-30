#!/usr/bin/env python3
"""Enriqueix hip_4deg.csv amb SpType/HD/B−V de hip_main.dat, hi afegeix
Tycho-2 (tyc2.tsv, V = VT − 0,090·(BT−VT)) i classifica cada candidata V≤8
com SEGUR/POSSIBLE/FORA per a cada tren amb les escales ANTIGUES 3,234 i
2,158 ″/px (criteri purament radial: semicostat curt i semidiagonal).

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/combina.py
(sessió ea55df18 del 16-08-2026). Promogut sense canviar cap número:
- hip_main.dat es llegeix de comu.HIP_MAIN, tyc2.tsv de comu.TYC2;
- hip_4deg.csv es llegeix i candidates_v8.csv s'escriu a comu.work('prediccio').
Sortida: candidates_v8.csv (42 estrelles V≤8 dins 4° al rescat).
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
import os
os.chdir(comu.work("prediccio"))

import numpy as np, pandas as pd, math

hip4 = pd.read_csv('hip_4deg.csv')
want = set(hip4.HIP.astype(int))
extra={}
with open(comu.HIP_MAIN) as f:
    for line in f:
        p=line.split('|')
        try: h=int(p[1])
        except: continue
        if h in want:
            extra[h]=dict(BV=p[37].strip(), HD=p[71].strip(), SpType=p[76].strip())
hip4['SpType']=[extra.get(h,{}).get('SpType','') for h in hip4.HIP]
hip4['HD']=[extra.get(h,{}).get('HD','') for h in hip4.HIP]
hip4['BV']=[extra.get(h,{}).get('BV','') for h in hip4.HIP]

lines=open(comu.TYC2).readlines()
hdr=[i for i,l in enumerate(lines) if l.startswith('_RAJ2000')][0]
cols=[c.strip() for c in lines[hdr].split('\t')]
rows=[]
for l in lines[hdr+3:]:
    if l.startswith('#') or not l.strip(): continue
    v=[x.strip() for x in l.rstrip('\n').split('\t')]
    if len(v)!=len(cols): continue
    rows.append(dict(zip(cols,v)))
ty=pd.DataFrame(rows)
for c in ['_RAJ2000','_DEJ2000','_r','BTmag','VTmag']:
    ty[c]=pd.to_numeric(ty[c],errors='coerce')
ty=ty.dropna(subset=['VTmag'])
ty['V']=np.where(ty.BTmag.notna(), ty.VTmag-0.090*(ty.BTmag-ty.VTmag), ty.VTmag)
ty['HIP_n']=pd.to_numeric(ty['HIP'],errors='coerce')
tsel=ty[(ty._r<=4.0)&(ty.V<=8.0)]
print("Tycho-2 amb V<=8,0 dins 4 deg:", len(tsel), "| dels quals sense HIP:", tsel.HIP_n.isna().sum())
print(tsel[tsel.HIP_n.isna()][['_RAJ2000','_DEJ2000','_r','BTmag','VTmag','V']].to_string(index=False))
h8=hip4[hip4.Vmag<=8.0].copy()
print("\nHipparcos V<=8,0 dins 4 deg:", len(h8))
miss=h8[~h8.HIP.isin(tsel.HIP_n.dropna().astype(int))]
print("HIP V<=8 que Tycho-2 no classifica V<=8 (color/blend):", len(miss))
print(miss[['HIP','Vmag','sep_deg']].to_string(index=False))

S_SONY,S_R6=3.234,2.158
sony_hh=5304/2*S_SONY/3600; sony_hw=7952/2*S_SONY/3600; sony_hd=math.hypot(sony_hw,sony_hh)
r6_hh=4640/2*S_R6/3600; r6_hw=6960/2*S_R6/3600; r6_hd=math.hypot(r6_hw,r6_hh)
print(f"\nSony camp {7952*S_SONY/3600:.3f} x {5304*S_SONY/3600:.3f} deg | semi curt {sony_hh:.3f} llarg {sony_hw:.3f} diag {sony_hd:.3f}")
print(f"R6   camp {6960*S_R6/3600:.3f} x {4640*S_R6/3600:.3f} deg | semi curt {r6_hh:.3f} llarg {r6_hw:.3f} diag {r6_hd:.3f}")
RSUN=947.07/3600.0
h8['r_Rsol']=h8.sep_deg/RSUN
h8['px_sony']=h8.sep_deg*3600/S_SONY
h8['px_r6']=h8.sep_deg*3600/S_R6
f=lambda r,hh,hd:'SEGUR' if r<=hh else ('POSSIBLE' if r<=hd else 'FORA')
h8['sony']=[f(r,sony_hh,sony_hd) for r in h8.sep_deg]
h8['r6']=[f(r,r6_hh,r6_hd) for r in h8.sep_deg]
pd.set_option('display.width',260)
print("\n=== V<=8,0 dins 4 graus, ordenades per separacio ===")
print(h8[['HIP','HD','Vmag','BV','SpType','sep_deg','r_Rsol','px_sony','sony','px_r6','r6']].to_string(index=False,
  formatters={'sep_deg':'{:.4f}'.format,'r_Rsol':'{:.2f}'.format,'px_sony':'{:.0f}'.format,'px_r6':'{:.0f}'.format}))
h8.to_csv('candidates_v8.csv',index=False)
print("fitxer:", Path.cwd() / 'candidates_v8.csv')
