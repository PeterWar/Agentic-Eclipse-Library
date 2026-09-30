#!/usr/bin/env python3
"""Punt zero, reparametritzat al centre del camp (posicio del Sol), i prova de
la degeneracio entre extincio diferencial i vinyetatge.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/zp2.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, pandas as pd, json

sol = json.load(open('final_solution.json'))
zpj = json.load(open('zp.json'))


def wls(A, y, clip=2.5, nit=6):
    ok = np.ones(len(y), bool)
    for _ in range(nit):
        s, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
        r = y - A@s
        sd = 1.4826*np.median(np.abs(r[ok]-np.median(r[ok])))
        new = np.abs(r-np.median(r[ok])) < clip*max(sd, 0.02)
        if (new == ok).all():
            break
        ok = new
    s, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
    r = y[ok]-A[ok]@s
    n, p = ok.sum(), A.shape[1]
    s2 = (r**2).sum()/max(n-p, 1)
    cov = s2*np.linalg.pinv(A[ok].T@A[ok])
    return s, np.sqrt(np.abs(np.diag(cov))), ok, float(np.sqrt(s2))


out = {}
for tag in ('sony', 'r6'):
    d = pd.read_csv(f'zp_{tag}.csv')
    nbad = (~np.isfinite(d.minst)).sum()
    d = d[np.isfinite(d.minst)].reset_index(drop=True)
    if nbad:
        print(f'(descartades {nbad} sense fotometria valida: obertura fora del sensor)')
    S = sol[tag]
    Xs = zpj[tag]['Xsun']
    y = (d.V - d.minst).values
    BV = np.where(np.isfinite(d.BV), d.BV, 0.0)
    dX = d.X.values - Xs
    px = (d.x.values - S['sun_x'])/1000.
    py = (d.y.values - S['sun_y'])/1000.
    hipmag = d.HIP.notna().values

    print(f'================ {tag} ================')
    models = {
        'ZP0 (constant)':            np.column_stack([np.ones(len(y))]),
        'ZP + k(X-Xsun)':            np.column_stack([np.ones(len(y)), -dX]),
        'ZP + k + color':            np.column_stack([np.ones(len(y)), -dX, -BV]),
        'ZP + gradient x,y':         np.column_stack([np.ones(len(y)), px, py]),
        'ZP + gradient + color':     np.column_stack([np.ones(len(y)), px, py, -BV]),
        'ZP + radial r^2':           np.column_stack([np.ones(len(y)), px**2+py**2]),
        "ZP + k + radial + color":   np.column_stack([np.ones(len(y)), -dX,
                                                      px**2+py**2, -BV]),
        "ZP + k + gradient + color": np.column_stack([np.ones(len(y)), -dX, px, py, -BV]),
    }
    for name, A in models.items():
        s, e, ok, rms = wls(A, y)
        extra = '  '.join(f'{v:+.3f}+-{ee:.3f}' for v, ee in zip(s[1:], e[1:]))
        print(f'  {name:26s} n={ok.sum():2d} rms={rms:.3f}  '
              f'ZP(Sol)={s[0]:+.3f}+-{e[0]:.3f}   {extra}')

    # direccio de la massa d'aire creixent sobre el sensor (anti-zenit)
    paZ = np.radians(S['pa_zenith'])
    vz = np.array([np.sin(paZ), -np.cos(paZ)])       # cap al zenit al sensor
    A = models['ZP + gradient + color']
    s, e, ok, rms = wls(A, y)
    g = np.array([s[1], s[2]])
    if np.hypot(*g) > 0:
        cosang = np.dot(g, -vz)/np.hypot(*g)
        print(f'  gradient espacial: modul {np.hypot(*g)*1000:.4f} mag/1000px, '
              f'angle amb la direccio d\'X creixent: {np.degrees(np.arccos(np.clip(cosang,-1,1))):.1f} deg')

    # model final: ZP al centre + k + color, nomes estrelles amb V d'Hipparcos
    A = models['ZP + k + color']
    s, e, ok, rms = wls(A, y)
    sh, eh, okh, rmsh = wls(A[hipmag], y[hipmag])
    print(f'  --> ADOPTAT  ZP(a X del Sol) = {s[0]:+.3f} +- {e[0]:.3f} mag  '
          f'(rms {rms:.3f}, n={ok.sum()})')
    print(f'      nomes V d\'Hipparcos: ZP = {sh[0]:+.3f} +- {eh[0]:.3f}  '
          f'rms={rmsh:.3f}  n={okh.sum()}/{hipmag.sum()}')
    d['ok_final'] = ok
    d['resid_final'] = y - A@s
    d.to_csv(f'zp2_{tag}.csv', index=False)
    out[tag] = dict(ZPsun=float(s[0]), eZPsun=float(e[0]), k=float(s[1]),
                    ek=float(e[1]), c=float(s[2]), rms=rms, n=int(ok.sum()),
                    Xsun=Xs, ZPsun_hip=float(sh[0]), rms_hip=rmsh)
    print()

print('DIFERENCIA entre trens del ZP al Sol: '
      f'{out["sony"]["ZPsun"]-out["r6"]["ZPsun"]:+.3f} mag '
      f'(+- {np.hypot(out["sony"]["eZPsun"], out["r6"]["eZPsun"]):.3f})')
json.dump(out, open('zp2.json', 'w'), indent=1)
import shutil
shutil.copy2('zp2.json', comu.out()/'zp2.json')
