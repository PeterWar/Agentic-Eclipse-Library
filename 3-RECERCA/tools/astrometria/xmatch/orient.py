#!/usr/bin/env python3
"""Orientacio: nord celeste al sensor, i comprovacio creuada amb la rotacio de
71,5 graus que el producte d'earthshine va ajustar contra el mapa LROC.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/orient.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, json
from skyfield.api import load, wgs84

ts = load.timescale()
eph = comu.efemeride()
lloc = eph['earth'] + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
t = ts.utc(2026, 8, 12, 18, 29, 48.0)
sol = json.load(open('final_solution.json'))

m = lloc.at(t).observe(eph['moon']).apparent()
ra, dec, _ = m.radec()
a = np.radians(ra._degrees); d = np.radians(dec.degrees)

# pol nord de l'ecliptica (J2000): RA=270 deg, Dec=+66,5607 deg
eps = np.radians(23.4392911)
pra, pdec = np.radians(270.0), np.radians(90.0)-eps
# angle de posicio del pol ecliptic vist des de la Lluna (nord -> est)
dra = pra - a
q = np.degrees(np.arctan2(np.sin(dra)*np.cos(pdec),
                          np.cos(d)*np.sin(pdec)-np.sin(d)*np.cos(pdec)*np.cos(dra)))
q %= 360
print('Lluna: RA %.4f Dec %.4f' % (ra._degrees, dec.degrees))
print(f'Angle de posicio del pol NORD de l\'ecliptica (aprox. l\'eix lunar, '
      f'inclinacio 1,54 graus): {q:.2f} deg des del nord celeste cap a l\'est')

for tag in ('sony', 'r6'):
    S = sol[tag]
    paN = S['pa_north']
    paE = S['pa_east']
    # sentit: angles del sensor mesurats en sentit HORARI des d'"amunt" (-y)
    # est esta a (paE - paN) mod 360 en sentit horari respecte del nord
    dNE = (paE - paN) % 360
    print(f'\n--- {tag} ---')
    print(f'  nord celeste: {paN:.2f} deg en sentit horari des d\'amunt de la imatge')
    print(f'  est celeste : {paE:.2f} deg   (nord->est = {dNE:.2f} deg horaris '
          f'=> {"NO hi ha mirall" if 180 < dNE < 360 else "IMATGE EN MIRALL"})')
    print(f'  zenit       : {S["pa_zenith"]:.2f} deg')
    print(f'  per posar el NORD AMUNT: gira la imatge {paN:.2f} graus en sentit '
          f'ANTIHORARI')
    # eix lunar al sensor: PA(eix) mesurat des del nord cap a l'est al cel;
    # al sensor, "cap a l'est" son (paE-paN) graus horaris des del nord
    sgn = 1.0 if 180 < dNE < 360 else -1.0
    axis_sensor = (paN - q) % 360      # est = sentit antihorari al sensor
    print(f'  eix nord lunar al sensor: {axis_sensor:.2f} deg horaris des d\'amunt')
    if tag == 'sony':
        print(f'  >>> el producte d\'earthshine va AJUSTAR una rotacio de 71,5 deg '
              f'contra el mapa LROC.')
        for cand in (axis_sensor, (axis_sensor) % 360, (-axis_sensor) % 360,
                     (180-axis_sensor) % 360):
            pass
        print(f'  >>> diferencia amb l\'eix lunar calculat: '
              f'{abs(((axis_sensor-71.5+180) % 360)-180):.2f} deg')
