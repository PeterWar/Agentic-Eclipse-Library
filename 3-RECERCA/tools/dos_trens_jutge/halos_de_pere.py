"""Els halos que Pere ha marcat en lila, mesurats APARELLATS.

No son un anell: al perfil radial mitja no hi ha res (derivada segona 0,0-0,5 σ).
Son ARCS locals, i la mediana azimutal hi es cega. Cada marca es compara amb
CONTROLS al MATEIX RADI i altres azimuts, que es l'unica comparacio justa.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
import cv2
from astropy.io import fits
from psd_tools import PSDImage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucli as N

H, W, RS = 8960, 8096, 440.60304883027544
MARQUES = "/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/" \
          "SONY_CIENCIA_20260827T104917Z/lliurables/Eclipsi_2026_SONY_CIENCIA_LILApsb"


def mascara_marques():
    L = list(PSDImage.open(MARQUES))[0]
    a = L.numpy()[..., :3].astype(np.float32)
    k0 = (a[..., 2] > a[..., 0] + 0.05) & (a[..., 2] > a[..., 1] + 0.05)
    k = np.zeros((H, W), bool)
    k[L.top:L.top + L.height, L.left:L.left + L.width] = k0
    n, lab, st, cen = cv2.connectedComponentsWithStats(
        cv2.dilate(k.astype(np.uint8), np.ones((25, 25), np.uint8)), 8)
    zones = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 1000:
            continue
        z = (lab == i)
        ys, xs = np.nonzero(z)
        r = np.hypot(xs - W / 2., ys - H / 2.) / RS
        th = np.degrees(np.arctan2(ys - H / 2., xs - W / 2.)) % 360
        zones.append(dict(mask=z, r=(r.min(), r.max()), th=(th.min(), th.max()),
                          n=int(z.sum()), rmid=float(np.median(r)),
                          thmid=float(np.median(th))))
    return zones, k


def controls(z, rad, ang, m, n=6):
    """Mateixa forma, mateix radi, azimuts diferents. Rotar la marca al voltant
    del Sol es la comparacio justa: mateixa area i mateixa banda radial."""
    ys, xs = np.nonzero(z["mask"])
    r = np.hypot(xs - W / 2., ys - H / 2.); t = np.arctan2(ys - H / 2., xs - W / 2.)
    out = []
    for k in range(1, n + 1):
        dt = 2 * np.pi * k / (n + 1)
        yy = (H / 2. + r * np.sin(t + dt)).astype(int)
        xx = (W / 2. + r * np.cos(t + dt)).astype(int)
        ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
        c = np.zeros((H, W), bool); c[yy[ok], xx[ok]] = True
        c &= m
        if c.sum() > 0.7 * z["n"]:
            out.append(c)
    return out


if __name__ == "__main__":
    d = N.darrer_run("SONY")
    zones, _ = mascara_marques()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2., xx - W / 2.); ang = np.arctan2(yy - H / 2., xx - W / 2.)
    del yy, xx
    m = np.load(os.path.join(d, "3-filtres", "MASCARA.npy"))
    prod = {"compost (lineal)": fits.getdata(os.path.join(d, "2-ldic", "CORONA_G.fits")).astype(np.float32),
            "pes": fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)}
    for c in ("PASSA_ALT", "RADIAL", "NRGF", "MGN"):
        prod[c] = np.load(os.path.join(d, "3-filtres", f"DETALL_{c}.npy"))

    print(f"{len(zones)} traços marcats\n")
    for i, z in enumerate(zones, 1):
        cs = controls(z, rad, ang, m)
        print(f"--- traç {i}: {z['n']:,} px · r {z['r'][0]:.3f}-{z['r'][1]:.3f} R☉ · "
              f"θ ~{z['thmid']:.0f}° · {len(cs)} controls al mateix radi")
        print(f"    {'producte':>18s} {'marca':>12s} {'controls':>12s} {'σ dels controls':>16s} {'desviació':>11s}")
        for nom, a in prod.items():
            v = float(np.nanmedian(a[z["mask"] & m]))
            cv_ = [float(np.nanmedian(a[c])) for c in cs]
            mu, sd = float(np.mean(cv_)), float(np.std(cv_))
            z_ = (v - mu) / sd if sd > 0 else np.nan
            print(f"    {nom:>18s} {v:12.5g} {mu:12.5g} {sd:16.4g} {z_:+10.2f} σ")
        print()
