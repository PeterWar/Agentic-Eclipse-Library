"""Quant amplifica cada banda angular el realçat multiescala?

La prova A del diagnòstic anterior diu que al compost LINEAL, a 2,05–2,55 R☉,
la potència azimutal per damunt de m=180 (estructures més estretes de 2°) és
del 0,0 %. Si a la FOTO n'hi ha molta, l'ha fabricada el renderitzat.

Es compara, banda per banda, la mateixa quantitat a:
  · el compost lineal normalitzat pel perfil radial (`norm`)
  · el mateix després de `realca` amb els paràmetres vius
  · la FOTO lliurada
"""
import os
import sys
import math

import numpy as np
import cv2
import tifffile
from scipy.ndimage import gaussian_filter

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M  # noqa: E402

OUT = M.OUT
NA = 4096
BANDES = [(5, 20), (20, 60), (60, 180), (180, 400), (400, 900), (900, 2000)]


def polar(img, cy, cx, nr):
    return cv2.warpPolar(np.nan_to_num(img, nan=0.0).astype(np.float32),
                         (nr, NA), (cx, cy), float(nr),
                         cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR)


def bandes(pol, rr, r0, r1):
    sel = (rr > r0) & (rr < r1)
    b = pol[:, sel].astype(np.float64)
    mu = b.mean(0, keepdims=True)
    b = b / np.maximum(mu, 1e-12) - 1.0
    F = np.fft.rfft(b * np.hanning(NA)[:, None], axis=0)
    P = (np.abs(F) ** 2).mean(1)
    # rms de contrast per banda (Parseval, finestra de Hann compensada)
    esc = 2.0 / (NA * (np.hanning(NA) ** 2).sum())
    return {(lo, hi): math.sqrt(max(P[lo:hi].sum() * esc, 0.0)) for lo, hi in BANDES}


def main():
    hdr = np.load(OUT / "hdr_vixen_countss.npy")
    varm = np.load(OUT / "hdr_vixen_var.npy")
    H, W, _ = hdr.shape
    cy, cx = H / 2.0, W / 2.0
    L = hdr[..., 1]
    valid = np.all(np.isfinite(hdr), axis=2)
    r = M.anells(H, W, cy, cx)
    base, _ = M.perfil_azimutal(np.where(valid, L, np.nan), r, min(H, W) / 2.0)
    norm = np.where(valid, L / np.maximum(base, 1e-9), 1.0)

    # realçat EXACTAMENT com el fa etapa_foto
    vG = np.nan_to_num(varm[..., 1])
    sig = np.sqrt(np.maximum(vG, 0)) / np.maximum(base, 1e-6)
    rs = r / M.R_SOL_PX
    cel_z = valid & (rs > 3.6) & (rs < 4.6)
    obs = float(np.std((norm - gaussian_filter(norm, 2.0))[cel_z]))
    esp = float(np.median(sig[cel_z]))
    print(f"porta de soroll: observat {obs:.5f} · esperat {esp:.5f} "
          f"→ factor {obs/esp:.3f}")
    sig = sig * (obs / esp if esp > 0 else 1.0)
    D = np.clip(M.realca(norm, M.ESCALES_DETALL, sig, 0.5), -1, 1)
    realcat = 1.0 + M.BETA_DETALL * D

    foto = tifffile.imread(OUT / "corona_vixen_FOTO.tif")
    if foto.dtype == np.uint16:
        foto = foto.astype(np.float64) / 65535.0
    # la FOTO va retallada: es reconstrueix la reixa completa
    fH = np.full((H, W), np.nan)
    fH[M.RETALL[0]:M.RETALL[1] + 1, M.RETALL[2]:M.RETALL[3] + 1] = \
        foto[..., 1].astype(np.float64)

    nr = int(min(H, W) / 2)
    capes = {
        "lineal (norm)": polar(norm, cy, cx, nr),
        "detall (1+βD)": polar(realcat, cy, cx, nr),
        "FOTO verd": polar(fH, cy, cx, nr),
    }
    rr = np.arange(nr) / M.R_SOL_PX

    for r0, r1 in [(1.35, 1.65), (2.05, 2.55), (3.15, 3.85)]:
        print(f"\n=== anell {r0}–{r1} R☉ : contrast rms per banda angular ===")
        print(f"{'banda m':>12} {'amplada':>14} " +
              " ".join(f"{k:>15}" for k in capes))
        res = {k: bandes(v, rr, r0, r1) for k, v in capes.items()}
        for lo, hi in BANDES:
            amp = f"{360/hi:.2f}°–{360/lo:.2f}°"
            fila = " ".join(f"{res[k][(lo,hi)]:15.5f}" for k in capes)
            print(f"{lo:5d}–{hi:5d} {amp:>14} {fila}")
        print(f"{'':>12} {'AMPLIFICACIÓ':>14} " +
              " ".join(f"{'':>15}" for _ in capes))
        b0 = res["lineal (norm)"]
        for lo, hi in BANDES:
            amp = f"{360/hi:.2f}°–{360/lo:.2f}°"
            g1 = res["detall (1+βD)"][(lo, hi)] / max(b0[(lo, hi)], 1e-12)
            g2 = res["FOTO verd"][(lo, hi)] / max(b0[(lo, hi)], 1e-12)
            print(f"{lo:5d}–{hi:5d} {amp:>14} {'':>15} {g1:14.1f}× {g2:14.1f}×")
    return 0


if __name__ == "__main__":
    sys.exit(main())
