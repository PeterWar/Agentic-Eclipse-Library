#!/usr/bin/env python3
"""Pic verd i pic qualsevol de cada estrella identificada a DSC06993 i DSC06987 (8 s) contra white_level.
Entrades: comu.DADES_300MM/{DSC06993,DSC06987}.ARW, comu.work('xmatch')/final_match_sony.csv, comu.work('sony')/offsets6.pkl. Sortida: stdout.

Origen: rescat estrelles_placa_flats_16-08/skeptic2/sat.py (sessio ea55df18, 16-08-2026).
Promogut a research/tools/astrometria/esceptic/: nomes canvien les rutes (comu). Cap constant tocada.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
import numpy as np, rawpy, pandas as pd, pickle
D=comu.DADES_300MM
tab=pd.read_csv(comu.work('xmatch')/'final_match_sony.csv')
off=pickle.load(open(comu.work('sony')/'offsets6.pkl','rb'))['off']
for name,e in (('DSC06993',8.0),('DSC06987',8.0)):
    with rawpy.imread(str(D/(name+'.ARW'))) as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
        wl=r.white_level
    green=(col==1)|(col==3)
    dx,dy=off[name]
    print(f'=== {name} exp={e}s white_level={wl} raw max global={raw.max():.0f} ===')
    print(f'   pixels >= 15000 al fotograma: {(raw>=15000).sum()}  (>=16000: {(raw>=16000).sum()})')
    rows=[]
    for i in range(len(tab)):
        x=tab.x.values[i]+dx; y=tab.y.values[i]+dy
        xi,yi=int(round(x)),int(round(y))
        if not(30<xi<raw.shape[1]-30 and 30<yi<raw.shape[0]-30): continue
        st=raw[yi-6:yi+7,xi-6:xi+7]; gm=green[yi-6:yi+7,xi-6:xi+7]
        rows.append((tab.det.values[i],tab.V.values[i],st[gm].max(),st.max(),np.median(raw[yi-40:yi+41,xi-40:xi+41])))
    rows.sort(key=lambda r:-r[2])
    print(f'   {"det":6s} {"V":>5s} {"pic_verd":>9s} {"pic_qualsevol":>13s} {"fons_local":>10s} {"marge_a_sat":>11s}')
    for d,V,pg,pa,bg in rows[:8]:
        print(f'   {d:6s} {V:5.2f} {pg:9.0f} {pa:13.0f} {bg:10.0f} {wl-pg:11.0f}')
