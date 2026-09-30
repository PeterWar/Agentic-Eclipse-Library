"""A quina ESCALA ANGULAR falla l'acord? És el que separa soroll de defecte.

Si el desacord és només a harmònics alts, és soroll i resolució i no hi ha res
a arreglar. Si també hi és als harmònics baixos —m ≤ 8, o sigui trets de 45° o
més— la corona interior té una forma que no és la de la corona, i això sí que
és un defecte.

El control continua sent Brno×Brno a la MATEIXA escala: sense ell, un número
baix no vol dir res.
"""
from __future__ import annotations

import itertools
import json
import os

import numpy as np

import nucli as N
from control2 import perfils

NTH = 1440


def filtra_harmonics(e, m, mmax):
    """Reconstrueix cada anell amb només els harmònics |k| ≤ mmax.

    Els forats (Lluna) s'omplen amb 0 sobre la mitjana de la part vàlida: així
    l'FFT no inventa una vora, i el resultat només es llegeix on m és cert.
    """
    x = np.where(m, e, np.nan)
    mu = np.nanmean(x, axis=1, keepdims=True)
    x = np.where(m, x - mu, 0.0)
    F = np.fft.rfft(x, axis=1)
    F[:, mmax + 1:] = 0.0
    return np.fft.irfft(F, n=e.shape[1], axis=1)


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.02), np.log(2.20), 100))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    E = {k: N.estructura_mask(P[k], M[k]) for k in P}
    pb = list(itertools.combinations(noms, 2))
    pn = [("NOSALTRES", n) for n in noms]

    for mmax in (4, 8, 16, 40, 120):
        Ef = {k: filtra_harmonics(E[k], M[k], mmax) for k in E}
        C = {p: N.corr_per_anell_mask(Ef[p[0]], Ef[p[1]], M[p[0]] & M[p[1]])[0]
             for p in pb + pn}
        print(f"\n--- només harmònics m ≤ {mmax}  (trets de ≥ {360/max(mmax,1):.0f}°) ---")
        print(f"{'R☉':>6s} {'B×B':>7s} {'N×B':>7s} {'dèficit':>8s}")
        for i in range(0, len(radis), 6):
            b = np.nanmedian([C[p][i] for p in pb])
            n = np.nanmedian([C[p][i] for p in pn])
            if not np.isfinite(b) or not np.isfinite(n):
                continue
            print(f"{radis[i]:6.3f} {b:7.3f} {n:7.3f} {b-n:8.3f}")
