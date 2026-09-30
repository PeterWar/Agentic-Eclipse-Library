"""Vistes de la V18. ⛔ Llenç sencer sempre; cap retall."""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v18")
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
VISTES = B + "CapesTotalsV18_vistes"


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    comp = np.load(os.path.join(CAU, "compost_v18.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "alfa_v18.npy"), mmap_mode="r")
    a = (np.asarray(alfa[::4, ::4], np.float32) / 255.0)[..., None]
    c = (np.asarray(comp[::4, ::4], np.float32) / 65535.0) * a + (1.0 - a)
    desa("V18_compost.png", (np.clip(c, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # l'abans: compost amb la Sony SENSE igualar (les peces del cau de la V17 de Pere)
    sota = np.load(os.path.join(CAU, "vixen_sota_rgb16.npy"), mmap_mode="r")
    sony = np.load(os.path.join(CAU, "sony_pere_rgb16.npy"), mmap_mode="r")
    mskp = np.load(os.path.join(CAU, "sony_pere_mask16.npy"), mmap_mode="r")
    alfav = np.load(os.path.join(CAU, "vixen_sota_alfa8.npy"), mmap_mode="r")
    s4 = np.asarray(sony[::4, ::4], np.float32) / 65535.0
    v4 = np.asarray(sota[::4, ::4], np.float32) / 65535.0
    m4 = (np.asarray(mskp[::4, ::4], np.float32) / 65535.0)[..., None]
    a4 = (np.asarray(alfav[::4, ::4], np.float32) / 255.0)[..., None]
    ab = s4 * m4 + v4 * a4 * (1 - m4)
    aa = a4 + m4 * (1 - a4)
    ab = ab + (1 - aa)
    desa("V17_de_Pere_amb_halos.png",
         (np.clip(ab, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # el camp de correcció ρ (G), i les marques de Pere a sobre del compost nou
    rho = np.load(os.path.join(CAU, "rho_q4.npy"))
    rg = np.clip((rho[..., 1] - 0.75) / 0.5, 0, 1)
    desa("V18_camp_correccio_rho_G.png", (rg * 255).astype(np.uint8))
    marca = np.load(os.path.join(CAU, "halos_marca.npy"), mmap_mode="r")
    m6 = np.asarray(marca[::4, ::4]) > 0
    img = (np.clip(c, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
    img[m6] = (0, 0, 255)
    desa("V18_compost_amb_marques_de_Pere.png", img)
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
