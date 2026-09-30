#!/usr/bin/env python3
"""Els moviments de la totalitat del 12-08-2026, amb números.

Tot el que es va moure durant els 103,7 s, ordenat per mida angular.
"""
import math
import numpy as np
from skyfield.api import load, wgs84
from skyfield.positionlib import position_of_radec

ts = load.timescale()
eph = load("/Users/USUARI/.cache/skyfield/de440s.bsp")
lloc = wgs84.latlon(42.299407, -5.02503, elevation_m=798)
obs = eph["earth"] + lloc

C2 = ts.utc(2026, 8, 12, 18, 28, 46)
MIG = ts.utc(2026, 8, 12, 18, 29, 38)
C3 = ts.utc(2026, 8, 12, 18, 30, 29.7)
DUR = 103.7

ESC_SONY, ESC_VIX = 3.2020, 2.1495


def sep_arcsec(p, q):
    return p.separation_from(q).arcseconds()


print("=" * 78)
print("ELS MOVIMENTS DE LA TOTALITAT — 103,7 s")
print("=" * 78)

# --- 1. moviment diürn (el que les muntures esborren) -----------------------
sol_c2 = obs.at(C2).observe(eph["sun"]).apparent()
sol_c3 = obs.at(C3).observe(eph["sun"]).apparent()
ra, dec, _ = sol_c2.radec()
diurn = 15.041 * math.cos(dec.radians)
print(f"\n1. ROTACIÓ DE LA TERRA (el que la muntura esborra)")
print(f"   Declinació del Sol       : {dec.degrees:+.2f}°")
print(f"   Taxa diürna              : {diurn:.2f} ″/s")
print(f"   En tota la totalitat     : {diurn*DUR/60:.1f}′ = {diurn*DUR/ESC_SONY:.0f} px (Sony)"
      f" / {diurn*DUR/ESC_VIX:.0f} px (Vixen)")
print(f"   En una sola pose de 10,3 s: {diurn*10.3:.0f}″ = {diurn*10.3/ESC_VIX:.0f} px")

# --- 2. la Lluna contra el Sol ----------------------------------------------
def sep_lluna_sol(t):
    s = obs.at(t).observe(eph["sun"]).apparent()
    m = obs.at(t).observe(eph["moon"]).apparent()
    return s, m

s2, m2 = sep_lluna_sol(C2)
s3, m3 = sep_lluna_sol(C3)
# vector relatiu Lluna - Sol en coordenades tangents
def tangent(a, b):
    """desplaçament de b respecte de a en ″ (E, N)"""
    ra_a, dec_a, _ = a.radec()
    ra_b, dec_b, _ = b.radec()
    de = (ra_b.radians - ra_a.radians) * math.cos(dec_a.radians) * 206264.806
    dn = (dec_b.radians - dec_a.radians) * 206264.806
    return de, dn

e2, n2 = tangent(s2, m2)
e3, n3 = tangent(s3, m3)
d = math.hypot(e3 - e2, n3 - n2)
pa = (math.degrees(math.atan2(e3 - e2, n3 - n2))) % 360
print(f"\n2. LA LLUNA CONTRA EL SOL (el que fa l'eclipsi)")
print(f"   Desplaçament relatiu     : {d:.1f}″ en {DUR:.1f} s = {d/DUR:.4f} ″/s")
print(f"   Angle de posició         : {pa:.0f}°")
print(f"   Al sensor                : {d/ESC_SONY:.0f} px (Sony) / {d/ESC_VIX:.0f} px (Vixen)")
print(f"   En una pose de 10,3 s    : {d/DUR*10.3:.1f}″ = {d/DUR*10.3/ESC_VIX:.1f} px")

# --- 3. la Lluna contra les estrelles ---------------------------------------
def sep_estels(t):
    m = obs.at(t).observe(eph["moon"]).apparent()
    return m

ra2, dec2, _ = m2.radec()
ra3, dec3, _ = m3.radec()
de = (ra3.radians - ra2.radians) * math.cos(dec2.radians) * 206264.806
dn = (dec3.radians - dec2.radians) * 206264.806
dm = math.hypot(de, dn)
print(f"\n3. LA LLUNA CONTRA LES ESTRELLES")
print(f"   Desplaçament             : {dm:.1f}″ en {DUR:.1f} s = {dm/DUR:.3f} ″/s")
print(f"   Al sensor Sony           : {dm/ESC_SONY:.1f} px")

# --- 4. aberració de la llum (relativitat especial) -------------------------
# comparem la posició aparent amb i sense aberració, per a una estrella del camp
ra_s, dec_s, _ = sol_c2.radec()
print(f"\n4. ABERRACIÓ DE LA LLUM (relativitat especial, v/c)")
# velocitat baricèntrica de l'observador
bary = (eph["earth"] + lloc).at(MIG)
v = bary.velocity.km_per_s
vmag = math.sqrt(sum(c * c for c in v))
c_kms = 299792.458
print(f"   Velocitat de l'observador: {vmag:.2f} km/s (translació + rotació)")
print(f"   Aberració màxima v/c     : {math.degrees(vmag/c_kms)*3600:.2f}″")
# aberració real per a una estrella del camp: angle entre apex i la línia de visió
apex = np.array(v) / vmag
los = sol_c2.xyz.km / np.linalg.norm(sol_c2.xyz.km)
cosang = float(np.dot(apex, los))
ang = math.degrees(math.acos(cosang))
aber = math.degrees(vmag / c_kms * math.sin(math.radians(ang))) * 3600
print(f"   Angle apex-Sol           : {ang:.1f}°")
print(f"   Aberració en aquest camp : {aber:.2f}″  = {aber/ESC_SONY:.1f} px (Sony)")
# variació a través del camp de 7,14°: d(aber)/dtheta = (v/c) cos(theta)
grad = math.degrees(vmag / c_kms * abs(math.cos(math.radians(ang)))) * 3600
print(f"   Gradient pel camp        : {grad*7.14/57.2958*57.2958/57.2958:.3f}″/°  →  "
      f"{grad*(7.14*math.pi/180):.2f}″ d'un extrem a l'altre del camp Sony")

# --- 5. refracció ------------------------------------------------------------
alt, az, _ = sol_c2.altaz()
h = alt.degrees
def R_bennett(h_deg):
    return 1.0 / math.tan(math.radians(h_deg + 7.31 / (h_deg + 4.4))) / 60.0  # graus
Rt = R_bennett(h)
print(f"\n5. REFRACCIÓ ATMOSFÈRICA")
print(f"   Altura del Sol a C2      : {h:.2f}°")
print(f"   Refracció total          : {Rt*60:.2f}′ = {Rt*3600:.0f}″"
      f"  ({Rt*3600/ESC_SONY:.0f} px al sensor Sony)")
dR = (R_bennett(h + 0.5) - R_bennett(h - 0.5)) * 3600
print(f"   Compressió del camp      : {abs(dR)/3600*100:.2f} % per grau  "
      f"(mesurat: 0,77 % Sony / 0,80 % Vixen)")
print(f"   Deriva per refracció     : 0,21 ″/s (mesurat, dins dels 0,610 ″/s de deriva)")
print(f"   Dispersió atmosfèrica R-B: 3,08″ a PA 170° (mesurat als retalls)")

# --- 6. la muntura -----------------------------------------------------------
print(f"\n6. LES MUNTURES")
print(f"   Vixen/iOptron, deriva    : 0,610 ± 0,010 ″/s constant = "
      f"{0.610/ESC_VIX:.2f} px/s → traç de {0.610*10.3/ESC_VIX:.1f} px en 10,3 s")
print(f"       en tota la totalitat : {0.610*DUR:.0f}″ = {0.610*DUR/ESC_VIX:.0f} px")
print(f"       origen               : ~0,21 refracció + ~0,48 error polar (~2°)")
print(f"   Skywatcher/Sony, salts   : +223 px (~12′) a C2+35 s i −715 px (~39′) a C2+50 s")
print(f"       + rotació de camp    : 0,138°")
print(f"       causa                : la mà a la lent en treure el filtre solar")

# --- 7. la corona ------------------------------------------------------------
R_SOL_KM = 695700.0
Rsol_as = 946.66
for v_kms in (50, 100, 200):
    dkm = v_kms * DUR
    das = dkm / R_SOL_KM * Rsol_as
    print(f"\n7. EL VENT SOLAR a {v_kms:3d} km/s: {dkm:6.0f} km en {DUR:.0f} s = "
          f"{das:5.1f}″ = {das/ESC_VIX:.1f} px (Vixen)" if v_kms == 100 else
          f"   ... a {v_kms:3d} km/s: {das:5.1f}″ = {das/ESC_VIX:4.1f} px")

# --- 8. la deflexió ----------------------------------------------------------
print(f"\n8. LA DEFLEXIÓ GRAVITATÒRIA (relativitat general)")
print(f"   Al limbe                 : 1,752″ = 0,55 px (Sony) / 0,82 px (Vixen)")
print(f"   A l'estrella més interna : 0,81″ (2,16 R☉) = 0,25 px / 0,38 px")
print(f"   A la vora del camp Sony  : 0,13″ (13,7 R☉) = 0,04 px")
print()
print("=" * 78)
print("ESCALA COMPARADA (tot en ″, al mateix camp i el mateix minut)")
print("=" * 78)
files = [
    ("Refracció atmosfèrica (total)", Rt * 3600),
    ("Rotació de la Terra (103,7 s)", diurn * DUR),
    ("Salt de la muntura Sony (el gros)", 715 * ESC_SONY),
    ("Deriva de la muntura Vixen (103,7 s)", 0.610 * DUR),
    ("La Lluna contra el Sol (103,7 s)", d),
    ("Aberració de la llum", aber),
    ("Dispersió atmosfèrica vermell-blau", 3.08),
    ("Residu de placa Sony / Vixen", 2.27),
    ("DEFLEXIÓ GR al limbe solar", 1.7516),
    ("DEFLEXIÓ GR a l'estrella més interna", 0.811),
    ("Residu de placa Vixen", 0.90),
]
for nom, val in sorted(files, key=lambda f: -f[1]):
    if val > 60:
        s = f"{val/60:.1f}′"
    else:
        s = f"{val:.2f}″"
    print(f"   {nom:<40} {s:>10}   {val/ESC_VIX:8.1f} px (Vixen)")
