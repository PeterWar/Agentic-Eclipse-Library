#!/usr/bin/env python3
"""FASE 0 · vistes de diagnòstic dels màsters de dark.

⛔ **NORMA: cap vista és un retall.** Tots els panells són el fotograma
SENCER, 7144x4760, amb els marges emmascarats inclosos i marcats. El que es
fa per cabre-hi és reduir la resolució (mitjana de blocs de 8x8 = 16 cel·les
CFA senceres), que no amaga cap zona.

Ús:
    python3 f0_vista_masters.py
"""

from __future__ import annotations

import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import rawpy  # noqa: E402
from astropy.io import fits  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

BLOC = 8


def redueix(a: np.ndarray, k: int = BLOC) -> np.ndarray:
    h, w = a.shape
    return a[: h // k * k, : w // k * k].reshape(h // k, k, w // k, k).mean(axis=(1, 3))


def main() -> int:
    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r)
    dir_m = os.path.join(comu.F0, "masters_dark")
    fs = sorted(glob.glob(dir_m + "/*.fits"),
                key=lambda p: float(p.split("_E")[1].rstrip("s.fits")))
    sortida = comu.OUT_VISTES
    os.makedirs(sortida, exist_ok=True)

    fig, axs = plt.subplots(4, 4, figsize=(26, 18), facecolor="#0b0b0b")
    for ax, p in zip(axs.ravel(), fs):
        e = float(p.split("_E")[1].rstrip("s.fits"))
        d = redueix(fits.getdata(p).astype(np.float64))
        med = np.median(d)
        im = ax.imshow(d, cmap="magma", vmin=med - 1.5, vmax=med + 3.0,
                       interpolation="nearest")
        # marges emmascarats, en coordenades reduïdes
        ax.add_patch(Rectangle((g.marge_esq / BLOC, g.marge_dalt / BLOC),
                               g.ample_visible / BLOC if hasattr(g, "ample_visible")
                               else (g.ample - g.marge_esq - g.marge_dreta) / BLOC,
                               (g.alt - g.marge_dalt - g.marge_baix) / BLOC,
                               fill=False, ec="#33ddff", lw=0.8, ls="--"))
        ax.set_title(f"{e:.6g} s   ·   mediana {med:.2f} DN",
                     color="#e8e8e8", fontsize=11, pad=4)
        ax.set_xticks([]); ax.set_yticks([])
        cb = plt.colorbar(im, ax=ax, fraction=0.032, pad=0.01)
        cb.ax.tick_params(colors="#bbbbbb", labelsize=7)
    fig.suptitle(
        "FASE 0 · màsters de dark de la Canon R6 III — FOTOGRAMA SENCER "
        f"({g.ample}x{g.alt}, marges inclosos; blau = vora de la zona activa)",
        color="#ffffff", fontsize=16, y=0.985)
    fig.text(0.5, 0.006,
             "Escala per panell: mediana −1,5 a +3,0 DN. Reducció 8x8 "
             "(mitjana de 16 cel·les CFA). Cap panell és un retall.",
             color="#999999", ha="center", fontsize=11)
    fig.tight_layout(rect=(0, 0.018, 1, 0.972))
    p1 = os.path.join(sortida, "F0_masters_dark_tots.png")
    fig.savefig(p1, dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)

    # el de 10 s, sencer i a més resolució, que és el que es mou
    p10 = [p for p in fs if p.endswith("E10s.fits")][0]
    d = redueix(fits.getdata(p10).astype(np.float64), 4)
    fig, ax = plt.subplots(figsize=(22, 15), facecolor="#0b0b0b")
    med = np.median(d)
    im = ax.imshow(d, cmap="magma", vmin=med - 1.5, vmax=med + 4.0, interpolation="nearest")
    ax.add_patch(Rectangle((g.marge_esq / 4, g.marge_dalt / 4),
                           (g.ample - g.marge_esq - g.marge_dreta) / 4,
                           (g.alt - g.marge_dalt - g.marge_baix) / 4,
                           fill=False, ec="#33ddff", lw=1.2, ls="--"))
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, fraction=0.03).ax.tick_params(colors="#bbbbbb")
    ax.set_title(f"Màster de dark 10 s — FOTOGRAMA SENCER {g.ample}x{g.alt}, "
                 f"mediana {med:.2f} DN, escala −1,5 / +4,0 DN",
                 color="#ffffff", fontsize=15)
    fig.tight_layout()
    p2 = os.path.join(sortida, "F0_master_dark_10s.png")
    fig.savefig(p2, dpi=110, facecolor=fig.get_facecolor()); plt.close(fig)
    print(p1); print(p2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
