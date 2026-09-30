"""Registre JUTJAT A ESCALA FINA. Rectifica `registra.py`.

⛔ El primer registre maximitzava la correlació de l'estructura sencera, que la
manen els harmònics baixos. Amb streamers radials, l'escala hi és gairebé
lliure: per això el vaig ancorar a R_lluna/R☉ = 1,0338 físic. Però la mesura
del limbe de Brno (`geometria.py`) surt esbiaixada cap endins —el seu disc
lunar té vora tractada— i l'ancoratge arrossega l'error: jutjant amb la banda
m = 13–80 apareix un òptim net a ×1,06 que puja la correlació fina de 0,383 a
0,589. Aquí els quatre paràmetres es tornen a ajustar amb aquesta banda.

Validació contra l'ajust: es fa amb 1,20–1,80 R☉ i es JUTJA a 1,80–2,40 R☉.
"""
from __future__ import annotations
import json, os
import numpy as np
from scipy.optimize import minimize

import nucli as N
from registra import a_la_resolucio
from detall3 import banda

NTH = 2880
BANDA = (13, 80)
R_AJUST = np.exp(np.linspace(np.log(1.20), np.log(1.80), 34))
R_JUTGE = np.exp(np.linspace(np.log(1.80), np.log(2.40), 34))


def fes(nom, reg0, lum, pes, LL, radis, verbose=True):
    br, bcy, bcx, bRL = N.carrega_brno(nom)
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    Rb0 = reg0["R_sol_px"]

    def perfils_nostres(rr):
        wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], rr, NTH)
        rf = np.nanpercentile(wp, 90, axis=1, keepdims=True)
        mn = np.isfinite(wp) & (wp > 0.05 * np.maximum(rf, 1e-12))
        p = a_la_resolucio(N.mostreja(lum, cy, cx, LL["R_sol_px"], rr, NTH),
                           rr, Rb0, NTH)
        return p, mn

    cache = {id(R_AJUST): perfils_nostres(R_AJUST), id(R_JUTGE): perfils_nostres(R_JUTGE)}

    def cost(p, rr, retorna=False):
        dx, dy, ls, dg = p
        Rb = Rb0 * np.exp(ls)
        pn, mn = cache[id(rr)]
        # ⚠️ `dg` va en GRAUS (el símplex hi posa passos de 0,3): sumar-hi un
        #    valor en radiants va ser un error meu que feia imprimir girs de 18°
        #    quan els aplicats eren de 0,2°.
        gir = reg0["gir_deg"] + dg
        pb = N.mostreja(br, bcy + dy, bcx + dx, Rb, rr, NTH, ang0=np.deg2rad(gir))
        mb = N.mascara_brno(nom, dict(reg0, cx=bcx + dx, cy=bcy + dy,
                                      R_sol_px=Rb, gir_deg=gir), rr, NTH, 0.030)
        m = mn & mb
        ple = m.all(axis=1)
        if ple.sum() < 8:
            return 1.0
        e0 = N.estructura_mask(pn, m)[ple]; e1 = N.estructura_mask(pb, m)[ple]
        ok = np.ones((int(ple.sum()), NTH), bool)
        c = np.nanmean(N.corr_per_anell_mask(
            banda(e0, *BANDA), banda(e1, *BANDA), ok)[0])
        return c if retorna else -c

    x0 = np.array([0.0, 0.0, np.log(1.06), 0.0])
    pas = np.array([2.0, 2.0, 0.01, 0.3])
    sim = np.vstack([x0] + [x0 + np.eye(4)[k] * pas[k] for k in range(4)])
    r = minimize(cost, x0, args=(R_AJUST,), method="Nelder-Mead",
                 options=dict(initial_simplex=sim, xatol=1e-5, fatol=1e-6,
                              maxiter=3000, maxfev=3000))
    dx, dy, ls, dg = r.x
    ca = cost(r.x, R_AJUST, True); cj = cost(r.x, R_JUTGE, True)
    c0a = cost(np.zeros(4), R_AJUST, True); c0j = cost(np.zeros(4), R_JUTGE, True)
    out = dict(reg0, cx=bcx + dx, cy=bcy + dy, R_sol_px=Rb0 * np.exp(ls),
               gir_deg=reg0["gir_deg"] + dg,
               escala_rel=float(np.exp(ls)), corr_fi_ajust=float(ca),
               corr_fi_jutge=float(cj))
    if verbose:
        print(f"{nom}")
        print(f"  escala ×{np.exp(ls):.4f}  gir {dg:+.3f}°  "
              f"centre ({dx:+.2f},{dy:+.2f}) px   R_lluna/R☉ "
              f"{bRL/(Rb0*np.exp(ls)):.4f}")
        print(f"  m13-80:  ajust 1,2-1,8 R☉ {c0a:.3f} → {ca:.3f}   "
              f"JUTGE 1,8-2,4 R☉ {c0j:.3f} → {cj:.3f}")
    return out


if __name__ == "__main__":
    reg = json.load(open(os.path.join(N.AQUI, "registre.json")))
    lum, pes, LL, S = N.carrega_nostre()
    nou = {n: fes(n, reg[n], lum, pes, LL, None) for n in sorted(reg)}
    with open(os.path.join(N.AQUI, "registre2.json"), "w") as fh:
        json.dump(nou, fh, indent=2)
