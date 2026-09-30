"""Tasques 2 i 3 alhora: UN sol parametre, DOS simptomes independents.

Els dos trens fan dues restes de cel independents, i aixo deixa dues marques:

  A) **fotometria** — la rao G_vixen/G_sony hauria de ser constant de 1,2 a
     4,2 R☉ i deriva un 13,5 %;
  B) **color** — el B/G dels dos discrepa un 2,7-3,6 % als fotogrames CRUS i
     del 5 al 11 % un cop restat el cel.

Si les dues son la mateixa causa, **un sol escalar sobre el nivell de cel** les
ha de millorar les DUES alhora. Si en millora una i empitjora l'altra, no ho es.

⛔ Aixo NO es un ajust per fer quadrar res: es una prova. El parametre te
un rang plausible declarat (research/100 acota la part constant del cel a
≲10 %) i el veredicte es si el minim de les dues corbes cau al mateix lloc i
dins d'aquell rang.
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
ANELL_COLOR = (2.50, 3.20)


def carrega(tren):
    d = N.darrer_run(tren)
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]
    L = {c: fits.getdata(os.path.join(d, "2-ldic", f"LDIC_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    C = {c: fits.getdata(os.path.join(d, "2-ldic", f"CEL_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    w = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
    return L, C, w, LL, os.path.basename(d)


if __name__ == "__main__":
    A = sys.argv[1].upper() if len(sys.argv) > 1 else "VIXEN"
    B = sys.argv[2].upper() if len(sys.argv) > 2 else "SONYTOT"
    D = {}
    for t in (A, B):
        D[t] = carrega(t)
        print(f"{t}: {D[t][4]}")
    LL = D[A][3]; RS = LL["R_sol_px"]; H, W = D[A][0]["G"].shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
    cy, cx = H / 2.0, W / 2.0

    # ---- comprovacio: CORONA == LDIC - CEL ?
    d0 = N.darrer_run(A)
    co = fits.getdata(os.path.join(d0, "2-ldic", "CORONA_G.fits")).astype(np.float32)
    dif = np.nanmax(np.abs(co - (D[A][0]["G"] - D[A][1]["G"])))
    print(f"\ncontrol: max|CORONA − (LDIC − CEL)| = {dif:.3g}  "
          f"({'la resta es exactament aixo' if dif < 1e-3 else '⛔ NO ho es'})")
    del co

    def perfil_G(t, f):
        L, C, w, _, _ = D[t]
        g = L["G"] - f * C["G"]
        P = N.mostreja(g, cy, cx, RS, RADIS, NTH)
        W_ = N.mostreja(w, cy, cx, RS, RADIS, NTH)
        ref = np.nanpercentile(W_, 90, axis=1, keepdims=True)
        m = np.isfinite(P) & (W_ > 0.05 * np.maximum(ref, 1e-12))
        P[~m] = np.nan
        return np.nanmedian(P, axis=1), m.sum(axis=1)

    def color(t, f):
        L, C, w, _, _ = D[t]
        lim = 0.05 * np.nanpercentile(w[w > 0], 90)
        k = (w > lim) & (rad >= ANELL_COLOR[0] * RS) & (rad < ANELL_COLOR[1] * RS)
        g = L["G"][k] - f * C["G"][k]
        b = L["B"][k] - f * C["B"][k]
        ok = np.isfinite(g) & (g > 0)
        return float(np.median(b[ok] / g[ok]))

    base = {t: perfil_G(t, 1.0) for t in (A, B)}
    k = (base[A][1] > 400) & (base[B][1] > 400) & np.isfinite(base[A][0]) \
        & np.isfinite(base[B][0])
    print(f"\n{'f cel Sony':>11s} {'deriva fotometrica':>19s} {'B/G ' + A:>10s} "
          f"{'B/G ' + B:>10s} {'dif B/G':>9s}")
    fs = np.arange(0.90, 1.105, 0.01)
    bA = color(A, 1.0)
    out = []
    for f in fs:
        pb, nb = perfil_G(B, f)
        kk = k & np.isfinite(pb) & (pb > 0)
        rho = base[A][0][kk] / pb[kk]
        dev = 100 * (rho.max() / rho.min() - 1)
        bB = color(B, f)
        out.append((f, dev, bB))
        print(f"{f:11.2f} {dev:18.2f}% {bA:10.4f} {bB:10.4f} "
              f"{100*(bB/bA-1):+8.2f}%")
    o = np.array(out)
    i = int(np.argmin(o[:, 1]))
    j = int(np.argmin(np.abs(o[:, 2] / bA - 1)))
    print(f"\n  mínim de la DERIVA FOTOMETRICA a f = {o[i,0]:.2f}  ({o[i,1]:.2f} %)")
    print(f"  el COLOR quadraria a f = {o[j,0]:.2f}")
    print("\n  → si els dos mínims cauen al mateix f, és el nivell del cel;\n"
          "    si cauen lluny, són dues causes diferents.")
