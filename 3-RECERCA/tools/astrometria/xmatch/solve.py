#!/usr/bin/env python3
"""Plate solve cec: cerca de rotacio + paritat + translacio per histograma.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/solve.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, pandas as pd, json, sys

def load_dets(tag):
    if tag == 'sony':
        rows = []
        for l in open(comu.work('sony')/'catalog_sony.txt'):
            if l.startswith('#') or not l.strip():
                continue
            p = l.split()
            rows.append(dict(id=p[0], x=float(p[1]), y=float(p[2]), R=float(p[3]),
                             flux=float(p[5]), err=float(p[6]), snr=float(p[7]),
                             nfr=int(p[10]), fwhm=float(p[11]), ba=float(p[12]),
                             RG=float(p[13]), BG=float(p[14])))
        d = pd.DataFrame(rows)
        d['xc0'], d['yc0'] = 3894.1, 2765.6
        return d
    else:
        d = pd.read_csv(comu.work('vixen')/'catalog_vixen_fonts.csv')
        d = d[d.classe.isin(['A', 'B'])].copy()
        d = d.rename(columns={'x_px': 'x', 'y_px': 'y', 'flux_G_ADUs': 'flux',
                              'SNR_pila': 'snr'})
        d['id'] = ['V%02d' % i for i in d['id']]
        d['xc0'], d['yc0'] = 3577.1, 2266.1
        return d.reset_index(drop=True)

SCALE = {'sony': 3.234, 'r6': 2.158}

def solve(tag, nbright_det=16, vlim_bright=9.0, step_deg=0.25, bin_px=10.0, rng=600.0):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat_{tag}.csv')
    s = SCALE[tag]
    cat = cat[(cat.sep_deg < 4.8) & (cat.Vuse <= vlim_bright)].reset_index(drop=True)
    U0 = cat.xi_as.values/s
    V0 = cat.eta_as.values/s
    db = dets.sort_values('snr', ascending=False).head(nbright_det)
    p = db.x.values - db.xc0.values
    q = db.y.values - db.yc0.values
    print(f'[{tag}] deteccions usades {len(db)} | cataleg V<={vlim_bright} dins 4,8 deg: {len(cat)}')

    best = None
    nb = int(2*rng/bin_px)
    for sigma in (+1, -1):
        Us = sigma*U0
        for th in np.arange(0, 360, step_deg):
            c, sn = np.cos(np.radians(th)), np.sin(np.radians(th))
            Ur = c*Us - sn*V0
            Vr = sn*Us + c*V0
            dx = (p[:, None] - Ur[None, :]).ravel()
            dy = (q[:, None] - Vr[None, :]).ravel()
            m = (np.abs(dx) < rng) & (np.abs(dy) < rng)
            if m.sum() < 3:
                continue
            H, _, _ = np.histogram2d(dx[m], dy[m], bins=[nb, nb],
                                     range=[[-rng, rng], [-rng, rng]])
            # suma 2x2 per no perdre pics a cavall de dues cel.les
            H2 = H[:-1, :-1]+H[1:, :-1]+H[:-1, 1:]+H[1:, 1:]
            k = H2.max()
            if best is None or k > best[0]:
                i, j = np.unravel_index(H2.argmax(), H2.shape)
                bx = -rng + (i+1)*bin_px
                by = -rng + (j+1)*bin_px
                best = (k, sigma, th, bx, by)
    print(f'[{tag}] MILLOR: n={int(best[0])} parella  paritat={best[1]:+d}  '
          f'theta={best[2]:.2f} deg  dx={best[3]:.0f} dy={best[4]:.0f}')
    return dets, cat, best

if __name__ == '__main__':
    res = {}
    for tag in ('sony', 'r6'):
        dets, cat, best = solve(tag)
        res[tag] = dict(n=int(best[0]), sigma=int(best[1]), theta=float(best[2]),
                        dx=float(best[3]), dy=float(best[4]))
    json.dump(res, open('coarse.json', 'w'), indent=1)
