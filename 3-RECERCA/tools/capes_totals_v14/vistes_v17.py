"""Vistes de la V17. ⛔ Sempre el llenç SENCER (norma de Pere): cap retall."""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v17")
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
DST = B + "CapesTotalsV17.psb"
VISTES = B + "CapesTotalsV17_vistes"


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    from psd_tools import PSDImage
    import fes_v14_pere as FP

    comp = np.load(os.path.join(CAU, "compost_v17.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "alfa_v17.npy"), mmap_mode="r")
    a = (np.asarray(alfa[::4, ::4], np.float32) / 255.0)[..., None]
    c = (np.asarray(comp[::4, ::4], np.float32) / 65535.0) * a + (1.0 - a)
    desa("V17_compost.png", (np.clip(c, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    desa("V17_compost_estirat.png",
         (np.clip(c * 1.8, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # la de la V16 (fusionada de Pere) al costat, per comparar
    p16 = PSDImage.open(B + "CapesTotalsV16.psb")
    st = p16.numpy()[::4, ::4]
    c16 = st[..., :3] * st[..., 3:4] + (1.0 - st[..., 3:4])
    desa("V16_compost_de_Pere.png",
         (np.clip(c16, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    del st, c16

    # la capa Sony nova sola, i la seva màscara
    psd = PSDImage.open(DST)
    W, H = psd.width, psd.height
    l13 = next(l for l in psd if l.name.startswith("13_"))
    arr = l13.numpy("color")[::4, ::4]
    desa("V17_capa_SONY_mes1s.png",
         (np.clip(arr, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    del arr
    m, _, _ = FP._decodifica_mascara(l13, W, H)
    desa("V17_capa_SONY_mes1s_mascara.png",
         (np.clip(m[::4, ::4], 0, 1) * 255).astype(np.uint8))
    del m
    # la màscara de la 09, abans (V16) i després
    l09v = next(l for l in PSDImage.open(B + "CapesTotalsV16.psb")
                if l.name.startswith("09_"))
    m0, _, _ = FP._decodifica_mascara(l09v, W, H)
    desa("V16_mascara_09.png", (np.clip(m0[::4, ::4], 0, 1) * 255).astype(np.uint8))
    l09 = next(l for l in psd if l.name.startswith("09_"))
    m1, _, _ = FP._decodifica_mascara(l09, W, H)
    desa("V17_mascara_09.png", (np.clip(m1[::4, ::4], 0, 1) * 255).astype(np.uint8))
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
