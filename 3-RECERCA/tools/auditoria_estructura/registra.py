"""Registra cada compost de Brno al NOSTRE marc solar, per estructura.

Dues cures que el primer intent no tenia i que canvien el resultat:

1. **Resolució igualada.** La nostra corona té R☉ = 441 px i la de Brno de 37 a
   148: el detall que ells NO resolen només pot decorrelacionar. Abans de
   comparar, el nostre perfil es desenfoca al píxel d'ells, anell a anell.
2. **Símplex inicial explícit.** Amb Nelder-Mead arrencant de zeros, el pas per
   defecte és 0,00025 i el centre no es mou (el 800 mm va sortir amb un
   desplaçament de 0,00 px, que no era una mesura sinó un optimitzador aturat).
"""
from __future__ import annotations

import json
import os

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import minimize

import nucli as N

RADIS_REG = np.exp(np.linspace(np.log(1.15), np.log(3.0), 70))
NTH = 1440
RATIO_LLUNA_SOL = 455.5018189722924 / 440.60304883027544   # el nostre dia


def perfil_nostre(lum, LL, radis, nth=NTH, ang0=0.0):
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    return N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, nth, ang0=ang0)


def a_la_resolucio(pol, radis, R_sol_altre, nth=NTH):
    """Desenfoca cada anell fins al píxel de l'altre instrument.

    Un píxel de l'altre subtendeix Δθ = 1/(r·R☉_altre) rad; en mostres del
    nostre perfil això són nth·Δθ/2π. Sense això comparem un instrument amb un
    altre de tres vegades més fi i en diem desacord.
    """
    out = np.empty_like(pol)
    for i, r in enumerate(radis):
        sig = nth / (2.0 * np.pi * r * R_sol_altre) * 0.45
        out[i] = gaussian_filter1d(pol[i], max(sig, 0.3), mode="wrap")
    return out


def registra(nom, lum_nos, LL, radis=RADIS_REG, nth=NTH, verbose=True):
    br, bcy, bcx, bRL = N.carrega_brno(nom)
    Rs0 = bRL / RATIO_LLUNA_SOL

    cru = perfil_nostre(lum_nos, LL, radis, nth)
    en = N.estructura(a_la_resolucio(cru, radis, Rs0, nth))

    def cost(p, retorna_c=False):
        dx, dy, ls, ang = p
        eb = N.estructura(N.mostreja(br, bcy + dy, bcx + dx, Rs0 * np.exp(ls),
                                     radis, nth, ang0=ang))
        c = N.corr_per_anell(en, eb)
        return (c if retorna_c else -np.nanmean(c))

    angs = np.deg2rad(np.arange(0.0, 360.0, 0.5))
    cs = np.array([-cost([0.0, 0.0, 0.0, a]) for a in angs])
    a0 = float(angs[int(np.argmax(cs))])
    if verbose:
        print(f"  gir gruixut {np.rad2deg(a0):7.2f}°  corr {cs.max():.4f}")

    # símplex inicial EXPLÍCIT: 2 px de centre, 1° de gir. ⛔ L'ESCALA NO ES
    # DEIXA LLIURE: l'estructura de la corona és radial i no la constreny (els
    # ajustos lliures donaven R_lluna/R☉ d'1,0237 a 1,0539 quan físicament és
    # 1,0338), i aquest ±1,5 % aterra justament al limbe, que és el que auditem.
    x0 = np.array([0.0, 0.0, a0])
    pas = np.array([2.0, 2.0, np.deg2rad(1.0)])
    sim = np.vstack([x0] + [x0 + np.eye(3)[k] * pas[k] for k in range(3)])
    cost3 = lambda p, **k: cost([p[0], p[1], 0.0, p[2]], **k)
    r = minimize(cost3, x0, method="Nelder-Mead",
                 options=dict(initial_simplex=sim, xatol=1e-5, fatol=1e-7,
                              maxiter=6000, maxfev=6000))
    dx, dy, ang = r.x; ls = 0.0
    c = cost([dx, dy, ls, ang], retorna_c=True)
    out = dict(nom=nom, dx=float(dx), dy=float(dy), escala=float(np.exp(ls)),
               gir_deg=float((np.rad2deg(ang) + 180) % 360 - 180),
               cy=float(bcy + dy), cx=float(bcx + dx),
               R_sol_px=float(Rs0 * np.exp(ls)), R_lluna_px=float(bRL),
               corr_mitjana=float(np.nanmean(c)),
               desplacament_Rsol=float(np.hypot(dx, dy) / (Rs0 * np.exp(ls))))
    if verbose:
        print(f"  refinat: centre ({out['cx']:7.2f},{out['cy']:7.2f})"
              f"  R☉ {out['R_sol_px']:6.2f} px  gir {out['gir_deg']:+7.3f}°"
              f"  corr {out['corr_mitjana']:.4f}")
        print(f"           Sol − Lluna = ({dx:+.2f},{dy:+.2f}) px"
              f" = {out['desplacament_Rsol']:.4f} R☉"
              f"   R_lluna/R☉ {bRL / out['R_sol_px']:.4f}")
    return out


if __name__ == "__main__":
    lum, pes, LL, S = N.carrega_nostre()
    print(f"nostre llenç {LL['W']}x{LL['H']}  R☉ {LL['R_sol_px']:.3f} px"
          f"   R_lluna/R☉ {RATIO_LLUNA_SOL:.4f}")
    res = {}
    for nom in sorted(os.listdir(N.BRNO_DIR)):
        if not nom.lower().endswith(".png"):
            continue
        print(nom)
        res[nom] = registra(nom, lum, LL)
    with open(os.path.join(N.AQUI, "registre.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print("\nresum:")
    for k, v in res.items():
        print(f"  {k:32s} gir {v['gir_deg']:+7.3f}°  corr {v['corr_mitjana']:.4f}"
              f"  Sol−Lluna {v['desplacament_Rsol']:.4f} R☉")
