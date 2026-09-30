"""Les capes de detall contra Brno, BANDA A BANDA d'escala angular.

Un passa-alt treu l'escala gran per definició, o sigui que correlacionar-lo
sencer contra una imatge que la conserva no vol dir res. Aquí es passa la
MATEIXA banda d'harmònics als dos costats i es pregunta, per a cada escala:
el que la nostra capa hi posa, hi és de veritat?

⛔ El control B×B es mesura a la mateixa banda: sense ell no hi ha manera de
saber si un 0,5 a escala fina és dolent o és el sostre.
"""
from __future__ import annotations
import itertools, os
import numpy as np
import nucli as N
from registra import a_la_resolucio
from control2 import perfils

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.15), np.log(2.40), 60))
CAPES = ("PASSA_ALT", "RADIAL", "NRGF", "MGN")
BANDES = [(1, 4), (5, 12), (13, 30), (31, 80), (81, 200)]


def banda(e, lo, hi):
    F = np.fft.rfft(np.nan_to_num(e), axis=1)
    G = np.zeros_like(F); G[:, lo:hi + 1] = F[:, lo:hi + 1]
    return np.fft.irfft(G, n=e.shape[1], axis=1)


if __name__ == "__main__":
    P, M, noms, R_ref, wp, radis = perfils(RADIS)
    cm = M["NOSALTRES"].copy()
    for n in noms:
        cm &= M[n]
    ple = cm.all(axis=1)          # només anells SENCERS: l'FFT hi és legítima
    print(f"anells sencers: {ple.sum()} de {len(RADIS)}"
          f"  ({RADIS[ple].min():.3f}–{RADIS[ple].max():.3f} R☉)\n")
    B = {n: N.estructura_mask(P[n], M[n])[ple] for n in noms}
    pb = list(itertools.combinations(noms, 2))

    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    E = {"COMPOST": N.estructura_mask(a_la_resolucio(
        N.mostreja(lum, cy, cx, LL["R_sol_px"], RADIS, NTH),
        RADIS, R_ref, NTH), cm)[ple]}
    del lum
    for c in CAPES:
        d = np.load(os.path.join(N.RUN, "3-filtres", f"DETALL_{c}.npy"))
        E[c] = N.estructura_mask(a_la_resolucio(
            N.mostreja(d, cy, cx, LL["R_sol_px"], RADIS, NTH),
            RADIS, R_ref, NTH), cm)[ple]
        del d

    ok = np.ones((ple.sum(), NTH), bool)
    print(f"{'banda m':>10s} {'tret de':>9s} | {'B×B':>6s} | "
          + " ".join(f"{k:>9s}" for k in ["COMPOST"] + list(CAPES)))
    for lo, hi in BANDES:
        Bb = {n: banda(B[n], lo, hi) for n in noms}
        bb = np.nanmean(np.nanmedian(
            [N.corr_per_anell_mask(Bb[a], Bb[b], ok)[0] for a, b in pb], axis=0))
        fila = []
        for k in ["COMPOST"] + list(CAPES):
            eb = banda(E[k], lo, hi)
            fila.append(np.nanmean(np.nanmedian(
                [N.corr_per_anell_mask(eb, Bb[n], ok)[0] for n in noms], axis=0)))
        print(f"{lo:4d}–{hi:<5d} {360/hi:7.1f}° | {bb:6.3f} | "
              + " ".join(f"{v:9.3f}" for v in fila))
