#!/usr/bin/env python3
"""Unicitat i taxa d'atzar del creuament: candidates a <5/<15/<45 px i 400 desplacaments+rotacions aleatoris (NUL).
Entrades: comu.work('xmatch')/{final_solution.json, cat2_{sony,r6}.csv, final_match_{sony,r6}.csv}. Sortida: stdout.
LLAVOR: l'original feia default_rng(7); es conserva (era fixa, no consta al mapa).

Origen: rescat estrelles_placa_flats_16-08/skeptic2/unic.py (sessio ea55df18, 16-08-2026).
Promogut a research/tools/astrometria/esceptic/: nomes canvien les rutes (comu). Cap constant tocada.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
import numpy as np, pandas as pd, json, sys
X=comu.work('xmatch')
sol=json.load(open(X/'final_solution.json'))
rng=np.random.default_rng(7)
SH={'sony':(7968,5320),'r6':(6960,4640)}
for tag in ('sony','r6'):
    S=sol[tag+'_radial']; px=np.array(S['px']); py=np.array(S['py'])
    cat=pd.read_csv(X/f'cat2_{tag}.csv')
    m=pd.read_csv(X/f'final_match_{tag}.csv')
    W,H=SH[tag]
    def proj(xi,eta):
        r2=xi*xi+eta*eta
        A=np.column_stack([np.ones_like(xi),xi,eta,xi*r2,eta*r2])
        return A@px,A@py
    for VLIM in (11.0,12.5):
        c=cat[(cat.sep_deg<5.0)&(cat.Vuse<=VLIM)]
        CX,CY=proj(c.xh_as.values,c.yh_as.values)
        inf=(CX>-200)&(CX<W+200)&(CY>-200)&(CY<H+200)
        CX,CY=CX[inf],CY[inf]
        DX,DY=m.x.values,m.y.values
        d=np.hypot(DX[:,None]-CX[None,:],DY[:,None]-CY[None,:])
        dmin=d.min(1)
        # unicitat: quantes candidates del cataleg a <5 px i <15 px de cada deteccio
        n5=(d<5).sum(1); n15=(d<15).sum(1); n45=(d<45).sum(1)
        # NUL: desplacaments aleatoris grans de la llista de deteccions
        nul=[]
        for _ in range(400):
            sx,sy=rng.uniform(-1500,1500,2)
            th=rng.uniform(0,2*np.pi)
            ct,st=np.cos(th),np.sin(th)
            cx0,cy0=W/2,H/2
            rx=cx0+(DX-cx0)*ct-(DY-cy0)*st+sx
            ry=cy0+(DX-cx0)*st+(DY-cy0)*ct+sy
            dd=np.hypot(rx[:,None]-CX[None,:],ry[:,None]-CY[None,:]).min(1)
            nul.append(dd)
        nul=np.array(nul)
        print(f'--- {tag}  Vlim={VLIM}  cataleg dins el quadre={len(CX)}  deteccions={len(DX)}')
        print(f'    REAL : dmin mediana={np.median(dmin):.2f} px, max={dmin.max():.2f}, '
              f'n(<2px)={(dmin<2).sum()}, n(<5px)={(dmin<5).sum()}')
        print(f'    NUL  : dmin mediana={np.median(nul):.1f} px, '
              f'esperats <2px={np.mean((nul<2).sum(1)):.2f}, <5px={np.mean((nul<5).sum(1)):.2f}, '
              f'<45px={np.mean((nul<45).sum(1)):.1f}')
        print(f'    UNICITAT: candidates alternatives dins 5px: max={n5.max()} (mediana {np.median(n5):.0f}); '
              f'dins 15px: max={n15.max()}, n_deteccions_amb>1={(n15>1).sum()}; dins 45px: max={n45.max()}, >1 a {(n45>1).sum()} deteccions')
    print()
