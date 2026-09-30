"""El control, ara HONEST: fora el disc lunar pintat de Brno.

Amb el disc dins, la comparació correlacionava la nostra corona contra una
taca negra constant i sortia una anticorrelació que no era cap mesura. Aquí
cada anell es compara NOMÉS als azimuts on tots dos tenen corona de veritat, i
es diu quants graus d'anell queden.
"""
from __future__ import annotations

import itertools
import json
import os

import numpy as np

import nucli as N
from registra import a_la_resolucio

NTH = 1440


def perfils(radis, nth=NTH):
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    noms = sorted(reg)
    R_ref = min(reg[n]["R_sol_px"] for n in noms)
    P, M = {}, {}
    for n in noms:
        br, _, _, _ = N.carrega_brno(n)
        p = N.mostreja(br, reg[n]["cy"], reg[n]["cx"], reg[n]["R_sol_px"],
                       radis, nth, ang0=np.deg2rad(reg[n]["gir_deg"]))
        M[n] = N.mascara_brno(n, reg[n], radis, nth)
        P[n] = a_la_resolucio(p, radis, R_ref, nth)

    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    nos = N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, nth)
    wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], radis, nth)
    P["NOSALTRES"] = a_la_resolucio(nos, radis, R_ref, nth)
    # la nostra validesa: hi ha d'haver pes de veritat
    ref = np.nanpercentile(wp, 90, axis=1, keepdims=True)
    M["NOSALTRES"] = np.isfinite(nos) & (wp > 0.05 * np.maximum(ref, 1e-12))
    return P, M, noms, R_ref, wp, radis


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.00), np.log(2.00), 161))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    E = {k: N.estructura_mask(P[k], M[k]) for k in P}

    pb = list(itertools.combinations(noms, 2))
    pn = [("NOSALTRES", n) for n in noms]
    C, NN = {}, {}
    for a, b in pb + pn:
        C[(a, b)], NN[(a, b)] = N.corr_per_anell_mask(E[a], E[b], M[a] & M[b])

    print(f"resolució comuna R☉ = {R_ref:.1f} px      "
          f"(graus d'anell útils entre parèntesis)\n")
    print(f"{'R☉':>6s} {'BRNO×BRNO':>20s} {'NOSALTRES×BRNO':>22s} {'pes':>7s}")
    print(f"{'':>6s} {'mediana pitjor':>20s} {'mediana pitjor  (°)':>22s}")
    for i in range(0, len(radis), 3):
        b = np.array([C[p][i] for p in pb])
        n = np.array([C[p][i] for p in pn])
        gr = np.median([NN[p][i] for p in pn]) * 360.0 / NTH
        if np.all(np.isnan(b)) and np.all(np.isnan(n)):
            continue
        f = lambda v, g: (f"{np.nanmedian(v):7.3f} {np.nanmin(v):7.3f}"
                          if np.isfinite(v).any() else "      —       —")
        print(f"{radis[i]:6.3f} {f(b,0):>20s} {f(n,0):>15s} {gr:6.0f}°"
              f" {np.nanmedian(wp[i]):7.3g}")
    np.savez(os.path.join(N.AQUI, "control2.npz"), radis=radis,
             **{f"{a}|{b}": v for (a, b), v in C.items()})
