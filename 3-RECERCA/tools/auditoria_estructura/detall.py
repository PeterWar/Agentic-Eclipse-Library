"""Poma amb poma: el NOSTRE DETALL FILTRAT contra la imatge filtrada de Brno.

Fins ara comparava el nostre compost cru contra el seu producte amb ACHF, i el
detall fi no hi era comparable per construcció. Aquí es comparen les capes de
detall de la fase 3, que és el que Pere mira.
"""
from __future__ import annotations
import itertools, json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio
from control2 import perfils

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.03), np.log(2.60), 90))
CAPES = ("PASSA_ALT", "RADIAL", "NRGF", "MGN")

if __name__ == "__main__":
    P, M, noms, R_ref, wp, radis = perfils(RADIS)
    B = {n: N.estructura_mask(P[n], M[n]) for n in noms}
    cm = M["NOSALTRES"].copy()
    for n in noms:
        cm &= M[n]
    pb = list(itertools.combinations(noms, 2))

    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    del lum

    E = {"COMPOST": N.estructura_mask(
        a_la_resolucio(N.mostreja(
            N.carrega_nostre()[0], cy, cx, LL["R_sol_px"], RADIS, NTH),
            RADIS, R_ref, NTH), cm)}
    for c in CAPES:
        d = np.load(os.path.join(N.RUN, "3-filtres", f"DETALL_{c}.npy"))
        E[c] = N.estructura_mask(a_la_resolucio(
            N.mostreja(d, cy, cx, LL["R_sol_px"], RADIS, NTH), RADIS, R_ref, NTH), cm)
        del d

    C = {("B", "B"): np.nanmedian(
        [N.corr_per_anell_mask(B[a], B[b], cm)[0] for a, b in pb], axis=0)}
    for k in E:
        C[k] = np.nanmedian([N.corr_per_anell_mask(E[k], B[n], cm)[0]
                             for n in noms], axis=0)

    print(f"{'R☉':>6s} {'B×B':>6s} | " + " ".join(f"{k:>9s}" for k in
                                                   ["COMPOST"] + list(CAPES)))
    for i in range(0, len(RADIS), 4):
        if cm[i].sum() * 360 // NTH < 300:
            continue
        print(f"{RADIS[i]:6.3f} {C[('B','B')][i]:6.3f} | "
              + " ".join(f"{C[k][i]:9.3f}" for k in ["COMPOST"] + list(CAPES)))
    print("\nmitjana 1,2–2,4 R☉:")
    m = (RADIS >= 1.2) & (RADIS <= 2.4)
    print(f"  B×B     {np.nanmean(C[('B','B')][m]):.4f}")
    for k in ["COMPOST"] + list(CAPES):
        print(f"  {k:8s}{np.nanmean(C[k][m]):.4f}")
