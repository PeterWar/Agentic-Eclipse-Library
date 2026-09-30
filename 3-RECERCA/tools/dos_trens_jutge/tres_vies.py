"""Vixen, Sony i Brno, tots tres al mateix anell.

Tanca el que el `research/114` §3 va deixar obert. Per sota d'1,12 R☉ la Vixen
discrepa de Brno mes del que s'explica per soroll. Amb un tercer testimoni la
taula de veritat es completa:

  Vixen ~ Sony  i  tots dos != Brno   ->  es del LLOC o del METODE nostre
  Sony ~ Brno   i  cap dels dos ~ Vixen -> el defecte es de la VIXEN
  els tres es-tan diferents            ->  la zona es poc fiable per a tothom

⛔ Brno×Brno era un sostre inflat (mateix equip, mateix pipeline). Vixen×Sony es
el primer control d'aquest projecte amb DOS INSTRUMENTS de veritat
independents.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np

import nucli as N

AUD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "auditoria_estructura")
NTH = 1440
RADIS = np.exp(np.linspace(np.log(1.02), np.log(2.60), 90))


def carrega_brno():
    """Els perfils de Brno, amb el registre bo i el seu disc lunar fora."""
    import importlib.util
    def mod(nom):
        sp = importlib.util.spec_from_file_location(
            "aud_" + nom, os.path.join(AUD, nom + ".py"))
        m = importlib.util.module_from_spec(sp); sys.modules["aud_" + nom] = m
        sp.loader.exec_module(m); return m
    an = mod("nucli")
    reg = json.load(open(os.path.join(AUD, an.REGISTRE)))
    P, M = {}, {}
    for n in sorted(reg):
        br, _, _, _ = an.carrega_brno(n)
        p = an.mostreja(br, reg[n]["cy"], reg[n]["cx"], reg[n]["R_sol_px"],
                        RADIS, NTH, ang0=np.deg2rad(reg[n]["gir_deg"]))
        M[n] = an.mascara_brno(n, reg[n], RADIS, NTH, 0.030)
        # sense desenfocar aqui: mes avall tot passa per la resolucio comuna
        P[n] = p
    return P, M, sorted(reg), reg


def perfil_tren(t):
    lum, pes, LL, S, d = N.carrega(t)
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    p = N.mostreja(lum, cy, cx, LL["R_sol_px"], RADIS, NTH)
    w = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)
    ref = np.nanpercentile(w, 90, axis=1, keepdims=True)
    m = np.isfinite(p) & (w > 0.05 * np.maximum(ref, 1e-12))
    return p, m, LL, os.path.basename(d)


if __name__ == "__main__":
    PB, MB, noms, reg = carrega_brno()
    P, M = {}, {}
    for t in ("VIXEN", "SONY"):
        P[t], M[t], LL, nom = perfil_tren(t)
        print(f"{t}: {nom}")
    # tot a la resolucio del MES BAST perque cap parella no tingui avantatge
    cm = M["VIXEN"] & M["SONY"]
    for n in noms:
        cm &= MB[n]
    graus = cm.sum(axis=1) * 360.0 / NTH

    # RESOLUCIO PER PARELLA. Igualar-ho tot al mes bast (el 200 mm, R☉ 38 px)
    # llencaria la resolucio dels altres tres i faria la corona interior
    # il.legible. Cada parella es compara al limit de la MES BASTA de les dues.
    RES = {"VIXEN": LL["R_sol_px"],                     # 440,6 px al llenc
           "SONY": LL["R_sol_px"] * N.ESC["VIXEN"] / N.ESC["SONY"]}   # 295,8
    for n in noms:
        RES[n] = reg[n]["R_sol_px"]
    CRU = dict(P); CRU.update(PB)
    print("resolucio (R☉ en px equivalents): "
          + " · ".join(f"{k.split('_')[-1][:8]} {v:.0f}" for k, v in RES.items()))

    def corr_parella(a, b):
        r = min(RES[a], RES[b])
        ea = N.estructura(N.a_la_resolucio(CRU[a], RADIS, r, NTH), cm)
        eb = N.estructura(N.a_la_resolucio(CRU[b], RADIS, r, NTH), cm)
        return N.corr(ea, eb, cm)

    vs = corr_parella("VIXEN", "SONY")
    vb = np.nanmedian([corr_parella("VIXEN", n) for n in noms], axis=0)
    sb = np.nanmedian([corr_parella("SONY", n) for n in noms], axis=0)
    bb = np.nanmedian([corr_parella(a, b) for a, b in itertools.combinations(noms, 2)],
                      axis=0)

    print(f"\n{'R☉':>6s} {'arc':>5s} | {'Vixen×Sony':>11s} {'Vixen×Brno':>11s} "
          f"{'Sony×Brno':>10s} | {'Brno×Brno':>10s}")
    for i in range(0, len(RADIS), 3):
        if graus[i] < 60 or not np.isfinite(vs[i]):
            continue
        print(f"{RADIS[i]:6.3f} {graus[i]:4.0f}° | {vs[i]:11.3f} {vb[i]:11.3f} "
              f"{sb[i]:10.3f} | {bb[i]:10.3f}")
    for a, b in ((1.03, 1.12), (1.12, 1.30), (1.30, 1.80), (1.80, 2.60)):
        k = (RADIS >= a) & (RADIS < b) & np.isfinite(vs)
        if k.sum():
            print(f"  mitjana {a:.2f}-{b:.2f} R☉ | {np.nanmean(vs[k]):11.3f} "
                  f"{np.nanmean(vb[k]):11.3f} {np.nanmean(sb[k]):10.3f} | "
                  f"{np.nanmean(bb[k]):10.3f}")
    np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tres_vies.npz"),
             radis=RADIS, vs=vs, vb=vb, sb=sb, bb=bb, graus=graus)
