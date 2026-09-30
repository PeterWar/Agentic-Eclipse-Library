#!/usr/bin/env python3
"""La prova que decideix: el residu del disc es FIX AL SENSOR o FIX AL SOL?

Si es fix al sensor -> es camp pla (pols, PRNU, vinyetatge): un flat el treuria.
Si es fix al sol    -> es estructura solar o error del model: cap flat no el treu.

Es correlacionen els residus de parelles de fotogrames amb el disc a llocs
diferents del sensor, en les dues alineacions. Nomes lectura.
"""
import os, itertools
import numpy as np
from scipy import ndimage
import final_dust as F

S = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
V = "/Users/USUARI/Desktop/Eclipse 2026/Vixen"


def collect(specs):
    out = []
    for lab, path, ped, R, tag in specs:
        res, use, cen, rows, gain, lvl = F.analyse(lab, path, ped, R, tag)
        out.append(dict(lab=lab, res=res, use=use, cy=cen[0], cx=cen[1], R=R, lvl=lvl, gain=gain))
    return out


def corr(a, b, sc):
    sg = sc / 2 / 2.355
    fa = ndimage.gaussian_filter(np.nan_to_num(a["res"], nan=0.0), sg)
    wa = ndimage.gaussian_filter(a["use"].astype(float), sg)
    fb = ndimage.gaussian_filter(np.nan_to_num(b["res"], nan=0.0), sg)
    wb = ndimage.gaussian_filter(b["use"].astype(float), sg)
    fa = fa / np.maximum(wa, 1e-6); fb = fb / np.maximum(wb, 1e-6)
    ma = ndimage.binary_erosion(a["use"], iterations=int(sc / 2) + 4)
    mb = ndimage.binary_erosion(b["use"], iterations=int(sc / 2) + 4)
    # --- alineat al SOL: els dos retalls ja son centrats al disc
    h = min(fa.shape[0], fb.shape[0]); w = min(fa.shape[1], fb.shape[1])
    m = ma[:h, :w] & mb[:h, :w]
    c_sol = np.corrcoef(fa[:h, :w][m], fb[:h, :w][m])[0, 1] if m.sum() > 3000 else np.nan
    n_sol = int(m.sum())
    # --- alineat al SENSOR: desplaca b pel salt del disc
    dy = b["cy"] - a["cy"]; dx = b["cx"] - a["cx"]
    fb2 = ndimage.shift(fb, (dy, dx), order=1, mode="constant", cval=0.0)
    mb2 = ndimage.shift(mb.astype(float), (dy, dx), order=0, mode="constant", cval=0.0) > 0.5
    h = min(fa.shape[0], fb2.shape[0]); w = min(fa.shape[1], fb2.shape[1])
    m2 = ma[:h, :w] & mb2[:h, :w]
    c_sen = np.corrcoef(fa[:h, :w][m2], fb2[:h, :w][m2])[0, 1] if m2.sum() > 3000 else np.nan
    return c_sol, n_sol, c_sen, int(m2.sum()), np.hypot(dx, dy) * 2


if __name__ == "__main__":
    print("=== R6 III + VSD90SS ===")
    r6 = collect([("R6 1/1600 19:01", f"{V}/572A2907.CR3", 511.5, 219.4, "x1"),
                  ("R6 1/2500 18:57", f"{V}/572A2906.CR3", 511.5, 219.4, "x2"),
                  ("R6 1/1250 19:27", f"{V}/572A2908.CR3", 511.5, 219.4, "x3")])
    print("\n  correlacio del residu entre parelles")
    print(f"  {'parella':<34}{'escala':>8}{'|salt|':>9}{'r(SOL)':>9}{'r(SENSOR)':>11}")
    for a, b in itertools.combinations(r6, 2):
        for sc in (60, 120, 260):
            cs, ns, cn, nn, d = corr(a, b, sc)
            print(f"  {a['lab'][:16]:<17}{b['lab'][:16]:<17}{sc:>6} px{d:>8.0f}px"
                  f"{cs:>9.3f}{cn:>11.3f}")
    print("\n=== A7RIIIA + 300 GM ===")
    so = collect([("Sony 19:38", f"{S}/DSC06928.ARW", 512.0, 146.4, "y1"),
                  ("Sony 19:43", f"{S}/DSC06931.ARW", 512.0, 146.4, "y2")])
    print("\n  correlacio del residu entre parelles")
    for a, b in itertools.combinations(so, 2):
        for sc in (60, 120, 260):
            cs, ns, cn, nn, d = corr(a, b, sc)
            print(f"  {a['lab']:<17}{b['lab']:<17}{sc:>6} px{d:>8.0f}px"
                  f"{cs:>9.3f}{cn:>11.3f}")
