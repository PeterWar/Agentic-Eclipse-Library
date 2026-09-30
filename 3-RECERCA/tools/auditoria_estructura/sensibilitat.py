"""Sensibilitat del dèficit interior a les DUES guardes.

Dues coses el poden fabricar i cap és la nostra corona: la vora tractada del
disc lunar de Brno (la seva) i la vora de la nostra màscara per fotograma (la
nostra). Si el dèficit desapareix en allunyar-se'n, no era un defecte; si
aguanta, sí que ho és.
"""
from __future__ import annotations
import itertools, json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio
from escales import filtra_harmonics
from mapes import fraccio_tapada

NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.02), np.log(1.60), 60))


def prepara():
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    noms = sorted(reg)
    R_ref = min(reg[n]["R_sol_px"] for n in noms)
    P, Mb = {}, {}
    for n in noms:
        br, _, _, _ = N.carrega_brno(n)
        P[n] = a_la_resolucio(
            N.mostreja(br, reg[n]["cy"], reg[n]["cx"], reg[n]["R_sol_px"],
                       RADIS, NTH, ang0=np.deg2rad(reg[n]["gir_deg"])),
            RADIS, R_ref, NTH)
        Mb[n] = lambda g, n=n: N.mascara_brno(n, reg[n], RADIS, NTH, g)
    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    P["NOSALTRES"] = a_la_resolucio(
        N.mostreja(lum, cy, cx, LL["R_sol_px"], RADIS, NTH), RADIS, R_ref, NTH)
    wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)
    tap, _ = fraccio_tapada(S, LL, RADIS, NTH)
    return P, Mb, noms, wp, tap


if __name__ == "__main__":
    P, Mb, noms, wp, tap = prepara()
    ref = np.nanpercentile(wp, 90, axis=1, keepdims=True)
    pb = list(itertools.combinations(noms, 2))
    pn = [("NOSALTRES", n) for n in noms]

    for gb, tp in ((0.012, 0.02), (0.030, 0.02), (0.060, 0.02), (0.030, 0.0001)):
        M = {n: Mb[n](gb) for n in noms}
        M["NOSALTRES"] = (np.isfinite(P["NOSALTRES"])
                          & (wp > 0.05 * np.maximum(ref, 1e-12)) & (tap <= tp))
        cm = M["NOSALTRES"].copy()
        for n in noms:
            cm &= M[n]
        # ⛔ SENSE FFT: sobre un arc parcial, omplir el forat de zeros i filtrar
        #    fa fuita de la vora, i la fuita és IDÈNTICA entre dues imatges de
        #    Brno (contingut gairebé igual) però no entre les seves i la nostra:
        #    inflava el control i desinflava el nostre. Aquí es correlaciona la
        #    dada tal com és, només als azimuts vàlids.
        E = {k: N.estructura_mask(P[k], cm) for k in P}
        C = {p: N.corr_per_anell_mask(E[p[0]], E[p[1]], cm)[0] for p in pb + pn}
        gr = cm.sum(axis=1) * 360.0 / NTH
        print(f"\n--- SENSE FFT · guarda Brno {gb:.3f} R☉ · «tapat» nostre ≤ {tp*100:g} % ---")
        print(f"{'R☉':>6s} {'arc':>5s} {'B×B':>7s} {'N×B':>7s} {'dèficit':>8s}")
        for i in range(0, len(RADIS), 3):
            b = np.nanmedian([C[p][i] for p in pb])
            n = np.nanmedian([C[p][i] for p in pn])
            if not np.isfinite(b) or not np.isfinite(n) or gr[i] < 60:
                continue
            print(f"{RADIS[i]:6.3f} {gr[i]:4.0f}° {b:7.3f} {n:7.3f} {b-n:8.3f}")
