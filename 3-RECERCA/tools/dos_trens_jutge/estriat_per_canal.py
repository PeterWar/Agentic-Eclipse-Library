"""Tasca 4: d'on surt la familia fina (lambda 4-12 px) que nomes te la Vixen.

`estriat_dos_trens.py` va deixar-ho aixi: la familia llarga (lambda 50-160 px a
10°/80°) es CEL —corona de veritat— i la fina (lambda 4-12 px) es **nomes de la
Vixen** i cau a 44,7° al seu marc de sensor. La Sony hi ensenya x0,78-1,07, o
sigui res. El mecanisme quedava sense confirmar.

La hipotesi que toca provar primer es la **quincunx del verd**: al mosaic
Bayer el pla G es una xarxa girada 45° i, amb el drizzle sobre fotogrames
ditherats, qualsevol residu de fase d'aquella xarxa surt en diagonal. Si es
aixo, la familia ha de viure **al canal G i no a R ni a B**.

⛔ La prova NO es mirar quina imatge te mes potencia: R, G i B tenen relacions
senyal/soroll molt diferents. Es mira l'**exces sobre la mediana de la seva
mateixa longitud d'ona**, que es adimensional i ja descompta el fons.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from astropy.io import fits

import nucli as N
from estriat import normalitza_radi, espectre, pics

R0, R1 = 1.40, 2.60
LAM_FI = (3.0, 15.0)
LAM_LLARG = (35.0, 200.0)


def carrega_canal(tren, canal):
    d = N.darrer_run(tren)
    a = fits.getdata(os.path.join(d, "2-ldic", f"CORONA_{canal}.fits")).astype(np.float32)
    w = fits.getdata(os.path.join(d, "2-ldic", f"PES_{canal}.fits")).astype(np.float32)
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    return a, w, S["llenc"], os.path.basename(d)


def analitza(tren, canal):
    a, w, LL, run = carrega_canal(tren, canal)
    H, W = a.shape
    RS = LL["R_sol_px"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
    k = (w > 0.05 * np.nanpercentile(w[w > 0], 90)) & (rad >= R0 * RS) & (rad <= R1 * RS) \
        & np.isfinite(a)
    z = normalitza_radi(a.astype(np.float64), k, rad)
    P = espectre(z, k)
    M, lams, angs = pics(P, LL["escala_arcsec_px"])
    Mn = M / np.nanmedian(M, axis=1, keepdims=True)
    return Mn, lams, angs, int(k.sum()), run


def millor(Mn, lams, angs, banda):
    b = (lams >= banda[0]) & (lams <= banda[1])
    sub = np.nan_to_num(Mn[b])
    i, j = np.unravel_index(int(np.argmax(sub)), sub.shape)
    return float(lams[b][i]), float(angs[j]), float(sub[i, j])


def a_marc_sensor(ang_llenc, tren):
    """L'angle del llenc (nord amunt) expressat al marc del SENSOR."""
    return (ang_llenc - (N.PA[tren] - 90.0)) % 180.0


if __name__ == "__main__":
    TRENS = sys.argv[1:] or ["VIXEN", "SONYTOT"]
    RES = {}
    for tren in TRENS:
        print(f"\n{tren}")
        for canal in ("R", "G", "B"):
            Mn, lams, angs, n, run = analitza(tren, canal)
            RES[(tren, canal)] = (Mn, lams, angs)
            lf, af, xf = millor(Mn, lams, angs, LAM_FI)
            ll, al, xl = millor(Mn, lams, angs, LAM_LLARG)
            print(f"  {canal}  ({run}, {n:,} px)")
            print(f"      FINA   λ {lf:6.2f} px  {af:5.1f}° llenç  "
                  f"({a_marc_sensor(af, tren):5.1f}° sensor)   ×{xf:5.2f}")
            print(f"      LLARGA λ {ll:6.1f} px  {al:5.1f}° llenç  "
                  f"({a_marc_sensor(al, tren):5.1f}° sensor)   ×{xl:5.2f}")

    # ---------------------------------------------- el verd contra R i B
    print("\n" + "=" * 74)
    print("LA PROVA: exces de la familia FINA (λ 3-15 px) canal a canal")
    print("=" * 74)
    print(f"{'tren':>10s} {'λ (px)':>8s} {'° sensor':>9s} {'R':>7s} {'G':>7s} "
          f"{'B':>7s}   {'G / mitjana(R,B)':>18s}")
    for tren in TRENS:
        Mn, lams, angs = RES[(tren, "G")]
        lf, af, xf = millor(Mn, lams, angs, LAM_FI)
        i = int(np.argmin(np.abs(np.log(lams / lf))))
        j = int(np.argmin(np.abs(((angs - af + 90) % 180) - 90)))
        v = {}
        for canal in ("R", "G", "B"):
            Mc = RES[(tren, canal)][0]
            v[canal] = float(np.nanmax(Mc[max(i - 1, 0):i + 2, max(j - 2, 0):j + 3]))
        rao = v["G"] / max(0.5 * (v["R"] + v["B"]), 1e-9)
        print(f"{tren:>10s} {lf:8.2f} {a_marc_sensor(af, tren):9.1f} {v['R']:7.2f} "
              f"{v['G']:7.2f} {v['B']:7.2f} {rao:18.2f}")
    print("\nSi la rao G/(R,B) es clarament > 1 a la Vixen i ~1 a la Sony,\n"
          "la familia fina viu al PLA VERD: es la quincunx del mosaic Bayer.")
