"""Vistes de la V19 (fons per raig). ⛔ Llenç sencer sempre; cap retall.

Escriu al cau (repo); es copien al costat del PSB quan l'accés al Desktop torna.
"""
from __future__ import annotations

import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAUF = os.path.join(AQUI, "cau_v19", "fons")
CAU19 = os.path.join(AQUI, "cau_v19")
VISTES = os.path.join(CAUF, "vistes")


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    F = np.load(os.path.join(CAUF, "F_v19_rgb16.npy"), mmap_mode="r")
    f4 = np.asarray(F[::4, ::4], np.float32) / 65535.0
    f8 = (np.clip(f4, 0, 1) * 255).astype(np.uint8)[..., ::-1]
    desa("V19_compost.png", f8)

    ab = np.load(os.path.join(CAU19, "compost_pere_q4.npy"))
    a8 = np.load(os.path.join(CAUF, "alfaT8.npy"), mmap_mode="r")
    # l'abans (la V18 de Pere) amb matte blanc on no hi havia cobertura
    cob = None
    import numpy as _np
    S16 = np.load(os.path.join(CAU19, "mask_v18.npy"), mmap_mode="r")
    A8v = np.load(os.path.join(AQUI, "cau_v18", "vixen_sota_alfa8.npy"),
                  mmap_mode="r")
    mq = np.asarray(S16[::4, ::4], np.float32) / 65535.0
    aq = np.asarray(A8v[::4, ::4], np.float32) / 255.0
    at = mq + aq * (1 - mq)
    abw = ab + (1 - at[..., None])
    desa("V18_de_Pere_abans.png",
         (np.clip(abw, 0, 1) * 255).astype(np.uint8)[..., ::-1])

    # el resultat amb les marques de Pere de les DUES rondes sobreposades
    img = f8.copy()
    mv = np.asarray(np.load(os.path.join(CAU19, "marques_verd.npy"),
                            mmap_mode="r")[::4, ::4]) > 0
    mt = np.asarray(np.load(os.path.join(CAU19, "marques_taronja.npy"),
                            mmap_mode="r")[::4, ::4]) > 0
    m1 = np.asarray(np.load(os.path.join(AQUI, "cau_v18", "halos_marca.npy"),
                            mmap_mode="r")[::4, ::4]) > 0
    img[m1] = (0, 0, 255)
    img[mv] = (80, 255, 80)
    img[mt] = (0, 165, 255)
    desa("V19_compost_amb_marques_de_Pere.png", img)

    # el fons B i la rampa
    Bf = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")
    b8 = (np.clip(np.asarray(Bf[::4, ::4], np.float32) / 65535.0, 0, 1)
          * 255).astype(np.uint8)[..., ::-1]
    desa("V19_fons_B.png", b8)
    ra = np.load(os.path.join(CAUF, "mask_rampa16.npy"), mmap_mode="r")
    desa("V19_rampa_mascara.png",
         (np.asarray(ra[::4, ::4], np.float32) / 257.0).astype(np.uint8))

    # les estrelles reinjectades, sobre el compost
    est = np.load(os.path.join(CAUF, "estrelles_v19.npy"))
    img2 = f8.copy()
    for x, y, c0, a_, mm in est:
        cv2.circle(img2, (int(x) // 4, int(y) // 4), 3,
                   (0, 255, 0) if c0 > 0 else (255, 200, 0), 1)
    desa("V19_estrelles_reinjectades.png", img2)
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
