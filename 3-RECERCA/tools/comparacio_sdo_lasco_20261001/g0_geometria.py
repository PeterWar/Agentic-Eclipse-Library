"""g0 · Geometria de la imatge final (V121/V123, 7933×5021) per comparar-la amb SDO/AIA, SOHO/LASCO i K-Cor.
Dues vies independents per al centre del Sol:
  (a) el centre del Sol al llenç V82/V114 (5361,8; 3775,0, de la placa d'estrelles) portat a la V120 amb la semblança
      de les 56 estrelles (de → a) i restant el retall de la V121;
  (b) el centre de la Lluna mesurat a la imatge menys el desplaçament Lluna−Sol de l'efemèride DE421 (topocèntric,
      Mirador Final 2) a l'instant de la Lluna de presentació (18:28:49 UTC, el del perfil LOLA).
Escriu GEOMETRIA_FINAL.json."""
import json, math, os, numpy as np
from pathlib import Path
ARREL = Path(__file__).resolve().parents[3]
OUT = ARREL / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001'
est = json.load(open(ARREL / '3-RECERCA/resultats/ia_output/apod_anotada_20260918/estrelles_final.json'))
mars = json.load(open(ARREL / '3-RECERCA/resultats/ia_output/apod_anotada_20260918/mars_final.json'))
e202 = json.load(open(ARREL / '3-RECERCA/resultats/v120_20260929/estrelles/ESTRELLES_202_V120.json'))['estrelles']
OFF = np.array([1385.67, 1147.95 + 77])          # retall V120 -> V121 (construeix_v13.py)
DM = np.array([1352.0, 1164.0]) - OFF             # marc de la final del 18-09 -> V121 (coses fixes al llenç: la Lluna)
SOL_LLENC = np.array([5361.8, 3775.0])            # centre del Sol al llenç V82/V114 (troba_estrelles_final.py)

# (a) semblança de -> a amb les 56 estrelles (i només les interiors, com a control)
de = np.array([s['de'] for s in e202]); a = np.array([s['a'] for s in e202])
def semblanca(p, q):
    A = np.zeros((2 * len(p), 4)); b = np.zeros(2 * len(p))
    A[0::2] = np.c_[p[:, 0], -p[:, 1], np.ones(len(p)), np.zeros(len(p))]; b[0::2] = q[:, 0]
    A[1::2] = np.c_[p[:, 1], p[:, 0], np.zeros(len(p)), np.ones(len(p))]; b[1::2] = q[:, 1]
    s, *_ = np.linalg.lstsq(A, b, rcond=None); return s
def aplica(s, p): return np.array([s[0] * p[0] - s[1] * p[1] + s[2], s[1] * p[0] + s[0] * p[1] + s[3]])
s_tot = semblanca(de, a)
d = np.hypot(*(de - SOL_LLENC).T); inn = d < 1800
s_int = semblanca(de[inn], a[inn])
sol_a_tot = aplica(s_tot, SOL_LLENC) - OFF; sol_a_int = aplica(s_int, SOL_LLENC) - OFF
print(f"(a) Sol a la V121: totes {sol_a_tot.round(2)} | interiors ({inn.sum()}) {sol_a_int.round(2)} | sense moure {(SOL_LLENC - OFF).round(2)}")
rot = math.degrees(math.atan2(s_tot[1], s_tot[0])); esc = math.hypot(s_tot[0], s_tot[1])
print(f"    semblança de->a: gir {rot:.4f}°, escala {esc:.6f}")

# Lluna i vectors N/E a la V121
mo = mars['moon']; lluna = np.array([mo['cx'], mo['cy']]) + DM; RL = mo['R']
th = math.radians(rot)
def gira(v): c, s_ = math.cos(th), math.sin(th); return np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]])
N = gira(np.array(mars['N'])); E = gira(np.array(mars['E']))
arcsec_px = est['plate_canvas']['arcsec_per_px'] / esc
print(f"Lluna a la V121 {lluna.round(2)} R {RL:.2f} px; escala {arcsec_px:.5f} ″/px; N {N.round(5)}; E {E.round(5)}")

# (b) efemèride
from skyfield.api import load, wgs84
ts = load.timescale(); eph = load(str(ARREL / '3-RECERCA/data/de421.bsp'))
earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
res = {}
for hh, mm, ss in [(18, 28, 46.0), (18, 28, 49.0)]:
    t = ts.utc(2026, 8, 12, hh, mm, ss)
    sa = lloc.at(t).observe(sun).apparent(); ma = lloc.at(t).observe(moon).apparent()
    ras, des, ds = sa.radec('date'); ram, dem, dm = ma.radec('date')
    # desplaçament Lluna - Sol al pla del cel (″): est = ΔRA cos δ, nord = Δδ
    dE = (ram.radians - ras.radians) * math.cos(des.radians) * 206264.806; dN = (dem.radians - des.radians) * 206264.806
    Rs = math.degrees(math.asin(695700.0 / ds.km)) * 3600; Rm = math.degrees(math.asin(1737.4 / dm.km)) * 3600
    sol_b = lluna - (dE * E + dN * N) / arcsec_px
    res[f'{hh}:{mm}:{ss:04.1f}'] = dict(dE=dE, dN=dN, sep=math.hypot(dE, dN), R_sol=Rs, R_lluna=Rm, sol_b=sol_b.tolist())
    print(f"(b) {hh}:{mm}:{ss:04.1f} UTC: Lluna−Sol E {dE:+.2f}″ N {dN:+.2f}″ (sep {math.hypot(dE, dN):.2f}″); R☉ {Rs:.2f}″, R☾ {Rm:.2f}″ "
          f"(R☾ mesurat {RL * arcsec_px:.2f}″) → Sol {sol_b.round(2)}; dif. amb (a) {(sol_b - sol_a_tot).round(2)} px")

# angle P del Sol i nord solar a la imatge
from sunpy.coordinates import sun as ssun
from astropy.time import Time
P = float(ssun.P(Time('2026-08-12T18:28:49')).deg)
n_sol = math.cos(math.radians(P)) * N + math.sin(math.radians(P)) * E      # nord solar = nord celeste girat P cap a l'est
e_sol = -math.sin(math.radians(P)) * N + math.cos(math.radians(P)) * E
ang_vert = math.degrees(math.atan2(n_sol[0], -n_sol[1]))
print(f"P = {P:.3f}°; nord solar a la imatge {n_sol.round(5)} ({ang_vert:.2f}° a la dreta de la vertical); est solar {e_sol.round(5)}")
geo = dict(imatge='V121/V123 (7933×5021); Sortides/estrelles_reals_20260930/e4_nova_v121.npy', sol_px=sol_a_tot.tolist(),
           sol_px_interiors=sol_a_int.tolist(), sol_px_efemeride=res['18:28:49.0']['sol_b'], lluna_px=lluna.tolist(), R_lluna_px=RL,
           arcsec_px=arcsec_px, nord_celeste=N.tolist(), est_celeste=E.tolist(), P_deg=P, nord_solar=n_sol.tolist(), est_solar=e_sol.tolist(),
           R_sol_arcsec=res['18:28:49.0']['R_sol'], R_sol_px=res['18:28:49.0']['R_sol'] / arcsec_px, efemeride=res,
           instant_lluna_utc='2026-08-12T18:28:49', lloc=dict(lat=42.299407, lon=-5.02503, alt_m=798.0))
json.dump(geo, open(OUT / 'GEOMETRIA_FINAL.json', 'w'), indent=1)
print('R☉ =', round(geo['R_sol_px'], 2), 'px')
