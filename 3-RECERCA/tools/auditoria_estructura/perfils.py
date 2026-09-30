"""Diagnosi per anell: correlació, gir efectiu i on es trenca l'acord.

El gir efectiu ANELL A ANELL és la peça que un registre global amaga: si el
nostre angle de posició fos bo, el desplaçament azimutal que millor casa amb
Brno ha de ser CONSTANT amb el radi. Si varia, hi ha alguna cosa que gira la
corona amb el radi, i això no ho fa cap corona.
"""
from __future__ import annotations

import json
import os

import numpy as np
from scipy.ndimage import gaussian_filter1d

import nucli as N
from registra import a_la_resolucio, RATIO_LLUNA_SOL

NTH = 1440


def desplacament_azimutal(a, b):
    """Millor desplaçament en θ (graus) per anell, per correlació circular."""
    out = np.full(a.shape[0], np.nan)
    pic = np.full(a.shape[0], np.nan)
    for i in range(a.shape[0]):
        u, v = a[i], b[i]
        if not (np.isfinite(u).all() and np.isfinite(v).all()):
            continue
        u = u - u.mean(); v = v - v.mean()
        F = np.fft.rfft(u) * np.conj(np.fft.rfft(v))
        cc = np.fft.irfft(F, n=u.size)
        cc /= np.sqrt((u * u).sum() * (v * v).sum())
        k = int(np.argmax(cc))
        # parabòlica sobre el pic
        y0, y1, y2 = cc[(k - 1) % cc.size], cc[k], cc[(k + 1) % cc.size]
        d = 0.5 * (y0 - y2) / max(y0 - 2 * y1 + y2, 1e-12)
        kk = (k + d + u.size / 2) % u.size - u.size / 2
        out[i] = kk * 360.0 / u.size
        pic[i] = y1
    return out, pic


def diagnosi(nom, lum_nos, LL, reg, radis, nth=NTH):
    br, bcy, bcx, _ = N.carrega_brno(nom)
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    Rb = reg["R_sol_px"]

    nos = N.mostreja(lum_nos, cy, cx, LL["R_sol_px"], radis, nth)
    nos = a_la_resolucio(nos, radis, Rb, nth)
    bro = N.mostreja(br, reg["cy"], reg["cx"], Rb, radis, nth,
                     ang0=np.deg2rad(reg["gir_deg"]))
    en, eb = N.estructura(nos), N.estructura(bro)
    c = N.corr_per_anell(en, eb)
    dth, pic = desplacament_azimutal(en, eb)
    return dict(radis=radis, corr=c, dth=dth, pic=pic, en=en, eb=eb,
                nos=nos, bro=bro)


if __name__ == "__main__":
    lum, pes, LL, S = N.carrega_nostre()
    reg = json.load(open(os.path.join(N.AQUI, "registre.json")))
    radis = np.exp(np.linspace(np.log(1.02), np.log(3.30), 160))

    print(f"{'radi R☉':>8s} " + " ".join(f"{k.split('_')[-1][:6]:>14s}"
                                         for k in sorted(reg)))
    D = {k: diagnosi(k, lum, LL, reg[k], radis) for k in sorted(reg)}
    for i, r in enumerate(radis):
        if i % 8:
            continue
        fila = " ".join(f"{D[k]['corr'][i]:7.3f}{D[k]['dth'][i]:+7.2f}"
                        for k in sorted(reg))
        print(f"{r:8.3f} {fila}")

    print("\ngir efectiu per trams (graus, mediana):")
    for k in sorted(reg):
        d = D[k]["dth"]
        trams = [(1.05, 1.15), (1.15, 1.35), (1.35, 1.8), (1.8, 2.5), (2.5, 3.3)]
        s = "  ".join(f"{a:.2f}-{b:.2f}:{np.nanmedian(d[(radis>=a)&(radis<b)]):+6.2f}"
                      for a, b in trams)
        print(f"  {k:32s} {s}")

    np.savez(os.path.join(N.AQUI, "diagnosi.npz"),
             radis=radis, **{f"corr_{k[:20]}": D[k]["corr"] for k in D},
             **{f"dth_{k[:20]}": D[k]["dth"] for k in D})
