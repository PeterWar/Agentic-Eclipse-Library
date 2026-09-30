"""Tasca 4, tercera peca (be fet): la familia fina GIRA amb l'azimut o no?

⛔ El primer intent partia l'anell en sectors i hi feia una FFT. No serveix:
la vora de la falca es una discontinuitat dura dins de la caixa i la seva fuita
domina l'espectre —els pics sortien tots a 45,5° i 134,5°, que son les
diagonals de la caixa, amb «excessos» de x245 que no son de la dada—.

Aqui es fa LOCAL i sense cap FFT: es filtra la banda (diferencia de gaussianes
centrada a lambda 6-10 px), es calcula el **tensor d'estructura** i, pixel a
pixel, l'orientacio dominant. Despres es compara amb la direccio RADIAL del
mateix pixel.

  estructura de CORONA  → orientacio ~ radial a tot arreu (gira amb l'azimut)
  artefacte de GRAELLA  → orientacio clavada al mateix angle del llenc
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import cv2
from astropy.io import fits

import nucli as N
from estriat import normalitza_radi

R0, R1 = 1.40, 2.60
S1, S2 = 1.2, 2.6          # diferencia de gaussianes: passa-banda λ ≈ 6-12 px
SIG_T = 6.0                # finestra del tensor d'estructura


def orienta(z, k):
    b = cv2.GaussianBlur(z, (0, 0), S1) - cv2.GaussianBlur(z, (0, 0), S2)
    b = np.where(k, b, 0.0).astype(np.float32)
    gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3)
    Jxx = cv2.GaussianBlur(gx * gx, (0, 0), SIG_T)
    Jyy = cv2.GaussianBlur(gy * gy, (0, 0), SIG_T)
    Jxy = cv2.GaussianBlur(gx * gy, (0, 0), SIG_T)
    # orientacio de la ESTRUCTURA (perpendicular al gradient dominant)
    ang = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)           # direccio del gradient
    est = (np.degrees(ang) + 90.0) % 180.0
    tr = Jxx + Jyy
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / np.maximum(tr, 1e-20)
    return est, coh, tr


def dang(a, b):
    d = np.abs(a - b) % 180.0
    return np.minimum(d, 180.0 - d)


if __name__ == "__main__":
    for tren in (sys.argv[1:] or ["VIXEN", "SONYTOT"]):
        d = N.darrer_run(tren)
        S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
        LL = S["llenc"]; RS = LL["R_sol_px"]
        a = fits.getdata(os.path.join(d, "2-ldic", "CORONA_G.fits")).astype(np.float32)
        w = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
        H, W = a.shape
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dy, dx = yy - H / 2.0, xx - W / 2.0
        rad = np.hypot(dy, dx)
        radial = (np.degrees(np.arctan2(dy, dx))) % 180.0
        th = (np.degrees(np.arctan2(dy, dx)) % 360.0)
        del yy, xx, dy, dx
        k = (w > 0.05 * np.nanpercentile(w[w > 0], 90)) & (rad >= R0 * RS) \
            & (rad <= R1 * RS) & np.isfinite(a)
        z = normalitza_radi(a.astype(np.float64), k, rad).astype(np.float32)
        est, coh, tr = orienta(z, k)
        # nomes on l'orientacio vol dir alguna cosa
        kk = k & (coh > 0.5) & (tr > np.percentile(tr[k], 50))
        dr = dang(est[kk], radial[kk])
        df = dang(est[kk], np.float32(169.5))
        print(f"\n{tren}: {os.path.basename(d)}  ({kk.sum():,} px amb orientació "
              f"definida de {k.sum():,})")
        print(f"  |orientació − RADIAL|  mediana {np.median(dr):5.1f}°   "
              f"< 20° al {100*np.mean(dr < 20):4.1f} % dels píxels")
        print(f"  |orientació − 169,5°|  mediana {np.median(df):5.1f}°   "
              f"< 20° al {100*np.mean(df < 20):4.1f} % dels píxels")
        print(f"  (a l'atzar seria 45,0° i 44,4 %)")
        print(f"  {'sector':>10s} {'radial':>8s} {'mediana orient.':>16s} "
              f"{'|−radial|':>10s} {'|−169,5°|':>11s}")
        for s in range(8):
            a0, a1 = s * 45.0, (s + 1) * 45.0
            m = kk & (th >= a0) & (th < a1)
            if m.sum() < 5000:
                continue
            e = est[m]
            # mediana circular de 180°: pel vector doble
            mu = 0.5 * np.degrees(np.arctan2(np.mean(np.sin(np.radians(2 * e))),
                                             np.mean(np.cos(np.radians(2 * e))))) % 180.0
            print(f"{a0:5.0f}-{a1:<4.0f} {(a0+a1)/2 % 180:8.1f} {mu:16.1f} "
                  f"{float(np.median(dang(e, (a0+a1)/2 % 180))):9.1f}° "
                  f"{float(np.median(dang(e, 169.5))):10.1f}°")
        del a, w, rad, radial, th, z, est, coh, tr
    print("\n  radial petit → CORONA (gira amb l'azimut) · 169,5° petit → GRAELLA")
