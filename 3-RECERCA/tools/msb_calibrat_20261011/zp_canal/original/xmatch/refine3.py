#!/usr/bin/env python3
"""Cerca grollera propia per a cada marc + refinament. Deixa la solucio definitiva.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/refine3.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, pandas as pd, json, pickle
from solve import load_dets, SCALE
from refine import fit_affine, fit_similarity, predict

FRAMES = {'eq_norefr': ('xi_as', 'eta_as'),
          'hor_refr':  ('xh_as', 'yh_as'),
          'hor_norefr': ('xh0_as', 'yh0_as')}


def coarse(tag, cx, cy, vlim=10.5, step=0.15, bin_px=10., rng=700.):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat2_{tag}.csv')
    cat = cat[(cat.sep_deg < 4.8) & (cat.Vuse <= vlim)].reset_index(drop=True)
    s = SCALE[tag]
    U0 = cat[cx].values/s; V0 = cat[cy].values/s
    p = dets.x.values - dets.xc0.values
    q = dets.y.values - dets.yc0.values
    nb = int(2*rng/bin_px); best = None
    for sg in (+1, -1):
        Us = sg*U0
        for th in np.arange(0, 360, step):
            c, sn = np.cos(np.radians(th)), np.sin(np.radians(th))
            Ur = c*Us - sn*V0; Vr = sn*Us + c*V0
            dx = (p[:, None]-Ur[None, :]).ravel(); dy = (q[:, None]-Vr[None, :]).ravel()
            m = (np.abs(dx) < rng) & (np.abs(dy) < rng)
            if m.sum() < 3:
                continue
            H, _, _ = np.histogram2d(dx[m], dy[m], bins=[nb, nb], range=[[-rng, rng]]*2)
            H2 = H[:-1, :-1]+H[1:, :-1]+H[:-1, 1:]+H[1:, 1:]
            i, j = np.unravel_index(H2.argmax(), H2.shape)
            if best is None or H2[i, j] > best[0]:
                best = (H2[i, j], sg, th, -rng+(i+1)*bin_px, -rng+(j+1)*bin_px)
    return best


def refine(tag, cx, cy, cs, vlim=11.0, tol0=45., tolmin=7., nit=8, model='affine'):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat2_{tag}.csv')
    cat = cat[(cat.sep_deg < 5.0) & (cat.Vuse <= vlim)].reset_index(drop=True)
    s = SCALE[tag]
    _, sg, th, dx0, dy0 = cs
    th = np.radians(th)
    par = np.array([dets.xc0[0]+dx0, np.cos(th)*sg/s, -np.sin(th)/s,
                    dets.yc0[0]+dy0, np.sin(th)*sg/s, np.cos(th)/s])
    xi = cat[cx].values; eta = cat[cy].values
    X = dets.x.values; Y = dets.y.values
    for tol in np.geomspace(tol0, tolmin, nit):
        px, py = predict(par, xi, eta)
        D = np.hypot(X[:, None]-px[None, :], Y[:, None]-py[None, :])
        j = D.argmin(axis=1); dmin = D[np.arange(len(X)), j]
        ok = dmin < tol
        for jj in np.unique(j[ok]):
            w = np.where(ok & (j == jj))[0]
            if len(w) > 1:
                k = w[np.argmin(dmin[w])]; ok[w] = False; ok[k] = True
        if ok.sum() < 4:
            break
        par = (fit_affine(xi[j[ok]], eta[j[ok]], X[ok], Y[ok]) if model == 'affine'
               else fit_similarity(xi[j[ok]], eta[j[ok]], X[ok], Y[ok])[0])
    px, py = predict(par, xi[j[ok]], eta[j[ok]])
    rms = float(np.sqrt(((X[ok]-px)**2+(Y[ok]-py)**2).mean()))
    x0, a, b, y0, c, d = par
    sx = 1/np.hypot(a, c); sy = 1/np.hypot(b, d)
    skew = np.degrees(np.arccos(abs((a*b+c*d)/(np.hypot(a, c)*np.hypot(b, d)))))-90.
    return dict(n=int(ok.sum()), rms=rms, sx=float(sx), sy=float(sy), skew=float(skew),
                par=par, ok=ok, j=j, dets=dets, cat=cat)


if __name__ == '__main__':
    store = {}
    for tag in ('sony', 'r6'):
        print(f'===== {tag}  (escala de referencia {SCALE[tag]} "/px) =====')
        for name, (cx, cy) in FRAMES.items():
            cs = coarse(tag, cx, cy)
            ra = refine(tag, cx, cy, cs, model='affine')
            rs = refine(tag, cx, cy, cs, model='sim')
            print(f'  {name:11s} coarse n={int(cs[0]):3d} th={cs[2]:7.2f} | '
                  f'AFI n={ra["n"]:3d} rms={ra["rms"]:5.2f} '
                  f'e1={ra["sx"]:.4f} e2={ra["sy"]:.4f} aniso={100*(ra["sx"]/ra["sy"]-1):+.3f}% '
                  f'noperp={ra["skew"]:+.3f}  | SIM n={rs["n"]:3d} rms={rs["rms"]:5.2f} e={rs["sx"]:.4f}')
            store[(tag, name)] = (ra, rs)
        print()
    pickle.dump({k: {kk: {a: b for a, b in v.items() if a not in ('dets', 'cat')}
                     for kk, v in zip(('afi', 'sim'), val)}
                 for k, val in store.items()}, open('frames.pkl', 'wb'))
