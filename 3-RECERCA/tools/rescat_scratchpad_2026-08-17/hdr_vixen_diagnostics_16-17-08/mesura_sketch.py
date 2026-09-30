"""Contrast per banda angular del sketch de Pere, per fixar l'objectiu.

El sketch va a 15312×10375 i no és un escalat pur de la FOTO, o sigui que la
geometria s'ha de resoldre: es busca el limbe lunar (el màxim del gradient
radial) i d'allà surten centre i escala.
"""
import sys
import math

import numpy as np
import cv2
import tifffile

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M  # noqa: E402

NA = 4096
BANDES = [(5, 20), (20, 60), (60, 180), (180, 400), (400, 900), (900, 2000)]
RAO_LLUNA = M.R_LLUNA_PX / M.R_SOL_PX      # 1,031 de magnitud local


def geometria(g, esc_previa=8):
    """Centre i radi del limbe sobre una versió reduïda."""
    p = cv2.resize(g, (g.shape[1] // esc_previa, g.shape[0] // esc_previa),
                   interpolation=cv2.INTER_AREA)
    llind = np.percentile(p, 99.5)
    ys, xs = np.nonzero(p >= llind)
    cy, cx = float(ys.mean()), float(xs.mean())
    for _ in range(6):
        h, w = p.shape
        yy = (np.arange(h) - cy)[:, None]
        xx = (np.arange(w) - cx)[None, :]
        rr = np.hypot(xx, yy).astype(np.int32)
        n = int(rr.max()) + 1
        prof = np.bincount(rr.ravel(), p.ravel(), n) / np.maximum(
            np.bincount(rr.ravel(), None, n), 1)
        rl = int(np.argmax(prof[3:])) + 3
        # recentra amb el moment del propi anell brillant
        m = (rr > rl - 2) & (rr < rl + 2)
        ys, xs = np.nonzero(m & (p > np.percentile(p[m], 40)))
        cy, cx = float(ys.mean()), float(xs.mean())
    return cy * esc_previa, cx * esc_previa, rl * esc_previa


def bandes(g, cy, cx, r_sol, r0, r1):
    nr = int(min(g.shape[0] - cy, cy, g.shape[1] - cx, cx))
    pol = cv2.warpPolar(g, (nr, NA), (cx, cy), float(nr),
                        cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR)
    rr = np.arange(nr) / r_sol
    sel = (rr > r0) & (rr < r1)
    if sel.sum() < 4:
        return None
    b = pol[:, sel].astype(np.float64)
    b = b / np.maximum(b.mean(0, keepdims=True), 1e-12) - 1.0
    F = np.fft.rfft(b * np.hanning(NA)[:, None], axis=0)
    P = (np.abs(F) ** 2).mean(1)
    esc = 2.0 / (NA * (np.hanning(NA) ** 2).sum())
    return {(lo, hi): math.sqrt(max(P[lo:hi].sum() * esc, 0.0))
            for lo, hi in BANDES}


def carrega(cami):
    a = tifffile.imread(cami)
    g = a[..., 1].astype(np.float32)
    del a
    return g / 65535.0 if g.max() > 2 else g


def main():
    res = {}
    for etiq, cami in [("SKETCH", "/Users/USUARI/Downloads/Sketchaprox.tif")] + \
            [(n.replace("corona_vixen_", "").replace(".tif", ""), str(M.OUT / n))
             for n in sys.argv[1:]]:
        g = carrega(cami)
        cy, cx, rl = geometria(g)
        r_sol = rl / RAO_LLUNA
        print(f"{etiq:9s} {g.shape[1]}×{g.shape[0]}  centre ({cx:.0f}, {cy:.0f})  "
              f"limbe {rl:.0f} px  →  R☉ = {r_sol:.1f} px  "
              f"(escala ×{r_sol/M.R_SOL_PX:.3f})")
        res[etiq] = {ar: bandes(g, cy, cx, r_sol, *ar)
                     for ar in [(1.35, 1.65), (2.05, 2.55), (3.15, 3.85)]}
        del g

    for ar in [(1.35, 1.65), (2.05, 2.55), (3.15, 3.85)]:
        print(f"\n=== anell {ar[0]}–{ar[1]} R☉ : contrast rms per banda ===")
        noms = [k for k in res if res[k][ar] is not None]
        print(f"{'banda m':>12} {'amplada':>13} " + " ".join(f"{k:>10}" for k in noms)
              + "     " + " ".join(f"{k[:7]+'/sk':>11}" for k in noms if k != "SKETCH"))
        for lo, hi in BANDES:
            v = " ".join(f"{res[k][ar][(lo,hi)]:10.5f}" for k in noms)
            q = " ".join(f"{res[k][ar][(lo,hi)]/max(res['SKETCH'][ar][(lo,hi)],1e-12):10.2f}×"
                         for k in noms if k != "SKETCH")
            print(f"{lo:5d}–{hi:5d} {360/hi:5.2f}°–{360/lo:5.2f}° {v}     {q}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
