#!/usr/bin/env python3
"""Versió NETA (sense marques) de les dues imatges d'estrelles, per a l'APOD.

Mateix processat que `mascara_estrelles.py` — pla verd cru, arcsinh, mateix
tint — però sense cercles ni text. NOMÉS LECTURA sobre els RAW originals.
Escriu a ~/Desktop/Eclipse 2026/APOD/.
"""
import os
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image

SORTIDA = "/Users/USUARI/Desktop/Eclipse 2026/APOD"
os.makedirs(SORTIDA, exist_ok=True)

TRENS = {
    "sony": dict(
        path="/Users/USUARI/Desktop/Eclipse 2026/300mm/DSC06993.ARW",
        pedestal=512.0, mitja_res=True, box=16,
        nom="eclipsi_sony_300mm_net",
    ),
    "vixen": dict(
        path="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/572A2983.CR3",
        pedestal=511.5, mitja_res=False, box=24,
        nom="eclipsi_vixen_vsd90ss_net",
    ),
}


def fons(a, box=16, suau=1.4):
    hh, ww = a.shape[0] // box, a.shape[1] // box
    med = np.median(a[:hh * box, :ww * box].reshape(hh, box, ww, box), axis=(1, 3))
    med = ndimage.gaussian_filter(med, suau)
    return ndimage.zoom(med, (a.shape[0] / hh, a.shape[1] / ww), order=3)[:a.shape[0], :a.shape[1]]


for tren, T in TRENS.items():
    with rawpy.imread(T["path"]) as r:
        raw = r.raw_image_visible.astype(np.float64) - T["pedestal"]
        col = r.raw_colors_visible.copy()

    if T["mitja_res"]:
        ys, xs = np.where(col[:2, :2] == 1)
        G = raw[int(ys[0])::2, int(xs[0])::2]
    else:
        verd = (col == 1) | (col == 3)
        Gm = np.where(verd, raw, 0.0)
        k = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float)
        su = ndimage.convolve(Gm, k, mode="nearest")
        nv = ndimage.convolve(verd.astype(float), k, mode="nearest")
        G = np.where(verd, raw, su / np.maximum(nv, 1))

    H, W = G.shape
    bg = fons(G, T["box"])
    res = G - bg
    sd = np.maximum(fons(np.abs(res), T["box"]) * 1.4826, 1e-6)
    snr = res / sd

    ctx = np.arcsinh(np.clip(G, 0, None) / 40.0)
    lo, hi = np.percentile(ctx, 1), np.percentile(ctx, 99.9)
    ctx = np.clip((ctx - lo) / (hi - lo), 0, 1)
    punts = np.clip(snr / 9.0, 0, 1) ** 0.75
    llindar = np.percentile(bg, 99.0)
    pes = ndimage.gaussian_filter(1.0 / (1.0 + (np.clip(bg, 0, None) / max(llindar, 1e-6)) ** 2), 12)
    lum = np.clip(ctx * 0.46 + punts * pes * 0.95, 0, 1)
    rgb = np.clip(np.stack([lum] * 3, -1)
                  + np.clip(ctx * 0.42, 0, 1)[..., None] * np.array([0.30, 0.16, -0.10]), 0, 1)
    img = Image.fromarray((rgb * 255).astype(np.uint8))

    png = os.path.join(SORTIDA, T["nom"] + ".png")
    img.save(png)
    # versió de lliurament, 2400 px d'ample
    w = 2400
    img.resize((w, round(H * w / W)), Image.LANCZOS).save(
        os.path.join(SORTIDA, T["nom"] + "_2400.jpg"), quality=92, subsampling=0)
    print(f"{tren:6s} {W}x{H}  →  {png}")

# i les anotades, redimensionades igual
for tren, base in (("sony", "estrelles_sony_marcades"), ("vixen", "estrelles_vixen_marcades")):
    src = f"/Users/USUARI/Desktop/Eclipse 2026/Estrelles/{base}.png"
    im = Image.open(src)
    w = 2400
    im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).convert("RGB").save(
        os.path.join(SORTIDA, base + "_2400.jpg"), quality=92, subsampling=0)
    print(f"{tren:6s} anotada  →  {base}_2400.jpg")
