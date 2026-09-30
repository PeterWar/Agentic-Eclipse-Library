"""Tasca 2, tercera peca: quant blau hi posa la CADENA i quant les CAMERES.

Els fotogrames CRUS dels dos trens discrepen poc en B/G (−2,7 % a 1,3-1,7 R☉ i
−3,6 % a 1,8-2,2). Els COMPOSTS en discrepen del −5 al −11 %. La diferencia,
doncs, no la posen els sensors: la posa el que hi ha entremig.

Aqui es mesura, per a cada tren i als MATEIXOS anells, el color de:
  LDIC    = el compost tal com surt de la fusio (encara amb cel)
  CORONA  = el mateix, amb el cel restat

⛔ Tot en ESPAI DE CAMERA (balanc de dia posat, matriu NO), que es on estan
mesurats els fotogrames crus. Barrejar espais ja ha donat una contradiccio.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from astropy.io import fits

import nucli as N

ANELLS = ((1.05, 1.30), (1.30, 1.70), (1.80, 2.20), (2.50, 3.20))
CRUS = {  # mediana dels fotogrames ben exposats (color_per_exposicio.py)
    ("VIXEN", "1.05-1.3"): (1.8077, 0.4928),
    ("VIXEN", "1.3-1.7"): (1.7228, 0.5022),
    ("VIXEN", "1.8-2.2"): (1.5395, 0.6078),
    ("SONYTOT", "1.3-1.7"): (1.7138, 0.4887),
    ("SONYTOT", "1.8-2.2"): (1.5508, 0.5861),
}


def mesura(tren):
    d = N.darrer_run(tren)
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]; RS = LL["R_sol_px"]
    out = {}
    for quin in ("LDIC", "CORONA"):
        C = {c: fits.getdata(os.path.join(d, "2-ldic", f"{quin}_{c}.fits")).astype(np.float32)
             for c in ("R", "G", "B")}
        w = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
        H, W = C["G"].shape
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
        lim = 0.05 * np.nanpercentile(w[w > 0], 90)
        for a, b in ANELLS:
            k = (w > lim) & (rad >= a * RS) & (rad < b * RS) & np.isfinite(C["G"]) \
                & (C["G"] > 0)
            if k.sum() < 20000:
                continue
            out[(quin, f"{a:g}-{b:g}")] = (
                float(np.median(C["R"][k] / C["G"][k])),
                float(np.median(C["B"][k] / C["G"][k])), int(k.sum()))
        del C, w, rad
    return out, os.path.basename(d)


if __name__ == "__main__":
    TRENS = sys.argv[1:] or ["VIXEN", "SONYTOT"]
    M = {}
    for t in TRENS:
        M[t], nom = mesura(t)
        print(f"{t}: {nom}")
    claus = [f"{a:g}-{b:g}" for a, b in ANELLS]
    for quin in ("crus", "LDIC", "CORONA"):
        print(f"\n{quin}   (espai de camera)")
        print(f"{'anell':>10s} | " + " | ".join(f"{t:^19s}" for t in TRENS)
              + " |   dif B/G")
        print(f"{'':>10s} | " + " | ".join(f"{'R/G':>9s} {'B/G':>9s}" for t in TRENS))
        for c in claus:
            fila, bg = [], []
            for t in TRENS:
                v = CRUS.get((t, c)) if quin == "crus" else M[t].get((quin, c))
                if v is None:
                    fila.append(f"{'—':>9s} {'—':>9s}"); bg.append(None)
                else:
                    fila.append(f"{v[0]:9.4f} {v[1]:9.4f}"); bg.append(v[1])
            dif = (f"{100*(bg[1]/bg[0]-1):+8.2f}%"
                   if len(bg) == 2 and None not in bg else "       —")
            print(f"{c:>10s} | " + " | ".join(fila) + f" | {dif}")
