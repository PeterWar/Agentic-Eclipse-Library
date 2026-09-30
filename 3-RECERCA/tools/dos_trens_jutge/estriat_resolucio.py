"""Tasca 4, segona peca: la familia fina «nomes de la Vixen» era RESOLUCIO?

`estriat_dos_trens.py` va concloure que la familia de lambda 6-9 px viu nomes a
la Vixen perque la Sony hi ensenya x2,2-2,6 contra x5,5-6,0. Pero la Sony entra
al llenc comu **remostrejada x1,49** (3,2020 -> 2,1495 ''/px): un senyal de
lambda 6,5 px de llenc son **4,4 px del seu sensor**, prop del seu Nyquist, i la
interpolacio bilineal l'atenua molt. ⛔ La comparacio no estava igualada en
resolucio, i `jutge.py` si que ho fa (desenfoca el mes fi al pixel del mes bast).

L'experiment: passar la Vixen pel MATEIX cami de remostreig que la Sony
—reduir x1,49 i tornar a pujar amb la mateixa interpolacio— i tornar a mesurar.
Si l'exces cau al nivell de la Sony, la familia **no es «de la Vixen»**: es
simplement mes fina que el pixel de la Sony i alla no es pot veure.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import cv2
from astropy.io import fits

import nucli as N
from estriat import normalitza_radi, espectre, pics

R0, R1 = 1.40, 2.60
# finestra PRE-REGISTRADA: on `estriat.npz` te el pic de la Vixen
LAM = (6.0, 10.0)
ANG = (163.0, 175.0)


def excess(a, w, LL, desenfoca=1.0):
    H, W = a.shape
    RS = LL["R_sol_px"]
    if desenfoca > 1.0:
        h2, w2 = int(round(H / desenfoca)), int(round(W / desenfoca))
        a = cv2.resize(cv2.resize(a, (w2, h2), interpolation=cv2.INTER_LINEAR),
                       (W, H), interpolation=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
    k = (w > 0.05 * np.nanpercentile(w[w > 0], 90)) & (rad >= R0 * RS) \
        & (rad <= R1 * RS) & np.isfinite(a)
    z = normalitza_radi(a.astype(np.float64), k, rad)
    M, lams, angs = pics(espectre(z, k), LL["escala_arcsec_px"])
    Mn = M / np.nanmedian(M, axis=1, keepdims=True)
    bl = (lams >= LAM[0]) & (lams <= LAM[1])
    ba = (angs >= ANG[0]) & (angs <= ANG[1])
    return float(np.nanmax(Mn[np.ix_(bl, ba)])), float(np.nanmean(Mn[np.ix_(bl, ba)]))


if __name__ == "__main__":
    print(f"finestra pre-registrada: λ {LAM[0]}-{LAM[1]} px de llenç · "
          f"{ANG[0]}-{ANG[1]}° · anell {R0}-{R1} R☉\n")
    print(f"{'tren':>10s} {'canal':>6s} {'tal com és':>12s} {'al píxel de la Sony':>21s}"
          f" {'que en queda':>13s}")
    for tren in ("VIXEN", "SONYTOT"):
        d = N.darrer_run(tren)
        S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
        w = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
        for canal in ("R", "G", "B"):
            a = fits.getdata(os.path.join(d, "2-ldic", f"CORONA_{canal}.fits")).astype(np.float32)
            x0, m0 = excess(a, w, S["llenc"], 1.0)
            if tren == "VIXEN":
                x1, m1 = excess(a, w, S["llenc"], N.ESC["SONY"] / N.ESC["VIXEN"])
                print(f"{tren:>10s} {canal:>6s} {x0:12.2f} {x1:21.2f} "
                      f"{100*x1/x0:12.0f}%")
            else:
                print(f"{tren:>10s} {canal:>6s} {x0:12.2f} {'(ja hi és)':>21s}")
            del a
    print("\nSi la Vixen desenfocada al píxel de la Sony baixa fins al valor de la\n"
          "Sony, la familia no distingeix els dos instruments: la comparacio\n"
          "anterior mesurava RESOLUCIO, no origen.")
