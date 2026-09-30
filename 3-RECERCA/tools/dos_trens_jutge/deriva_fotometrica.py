"""Tasca 3: la deriva fotometrica del 10,8 % entre trens de 1,2 a 4 R☉.

El flat ja va quedar exculpat (`research/115` §11: corregir-lo empitjorava la
deriva). El sospitos que queda son **les dues restes de cel independents**: cada
tren mesura el seu vector de cel i el seu nivell, i un error de nivell del cel
es un error ADDITIU sobre la corona que creix cap enfora, perque el cel guanya.

L'experiment: la rao entre trens

    rho(r) = G_vixen(r) / G_sony(r)

hauria de ser CONSTANT (els dos trens veuen la mateixa corona; el que canvia es
l'obertura i la transmissio, que son un escalar). Si no ho es, s'ajusta

    G_vixen(r) = a * ( G_sony(r) + d )

amb NOMES DOS parametres. Si un `d` petit comparat amb el cel que ja s'ha restat
aplana la rao, la causa es el nivell del cel. Si no, no ho es.

⚠️ El signe importa: `d > 0` vol dir que a la Sony li hem restat cel de MES.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from astropy.io import fits

import nucli as N

RADIS = np.exp(np.linspace(np.log(1.15), np.log(4.20), 90))
NTH = 720


def perfils(tren):
    d = N.darrer_run(tren)
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]
    g = fits.getdata(os.path.join(d, "2-ldic", "CORONA_G.fits")).astype(np.float32)
    cel = fits.getdata(os.path.join(d, "2-ldic", "CEL_G.fits")).astype(np.float32)
    pes = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    P = N.mostreja(g, cy, cx, LL["R_sol_px"], RADIS, NTH)
    C = N.mostreja(cel, cy, cx, LL["R_sol_px"], RADIS, NTH)
    W = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)
    ref = np.nanpercentile(W, 90, axis=1, keepdims=True)
    m = np.isfinite(P) & (W > 0.05 * np.maximum(ref, 1e-12))
    P[~m] = np.nan; C[~m] = np.nan
    return (np.nanmedian(P, axis=1), np.nanmedian(C, axis=1),
            m.sum(axis=1), os.path.basename(d))


if __name__ == "__main__":
    A = sys.argv[1].upper() if len(sys.argv) > 1 else "VIXEN"
    B = sys.argv[2].upper() if len(sys.argv) > 2 else "SONYTOT"
    pa, ca, na, da = perfils(A)
    pb, cb, nb, db = perfils(B)
    print(f"{A}: {da}\n{B}: {db}\n")
    k = (na > 400) & (nb > 400) & np.isfinite(pa) & np.isfinite(pb) & (pa > 0) & (pb > 0)
    r, ga, gb, sa, sb = RADIS[k], pa[k], pb[k], ca[k], cb[k]

    rho = ga / gb
    rho0 = rho / np.median(rho)
    print(f"{'R☉':>6s} {'G ' + A:>12s} {'G ' + B:>12s} {'cel ' + A:>10s} "
          f"{'cel ' + B:>10s} {'rho norm':>9s}")
    for i in range(0, len(r), 6):
        print(f"{r[i]:6.3f} {ga[i]:12.1f} {gb[i]:12.1f} {sa[i]:10.1f} {sb[i]:10.1f} "
              f"{rho0[i]:9.4f}")
    dev = 100 * (rho0.max() / rho0.min() - 1)
    print(f"\nDERIVA SENSE CURA: {dev:.2f} % de {r.min():.2f} a {r.max():.2f} R☉")

    # ------------------------------------------- ajust de dos parametres: a i d
    def residu(d_):
        y = gb + d_
        if np.any(y <= 0):
            return 1e9
        a = np.median(ga / y)
        rr = ga / (a * y)
        return float(rr.max() / rr.min() - 1)

    # el cel restat a la Sony marca l'escala del que es plausible
    esc = float(np.median(sb))
    ds = np.linspace(-2.0 * esc, 2.0 * esc, 4001)
    vs = np.array([residu(x) for x in ds])
    i = int(np.argmin(vs))
    dmin = float(ds[i])
    a = float(np.median(ga / (gb + dmin)))
    rr = ga / (a * (gb + dmin))
    print(f"\nAJUST  G_{A} = a · (G_{B} + d)")
    print(f"  a = {a:.4f}   d = {dmin:+.2f}  (cel restat a {B}: mediana {esc:.1f}, "
          f"o sigui d = {100*dmin/max(esc,1e-9):+.1f} % del cel)")
    print(f"  deriva residual: {100*vs[i]:.2f} %   (era {dev:.2f} %)")
    print(f"\n{'R☉':>6s} {'rho norm':>9s} {'amb cura':>9s}")
    for i2 in range(0, len(r), 6):
        print(f"{r[i2]:6.3f} {rho0[i2]:9.4f} {rr[i2]/np.median(rr):9.4f}")

    # ------------------------------------- i el mateix, pero movent el cel de A
    def residu_a(d_):
        y = ga + d_
        if np.any(y <= 0):
            return 1e9
        aa = np.median(y / gb)
        rr2 = y / (aa * gb)
        return float(rr2.max() / rr2.min() - 1)
    esca = float(np.median(sa))
    dsa = np.linspace(-2.0 * esca, 2.0 * esca, 4001)
    vsa = np.array([residu_a(x) for x in dsa])
    ia = int(np.argmin(vsa))
    print(f"\n(mateix ajust movent el cel de {A}: d = {dsa[ia]:+.2f} = "
          f"{100*dsa[ia]/max(esca,1e-9):+.1f} % del seu cel · deriva residual "
          f"{100*vsa[ia]:.2f} %)")
