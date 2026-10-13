#!/usr/bin/env python3
"""Solucio de placa definitiva al marc horitzontal refractat, amb rebuig
d'atipics i terme de distorsio radial opcional. Dona escala, PA del nord
celeste, centre i residus.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/final_solve.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, pandas as pd, json, pickle
from skyfield.api import load, wgs84, Star
from solve import load_dets, SCALE
from refine3 import coarse, predict

ts = load.timescale()
eph = comu.efemeride()
lloc = eph['earth'] + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
TEMP, PRES = 20.0, 930.0
EPOCHS = {'sony': (2026, 8, 12, 18, 29, 48.0), 'r6': (2026, 8, 12, 18, 29, 18.6)}
CX, CY = 'xh_as', 'yh_as'


def fit_lin(xi, eta, X, Y, w=None, radial=False):
    cols = [np.ones_like(xi), xi, eta]
    if radial:
        r2 = xi*xi + eta*eta
        cols += [xi*r2, eta*r2]
    A = np.column_stack(cols)
    if w is None:
        w = np.ones_like(xi)
    W = np.sqrt(w)[:, None]
    px, *_ = np.linalg.lstsq(A*W, X*np.sqrt(w), rcond=None)
    py, *_ = np.linalg.lstsq(A*W, Y*np.sqrt(w), rcond=None)
    return px, py, A


def apply(px, py, xi, eta, radial=False):
    cols = [np.ones_like(xi), xi, eta]
    if radial:
        r2 = xi*xi+eta*eta
        cols += [xi*r2, eta*r2]
    A = np.column_stack(cols)
    return A@px, A@py


def solve_final(tag, vlim=11.0, radial=False, clip=3.0, verbose=True):
    dets = load_dets(tag)
    cat = pd.read_csv(f'cat2_{tag}.csv')
    cat = cat[(cat.sep_deg < 5.0) & (cat.Vuse <= vlim)].reset_index(drop=True)
    s = SCALE[tag]
    cs = coarse(tag, CX, CY)
    _, sg, th, dx0, dy0 = cs
    thr = np.radians(th)
    par = np.array([dets.xc0[0]+dx0, np.cos(thr)*sg/s, -np.sin(thr)/s,
                    dets.yc0[0]+dy0, np.sin(thr)*sg/s, np.cos(thr)/s])
    xi = cat[CX].values; eta = cat[CY].values
    X = dets.x.values; Y = dets.y.values
    px = np.array([par[0], par[1], par[2]]); py = np.array([par[3], par[4], par[5]])
    use_rad = False
    for k, tol in enumerate(list(np.geomspace(45., 7., 8)) + [7.]*6):
        Px, Py = apply(px, py, xi, eta, use_rad)
        D = np.hypot(X[:, None]-Px[None, :], Y[:, None]-Py[None, :])
        j = D.argmin(axis=1); dmin = D[np.arange(len(X)), j]
        ok = dmin < tol
        for jj in np.unique(j[ok]):
            w = np.where(ok & (j == jj))[0]
            if len(w) > 1:
                b = w[np.argmin(dmin[w])]; ok[w] = False; ok[b] = True
        if ok.sum() < 5:
            break
        if k >= 8:                       # a partir d'aqui, sigma-clipping
            Px2, Py2 = apply(px, py, xi[j[ok]], eta[j[ok]], use_rad)
            r = np.hypot(X[ok]-Px2, Y[ok]-Py2)
            sig = 1.4826*np.median(np.abs(r-np.median(r)))
            keep = r < np.median(r)+clip*max(sig, 0.5)
            idx = np.where(ok)[0]
            ok[idx[~keep]] = False
            use_rad = radial
        px, py, _ = fit_lin(xi[j[ok]], eta[j[ok]], X[ok], Y[ok], radial=use_rad)
    Px2, Py2 = apply(px, py, xi[j[ok]], eta[j[ok]], use_rad)
    res = np.hypot(X[ok]-Px2, Y[ok]-Py2)
    n = int(ok.sum())
    nparam = len(px)*2
    rms = float(np.sqrt((res**2).sum()/max(2*n-nparam, 1)*2))
    a, b = px[1], px[2]; c, d = py[1], py[2]
    sx = 1/np.hypot(a, c); sy = 1/np.hypot(b, d)
    scale = 1/np.sqrt(abs(a*d-b*c))
    skew = np.degrees(np.arccos(abs((a*b+c*d)/(np.hypot(a, c)*np.hypot(b, d)))))-90.

    # --- direccio del NORD CELESTE sobre el sensor ---
    t = ts.utc(*EPOCHS[tag])
    aps = lloc.at(t).observe(eph['sun']).apparent()
    sra, sdec, sdist = aps.radec()
    salt, saz, _ = aps.altaz(temperature_C=TEMP, pressure_mbar=PRES)

    def altaz_of(ra_deg, dec_deg):
        st = Star(ra_hours=ra_deg/15., dec_degrees=dec_deg)
        ap = lloc.at(t).observe(st).apparent()
        al, az, _ = ap.altaz(temperature_C=TEMP, pressure_mbar=PRES)
        return al.degrees, az.degrees

    def to_tangent(al, az):
        def uv(A, Z):
            A = np.radians(A); Z = np.radians(Z)
            return np.array([np.cos(A)*np.cos(Z), np.cos(A)*np.sin(Z), np.sin(A)])
        ur = uv(salt.degrees, saz.degrees)
        zen = np.array([0., 0., 1.])
        f2 = zen-ur*np.dot(zen, ur); f2 /= np.linalg.norm(f2)
        f1 = np.cross(f2, ur)
        u = uv(al, az); u = u/np.linalg.norm(u)
        den = np.dot(u, ur)
        return np.degrees(np.dot(u, f1)/den)*3600, np.degrees(np.dot(u, f2)/den)*3600

    step = 600.0/3600.
    xN, yN = to_tangent(*altaz_of(sra._degrees, sdec.degrees+step))
    xE, yE = to_tangent(*altaz_of(sra._degrees+step/np.cos(np.radians(sdec.degrees)),
                                  sdec.degrees))
    x0s, y0s = to_tangent(salt.degrees, saz.degrees)
    P0 = apply(px, py, np.array([x0s]), np.array([y0s]), use_rad)
    PN = apply(px, py, np.array([xN]), np.array([yN]), use_rad)
    PE = apply(px, py, np.array([xE]), np.array([yE]), use_rad)
    vN = np.array([PN[0][0]-P0[0][0], PN[1][0]-P0[1][0]])
    vE = np.array([PE[0][0]-P0[0][0], PE[1][0]-P0[1][0]])
    pa_N = np.degrees(np.arctan2(vN[0], -vN[1])) % 360   # antihorari des d'"amunt" (-y)
    pa_E = np.degrees(np.arctan2(vE[0], -vE[1])) % 360
    # zenit
    xZ, yZ = 0.0, 600.0
    PZ = apply(px, py, np.array([xZ]), np.array([yZ]), use_rad)
    vZ = np.array([PZ[0][0]-P0[0][0], PZ[1][0]-P0[1][0]])
    pa_Z = np.degrees(np.arctan2(vZ[0], -vZ[1])) % 360
    mirror = bool((a*d-b*c) > 0)   # y avall => det>0 vol dir imatge en mirall al cel

    out = dict(tag=tag, n=n, rms=rms, scale=float(scale), sx=float(sx), sy=float(sy),
               skew=float(skew), pa_north=float(pa_N), pa_east=float(pa_E),
               pa_zenith=float(pa_Z), mirror=mirror,
               sun_x=float(P0[0][0]), sun_y=float(P0[1][0]),
               radial=use_rad, px=list(map(float, px)), py=list(map(float, py)),
               scale_ref=SCALE[tag])
    if verbose:
        print(f'--- {tag} ---  n={n}  rms={rms:.2f} px  radial={use_rad}')
        print(f'    escala   = {scale:.4f} "/px   (referencia {SCALE[tag]}, '
              f'{100*(scale/SCALE[tag]-1):+.2f} %)')
        print(f'    anisotropia {100*(sx/sy-1):+.3f} %   no-perpendicularitat {skew:+.3f} deg')
        print(f'    PA nord celeste = {pa_N:.2f} deg   PA est = {pa_E:.2f}   '
              f'PA zenit = {pa_Z:.2f}   mirall={mirror}')
        print(f'    centre del SOL al sensor = ({P0[0][0]:.1f}, {P0[1][0]:.1f}) px  '
              f'| centre lunar adoptat = ({dets.xc0[0]:.1f}, {dets.yc0[0]:.1f})')
    # taula d'aparellaments
    rows = []
    ii = np.where(ok)[0]
    for k2, i2 in enumerate(ii):
        j2 = j[i2]
        rows.append(dict(det=dets.id[i2], x=X[i2], y=Y[i2], HIP=cat.HIP[j2],
                         TYC=cat.TYC[j2], HD=cat.HD[j2], V=cat.Vuse[j2],
                         BV=cat.BVuse[j2], Sp=cat.Sp[j2], sep_deg=cat.sep_deg[j2],
                         resid=float(res[k2]),
                         dx=float(X[i2]-Px2[k2]), dy=float(Y[i2]-Py2[k2]),
                         flux=dets.flux[i2], snr=dets.snr[i2]))
    tab = pd.DataFrame(rows).sort_values('V')
    tab.to_csv(f'final_match_{tag}.csv', index=False)
    return out, tab


if __name__ == '__main__':
    res = {}
    for tag in ('sony', 'r6'):
        for rad in (False, True):
            o, tab = solve_final(tag, radial=rad)
            if not rad:
                res[tag] = o
            else:
                res[tag+'_radial'] = o
        print()
    json.dump(res, open('final_solution.json', 'w'), indent=1)
    # productes finals: copia a comu.out()
    import shutil
    for f in ('final_solution.json', 'final_match_sony.csv', 'final_match_r6.csv'):
        shutil.copy2(f, comu.out()/f)
