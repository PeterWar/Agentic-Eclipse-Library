#!/usr/bin/env python3
"""Efemèrides del Sol i dels planetes al mig de la totalitat (skyfield + DE440s).

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sol_planetes.py
(sessió ea55df18 del 16-08-2026). Promogut sense canviar cap número: només
l'efemèride surt ara de comu.efemeride() en lloc d'una ruta absoluta.
Només escriu a stdout. És d'on surten el centre de cerca J2000 (142,10549 /
+14,90721) i el radi solar aparent ≈947,07″ que la resta de la cadena porta
com a constant.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu

from skyfield.api import load, wgs84, Star
from skyfield.framelib import ecliptic_frame
import numpy as np

ts = load.timescale()
eph = comu.efemeride()
t = ts.utc(2026, 8, 12, 18, 29, 38)

earth = eph['earth']
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)

sun = eph['sun']
app_sun = lloc.at(t).observe(sun).apparent()
ra, dec, dist = app_sun.radec()   # apparent of-date? default is ICRF
ra_d, dec_d, _ = app_sun.radec(epoch='date')
alt, az, _ = app_sun.altaz(temperature_C=20.0, pressure_mbar=930.0)
alt0, az0, _ = app_sun.altaz()

print("=== SOL, 2026-08-12 18:29:38 UTC ===")
print("RA (ICRS/J2000) :", ra.hstr(), " =", round(ra._degrees,5), "deg")
print("Dec(ICRS/J2000) :", dec.dstr(), " =", round(dec.degrees,5), "deg")
print("RA (de la data) :", ra_d.hstr(), " =", round(ra_d._degrees,5), "deg")
print("Dec(de la data) :", dec_d.dstr(), " =", round(dec_d.degrees,5), "deg")
print("distancia UA    :", round(dist.au,6))
print("Alt geometrica  :", round(alt0.degrees,4), " Az:", round(az0.degrees,4))
print("Alt refractada  :", round(alt.degrees,4), " Az:", round(az.degrees,4))
print("massa aire (Pickering, alt refr):", round(1/np.sin(np.radians(alt.degrees + 244/(165+47*alt.degrees**1.1))),3))
sd = np.degrees(np.arcsin(696000.0/(dist.au*149597870.7)))*3600
print("radi solar aparent (arcsec):", round(sd,2))

targets = {'mercury':'mercury barycenter','venus':'venus barycenter','mars':'mars barycenter',
           'jupiter':'jupiter barycenter','saturn':'saturn barycenter'}
print()
print("=== PLANETES: separacio al centre del Sol ===")
res={}
for name, key in targets.items():
    p = lloc.at(t).observe(eph[key]).apparent()
    sep = app_sun.separation_from(p)
    pra, pdec, pd = p.radec()
    palt, paz, _ = p.altaz()
    # angle de posicio respecte del Sol
    res[name]=(sep.degrees, pra._degrees, pdec.degrees, palt.degrees, paz.degrees, pd.au)
    print(f"{name:9s} sep={sep.degrees:7.3f} deg  RA={pra._degrees:8.4f} Dec={pdec.degrees:8.4f}  alt={palt.degrees:7.3f}  d={pd.au:.4f} UA")

# elongacio i fase per magnitud
print()
print("=== dades per a magnitud (Sol-planeta-observador) ===")
sun_from_earthc = eph['earth'].at(t).observe(sun)
for name,key in targets.items():
    p_helio = eph[key].at(t).observe(sun)  # not needed
for name,key in targets.items():
    obj = eph[key]
    v_obs = lloc.at(t).observe(obj).apparent()
    r_helio = (obj - sun).at(t).position.au
    r = np.linalg.norm(r_helio)
    delta = v_obs.distance().au
    # angle de fase
    sun_dist = app_sun.distance().au
    cosphase = (r**2 + delta**2 - sun_dist**2)/(2*r*delta)
    phase = np.degrees(np.arccos(np.clip(cosphase,-1,1)))
    print(f"{name:9s} r={r:.5f} UA  delta={delta:.5f} UA  angle de fase={phase:.2f} deg")
