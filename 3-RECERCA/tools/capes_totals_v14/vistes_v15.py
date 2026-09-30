"""Vistes de la V15. ⛔ Sempre el llenç SENCER (norma de Pere): cap retall;
el que canvia és només l'escala de reducció i l'estirament.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v15")
import fes_v15 as F

VISTES = os.path.join(os.path.dirname(F.DST), "CapesTotalsV15_vistes")


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def main():
    os.makedirs(VISTES, exist_ok=True)
    rebut = json.load(open(os.path.join(CAU, "rebut_v15.json")))
    W, H = rebut["llenc"]
    comp = np.load(os.path.join(CAU, "compost_v15.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "alfa_v15.npy"), mmap_mode="r")

    a = (np.asarray(alfa[::4, ::4], np.float32) / 255.0)[..., None]
    c = (np.asarray(comp[::4, ::4], np.float32) / 65535.0) * a + (1.0 - a)
    desa("V15_compost.png", (np.clip(c, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    desa("V15_compost_estirat.png",
         (np.clip(c * 2.2, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    del a, c

    # la capa Sony sola (render + màscara), al llenç sencer reduït
    from psd_tools import PSDImage
    psd = PSDImage.open(F.DST)
    sony = list(psd)[0]
    x0, y0, x1, y1 = sony.bbox
    arr = sony.numpy("color")[::4, ::4]
    buf = np.zeros((H // 4 + 1, W // 4 + 1, 3), np.float32)
    buf[y0 // 4:y0 // 4 + arr.shape[0], x0 // 4:x0 // 4 + arr.shape[1]] = arr
    desa("V15_capa_SONY_8s.png",
         (np.clip(buf, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    del arr, buf
    import fes_v14_pere as FP
    m, _, _ = FP._decodifica_mascara(sony, W, H)
    desa("V15_capa_SONY_8s_mascara.png",
         (np.clip(m[::4, ::4], 0, 1) * 255).astype(np.uint8))
    del m

    # on és la V14 dins de la V15: el contorn del llenç vell sobre el compost
    padx, pady = rebut["pad"]
    a = (np.asarray(alfa[::4, ::4], np.float32) / 255.0)[..., None]
    c = (np.asarray(comp[::4, ::4], np.float32) / 65535.0) * a + (1.0 - a)
    img = (np.clip(c * 2.2, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
    cv2.rectangle(img, (padx // 4, pady // 4),
                  ((padx + 7648) // 4, (pady + 5353) // 4), (0, 255, 255), 2)
    desa("V15_on_es_la_V14.png", img)
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
