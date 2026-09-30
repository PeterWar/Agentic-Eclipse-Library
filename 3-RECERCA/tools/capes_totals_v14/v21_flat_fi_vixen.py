"""La mota del sensor R6: correcció amb el flat fi, al marc lunar.

El run 017 calibra amb FLAT_RADIAL (validat), que per construcció no porta
l'estructura local del sensor. El MASTER_FINE_SENSOR dels flats del 22-08 sí:
a (3579, 2374) hi ha una mota de ±4-6 % que al marc lunar es disfressa de
tret lunar (+33 comptes al Vixen; la Sony no la veu). Corregim dividint cada
fotograma Vixen pel flat fi remostrejat amb la mateixa geometria.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2
from astropy.io import fits as AF

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17

MB = (6465.398680355321, 6752.632845814709)
FF = ("/Users/USUARI/Downloads/Eclipse 2026/output/flats_20260822/"
      "vixen_r6iii_posterior_v1/MASTER_FINE_SENSOR_FACTOR_CFA.fits")
FRAMES = ["572A2979", "572A2980", "572A2981", "572A2982", "572A2983", "572A2984"]


def main():
    flat = np.nan_to_num(AF.getdata(FF).astype(np.float32), nan=1.0)
    flat[flat < 0.5] = 1.0
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    sv = F17.SV16(); geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    V = F15.RUN_VIXEN
    S13 = json.load(open(os.path.join(V, "4-rebuts", "F1.3_registre.json")))["fotogrames"]
    Xv, Yv = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                         np.arange(y0, y1, dtype=np.float32))
    x15, y15 = sv.enrere(Xv, Yv)
    px = (x15 - geo15.padx - F15.SENSOR_A_V13[0]).astype(np.float32)
    py = (y15 - geo15.pady - F15.SENSOR_A_V13[1]).astype(np.float32)
    m15 = sv.enrere(np.float32(MB[0]), np.float32(MB[1]))
    mbx = float(m15[0] - geo15.padx - F15.SENSOR_A_V13[0])
    mby = float(m15[1] - geo15.pady - F15.SENSOR_A_V13[1])
    for f in FRAMES:
        v = S13[f + ".CR3"]
        mx = v["sol_x"] + v["lluna_dx"]; my = v["sol_y"] + v["lluna_dy"]
        rx = px - mbx + mx; ry = py - mby + my
        Ffi = cv2.remap(flat, rx, ry, cv2.INTER_LINEAR, borderValue=1.0)
        src = f"{CAU}/lluna_vixen_{f}_lineal.npy"
        crua = f"{CAU}/lluna_vixen_{f}_lineal_SENSE_FLATFI.npy"
        if not os.path.exists(crua):
            os.rename(src, crua)
        A = np.load(crua)
        np.save(src, (A / Ffi[..., None]).astype(np.float32))
        z = Ffi[500:560, 300:360]
        print(f"  {f}: flat fi a la zona de la mota min {z.min():.4f} "
              f"max {z.max():.4f} — corregit")


if __name__ == "__main__":
    main()
