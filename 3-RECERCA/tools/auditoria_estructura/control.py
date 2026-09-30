"""EL CONTROL QUE DECIDEIX: Brno contra Brno, al mateix anell.

Si la correlació s'ensorra a 1,08 R☉ també ENTRE ELLS, la zona és poc fiable
als seus productes (vora de la Lluna) i el forat no és nostre. Si entre ells
aguanta i només s'ensorra contra nosaltres, el defecte és NOSTRE.

⛔ Sense aquest control, «la correlació cau» no vol dir res: no hi ha cap
nivell de correlació que sigui bo o dolent per si sol.
"""
from __future__ import annotations

import itertools
import json
import os

import numpy as np

import nucli as N
from registra import a_la_resolucio

NTH = 1440


def perfil_brno(nom, reg, radis, R_ref, nth=NTH):
    br, _, _, _ = N.carrega_brno(nom)
    p = N.mostreja(br, reg["cy"], reg["cx"], reg["R_sol_px"], radis, nth,
                   ang0=np.deg2rad(reg["gir_deg"]))
    return a_la_resolucio(p, radis, R_ref, nth)


if __name__ == "__main__":
    reg = json.load(open(os.path.join(N.AQUI, "registre.json")))
    noms = sorted(reg)
    radis = np.exp(np.linspace(np.log(1.00), np.log(1.60), 121))
    # tots a la resolució del MÉS BAST (200 mm, R☉ 37,7 px) perquè cap parella
    # no tingui avantatge: és l'única manera que els números siguin comparables
    R_ref = min(reg[n]["R_sol_px"] for n in noms)
    print(f"resolució comuna: R☉ = {R_ref:.2f} px (la del més bast)\n")

    P = {n: N.estructura(perfil_brno(n, reg[n], radis, R_ref)) for n in noms}

    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    nos = N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, NTH)
    P["NOSALTRES"] = N.estructura(a_la_resolucio(nos, radis, R_ref, NTH))

    parelles_b = list(itertools.combinations(noms, 2))
    parelles_n = [("NOSALTRES", n) for n in noms]
    C = {p: N.corr_per_anell(P[p[0]], P[p[1]]) for p in parelles_b + parelles_n}

    print(f"{'R☉':>6s} {'BRNO×BRNO (6 parelles)':>24s} {'NOSALTRES×BRNO (4)':>24s}")
    print(f"{'':>6s} {'mediana   pitjor':>24s} {'mediana   pitjor':>24s}")
    for i, r in enumerate(radis):
        if i % 4:
            continue
        b = np.array([C[p][i] for p in parelles_b])
        n = np.array([C[p][i] for p in parelles_n])
        print(f"{r:6.3f} {np.nanmedian(b):11.3f} {np.nanmin(b):8.3f}"
              f" {np.nanmedian(n):15.3f} {np.nanmin(n):8.3f}")

    np.savez(os.path.join(N.AQUI, "control.npz"), radis=radis,
             **{f"{a}|{b}": v for (a, b), v in C.items()})
