"""Vistes de la V19. ⛔ Llenç sencer sempre; cap retall."""
from __future__ import annotations

import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19")
CAU18 = os.path.join(AQUI, "cau_v18")
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
VISTES = B + "CapesTotalsV19_vistes"


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    comp = np.load(os.path.join(CAU, "compost_v19.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "alfa_v19.npy"), mmap_mode="r")
    a = (np.asarray(alfa[::4, ::4], np.float32) / 255.0)[..., None]
    c = (np.asarray(comp[::4, ::4], np.float32) / 65535.0) * a + (1.0 - a)
    c8 = (np.clip(c, 0, 1) * 255).astype(np.uint8)[..., ::-1]
    desa("V19_compost.png", c8)

    # l'abans: el compost de la V18 tal com Pere el veia (sense els traços)
    ab = np.load(os.path.join(CAU, "compost_pere_q4.npy"))
    mq = (np.asarray(np.load(os.path.join(CAU18, "sony_pere_mask16.npy"),
                             mmap_mode="r")[::4, ::4], np.float32) / 65535.0)
    aq = (np.asarray(np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"),
                             mmap_mode="r")[::4, ::4], np.float32) / 255.0)
    at = mq + aq * (1 - mq)
    abw = ab + (1 - at[..., None])
    desa("V18_de_Pere_abans.png",
         (np.clip(abw, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # el resultat amb les marques de Pere sobreposades (verd i taronja seus)
    mv = np.asarray(np.load(os.path.join(CAU, "marques_verd.npy"),
                            mmap_mode="r")[::4, ::4]) > 0
    mt = np.asarray(np.load(os.path.join(CAU, "marques_taronja.npy"),
                            mmap_mode="r")[::4, ::4]) > 0
    img = c8.copy()
    img[mv] = (80, 255, 80)     # BGR: verd
    img[mt] = (0, 165, 255)     # BGR: taronja
    desa("V19_compost_amb_marques_de_Pere.png", img)

    # el camp de correcció (G) i el seu croma R/G
    rho = np.load(os.path.join(CAU, "rho_v19_q4.npy"))
    rg = np.clip((rho[..., 1] - 0.75) / 0.5, 0, 1)
    desa("V19_camp_correccio_rho_G.png", (rg * 255).astype(np.uint8))
    cr = np.clip((rho[..., 0] / rho[..., 1] - 0.80) / 0.25, 0, 1)
    desa("V19_camp_correccio_croma_RG.png", (cr * 255).astype(np.uint8))
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
