"""Vistes de la V21. ⛔ Llenç sencer sempre; cap retall."""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
CAU19 = os.path.join(AQUI, "cau_v19")
CAUF = os.path.join(CAU19, "fons")
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
VISTES = B + "CapesTotalsV21_vistes"


def desa(nom, img8):
    cv2.imwrite(os.path.join(VISTES, nom), img8)
    print(f"  {nom}")


def flatten_v21():
    """El mateix flatten que la fusionada del PSB, a 1/4."""
    q = 4
    mS = np.load(os.path.join(CAU19, "mask_v18.npy"), mmap_mode="r")[::q, ::q]
    mF = np.load(os.path.join(CAUF, "mask_rampa16.npy"), mmap_mode="r")[::q, ::q]
    S12 = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")[::q, ::q]
    V16 = np.load(os.path.join(AQUI, "cau_v18", "vixen_sota_rgb16.npy"),
                  mmap_mode="r")[::q, ::q]
    A8 = np.load(os.path.join(AQUI, "cau_v18", "vixen_sota_alfa8.npy"),
                 mmap_mode="r")[::q, ::q]
    Bf = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")[::q, ::q]
    E16 = None  # les 87 estrelles són invisibles a 1/4; cercles a la vista de marques
    Sm = None
    meta = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    ya, yb = meta["banda_lluna"]
    apl = np.load(os.path.join(CAU, "apilat_lluna_rgb.npy"), mmap_mode="r")
    trl = np.load(os.path.join(CAU, "apilat_lluna_tres.npy"), mmap_mode="r")
    mx16, my16 = meta["lluna_base_canvas"]
    Rl = meta["rl_canvas"]

    ms = np.asarray(mS, np.float32) / 65535.0
    mf = np.asarray(mF, np.float32) / 65535.0
    av = np.asarray(A8, np.float32) / 255.0
    H4, W4 = ms.shape
    yy = np.arange(H4, dtype=np.float32)[:, None] * q
    xx = np.arange(W4, dtype=np.float32)[None, :] * q
    dl = np.hypot(xx - mx16, yy - my16)
    me4 = np.zeros((H4, W4), np.float32)
    fila0 = int(np.ceil(ya / q))
    apl4 = np.asarray(apl[(fila0 * q - ya)::q, ::q], np.float32)
    trl4 = np.asarray(trl[(fila0 * q - ya)::q, ::q], np.float32)
    nf = apl4.shape[0]
    me4[fila0:fila0 + nf] = (np.clip(((Rl - 8.0) - dl[fila0:fila0 + nf]) / 5.0,
                                     0, 1) * trl4)
    out = np.empty((H4, W4, 3), np.float32)
    for ch in range(3):
        C = (np.asarray(S12[..., ch], np.float32) * ms
             + np.asarray(V16[..., ch], np.float32) * av * (1 - ms))
        F = C * (1 - mf) + np.asarray(Bf[..., ch], np.float32) * mf
        E4 = np.zeros((H4, W4), np.float32)
        E4[fila0:fila0 + nf] = apl4[..., ch]
        F = F * (1 - me4) + E4 * me4
        out[..., ch] = np.clip(F, 0, 65535) / 65535.0
    return out


def main():
    os.makedirs(VISTES, exist_ok=True)
    f4 = flatten_v21()
    f8 = (np.clip(f4, 0, 1) * 255).astype(np.uint8)[..., ::-1]
    desa("V21_compost.png", f8)

    est = np.load(os.path.join(CAU, "estrelles_v21_purga.npy"))
    img = f8.copy()
    for x, y, c0, a_ in est:
        cv2.circle(img, (int(x) // 4, int(y) // 4), 6, (0, 255, 0), 1)
    desa("V21_compost_amb_estrelles_marcades.png", img)

    # l'apilat registrat a les estrelles, sencer (per comparar amb la capa 12)
    ap = np.load(os.path.join(CAU, "apilat_estrelles_rgb.npy"), mmap_mode="r")
    a8 = (np.clip(np.asarray(ap[::4, ::4], np.float32) / 65535.0, 0, 1)
          * 255).astype(np.uint8)[..., ::-1]
    desa("V21_apilat_registrat_estrelles.png", a8)

    # el llenç amb NOMÉS la capa d'earthshine (sobre negre): on és i què porta
    meta = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    ya, yb = meta["banda_lluna"]
    apl = np.load(os.path.join(CAU, "apilat_lluna_rgb.npy"), mmap_mode="r")
    H4, W4 = f4.shape[:2]
    e4 = np.zeros((H4, W4, 3), np.float32)
    fila0 = int(np.ceil(ya / 4))
    apl4 = np.asarray(apl[(fila0 * 4 - ya)::4, ::4], np.float32) / 65535.0
    e4[fila0:fila0 + apl4.shape[0]] = apl4
    desa("V21_capa_earthshine_al_llenc.png",
         (np.clip(e4, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    print(f"\nvistes a {VISTES}")


if __name__ == "__main__":
    main()
