#!/usr/bin/env python3
"""PREDICCIÓ del camp d'estrelles: Hipparcos (hip_main.dat, CDS I/239) dins de
4,0° del Sol aparent al mig de la totalitat, totes les magnituds.

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/estrelles.py
(sessió ea55df18 del 16-08-2026). Promogut sense canviar cap número:
- l'efemèride surt de comu.efemeride();
- hip_main.dat es llegeix de comu.HIP_MAIN (abans: 'hip_main.dat' al cwd);
- hip_4deg.csv s'escriu a comu.work('prediccio') (abans: al cwd).
Sortida: hip_4deg.csv (112 estrelles al rescat) i el recompte per magnitud.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
import os
os.chdir(comu.work("prediccio"))

from skyfield.api import load, wgs84, Star
from skyfield.data import hipparcos
import numpy as np, pandas as pd

ts = load.timescale()
eph = comu.efemeride()
t = ts.utc(2026, 8, 12, 18, 29, 38)
earth = eph['earth']
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
app_sun = lloc.at(t).observe(eph['sun']).apparent()
sra, sdec, sdist = app_sun.radec()

with open(comu.HIP_MAIN) as f:
    df = hipparcos.load_dataframe(f)
print("entrades amb astrometria:", len(df))

# prefiltre gros per RA/Dec J2000 (deg)
ra = df['ra_degrees'].values; dec = df['dec_degrees'].values
c = np.radians(142.10549); d0 = np.radians(14.90721)
cosang = np.sin(np.radians(dec))*np.sin(d0) + np.cos(np.radians(dec))*np.cos(d0)*np.cos(np.radians(ra)-c)
sep0 = np.degrees(np.arccos(np.clip(cosang,-1,1)))
m = (sep0 < 6.0)
sub = df[m].copy()
sub['sep_j2000'] = sep0[m]
print("dins 6 deg (J2000, cataleg):", len(sub))

rows=[]
for hip, r in sub.iterrows():
    if not np.isfinite(r['magnitude']): continue
    st = Star.from_dataframe(df.loc[hip])
    ap = lloc.at(t).observe(st).apparent()
    sep = app_sun.separation_from(ap)
    ara, adec, _ = ap.radec()
    rows.append((int(hip), r['magnitude'], sep.degrees, ara._degrees, adec.degrees, r['ra_degrees'], r['dec_degrees'], r['parallax_mas']))

out = pd.DataFrame(rows, columns=['HIP','Vmag','sep_deg','ra_app','dec_app','ra_j2000','dec_j2000','plx_mas'])
out = out.sort_values('sep_deg')
sel = out[(out.sep_deg<=4.0)]
print()
print("=== Hipparcos dins 4,0 graus del centre del Sol (totes les magnituds del cataleg) ===")
pd.set_option('display.width',200)
print(sel[sel.Vmag<=9.5].to_string(index=False))
print()
print("recompte per magnitud dins 4 deg:")
for lim in [5,6,7,8,9,10,11]:
    print(f"  V<= {lim}: {(sel.Vmag<=lim).sum()}")
sel.to_csv('hip_4deg.csv', index=False)
print("fitxer:", Path.cwd() / 'hip_4deg.csv')
