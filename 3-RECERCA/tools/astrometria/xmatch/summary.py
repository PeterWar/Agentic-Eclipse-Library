#!/usr/bin/env python3
"""Resum final: prova del radi (pas 1), identificacions i taules.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/summary.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, pandas as pd, json

sol = json.load(open('final_solution.json'))
RSUN = 947.07
PRED = {  # HIP -> (nom, V, radi previst en px Sony, radi previst en px R6)
    46232: ('HIP 46232', 6.31, 2026, 3036), 47096: ('7 Leonis', 6.32, 2086, 3126),
    45874: ('HIP 45874', 6.57, 2000, 2997), 46713: ('HIP 46713', 6.92, 2409, 3610),
    46771: ('xi Leonis', 4.99, 4125, None), 47723: ('psi Leonis', 5.36, 4235, None),
    45410: ('pi2 Cancri', 5.36, 3554, None), 47189: ('8 Leonis', 5.73, 2867, 4296),
    45170: ('pi1 Cancri', 6.49, 4348, None), 45699: ('83 Cancri', 6.61, 4013, None),
    47266: ('11 Leonis', 6.63, 2652, 3975), 45879: ('HIP 45879', 6.67, 2776, 4160),
    46345: ('HIP 46345', 6.83, 783, 1174), 46335: ('HIP 46335', 7.77, 637, 954),
    46745: ('HIP 46745', 7.66, 1291, 1935), 46415: ('HIP 46415', 7.79, 1296, 1942),
}

print('#################### PAS 1: PROVA DEL RADI ####################')
for tag, scale_old, cxold, cyold in (('sony', 3.234, 3894.1, 2765.6),
                                     ('r6', 2.158, 3577.1, 2266.1)):
    d = pd.read_csv(f'final_match_{tag}.csv')
    S = sol[tag]
    d['r_det_old'] = np.hypot(d.x-cxold, d.y-cyold)          # radi al centre LUNAR
    d['r_det_new'] = np.hypot(d.x-S['sun_x'], d.y-S['sun_y'])  # radi al centre SOLAR ajustat
    d['r_pred'] = d.sep_deg*3600/S['scale']
    d['dr'] = d.r_det_new - d.r_pred
    print(f'\n=== {tag} === n={len(d)} identificades')
    print(f'  radi mesurat (centre solar ajustat) contra radi previst per efemerides:')
    print(f'    mediana |dr| = {d.dr.abs().median():.2f} px   '
          f'p90 = {d.dr.abs().quantile(0.9):.2f} px   max = {d.dr.abs().max():.2f} px')
    d['dr_old'] = d.r_det_old - d.sep_deg*3600/scale_old
    print(f'  amb el centre LUNAR i l\'escala anterior ({scale_old} "/px):')
    print(f'    mediana |dr| = {d.dr_old.abs().median():.2f} px   '
          f'p90 = {d.dr_old.abs().quantile(0.9):.2f} px   '
          f'max = {d.dr_old.abs().max():.2f} px')
    # quantes casen a diverses toleràncies nomes pel radi
    for tol in (5, 10, 20, 40):
        print(f'    dins de {tol:3d} px: {(d.dr_old.abs() < tol).sum():2d}/{len(d)}')
    d.to_csv(f'radi_{tag}.csv', index=False)

print('\n\n############ candidates de la PREDICCIO: recuperades? ############')
for tag in ('sony', 'r6'):
    d = pd.read_csv(f'radi_{tag}.csv')
    hips = set(d.HIP.dropna().astype(int))
    print(f'\n=== {tag} ===')
    print(f'  {"estrella":13s} {"V":>5s} {"px previst":>10s} {"px mesurat":>10s} '
          f'{"dif":>7s}  deteccio')
    for hip, (nm, V, ps, pr) in sorted(PRED.items(), key=lambda kv: kv[1][1]):
        pp = ps if tag == 'sony' else pr
        if hip in hips:
            row = d[d.HIP == hip].iloc[0]
            print(f'  {nm:13s} {V:5.2f} {str(pp) if pp else "-":>10s} '
                  f'{row.r_det_old:10.0f} {row.r_det_old-(pp or np.nan):7.0f}  {row.det}')
        else:
            print(f'  {nm:13s} {V:5.2f} {str(pp) if pp else "-":>10s} '
                  f'{"-":>10s} {"":>7s}  NO detectada')

print('\n\n#################### PAS 2: SOLUCIO DE PLACA ####################')
for tag, ref in (('sony', 3.234), ('r6', 2.158)):
    S = sol[tag]
    Sr = sol[tag+'_radial']
    print(f'\n=== {tag} ===')
    print(f'  n estrelles          : {S["n"]}  (amb terme radial: {Sr["n"]})')
    print(f'  rms residual         : {S["rms"]:.2f} px  (amb radial: {Sr["rms"]:.2f} px)')
    print(f'  escala ajustada      : {S["scale"]:.4f} "/px  '
          f'(amb radial, a l\'eix: {Sr["scale"]:.4f})')
    print(f'  escala de referencia : {ref} "/px  -> diferencia '
          f'{100*(S["scale"]/ref-1):+.2f} % ({100*(Sr["scale"]/ref-1):+.2f} % amb radial)')
    print(f'  anisotropia          : {100*(S["sx"]/S["sy"]-1):+.3f} %   '
          f'no-perpendicularitat {S["skew"]:+.3f} deg')
    print(f'  PA nord celeste      : {S["pa_north"]:.2f} deg (horari des d\'amunt)')
    print(f'  centre del Sol       : ({S["sun_x"]:.1f}, {S["sun_y"]:.1f}) px')
    px = 4.51e-3 if tag == 'sony' else 5.17e-3
    print(f'  focal implicada      : {206265*px/Sr["scale"]:.1f} mm')
