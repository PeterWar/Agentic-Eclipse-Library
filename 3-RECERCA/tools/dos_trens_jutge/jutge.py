"""Vixen contra Sony, i tots dos contra Brno. El jutge que faltava.

Tanca dues coses que el `research/114` va deixar obertes:

1. **La corona interior per sota d'1,12 R☉.** Allà la Vixen discrepa de Brno
   més del que s'explica per soroll (la seva dada és 0,99 consistent amb ella
   mateixa). Si la Sony hi coincideix amb la Vixen i totes dues discrepen de
   Brno, el que passa és seu o del lloc; si la Sony coincideix amb Brno i no
   amb la Vixen, el defecte és de la Vixen.
2. **Quant val el sostre de veritat.** «Brno×Brno» és un sostre inflat (mateix
   equip, mateix pipeline). **Vixen×Sony** és el primer control d'aquest
   projecte amb dos instruments de veritat independents: altres òptiques, altre
   sensor, altre muntatge, altre apuntament.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np

import nucli as N

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.02), np.log(3.00), 100))
BANDES = [(1, 4), (5, 12), (13, 30), (31, 80), (81, 200)]


def perfil(tren, radis, nth=NTH):
    lum, pes, LL, S, d = N.carrega(tren)
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    p = N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, nth)
    w = N.mostreja(pes, cy, cx, LL["R_sol_px"], radis, nth)
    ref = np.nanpercentile(w, 90, axis=1, keepdims=True)
    m = np.isfinite(p) & (w > 0.05 * np.maximum(ref, 1e-12))
    return p, m, LL, os.path.basename(d)


if __name__ == "__main__":
    A = sys.argv[1].upper() if len(sys.argv) > 1 else "VIXEN"
    B = sys.argv[2].upper() if len(sys.argv) > 2 else "SONY"
    P, M, info = {}, {}, {}
    for t in (A, B):
        P[t], M[t], LL, nom = perfil(t, RADIS)
        info[t] = nom
        print(f"{t}: {nom}")

    # ⏭️ Igualem la resolució: la Sony mostreja el cel 1,49 vegades més bast.
    # tots dos al pixel del MES BAST
    esc = {k: N.ESC.get(k, N.ESC["SONY"] if k.startswith("SONY") else N.ESC["VIXEN"])
           for k in (A, B)}
    bast = max(esc[A], esc[B])
    for t in (A, B):
        if esc[t] < bast:
            r_ = LL["R_sol_px"] * esc[t] / bast
            P[t] = N.a_la_resolucio(P[t], RADIS, r_, NTH)
            print(f"\n{t} desenfocat al pixel del mes bast (R☉ equiv. {r_:.1f} px)")

    cm = M[A] & M[B]
    graus = cm.sum(axis=1) * 360.0 / NTH
    E = {t: N.estructura(P[t], cm) for t in P}
    c = N.corr(E[A], E[B], cm)

    print(f"\n{'R☉':>6s} {'arc':>5s} {A + ' × ' + B:>18s}")
    for i in range(0, len(RADIS), 3):
        if graus[i] < 60:
            continue
        print(f"{RADIS[i]:6.3f} {graus[i]:4.0f}° {c[i]:13.3f}")

    print("\nper bandes d'escala angular (anells sencers):")
    ple = cm.all(axis=1)
    print(f"  anells sencers: {ple.sum()} ({RADIS[ple].min():.3f}–{RADIS[ple].max():.3f} R☉)")
    ok = np.ones((int(ple.sum()), NTH), bool)
    print(f"  {'banda m':>10s} {'tret de':>8s} {A + ' × ' + B:>18s}")
    for lo, hi in BANDES:
        v = N.corr(N.banda(E[A][ple], lo, hi), N.banda(E[B][ple], lo, hi), ok)
        print(f"  {lo:4d}–{hi:<5d} {360/hi:6.1f}° {np.nanmean(v):13.3f}")
    np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jutge.npz"),
             radis=RADIS, corr=c, graus=graus)
