#!/usr/bin/env python3
"""FASE 2 · pas final — treure el CEL per SIMETRIA (quàdrica contra r^-p).

⛔ **El mètode del COLOR de `research/100` §D no serveix en aquestes dades, i
el motiu és físic.** Mesurat el 26-08 al camp llunyà: b_R=1,018, b_G=1,
b_B=0,876 — el cel NO és blau, és càlid. Amb el Sol a 9° i massa d'aire ~6
l'extinció enrogeix el cel **i la corona alhora**, o sigui que les dues
components tenen gairebé el mateix color i la descomposició és degenerada:
aplicada tal qual, deixa el perfil a −11.824 a 2 R☉. És el mateix mur que
`research/107` §2 descriu ("la direcció cromàtica dels arcs és idèntica a la
de la corona E").

El que SÍ que les separa és la **SIMETRIA**, que és la doctrina del projecte:

    I(x,y) = [ a0 + a1 x + a2 y + a3 x² + a4 y² + a5 xy ]  +  A (r/R☉)^-p
             \\_____________ CEL: suau i sense centre ____/     \\_ CORONA _/

Es resol tot alhora, amb retall robust per no deixar que els plomalls manin,
i **només es resta la quàdrica**: la potència radial es queda, que és corona.

⚠️ Límit declarat: a 5 R☉ el cel val 9,2 vegades la corona (`research/99`), o
sigui que qualsevol error de la quàdrica hi pesa. El que s'hi resta és cel amb
una fracció desconeguda però petita de fons coronal llis.
"""

from __future__ import annotations

import json, os, sys
import numpy as np
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

RS = 440.60
R_MIN = 2.6          # R☉: a partir d'aquí el cel ja mana
PS = (2.0, 2.5, 3.0, 3.5)


def main():
    C = {c: fits.getdata(os.path.join(comu.F2, f"LDIC_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    P = fits.getdata(os.path.join(comu.F2, "LDIC_pes_G.fits")).astype(np.float32)
    H, W = C["G"].shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H/2.0, xx - W/2.0)
    bo = (P > 0.02*P.max()) & (rad > R_MIN*RS)
    for c in C: bo &= np.isfinite(C[c])
    print(f"zona d'ajust (> {R_MIN} R☉ amb dada): {int(bo.sum()):,} px")

    sub = np.zeros((H, W), bool); sub[::3, ::3] = True
    m = bo & sub
    X = ((xx[m]-W/2)/RS).astype(np.float64); Y = ((yy[m]-H/2)/RS).astype(np.float64)
    R_ = (rad[m]/RS).astype(np.float64)
    del yy, xx

    res = {}
    millor = None
    for p in PS:
        A = np.c_[np.ones_like(X), X, Y, X*X, Y*Y, X*Y, R_**(-p)]
        cost = 0.0; coef = {}
        for c in ("R", "G", "B"):
            b = C[c][m].astype(np.float64)
            ok = np.ones(len(b), bool)
            for _ in range(5):
                sol, *_ = np.linalg.lstsq(A[ok], b[ok], rcond=None)
                r_ = b - A @ sol
                s = 1.4826*np.median(np.abs(r_ - np.median(r_)))
                ok = (r_ < 2.0*s) & (r_ > -3.0*s)     # retall asimètric: els
                if ok.sum() < 5000: break             # plomalls són positius
            coef[c] = sol; cost += float(np.median(np.abs(r_[ok])))
        res[p] = (cost, coef)
        print(f"  p={p:.1f}  residu robust {cost:9.2f}   A_G={coef['G'][6]:10.1f}")
        if millor is None or cost < res[millor][0]: millor = p
    p = millor; coef = res[p][1]
    print(f"\n⏭️ exponent triat: p = {p}")

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    Xf = ((xx-W/2)/RS); Yf = ((yy-H/2)/RS); del yy, xx
    dades = (P > 0.02*P.max())
    for c in C: dades &= np.isfinite(C[c])
    out = {}
    print(f"\n{'canal':>5} | {'cel al centre':>13} | {'gradient':>26}")
    for c in ("R", "G", "B"):
        k = coef[c]
        cel = (k[0] + k[1]*Xf + k[2]*Yf + k[3]*Xf*Xf + k[4]*Yf*Yf + k[5]*Xf*Yf).astype(np.float32)
        out[c] = np.where(dades, C[c] - cel, np.nan).astype(np.float32)
        print(f"{c:>5} | {k[0]:13.2f} | dx {k[1]:+8.2f}  dy {k[2]:+8.2f} /R☉")
        fits.PrimaryHDU(out[c]).writeto(os.path.join(comu.F2, f"LDIC_cel_restat_{c}.fits"),
                                        overwrite=True)
        fits.PrimaryHDU(np.where(dades, cel, np.nan).astype(np.float32)).writeto(
            os.path.join(comu.F2, f"CEL_{c}.fits"), overwrite=True)

    rad = np.hypot(*np.mgrid[0:H, 0:W].astype(np.float32)) * 0 + \
          np.hypot(np.mgrid[0:H, 0:W][0].astype(np.float32)-H/2,
                   np.mgrid[0:H, 0:W][1].astype(np.float32)-W/2)
    print(f"\n{'r (R☉)':>8} | {'G abans':>10} {'G després':>10} | {'cel/corona':>11}")
    for r0 in (1.1, 1.5, 2.0, 2.6, 3.0, 4.0, 5.0, 7.0, 9.0):
        m2 = dades & (rad > r0*RS) & (rad < (r0+0.06)*RS)
        if m2.sum() < 200: continue
        a_ = float(np.nanmedian(C["G"][m2])); b_ = float(np.nanmedian(out["G"][m2]))
        print(f"{r0:8.1f} | {a_:10.1f} {b_:10.1f} | {(a_-b_)/max(b_,1e-6):11.2f}")

    json.dump({"exponent_p": p, "coef": {c: coef[c].tolist() for c in coef},
               "r_min_ajust_Rsol": R_MIN,
               "metode": "quadrica (cel) + A r^-p (corona), ajust conjunt robust; "
                         "es resta NOMES la quadrica",
               "color_descartat": {"b_R": 1.0182, "b_B": 0.8759,
                                   "motiu": "el camp llunya NO es blau: l extincio a X~6 "
                                            "enrogeix cel i corona igual"}},
              open(os.path.join(comu.REBUTS, "F2_cel.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
