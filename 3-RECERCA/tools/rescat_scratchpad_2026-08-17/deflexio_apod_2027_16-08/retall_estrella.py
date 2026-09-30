#!/usr/bin/env python3
"""Retall real de l'estrella heroi, dels dos trens, per a l'animació.

HIP 46345 (S05 a la Sony, A-06 al Vixen): l'estrella interior més neta que
tenim. La seva llum va passar a 2,65 radis solars del centre del Sol.
"""
import json
import math
import numpy as np
import rawpy
from scipy import ndimage

SORTIDA = "/Users/USUARI/Desktop/Eclipse 2026/APOD"

TRENS = {
    "vixen": dict(
        path="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/572A2983.CR3",
        pedestal=511.5, esc=2.1495, sol=(3570.8, 2267.1), mitja=False,
        estrelles={"HIP 46345": (3091.35, 3333.33), "HIP 46335": (3385.56, 3198.57),
                   "HIP 46232": (6548.42, 1622.32)},
        titol="Vixen VSD90SS + R6 III", exp="10,3 s",
    ),
    "sony": dict(
        path="/Users/USUARI/Desktop/Eclipse 2026/300mm/DSC06993.ARW",
        pedestal=512.0, esc=3.2020, sol=(3894.7, 2768.7), mitja=True,
        estrelles={"HIP 46345": (3233.8, 3192.6), "HIP 46335": (3448.1, 3224.8)},
        titol="Sony A7R IIIA + 300 mm", exp="8 s",
        # la llista Sony està referida al segment posterior al salt
        offset=(-227.6, 706.5),
    ),
}

R_SOL = 946.66
ALPHA = 1.7516
N = 21          # mida del retall, en píxels del sensor
meta = {}

for tren, T in TRENS.items():
    with rawpy.imread(T["path"]) as r:
        raw = r.raw_image_visible.astype(np.float64) - T["pedestal"]
        col = r.raw_colors_visible.copy()
    if T["mitja"]:
        ys, xs = np.where(col[:2, :2] == 1)
        G = raw[int(ys[0])::2, int(xs[0])::2]
        fac, off0 = 2.0, (int(xs[0]), int(ys[0]))
    else:
        verd = (col == 1) | (col == 3)
        k = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float)
        su = ndimage.convolve(np.where(verd, raw, 0.0), k, mode="nearest")
        nv = ndimage.convolve(verd.astype(float), k, mode="nearest")
        G = np.where(verd, raw, su / np.maximum(nv, 1))
        fac, off0 = 1.0, (0, 0)

    for nom, (sx, sy) in T["estrelles"].items():
        x, y = sx, sy
        if "offset" in T:
            x += T["offset"][0]; y += T["offset"][1]
        X, Y = (x - off0[0]) / fac, (y - off0[1]) / fac
        i, j = int(round(Y)), int(round(X))
        h = N // 2
        cut = G[i-h:i+h+1, j-h:j+h+1].astype(np.float64)
        if cut.shape != (N, N):
            print(f"  {tren} {nom}: fora de camp"); continue
        # fons local d'un anell exterior
        yy, xx = np.mgrid[0:N, 0:N]
        rr = np.hypot(yy - h, xx - h)
        anell = (rr > h - 3.5) & (rr <= h - 0.5)
        bg = np.median(cut[anell])
        cut = cut - bg
        # centroide de precisió sobre la finestra central
        w = np.clip(cut, 0, None)
        m = rr <= 4.5
        cy = float((yy[m] * w[m]).sum() / w[m].sum())
        cx = float((xx[m] * w[m]).sum() / w[m].sum())
        # geometria: direcció radial cap enfora des del Sol
        dx, dy = (sx - T["sol"][0]) * T["esc"], (sy - T["sol"][1]) * T["esc"]
        rad = math.hypot(dx, dy)
        rsol = rad / R_SOL
        ux, uy = dx / rad, dy / rad
        gr = ALPHA / rsol
        meta.setdefault(nom, {})[tren] = dict(
            escala=T["esc"], r_sol=round(rsol, 3),
            gr_arcsec=round(gr, 4), newton_arcsec=round(gr / 2, 4),
            gr_px=round(gr / T["esc"], 4), newton_px=round(gr / 2 / T["esc"], 4),
            radial=[round(ux, 4), round(uy, 4)],
            centroide=[round(cx, 3), round(cy, 3)],
            pic=round(float(cut.max()), 1),
            fwhm_px=round(float(2.355 * math.sqrt(max(
                (w[m] * ((yy[m]-cy)**2 + (xx[m]-cx)**2)).sum() / w[m].sum() / 2, 0.01))), 2),
            titol=T["titol"], exp=T["exp"], n=N,
            dades=[[round(float(v), 1) for v in fila] for fila in cut],
        )
        print(f"  {tren:6s} {nom}: r={rsol:.3f} R☉  pic {cut.max():7.1f} ADU  "
              f"FWHM {meta[nom][tren]['fwhm_px']:.2f} px  "
              f"GR {gr:.3f}″ = {gr/T['esc']:.3f} px")

json.dump(meta, open(f"{SORTIDA}/retalls_estrelles.json", "w"), indent=1)
print(f"\n  desat a {SORTIDA}/retalls_estrelles.json")
