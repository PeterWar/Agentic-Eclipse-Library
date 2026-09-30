"""Escales angulars, ara amb MÍNIMS QUADRATS sobre l'arc vàlid.

⛔ Rectifica `escales.py` i `escales2.py`: allà els harmònics es treien amb una
FFT sobre l'anell amb els forats omplerts de zeros, i sobre un arc parcial això
fa fuita de la vora. La fuita és quasi idèntica entre dues imatges de Brno
—tenen el mateix contingut— i diferent entre les seves i la nostra, o sigui que
inflava el control i desinflava el nostre alhora. Aquí cada anell s'ajusta amb
un disseny cos/sin només als azimuts vàlids, que és el que toca.
"""
from __future__ import annotations
import itertools, json, os
import numpy as np
import nucli as N
from control2 import perfils

NTH = 1440


def ajusta(e, m, mmax):
    """Component de |k| ≤ mmax, per mínims quadrats sobre els azimuts vàlids."""
    th = np.linspace(0, 2 * np.pi, e.shape[1], endpoint=False)
    out = np.full_like(e, np.nan)
    cols = [np.ones_like(th)]
    for k in range(1, mmax + 1):
        cols += [np.cos(k * th), np.sin(k * th)]
    A = np.column_stack(cols)
    for i in range(e.shape[0]):
        g = m[i] & np.isfinite(e[i])
        if g.sum() < 4 * A.shape[1]:
            continue
        c, *_ = np.linalg.lstsq(A[g], e[i][g], rcond=None)
        out[i] = A @ c
    return out


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.02), np.log(2.20), 80))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    E = {k: N.estructura_mask(P[k], M[k]) for k in P}
    cm = M["NOSALTRES"].copy()
    for n in noms:
        cm &= M[n]
    graus = cm.sum(axis=1) * 360.0 / NTH
    pb = list(itertools.combinations(noms, 2)); pn = [("NOSALTRES", n) for n in noms]

    taula = {}
    for mmax in (2, 4, 8, 24, None):
        Ef = E if mmax is None else {k: ajusta(E[k], cm, mmax) for k in E}
        C = {p: N.corr_per_anell_mask(Ef[p[0]], Ef[p[1]], cm)[0] for p in pb + pn}
        taula[mmax] = ([np.array([C[p] for p in pb]), np.array([C[p] for p in pn])])

    print(f"{'R☉':>6s} {'arc':>5s} | " + " | ".join(
        f"{('m≤'+str(m)) if m else 'tot':>13s}" for m in (2, 4, 8, 24, None)))
    print(f"{'':>6s} {'':>5s} | " + " | ".join("  B×B    N×B " for _ in range(5)))
    for i in range(0, len(radis), 3):
        if graus[i] < 90:
            continue
        cel = []
        for m in (2, 4, 8, 24, None):
            b, n = taula[m]
            cel.append(f"{np.nanmedian(b[:, i]):6.3f} {np.nanmedian(n[:, i]):6.3f}")
        print(f"{radis[i]:6.3f} {graus[i]:4.0f}° | " + " | ".join(cel))
