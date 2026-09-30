"""V21b: la capa EARTHSHINE definitiva — el residu asimètric del disc, visible.

El disc en lineal = VEL (radialment simètric, llum escampada) + EARTHSHINE
(estructura asimètrica: maria, terres altes, Aristarchus). La capa nova:

    display = P + (asim_suau / escala) · A

amb P (pedestal) i A (amplitud) DECLARATS (cosmètic; l'honestedat és al rebut:
l'amplitud lineal real és ±5-10 % del vel). Monocrom (el color del residu és
soroll; Pere regrada). Es desa el contingut i la màscara per al muntatge.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")

PEDESTAL = 0.42       # nivell mitjà del disc al render (fosc, de lluna cendrosa)
AMPLITUD = 0.20       # excursió per a ±escala (p95 de |asim|)
SIGMA_SUAU = 2.5      # px: treu el gra sense tocar les maria


def main():
    res = np.load(os.path.join(CAU, "earthshine_lineal_residus.npy"))
    vels = np.load(os.path.join(CAU, "earthshine_lineal_vels.npy"))
    disc = np.load(os.path.join(CAU, "earthshine_lineal_disc.npy"))
    mj = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    ya, yb = mj["banda_lluna"]
    mx, my = mj["lluna_base_canvas"]
    Rl = mj["rl_canvas"]
    h, W = disc.shape
    yy = np.arange(h, dtype=np.float32)[:, None] + ya
    xx = np.arange(W, dtype=np.float32)[None, :]
    dl = np.hypot(xx - mx, yy - my)

    # residu asimètric: total − perfil radial (mediana per anell de 3 px)
    tot = vels[..., 1] + res[..., 1]
    db = (dl / 3.0).astype(np.int32)
    asim = np.zeros_like(tot)
    for b in range(int(Rl / 3) + 2):
        m = disc & (db == b)
        if m.sum() > 40:
            asim[m] = tot[m] - np.median(tot[m])
    asim = cv2.GaussianBlur(np.where(disc, asim, 0), (0, 0), SIGMA_SUAU)
    zona = disc & (dl < Rl - 16)
    s = float(np.percentile(np.abs(asim[zona]), 95))
    print(f"escala (p95 |asim| G): {s:.1f} comptes lineals "
          f"(vel mediana {np.median(tot[zona]):.0f})")

    disp = np.clip(PEDESTAL + asim / s * AMPLITUD, 0.0, 1.0).astype(np.float32)
    E16 = np.clip(np.rint(disp * 65535.0), 0, 65535).astype(np.uint16)
    E16 = np.dstack([E16, E16, E16])
    # màscara: el disc amb ploma, fins on la separació és de fiar
    mask = np.clip(((Rl - 10.0) - dl) / 6.0, 0, 1).astype(np.float32)
    mask *= disc.astype(np.float32)
    M16 = np.clip(np.rint(mask * 65535.0), 0, 65535).astype(np.uint16)
    np.save(os.path.join(CAU, "capa_earthshine2_E16.npy"), E16)
    np.save(os.path.join(CAU, "capa_earthshine2_M16.npy"), M16)
    json.dump({"pedestal": PEDESTAL, "amplitud": AMPLITUD,
               "escala_p95_lineal": s, "sigma_suau_px": SIGMA_SUAU,
               "amplitud_lineal_relativa":
                   f"±{s / float(np.median(tot[zona])) * 100:.1f} % del vel"},
              open(os.path.join(CAU, "capa_earthshine2_meta.json"), "w"),
              indent=1)
    print("capa earthshine2 desada (contingut + màscara)")


if __name__ == "__main__":
    main()
