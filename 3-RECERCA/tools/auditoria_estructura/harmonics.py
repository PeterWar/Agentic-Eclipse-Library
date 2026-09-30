"""Quin harmònic és el residu, i cap on apunta.

Si el residu de la corona interior és un DIPOL (m=1) i la seva fase apunta cap
on la Lluna està desplaçada, la causa és la Lluna i no la corona. La fase és la
prova: una coincidència de posició no és una causa, però una fase que segueix
un vector conegut sí que ho és.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import nucli as N
from control2 import perfils
from escales import filtra_harmonics

NTH = 1440
BRNO = "TSE2026_Trigaza_800mm.png"


def cap_a_llenc(dx, dy, pa):
    a = math.radians(-pa); ca, sa = math.cos(a), math.sin(a)
    return ca * dx - sa * dy, sa * dx + ca * dy


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.02), np.log(1.60), 90))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    E = {k: N.estructura_mask(P[k], M[k]) for k in P}

    lum, pes, LL, S = N.carrega_nostre()
    pa = LL["pa_north_deg"]
    fr = [v for v in S["fotogrames"].values() if v.get("coronal")]
    d = np.array([cap_a_llenc(v["lluna_dx"], v["lluna_dy"], pa) for v in fr])
    mitj = d.mean(axis=0)
    rec = d[np.argmax(np.hypot(*(d - mitj).T))] - mitj
    ang_mitj = math.degrees(math.atan2(mitj[1], mitj[0])) % 360
    ang_rec = math.degrees(math.atan2(rec[1], rec[0])) % 360
    print(f"Lluna al llenç: posició mitjana ({mitj[0]:+.2f},{mitj[1]:+.2f}) px"
          f" = {np.hypot(*mitj)/LL['R_sol_px']:.4f} R☉ cap a θ = {ang_mitj:.1f}°")
    print(f"                recorregut cap a θ = {ang_rec:.1f}°"
          f"  (± {np.hypot(*rec)/LL['R_sol_px']:.4f} R☉)\n")

    th = np.linspace(0.0, 2 * np.pi, NTH, endpoint=False)
    mk = M["NOSALTRES"] & M[BRNO]
    a = filtra_harmonics(E["NOSALTRES"], mk, 8)
    b = filtra_harmonics(E[BRNO], mk, 8)

    print(f"{'R☉':>6s} {'|res|':>6s}  " + "  ".join(f"m={m}" for m in range(1, 5))
          + "     fase m=1")
    for i in range(0, len(radis), 3):
        k = mk[i]
        if k.sum() < 200:
            continue
        r = (a[i] - b[i])[k]; t = th[k]
        r = r - r.mean()
        amp, fase = [], None
        for m in range(1, 5):
            c = 2.0 * (r * np.cos(m * t)).sum() / k.sum()
            s = 2.0 * (r * np.sin(m * t)).sum() / k.sum()
            amp.append(math.hypot(c, s))
            if m == 1:
                fase = math.degrees(math.atan2(s, c)) % 360
        print(f"{radis[i]:6.3f} {np.sqrt((r*r).mean()):6.2f}  "
              + "  ".join(f"{v:5.2f}" for v in amp)
              + f"   {fase:7.1f}°  (Lluna a {ang_mitj:.0f}°)")
