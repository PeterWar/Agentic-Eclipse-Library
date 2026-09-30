"""Contrast azimutal contra radi. Al nostre compost és FÍSIC (és lineal).

Si el contrast fraccionari s'ensorra cap endins mentre el de Brno no, la
corona interior està VELADA: llum difosa que hi suma un pedestal que no és
corona. El número és directe i no depèn de cap corba de to al nostre costat.
"""
from __future__ import annotations
import json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio
from control2 import perfils

NTH = 1440


def contrast(pol, m, mmax=8):
    """rms azimutal de la part de gran escala, relatiu a la mediana de l'anell."""
    out = np.full(pol.shape[0], np.nan)
    for i in range(pol.shape[0]):
        k = m[i] & np.isfinite(pol[i])
        if k.sum() < 300:
            continue
        x = pol[i].copy(); mu = np.median(x[k])
        if not np.isfinite(mu) or mu <= 0:
            continue
        y = np.where(k, x - mu, 0.0)
        F = np.fft.rfft(y); F[mmax + 1:] = 0.0
        y = np.fft.irfft(F, n=x.size)
        out[i] = float(np.sqrt((y[k] ** 2).mean()) / mu)
    return out


if __name__ == "__main__":
    radis = np.exp(np.linspace(np.log(1.02), np.log(2.60), 120))
    P, M, noms, R_ref, wp, radis = perfils(radis)
    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0

    # el NOSTRE, sense passar per l'estructura normalitzada: valors lineals
    nos = N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, NTH)
    cn = contrast(nos, M["NOSALTRES"])
    cb = {n: contrast(P[n], M[n]) for n in noms}

    print(f"{'R☉':>6s} {'NOSALTRES':>10s}   " +
          "  ".join(f"{n.split('_')[-1][:6]:>7s}" for n in noms))
    print("        (lineal)     (tonificats: la forma val, el nivell no)")
    for i in range(0, len(radis), 3):
        v = [cb[n][i] for n in noms]
        if not np.isfinite(cn[i]) and not np.isfinite(np.nanmean(v)):
            continue
        print(f"{radis[i]:6.3f} {cn[i]*100:9.2f}%   " +
              "  ".join(f"{x*100:6.2f}%" for x in v))

    # el número que decideix: contrast a 1,07 relatiu al de 1,30
    def rel(c):
        a = np.interp(1.07, radis, c); b = np.interp(1.30, radis, c)
        return a / b
    print(f"\ncontrast(1,07 R☉) / contrast(1,30 R☉):")
    print(f"  NOSALTRES {rel(cn):.3f}")
    for n in noms:
        print(f"  {n:32s} {rel(cb[n]):.3f}")
