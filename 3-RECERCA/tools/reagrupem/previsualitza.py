#!/usr/bin/env python3
"""Previsualització del lliurament. ⛔ SEMPRE el llenç sencer, mai un retall."""
from __future__ import annotations
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402


def red(a, k):
    h, w = a.shape[:2]
    a = a[:h//k*k, :w//k*k]
    if a.ndim == 3:
        return a.reshape(h//k, k, w//k, k, 3).mean(axis=(1, 3))
    return a.reshape(h//k, k, w//k, k).mean(axis=(1, 3))


def superposa(b, d):
    """Mode Superposar de Photoshop."""
    return np.where(b <= 0.5, 2*b*d, 1 - 2*(1-b)*(1-d))


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    base = np.load(os.path.join(comu.F3, "BASE_rgb.npy"))
    m = np.load(os.path.join(comu.F3, "MASCARA.npy"))
    import json
    from astropy.io import fits
    F3 = json.load(open(os.path.join(comu.REBUTS, "F3_filtres.json")))
    anc = F3["corba_to"]["valor_ancora"]
    mult = {c: anc["G"]/anc[c] for c in ("R", "G", "B")}
    import f3_filtres as F
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy-H/2.0, xx-W/2.0); del yy, xx
    neu = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(("R", "G", "B")):
        C = fits.getdata(os.path.join(comu.F2, f"COLOR_cel_restat_{c}.fits")).astype(np.float32)
        neu[..., i], _ = F.corba_to(C*mult[c], rad, m)

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pass
    mm = red(m.astype(np.float32), k) > 0.5
    vistes = [("BASE calibrada", red(base, k)), ("BASE color neutralitzat", red(neu, k))]
    for nom, fx in (("passa-alt", "PASSA_ALT"), ("radial (plomalls)", "RADIAL"),
                    ("NRGF", "NRGF"), ("MGN", "MGN")):
        d = red(np.load(os.path.join(comu.F3, f"DETALL_{fx}.npy")), k)
        vistes.append((f"neutralitzat + {nom}",
                       superposa(red(neu, k), np.dstack([d]*3))))
    fig, axs = plt.subplots(2, 3, figsize=(30, 22), facecolor="#000000")
    for ax, (nom, im) in zip(axs.ravel(), vistes):
        ax.imshow(np.clip(np.where(mm[..., None], im, 0.0), 0, 1))
        ax.set_title(nom, color="#eeeeee", fontsize=17); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(f"LLIURAMENT VIXEN + R6 III · LLENÇ SENCER {W}x{H} px "
                 f"(±9,14 x ±10,13 R☉) · reduït {k}x · cap panell és un retall",
                 color="#ffffff", fontsize=22, y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    p = comu.vista(f"LLIURAMENT_x{k}.png")
    fig.savefig(p, dpi=95, facecolor=fig.get_facecolor()); plt.close(fig)
    print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
