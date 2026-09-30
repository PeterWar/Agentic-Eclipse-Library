"""Els dos trens, cara a cara, al llenç sencer i a l'Output.

Tres panells al MATEIX marc: Vixen, Sony i la diferència d'estructura. Com que
tots dos aterren al llenç comú, es poden mirar l'un damunt de l'altre sense cap
transformació pel mig.
"""
from __future__ import annotations
import json, os
import sys
import numpy as np
import cv2
from PIL import Image

import nucli as N

K = 4
SORTIDA = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/DOS_TRENS")


def perfil_radial(a, rad, m, nb=900, rmax=None):
    rmax = rmax or float(rad[m].max())
    idx = np.clip((rad / rmax * nb).astype(np.int32), 0, nb - 1)
    k = m & np.isfinite(a)
    c = np.bincount(idx[k], None, nb); s = np.bincount(idx[k], a[k], nb)
    mu = np.where(c > 200, s / np.maximum(c, 1), np.nan)
    s2 = np.bincount(idx[k], np.abs(a[k] - mu[idx[k]]), nb)
    sd = np.where(c > 200, s2 / np.maximum(c, 1), np.nan) * 1.4826
    for v in (mu, sd):
        bo = np.isfinite(v)
        v[:] = np.interp(np.arange(nb), np.arange(nb)[bo], v[bo])
    return mu[idx], np.maximum(sd[idx], 1e-12)


def gris(a, m, lo=-2.2, hi=2.2):
    v = np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1)
    g = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
    g[~m] = np.array([110, 35, 130], np.uint8)
    return g


if __name__ == "__main__":
    os.makedirs(SORTIDA, exist_ok=True)
    A = sys.argv[1].upper() if len(sys.argv) > 1 else "VIXEN"
    B = sys.argv[2].upper() if len(sys.argv) > 2 else "SONY"
    E, M, runs = {}, {}, {}
    for t in (A, B):
        lum, pes, LL, S, d = N.carrega(t)
        H, W = lum.shape
        h, w = H // K, W // K
        small = lambda a: cv2.resize(a.astype(np.float32), (w, h),
                                     interpolation=cv2.INTER_AREA)
        a = small(lum); p = small(pes); del lum, pes
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        rad = np.hypot(yy - h / 2.0, xx - w / 2.0) * K / LL["R_sol_px"]
        del yy, xx
        ref = np.nanpercentile(p[rad < 6.0], 90)
        m = np.isfinite(a) & (p > 0.02 * ref) & (rad > 1.0) & (rad < 9.5)
        mu, sd = perfil_radial(a.astype(np.float64), rad, m)
        E[t] = (a - mu) / sd; M[t] = m; runs[t] = os.path.basename(d)
        print(f"{t}: {runs[t]} · {m.sum():,} px amb dada")

    tots = M[A] & M[B]
    dif = np.where(tots, E[A] - E[B], np.nan)
    pans = [gris(E[A], M[A]), gris(E[B], M[B]), gris(dif, tots, -3, 3)]
    h, w = pans[0].shape[:2]
    tela = np.full((h, w * 3 + 24, 3), 20, np.uint8)
    for i, im in enumerate(pans):
        tela[:, i * (w + 12):i * (w + 12) + w] = im
    p = os.path.join(SORTIDA, f"ESTRUCTURA_{A}_{B}_diferencia_x{K}.png")
    Image.fromarray(tela).save(p)
    print(f"\n{p}\n  llenç sencer reduït ×{K} · panells: {A} · {B} · diferència"
          f"\n  lila = sense dada · comparteixen la mateixa graella exactament")
