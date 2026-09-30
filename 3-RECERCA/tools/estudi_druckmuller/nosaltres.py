"""El nostre producte amb la MATEIXA vara que Brno.

Tres nivells, per saber si el marro es de la DADA o del RENDERITZAT:
  A. CORONA_{R,G,B}.fits  -> dada lineal amb el cel ja restat
  B. BASE_rgb.npy         -> el que es lliura (corba de to aplicada)
"""
import json, os
import numpy as np
from astropy.io import fits

R = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
g = json.load(open(R + "4-rebuts/F1.2_sol_llenc.json"))["llenc"]
W, H, Rsol = g["W"], g["H"], g["R_sol_px"]
cy, cx = H / 2.0, W / 2.0
yy, xx = np.mgrid[0:H, 0:W]
r = np.hypot(yy - cy, xx - cx).astype(np.float32) / Rsol
del yy, xx
r_ple = min(cy, cx) / Rsol
print(f"llenc {W}x{H}  R_sol {Rsol:.1f} px  anell sencer fins a {r_ple:.2f} R_sol\n")


def estructura(cub, etiq, vores):
    print(f"--- {etiq} ---")
    print(f"{'r':>6} {'cob':>5} {'nivell':>9} | {'TOT R/G':>8} {'TOT B/G':>8} | {'EST R/G':>8} {'EST B/G':>8}")
    fil = []
    for a, b in zip(vores[:-1], vores[1:]):
        m = (r >= a) & (r < b)
        n = int(m.sum())
        if n < 2000:
            continue
        v = np.stack([c[m] for c in cub], axis=1).astype(np.float64)
        ok = np.isfinite(v).all(axis=1)
        v = v[ok]
        if v.shape[0] < 2000:
            continue
        cob = ok.sum() / n
        lv = v @ np.array([0.2126, 0.7152, 0.0722])
        alt = lv >= np.percentile(lv, 85)
        baix = lv <= np.percentile(lv, 35)
        e = v[alt].mean(0) - v[baix].mean(0)
        t = v.mean(0)
        rc = float(np.sqrt(a * b))
        fil.append((rc, cob, float(np.median(lv)), t[0]/t[1], t[2]/t[1],
                    e[0]/e[1] if abs(e[1]) > 1e-12 else np.nan,
                    e[2]/e[1] if abs(e[1]) > 1e-12 else np.nan))
        print(f"{rc:6.2f} {cob*100:4.0f}% {np.median(lv):9.4g} | {t[0]/t[1]:8.3f} {t[2]/t[1]:8.3f} "
              f"| {fil[-1][5]:8.3f} {fil[-1][6]:8.3f}")
    f = [x for x in fil if x[1] > 0.999 and x[0] < 5.0]
    if f:
        rg = np.array([x[5] for x in f]); bg = np.array([x[6] for x in f])
        print(f"  >> mediana 1,05-5,0 R_sol amb anell SENCER:  EST R/G {np.nanmedian(rg):.3f}   EST B/G {np.nanmedian(bg):.3f}")
    return fil


vores = np.geomspace(1.05, 9.0, 22)
cor = [fits.getdata(R + f"2-ldic/CORONA_{c}.fits").astype(np.float32) for c in "RGB"]
fc = estructura(cor, "A. DADA LINEAL (CORONA_*.fits, cel restat)", vores)
del cor
print()
base = np.load(R + "3-filtres/BASE_rgb.npy")
fb = estructura([base[:, :, i] for i in range(3)], "B. EL QUE ES LLIURA (BASE_rgb, corba de to)", vores)
json.dump({"corona": fc, "base": fb}, open(os.path.dirname(os.path.abspath(__file__)) + "/nosaltres.json", "w"), indent=1)
