"""Mesura la CUA DE LA PSF del limbe lunar en fotogrames crus.

La pregunta és concreta: a quina distància del limbe lunar deixa de veure's la
llum que la Lluna hauria de tapar? Aquest número és la guarda que la màscara
per fotograma necessita, i ara mateix val 2 px, que és el que la va posar
«PSF del limbe + error d'ajust» sense mesurar-la mai.

⛔ No es mesura amb el compost: dins de la intersecció dels discos el pes és 0
i no hi ha dada. Es mesura fotograma a fotograma, al seu propi marc de sensor.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import rawpy

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402

import nucli as N  # noqa: E402

RUN = N.RUN


def perfil_radial_lunar(ruta, v, RL, ped, sat, nb=260, r0=0.80, r1=1.35):
    """Perfil de brillantor centrat a la LLUNA d'aquest fotograma, en R_lluna."""
    with rawpy.imread(ruta) as r:
        raw = r.raw_image.astype(np.float32)
        g = comu.geometria(r)
        mc = comu.mapa_colors(r)
    verd = (mc == 1) | (mc == 3)
    y, x = np.nonzero(verd)
    val = raw[y, x] - ped
    bo = (raw[y, x] < sat * 0.98)
    mlx = v["sol_x"] + v["lluna_dx"]; mly = v["sol_y"] + v["lluna_dy"]
    rr = np.hypot(x - mlx, y - mly) / RL
    m = bo & (rr >= r0) & (rr < r1)
    idx = ((rr[m] - r0) / (r1 - r0) * nb).astype(np.int32)
    c = np.bincount(idx, None, nb)
    s = np.bincount(idx, val[m].astype(np.float64), nb)
    prof = np.where(c > 50, s / np.maximum(c, 1), np.nan)
    rad = r0 + (np.arange(nb) + 0.5) / nb * (r1 - r0)
    return rad, prof, c


if __name__ == "__main__":
    S = json.load(open(os.path.join(RUN, "4-rebuts", "F1.2_sol_llenc.json")))
    RL = S["contactes"]["R_lluna_px"]
    cfg = comu.TRENS["VIXEN"]
    ped, sat = cfg["pedestal_dn"], cfg["saturacio_dn"]
    fr = {k: v for k, v in S["fotogrames"].items() if v.get("coronal")}

    # el vector Lluna−Sol: quant llisca, i cap on
    d = np.array([[v["lluna_dx"], v["lluna_dy"]] for v in fr.values()])
    print(f"{len(fr)} fotogrames coronals")
    print(f"  Lluna−Sol: x {d[:,0].min():+.2f}…{d[:,0].max():+.2f} px, "
          f"y {d[:,1].min():+.2f}…{d[:,1].max():+.2f} px")
    rec = np.hypot(*(d.max(axis=0) - d.min(axis=0)))
    print(f"  recorregut {rec:.2f} px = {rec/440.603:.4f} R☉"
          f"   direcció {np.degrees(np.arctan2(*(d.max(axis=0)-d.min(axis=0))[::-1])):+.1f}° (sensor)")

    # tria: exposicions llargues (on la corona interior ja és brillant) i curtes
    tri = sorted(fr.items(), key=lambda kv: kv[1]["exp"])
    for nom, v in [tri[0], tri[len(tri)//2], tri[-1]]:
        ruta = os.path.join(cfg["dir"], "totalitat", nom)
        if not os.path.exists(ruta):
            print(f"  (no hi és {nom})"); continue
        rad, prof, c = perfil_radial_lunar(ruta, v, RL, ped, sat)
        fora = np.nanmedian(prof[(rad > 1.15) & (rad < 1.30)])
        dins = np.nanmedian(prof[(rad > 0.80) & (rad < 0.88)])
        print(f"\n{nom}  exp {v['exp']:.4g} s   fora(1,15-1,30 R_ll) {fora:8.1f} DN"
              f"   dins(0,80-0,88) {dins:8.1f} DN")
        print("   r/R_ll   DN      (DN−terra)/fora")
        for rr in (0.90, 0.94, 0.97, 0.99, 1.00, 1.01, 1.02, 1.03, 1.05,
                   1.08, 1.12, 1.20):
            k = int(np.argmin(np.abs(rad - rr)))
            ex = (prof[k] - dins) / max(fora - dins, 1e-9)
            print(f"   {rad[k]:6.3f} {prof[k]:9.1f}   {ex:+8.4f}"
                  f"   ({(rad[k]-1.0)*RL:+6.1f} px del limbe)")
