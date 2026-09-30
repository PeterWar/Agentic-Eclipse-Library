#!/usr/bin/env python3
"""L'eclipsi del 2 d'agost de 2027: durada, altura i — sobretot — quan es pot
fotografiar de nit el mateix camp d'estrelles a la mateixa altura.

El camp de comparació nocturn és l'única cosa que Eddington tenia i nosaltres
no. Perquè resti la distorsió òptica pròpia ha de venir de la MATEIXA òptica,
el MATEIX focus i, tant com es pugui, la MATEIXA altura sobre l'horitzó.
"""
import math
import numpy as np
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame

ts = load.timescale()
eph = load("/Users/USUARI/.cache/skyfield/de440s.bsp")

LLOCS = [
    ("Cadis",        36.53,  -6.29,   10),
    ("Malaga",       36.72,  -4.42,   10),
    ("Almeria",      36.84,  -2.47,   20),
    ("Tanger",       35.77,  -5.80,   50),
    ("Oran",         35.70,  -0.63,   90),
    ("Constantina",  36.36,   6.61,  640),
    ("Sfax",         34.74,  10.76,   20),
    ("Bengasi",      32.12,  20.07,    5),
    ("Luxor",        25.69,  32.64,   76),
    ("Aswan",        24.09,  32.90,  190),
    ("Jiddah",       21.49,  39.19,   10),
]

R_MOON_KM, R_SUN_KM, AU = 1737.4, 695700.0, 149597870.7

print("=" * 92)
print("L'ECLIPSI DEL 2 D'AGOST DE 2027, LLOC PER LLOC")
print("=" * 92)
print(f"\n  {'lloc':<13} {'màxim UTC':>10} {'sep':>7} {'durada':>8} {'altura':>7} "
      f"{'m. aire':>8} {'nota':>6}")
print("  " + "-" * 76)

resultats = {}
for nom, lat, lon, alt_m in LLOCS:
    site = eph["earth"] + wgs84.latlon(lat, lon, elevation_m=alt_m)
    t = ts.utc(2027, 8, 2, 7, np.arange(0, 240, 0.25))
    s = site.at(t).observe(eph["sun"]).apparent()
    m = site.at(t).observe(eph["moon"]).apparent()
    sep = s.separation_from(m).arcseconds()
    i = int(np.argmin(sep))
    tmax = t[i]
    # radis aparents al màxim
    ds = site.at(tmax).observe(eph["sun"]).apparent().distance().au * AU
    dm = site.at(tmax).observe(eph["moon"]).apparent().distance().au * AU
    Rs = math.degrees(math.asin(R_SUN_KM / ds)) * 3600
    Rm = math.degrees(math.asin(R_MOON_KM / dm)) * 3600
    # taxa relativa: desplaçament del vector Lluna−Sol al pla tangent, no de la
    # separació (que prop del mínim varia de manera quadràtica i no serveix)
    def rel(tt):
        ss = site.at(tt).observe(eph["sun"]).apparent()
        mm = site.at(tt).observe(eph["moon"]).apparent()
        r1, d1, _ = ss.radec()
        r2, d2, _ = mm.radec()
        return ((r2.radians - r1.radians) * math.cos(d1.radians) * 206264.806,
                (d2.radians - d1.radians) * 206264.806)
    ta = ts.tt_jd(tmax.tt - 60.0 / 86400)
    tb = ts.tt_jd(tmax.tt + 60.0 / 86400)
    (ea, na), (eb, nb) = rel(ta), rel(tb)
    taxa = math.hypot(eb - ea, nb - na) / 120.0
    dmax = Rm - Rs
    dur = 2 * math.sqrt(max(dmax ** 2 - sep[i] ** 2, 0.0)) / taxa if taxa > 0 else 0.0
    a, az, _ = site.at(tmax).observe(eph["sun"]).apparent().altaz()
    X = 1 / math.sin(math.radians(a.degrees))
    nota = "TOTAL" if sep[i] < dmax else "parcial"
    print(f"  {nom:<13} {tmax.utc_strftime('%H:%M:%S'):>10} {sep[i]:6.0f}″ "
          f"{dur:7.0f} s {a.degrees:6.1f}° {X:8.2f} {nota:>8}")
    resultats[nom] = dict(t=tmax, alt=a.degrees, az=az.degrees, lat=lat, lon=lon,
                          h=alt_m, dur=dur, Rs=Rs, Rm=Rm)

print(f"\n  (radi solar aparent {resultats['Luxor']['Rs']:.1f}″, lunar "
      f"{resultats['Luxor']['Rm']:.1f}″ → la Lluna sobresurt "
      f"{resultats['Luxor']['Rm']-resultats['Luxor']['Rs']:.0f}″)")

# ─────────────────────────────────── el camp d'estrelles: on cau i com és de pobre
print("\n" + "=" * 92)
print("EL CAMP D'ESTRELLES: ON MIRAREM")
print("=" * 92)
for etiqueta, t in (("2026-08-12 (León)", ts.utc(2026, 8, 12, 18, 29, 38)),
                    ("2027-08-02 (Luxor)", resultats["Luxor"]["t"])):
    site = eph["earth"] + wgs84.latlon(30.0, 0.0)
    s = site.at(t).observe(eph["sun"]).apparent()
    ra, dec, _ = s.radec()
    gal = s.frame_latlon(load('hipparcos')) if False else None
    # latitud galàctica a mà (pol nord galàctic J2000: 12h51m26.28s, +27°07'42")
    rag, decg = math.radians(192.85948), math.radians(27.12825)
    a, d = ra.radians, dec.radians
    b = math.asin(math.sin(decg) * math.sin(d) +
                  math.cos(decg) * math.cos(d) * math.cos(a - rag))
    print(f"\n  {etiqueta}")
    print(f"     Sol a RA {ra.hours:.3f} h, Dec {dec.degrees:+.2f}°  ·  "
          f"latitud galàctica {math.degrees(b):+.1f}°")

print("""
  Les dues dates miren gairebé el mateix tros de cel i totes dues cauen lluny
  del pla de la Via Làctia. El camp del 2027 NO serà gaire més ric que el del
  2026: el que canviarà de debò és la fondària a què s'hi pot arribar.""")

# ────────────────────────────── quan es pot fer el camp de comparació, de nit
print("\n" + "=" * 92)
print("EL CAMP DE COMPARACIÓ: QUAN ES POT FOTOGRAFIAR DE NIT, A LA MATEIXA ALTURA")
print("=" * 92)

for lloc in ("Luxor", "Malaga"):
    R = resultats[lloc]
    site = eph["earth"] + wgs84.latlon(R["lat"], R["lon"], elevation_m=R["h"])
    s = site.at(R["t"]).observe(eph["sun"]).apparent()
    ra, dec, _ = s.radec()
    obj = eph["earth"]  # posició fixa del camp: la fem servir via angle horari
    print(f"\n  {lloc}  (latitud {R['lat']:.1f}°)")
    print(f"     durant l'eclipsi el camp és a {R['alt']:.1f}° d'altura, azimut {R['az']:.0f}°")
    culm = 90 - abs(R["lat"] - dec.degrees)
    print(f"     el mateix camp culmina a {culm:.1f}° des d'aquest lloc")
    if culm < R["alt"] - 0.5:
        print("     ⛔ des d'aquí no s'hi pot arribar de nit: cal pujar de latitud")
        continue
    # angle horari al qual el camp és a l'altura de l'eclipsi
    phi, dd = math.radians(R["lat"]), dec.radians
    c = ((math.sin(math.radians(R["alt"])) - math.sin(phi) * math.sin(dd)) /
         (math.cos(phi) * math.cos(dd)))
    HA = math.degrees(math.acos(max(-1, min(1, c)))) / 15.0
    print(f"     hi passa a un angle horari de ±{HA:.2f} h "
          f"({'culminació' if HA < 0.3 else 'dues vegades cada nit'})")
    # dates en què això cau de nit fosca: LST = RA ± HA amb el Sol sota -18°
    dies = []
    for dia in range(-260, 60, 2):
        tt = ts.utc(2027, 8, 2 + dia, np.arange(0, 24, 0.1))
        lst = site.at(tt).from_altaz(alt_degrees=90, az_degrees=0)  # no cal
        # angle horari del camp = LST - RA
        lst_h = np.array([x.gast for x in tt]) + R["lon"] / 15.0
        ha = (lst_h - ra.hours + 12) % 24 - 12
        solalt = np.array(site.at(tt).observe(eph["sun"]).apparent().altaz()[0].degrees)
        bo = (np.abs(np.abs(ha) - HA) < 0.12) & (solalt < -18)
        if bo.any():
            dies.append(tt[int(np.argmax(bo))])
    if dies:
        print(f"     ✅ el camp és a aquella altura amb cel astronòmicament fosc entre "
              f"{dies[0].utc_strftime('%d %b %Y')} i {dies[-1].utc_strftime('%d %b %Y')}")
        mig = dies[len(dies) // 2]
        print(f"        millor moment central: {mig.utc_strftime('%d %b %Y, %H:%M UTC')}")
    else:
        print("     ⛔ no hi ha cap nit amb el camp a aquella altura i el cel fosc")
