"""c5 · Comparació D: pressupost d'incerteses de la mediana azimutal de la nostra MSB a 1,2, 1,5, 2,5 i 4 R☉. Encàrrec «comparacions», 11-10-2026.

Anells [0,99·r; 1,01·r], píxels sense cap bit d'exclusió (com els perfils del mapa). Cada terme amb la seva font:
  - termes multiplicatius constants del mapa (msb_comu.SIS_REL): punt zero i terme de color 10 %, deriva de transparència 4 %,
    inversió del color i cadena 2,5 %, flat 1,6 %, linealitat 0,13 %; i, a part, el bootstrap del punt zero verd (zp_canal, post hoc);
  - extinció: k de 0,35 a 0,72 sobre la mediana azimutal (i, a part, el valor local a la vertical, sectors del zenit i de l'antizenit);
  - cel: la dispersió entre els models a, b, c sobre la mediana, amb el terra d'1e-9 B☉;
  - geometria: la mediana amb els tres centres alternatius del Sol (perfils del mapa);
  - soroll: SIGMA_STAT del FITS 2×2 / √N (cota alta: la dispersió real és 0,10–0,37 vegades SIGMA_STAT);
  - fora del total (sense model o només per a una comparació): halo de la nostra òptica, transferència Sony·ρ, banda (verd → Orange).
Escriu comparacions/pressupost/."""
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
OUT = cc.RES / 'pressupost'; OUT.mkdir(parents=True, exist_ok=True)
RADIS = (1.2, 1.5, 2.5, 4.0)
msb = np.load(cc.PLE / 'msb_ple.npy', mmap_mode='r'); noe = np.load(cc.PLE / 'msb_noext_ple.npy', mmap_mode='r'); flg = np.load(cc.PLE / 'flags_ple.npy', mmap_mode='r')
MA = mc.MassaAire(); CEL = mc.coef_cel(); g = mc.geo_llenc()
acc = {r0: {k: [] for k in ('msb', 'noe', 'skyA', 'skyC', 'k035', 'k072', 'E', 'pa')} for r0 in RADIS}
RM = 4.05
y0 = int(mc.SOL_XY[1] - RM * 1.01 * mc.RSOL_PX); y1 = int(mc.SOL_XY[1] + RM * 1.01 * mc.RSOL_PX) + 1
x0 = int(mc.SOL_XY[0] - RM * 1.01 * mc.RSOL_PX); x1 = int(mc.SOL_XY[0] + RM * 1.01 * mc.RSOL_PX) + 1
for ya in range(y0, y1, 512):
    yb = min(ya + 512, y1)
    yy = np.arange(ya, yb, dtype=np.float64)[:, None] * np.ones((1, x1 - x0)); xx = np.ones((yb - ya, 1)) * np.arange(x0, x1, dtype=np.float64)[None, :]
    r, pa = g.polar(xx, yy)
    sel_any = np.zeros(r.shape, bool)
    for r0 in RADIS:
        sel_any |= (r >= 0.99 * r0) & (r < 1.01 * r0)
    if not sel_any.any():
        continue
    m = np.asarray(msb[ya:yb, x0:x1], np.float64); n_ = np.asarray(noe[ya:yb, x0:x1], np.float64); f = np.asarray(flg[ya:yb, x0:x1])
    X = mc.kasten_young(MA.altura_bloc(ya, yb, x0, x1)); E = mc.factor_extincio(X, MA.X_sol)
    Sa, Sb, Sc = (mc.cel_model(xx, yy, k, CEL) for k in ('a', 'b', 'c'))
    vals = dict(msb=m, noe=n_, skyA=m + mc.FAC_G * E * (Sb - Sa), skyC=m + mc.FAC_G * E * (Sb - Sc),
                k035=n_ * mc.factor_extincio(X, MA.X_sol, 0.35), k072=n_ * mc.factor_extincio(X, MA.X_sol, 0.72), E=E, pa=pa)
    ok = ((f & cc.TOCA) == 0) & np.isfinite(m)
    for r0 in RADIS:
        s = ok & (r >= 0.99 * r0) & (r < 1.01 * r0)
        for k, v in vals.items():
            acc[r0][k].append(v[s])
# soroll (FITS 2×2)
from astropy.io import fits   # noqa: E402
hf = fits.open(mc.MAPA / 'msb_mapa_2x2.fits', memmap=True)
SST = hf['SIGMA_STAT'].data; FL2 = hf['FLAGS'].data
h0 = hf[0].header
yy2, xx2 = np.mgrid[0:SST.shape[0], 0:SST.shape[1]].astype(np.float64)
r2, _ = g.polar(2 * xx2 + 0.5, 2 * yy2 + 0.5)
prof = {}
import pandas as pd   # noqa: E402
AZ = pd.read_csv(mc.MAPA / 'perfils/perfil_azimutal.csv')
SEC = pd.read_csv(mc.MAPA / 'perfils/perfil_sectors_10graus.csv')
sis = mc.SIS_REL
taula = []
for r0 in RADIS:
    A = {k: np.concatenate(v) for k, v in acc[r0].items()}
    med = {k: float(np.median(A[k])) for k in ('msb', 'noe', 'skyA', 'skyC', 'k035', 'k072')}
    M = med['msb']
    ext_az = max(abs(med['k035'] / M - 1), abs(med['k072'] / M - 1))
    # vertical: sectors del zenit (33,2°) i de l'antizenit (213,2°)
    pz = np.abs((A['pa'] - 33.21 + 180) % 360 - 180) < 5; pn = np.abs((A['pa'] - 213.21 + 180) % 360 - 180) < 5
    ext_vert = {}
    for nom, s in (('zenit', pz), ('antizenit', pn)):
        mm = float(np.median(A['msb'][s]))
        ext_vert[nom] = dict(E_mediana=float(np.median(A['E'][s])),
                             k035=float(np.median(A['k035'][s]) / mm - 1), k072=float(np.median(A['k072'][s]) / mm - 1))
    sky = max(abs(med['skyA'] / M - 1), abs(med['skyC'] / M - 1), 1e-9 / M)
    # geometria: anell del perfil del mapa que conté r0
    row = AZ[(AZ.r_in <= r0) & (AZ.r_out > r0)].iloc[0]
    alt = [c for c in AZ.columns if c.startswith('MSB_median_centre_')]
    geo = max(abs(row[c] / row['MSB_median'] - 1) for c in alt)
    sel2 = (r2 >= 0.99 * r0) & (r2 < 1.01 * r0) & ((FL2 & cc.TOCA) == 0) & np.isfinite(SST)
    stat = float(np.median(SST[sel2]) / math.sqrt(sel2.sum()) / M)
    bloc = dict(r=r0, n_px=int(A['msb'].size), MSB_mediana=M, MSB_sense_extincio=med['noe'],
                frac_sony=float(row['frac_sony_dominated']),
                termes_rel=dict(punt_zero_i_terme_color=sis['zero_point_and_colour_term'], deriva_transparencia=sis['transparency_drift_in_totality'],
                                inversio_color_i_cadena=sis['colour_inversion_and_chain'], flat=sis['flat_field'], linealitat=sis['linearity'],
                                extincio_k_035_072_mediana=ext_az, cel_models_i_terra=sky, geometria_centre=float(geo), soroll_cota_alta=stat),
                extincio_vertical=ext_vert,
                cel_detall=dict(skyA=med['skyA'] / M - 1, skyC=med['skyC'] / M - 1, terra=1e-9 / M))
    bloc['total_quadratic'] = float(math.sqrt(sum(v * v for v in bloc['termes_rel'].values())))
    taula.append(bloc)
    print(r0, json.dumps(bloc, default=float)[:900], flush=True)

FORA = dict(
    punt_zero_bootstrap='zp_canal (post hoc): fac_G mediana 2,61e-11 (−6 %), 68 %: 2,31–2,75e-11 (−17 % / −1 %): asimètric cap avall',
    halo_optica='sense model; cota del C2: excés en medianes ×1,05–1,23 (C&H 2015) o ×1,22–1,42 (SSW) a 2,4–5,5 R☉, i en pendents ×1,2–2,0',
    transferencia_sony_rho='r > 1,9 R☉: el mapa és Sony·ρ en unitats Vixen; amb el factor propi de la Sony quedaria ~+20 % (0,83 entre trens, scout); no s\'inclou',
    banda_verd_a_orange='només per a la comparació amb el C2: MSB_orange/MSB_G = 0,886 (−11 %) ± 6 % (w 0,25–0,75), dominat pel punt zero vermell '
                        '(bootstrap: 0,94, 68 % 0,90–1,00); vegeu banda/BANDA.json',
)
with open(OUT / 'pressupost.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    noms = list(taula[0]['termes_rel'].keys())
    w.writerow(['terme'] + [f'r={b["r"]}' for b in taula])
    w.writerow(['MSB_mediana'] + [f"{b['MSB_mediana']:.3e}" for b in taula])
    for nm in noms:
        w.writerow([nm] + [f"{100 * b['termes_rel'][nm]:.2f}%" for b in taula])
    w.writerow(['total_quadratic'] + [f"{100 * b['total_quadratic']:.1f}%" for b in taula])
json.dump(dict(guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), radis=RADIS, anell='[0,99 r; 1,01 r]', taula=taula, fora_del_total=FORA,
               entrades_sha256={cc.rel(cc.PLE / 'msb_ple.npy'): cc.sha256(cc.PLE / 'msb_ple.npy'),
                                cc.rel(cc.PLE / 'msb_noext_ple.npy'): cc.sha256(cc.PLE / 'msb_noext_ple.npy'),
                                cc.rel(cc.PLE / 'flags_ple.npy'): cc.sha256(cc.PLE / 'flags_ple.npy'),
                                cc.rel(mc.MAPA / 'msb_mapa_2x2.fits'): cc.sha256(mc.MAPA / 'msb_mapa_2x2.fits'),
                                cc.rel(mc.MAPA / 'perfils/perfil_azimutal.csv'): cc.sha256(mc.MAPA / 'perfils/perfil_azimutal.csv')},
               segons=round(time.time() - T0, 1)), open(OUT / 'PRESSUPOST.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(open(OUT / 'pressupost.csv').read())
print(f'fet ({time.time() - T0:.0f} s)')
