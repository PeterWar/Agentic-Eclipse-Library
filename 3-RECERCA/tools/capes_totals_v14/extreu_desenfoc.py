"""Extreu les peces del V18-DesenfocRadialZoom de Pere al cau_v19/desenfoc/.

[1] = l'original (visible, sense màscara)   → capa1_rgb16.npy
[2] = el duplicat desenfocat (visible)      → capa2_rgb16.npy + capa2_mask16.npy
[0],[3] = experiments apagats               → només metadades i mostres 1/4
I troba el centre del Sol al retall per correlació amb el compost de la V18.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2
from psd_tools import PSDImage
from psd_tools.compression import decompress

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19", "desenfoc")
CAU19 = os.path.join(AQUI, "cau_v19")
B = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
     "1-Unint Capes/Capes Totals/")
PSB = B + "V18-DesenfocRadialZoom.psb"
SOL_V18 = (6469.2, 6757.6)
RS = 455.5


def canal(layer, cid, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w, h = rec.right - rec.left, rec.bottom - rec.top
            if cid == -2 and rec.mask_data is not None:
                ms = rec.mask_data
                w, h = ms.right - ms.left, ms.bottom - ms.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            return np.frombuffer(arr, ">u2" if depth == 16 else "u1").reshape(h, w)
    return None


def main():
    os.makedirs(CAU, exist_ok=True)
    psd = PSDImage.open(PSB)
    d, v = psd.depth, psd.version
    capes = list(psd)
    W, H = psd.width, psd.height

    for i, noms in ((1, "capa1"), (2, "capa2")):
        ly = capes[i]
        rgb = np.stack([canal(ly, c, d, v) for c in (0, 1, 2)], -1)
        np.save(os.path.join(CAU, f"{noms}_rgb16.npy"), rgb)
        print(f"{noms}: {rgb.shape} desada")
        m = canal(ly, -2, d, v)
        if m is not None:
            np.save(os.path.join(CAU, f"{noms}_mask16.npy"), m)
            print(f"{noms}_mask: mitjana {m.mean()/655.35:.1f} %")
        del rgb, m
    for i, noms in ((0, "capa0"), (3, "capa3")):
        ly = capes[i]
        rgb = np.stack([canal(ly, c, d, v)[::4, ::4] for c in (0, 1, 2)], -1)
        np.save(os.path.join(CAU, f"{noms}_rgb16_q4.npy"), rgb)
        m = canal(ly, -2, d, v)
        if m is not None:
            np.save(os.path.join(CAU, f"{noms}_mask16_q4.npy"), m[::4, ::4])
        del rgb, m

    # centre del Sol al retall: correlació de fase de la capa 1 amb el compost
    # V18 (cau_v19/compost_pere_q4.npy, llenç 12415x12095 a 1/4)
    c1 = np.load(os.path.join(CAU, "capa1_rgb16.npy"), mmap_mode="r")
    g1 = np.asarray(c1[::4, ::4, 1], np.float32) / 65535.0
    cp = np.load(os.path.join(CAU19, "compost_pere_q4.npy"), mmap_mode="r")
    gp = np.asarray(cp[..., 1], np.float32)
    Hq, Wq = g1.shape
    # finestra del mateix cost al voltant del centre de cada un
    win = np.hanning(Hq)[:, None] * np.hanning(Wq)[None, :]
    a = (g1 - g1.mean()) * win
    Hp, Wp = gp.shape
    bb = np.zeros_like(gp)
    bb[:] = gp - gp.mean()
    A = np.fft.rfft2(a, s=(Hp, Wp))
    Bf = np.fft.rfft2(bb)
    R = Bf * np.conj(A)
    R /= np.maximum(np.abs(R), 1e-9)
    r = np.fft.irfft2(R, s=(Hp, Wp))
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    print(f"correlació de fase: pic a (x={ix*4}, y={iy*4}) resp {r.max():.3f}")
    # el pic (dy,dx) = desplaçament del retall dins del llenç V18 (en px 1/1)
    ox, oy = ix * 4, iy * 4
    sol_crop = (SOL_V18[0] - ox, SOL_V18[1] - oy)
    print(f"origen del retall dins la V18: ({ox},{oy}) → Sol al retall {sol_crop}")
    json.dump({"llenc": [W, H], "origen_dins_v18": [ox, oy],
               "sol_crop": list(sol_crop), "rs": RS,
               "resp_correlacio": float(r.max())},
              open(os.path.join(CAU, "geometria.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
