"""Com `escales.py`, però amb MÀSCARA COMUNA a totes les parelles.

⛔ El control anterior no era just: Brno×Brno es mesurava sobre un anell molt
més sencer que Nosaltres×Brno, perquè les dues Llunes de Brno són gairebé al
mateix lloc i la nostra zona sense dada no hi entrava. Sobre un arc parcial els
harmònics deixen de ser ortogonals i el número s'infla. Aquí totes les parelles
es mesuren exactament als mateixos azimuts.
"""
from __future__ import annotations

import itertools
import os

import numpy as np

import nucli as N
from control2 import perfils
from escales import filtra_harmonics


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.02), np.log(2.20), 100))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    E = {k: N.estructura_mask(P[k], M[k]) for k in P}

    comu_m = M["NOSALTRES"].copy()
    for n in noms:
        comu_m &= M[n]
    graus = comu_m.sum(axis=1) * 360.0 / comu_m.shape[1]

    pb = list(itertools.combinations(noms, 2))
    pn = [("NOSALTRES", n) for n in noms]

    for mmax in (4, 8, 40):
        Ef = {k: filtra_harmonics(E[k], comu_m, mmax) for k in E}
        C = {p: N.corr_per_anell_mask(Ef[p[0]], Ef[p[1]], comu_m)[0]
             for p in pb + pn}
        print(f"\n--- m ≤ {mmax}, MÀSCARA COMUNA ---")
        print(f"{'R☉':>6s} {'arc':>5s} {'B×B':>7s} {'N×B':>7s} {'dèficit':>8s}")
        for i in range(0, len(radis), 4):
            b = np.nanmedian([C[p][i] for p in pb])
            n = np.nanmedian([C[p][i] for p in pn])
            if not np.isfinite(b) or not np.isfinite(n):
                continue
            print(f"{radis[i]:6.3f} {graus[i]:4.0f}° {b:7.3f} {n:7.3f} {b-n:8.3f}")
