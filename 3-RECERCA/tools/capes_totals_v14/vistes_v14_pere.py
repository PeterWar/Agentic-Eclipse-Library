"""Vistes de la V14 (edició de la V13_Pere). ⛔ Sempre el llenç SENCER: cap retall
(norma de Pere del 26-08); el que canvia entre vistes és només l'escala i l'estirament.

- compostos a 1/2 de mida; parell de blink del limbe a MIDA COMPLETA i estirat ×3
  (el vel i la vora es veuen allà); fulls de contacte de màscares a 1/8.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v13pere")
import fes_v14_pere as F

VISTES = os.path.join(os.path.dirname(F.DST), "CapesTotalsV14_vistes")


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    from psd_tools import PSDImage

    comp14 = np.load(os.path.join(CAU, "compost_v14.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "alfa_v14.npy"), mmap_mode="r")
    a14 = (np.asarray(alfa, np.float32) / 255.0)[..., None]
    c14 = np.asarray(comp14, np.float32) / 65535.0 * a14 + (1.0 - a14)
    st13 = PSDImage.open(F.SRC).numpy()
    a13 = st13[..., 3:4]
    c13 = st13[..., :3] * a13 + (1.0 - a13)

    for nom, c in (("V14", c14), ("V13Pere", c13)):
        desa(f"{nom}_compost.png",
             (np.clip(c, 0, 1) * 255).astype(np.uint8)[::2, ::2][..., ::-1])
        desa(f"{nom}_limbe_estirat.png",
             (np.clip(c * 3.0, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # màscares: full de contacte 3×4 (1/8) dels dos fitxers
    v14 = PSDImage.open(F.DST)
    v13 = PSDImage.open(F.SRC)
    W, H = v13.width, v13.height
    for nom, psd in (("V13Pere", v13), ("V14", v14)):
        fulles = []
        for layer in psd:
            num = layer.name.split("_")[0]
            m, _, _ = F._decodifica_mascara(layer, W, H)
            im = np.ascontiguousarray(
                (np.clip(m, 0, 1) * 255).astype(np.uint8)[::8, ::8])
            cv2.putText(im, num, (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 2.2, 255, 4)
            fulles.append(im)
        files = [np.concatenate(fulles[i:i + 4], axis=1) for i in (0, 4, 8)]
        desa(f"{nom}_mascares_contacte.png", np.concatenate(files, axis=0))

    # les protagonistes, senceres a 1/4: 12 (intacta), 11, 10 i 01, abans/després
    for numv in ("12", "11", "10", "01"):
        for nom, psd in (("V13Pere", v13), ("V14", v14)):
            layer = next(l for l in psd if l.name.split("_")[0] == numv)
            m, _, _ = F._decodifica_mascara(layer, W, H)
            desa(f"{nom}_mascara_{numv}.png",
                 (np.clip(m, 0, 1) * 255).astype(np.uint8)[::4, ::4])
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
