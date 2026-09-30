"""Cataleg projectat al pla tangent de DUES maneres:
   (a) equatorial sense refraccio  (xi=est, eta=nord)
   (b) horitzontal AMB refraccio   (xh=azimutal, yh=cap al zenit)
Aixi es pot veure si l'esbiaix de l'ajust afi es refraccio diferencial."""
import numpy as np, pandas as pd, json
from skyfield.api import load, wgs84, Star

ts = load.timescale()
eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')
lloc = eph['earth'] + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)

TEMP, PRES = 20.0, 930.0     # hipotesi; l'efecte de la refraccio diferencial hi es proporcional
EPOCHS = {'sony': (2026, 8, 12, 18, 29, 48.0), 'r6': (2026, 8, 12, 18, 29, 18.6)}


def uvec_altaz(alt_deg, az_deg):
    a = np.radians(alt_deg); z = np.radians(az_deg)
    return np.array([np.cos(a)*np.cos(z), np.cos(a)*np.sin(z), np.sin(a)])  # N, E, Up


def uvec_radec(ra_deg, dec_deg):
    a = np.radians(ra_deg); d = np.radians(dec_deg)
    return np.array([np.cos(d)*np.cos(a), np.cos(d)*np.sin(a), np.sin(d)])


def tangent(u, ur, e1, e2):
    w = u/np.linalg.norm(u, axis=0)
    den = (w*ur[:, None]).sum(axis=0)
    xi = (w*e1[:, None]).sum(axis=0)/den
    eta = (w*e2[:, None]).sum(axis=0)/den
    return np.degrees(xi)*3600, np.degrees(eta)*3600


ty = pd.read_csv('cat_sony.csv')   # nomes per reaprofitar RA/Dec J2000 i magnituds
info = {}
for tag, e in EPOCHS.items():
    t = ts.utc(*e)
    st = Star(ra_hours=ty._RAJ2000.values/15.0, dec_degrees=ty._DEJ2000.values,
              ra_mas_per_year=ty.pmRA.fillna(0).values,
              dec_mas_per_year=ty.pmDE.fillna(0).values,
              epoch=ts.tt(jd=2451545.0))
    ap = lloc.at(t).observe(st).apparent()
    aps = lloc.at(t).observe(eph['sun']).apparent()

    # --- (a) equatorial, sense refraccio ---
    ra, dec, _ = ap.radec()
    sra, sdec, sdist = aps.radec()
    ur = uvec_radec(sra._degrees, sdec.degrees)
    pole = np.array([0., 0., 1.])
    e2 = pole - ur*np.dot(pole, ur); e2 /= np.linalg.norm(e2)     # nord
    e1 = np.cross(e2, ur)                                          # est
    U = uvec_radec(ra._degrees, dec.degrees)
    xi, eta = tangent(U, ur, e1, e2)

    # --- (b) horitzontal, amb refraccio ---
    alt, az, _ = ap.altaz(temperature_C=TEMP, pressure_mbar=PRES)
    salt, saz, _ = aps.altaz(temperature_C=TEMP, pressure_mbar=PRES)
    urh = uvec_altaz(salt.degrees, saz.degrees)
    zen = np.array([0., 0., 1.])
    f2 = zen - urh*np.dot(zen, urh); f2 /= np.linalg.norm(f2)      # cap al zenit
    f1 = np.cross(f2, urh)
    Uh = uvec_altaz(alt.degrees, az.degrees)
    xh, yh = tangent(Uh, urh, f1, f2)

    # --- (c) horitzontal SENSE refraccio (control) ---
    alt0, az0, _ = ap.altaz()
    salt0, saz0, _ = aps.altaz()
    urh0 = uvec_altaz(salt0.degrees, saz0.degrees)
    g2 = zen - urh0*np.dot(zen, urh0); g2 /= np.linalg.norm(g2)
    g1 = np.cross(g2, urh0)
    xh0, yh0 = tangent(uvec_altaz(alt0.degrees, az0.degrees), urh0, g1, g2)

    d = ty.copy()
    d['xi_as'], d['eta_as'] = xi, eta
    d['xh_as'], d['yh_as'] = xh, yh
    d['xh0_as'], d['yh0_as'] = xh0, yh0
    d['sep_deg'] = np.degrees(np.arccos(np.clip(
        (uvec_radec(ra._degrees, dec.degrees)*ur[:, None]).sum(axis=0), -1, 1)))
    d = d.sort_values('sep_deg').reset_index(drop=True)
    d.to_csv(f'cat2_{tag}.csv', index=False)

    # angle parallactic: rotacio de la base equatorial a la horitzontal
    # projecta el "nord" celeste (e2) sobre la base horitzontal (f1,f2) via alt/az
    # ho fem numericament amb un punt de prova 60" al nord del Sol
    eps = np.radians(60/3600.)
    pn = ur*np.cos(eps) + e2*np.sin(eps)
    dpn = np.degrees(np.arctan2(np.dot(pn, e1), np.dot(pn, e2)))  # ~0 per construccio
    # el converteixo a alt/az fent servir la matriu equatorial->horitzontal implicita:
    info[tag] = dict(sun_alt_refr=float(salt.degrees), sun_az=float(saz.degrees),
                     sun_alt_geom=float(salt0.degrees),
                     Rsun_as=float(np.degrees(np.arcsin(696000.0/(sdist.au*149597870.7)))*3600))
    print(f'{tag}: Sol alt refr={salt.degrees:.4f} geom={salt0.degrees:.4f} az={saz.degrees:.4f}')

json.dump(info, open('suns2.json', 'w'), indent=1)
print('fet')
