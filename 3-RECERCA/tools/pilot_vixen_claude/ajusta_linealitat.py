"""Ajust de la corba de resposta del sensor des dels solapaments entre exposicions.

## El model, i per què té tan pocs graus de llibertat

`x = (RAW − fosc)/(pou − fosc)` és el nivell normalitzat. La correcció és
**identitat fins a un genoll** i després una desviació suau:

    x_veritable = x · c(x),   c(x) = 1 + a₁·u + a₂·u²,   u = max(0, (x−x₀)/(1−x₀))

⛔ **Tres graus de llibertat com a molt**, i `x₀` fix, no ajustat: amb més,
l'ajust absorbiria transparència i corona. És la parametrització que Codex va
recomanar al contrast del 25-08-2026.

## ⛔⛔ ESTAT: la corba NO és identificable amb la dada del pilot

Provat el 25-08-2026 amb quatre parells i quatre plantejaments successius. Cada
vegada la **guarda** —cap correcció pot passar de l'1 % al sostre, perquè la
mesura directa en diu 0,3 %— l'ha aturat:

| plantejament | a₁ | correcció al sostre |
|---|---:|---:|
| lliure, sense terra | +1,479 | **+98,6 %** |
| terra sobre el nivell cru | +0,598 | +39,9 % |
| terra sobre la corona neta | +0,511 | +34,1 % |
| sense genoll, sostre de nivell 0,88, ordre 2 | +0,087 | **+4,0 %** |

⚠️ **I queda un confusor que no s'ha exclòs: el FLAT.** Si el flat radial té un
error, el quocient entre exposicions depèn del **radi**; i com que el nivell
correlaciona amb el radi, es disfressa de dependència del nivell. Per separar-ho
cal mesurar dins d'**anells estrets**, i allà on el fotograma llarg encara no
satura no hi ha prou recorregut de nivell per fer-ho.

⏭️ **Mentre no s'identifiqui, la reserva segura és la que Codex va proposar:
abaixar el SOSTRE.** Amb 0,70 i rampa 0,50, dues de tres costures cauen de 2 a
3 vegades i el cost al jutge és −0,0092, comparable a llençar 12 fotogrames de
68. Vegeu `research/100` §E.10.

## Com s'observa

Dos fotogrames del mateix instant amb exposicions `t_c < t_l` han de donar el
mateix senyal per segon. El que es mesura és

    quocient(x_l) = R∞ · c(x_c) / c(x_l),     amb x_c ≈ x_l · t_c/t_l

⛔ i **el cel es resta abans**, perquè és additiu i varia entre fotogrames: sense
restar-lo, tota la dependència del nivell l'explica el cel i no queda res del
sensor (mesurat el 25-08-2026: −4,41 % a −2,90 % explicats per Δcel = −9,5 ADU/s).

`R∞` és lliure **per parell** —s'hi menja transparència, temps d'exposició i
qualsevol constant— i `a₁, a₂` són **comuns a tots els parells**. Aquesta és la
salvaguarda: la corba ha d'explicar parells diferents alhora.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import pilot as PL  # noqa: E402

POU = C.POU - C.PEDESTAL


def punts_del_parell(fc, fl, n=26, x_min=0.15, x_max=0.88):
    mc, sc = C.calibra(fc); ml, sl = C.calibra(fl)
    dy = int(round((fl.sol_usat[1] - fc.sol_usat[1]) / 2.0)) * 2
    dx = int(round((fl.sol_usat[0] - fc.sol_usat[0]) / 2.0)) * 2
    mc = np.roll(mc, (dy, dx), axis=(0, 1)); sc = np.roll(sc, (dy, dx), axis=(0, 1))
    out = []
    for nom in ("G1", "G2"):
        pc, oy, ox = C.plans(mc)[nom]; pl_, _, _ = C.plans(ml)[nom]
        satc = C.plans(sc.astype(np.uint8))[nom][0]; satl = C.plans(sl.astype(np.uint8))[nom][0]
        rr = C.anells(*pc.shape, (fl.sol_usat[1] - oy) / 2,
                      (fl.sol_usat[0] - ox) / 2) * 2 / C.R_SOL_PX
        an = (rr > C.FONS_ANELL[0]) & (rr < C.FONS_ANELL[1]) & (satc == 0) & (satl == 0)
        if an.sum() < 5000:
            continue
        cc = float(np.median(pc[an])) / fc.exp_s
        cl = float(np.median(pl_[an])) / fl.exp_s
        # ⛔ **Sostre de nivell**, i no és el pou. Mesurat el 25-08-2026: als
        # calaixos de x > 0,95 el quocient s'ensorra de 0,96 a 0,23 perquè el
        # fotograma llarg **ja retalla** i la màscara de saturació no ho atrapa
        # —és el mateix que research/99 va trobar: «el nivell de blanc efectiu
        # no és 16383»—. Aquells punts dominaven l'ajust i el feien degenerat.
        bo = ((satc == 0) & (satl == 0) & (pl_ > x_min * POU) & (pl_ < x_max * POU)
              & (rr > 1.15) & (rr < 4.0))
        if bo.sum() < 50000:
            continue
        tc = pc[bo] / fc.exp_s - cc; tl = pl_[bo] / fl.exp_s - cl
        # ⛔ El terra ha d'anar sobre el senyal AMB EL CEL JA TRET, no sobre el
        # nivell cru. Al fotograma de 10,079 s, un 15 % del pou són 236 ADU/s i
        # el cel en val 433: la corona hi és NEGATIVA. Amb el terra sobre el
        # nivell cru, l'ajust menjava aquells punts i sortia degenerat
        # (a₁ = +0,60, residu 4.500 %).
        k = (tc > 2.0 * cc) & (tl > 2.0 * cl)
        q = tl[k] / tc[k]
        x = pl_[bo][k] / POU
        v = np.unique(np.quantile(x, np.linspace(0.02, 0.999, n + 1)))
        idx = np.clip(np.digitize(x, v) - 1, 0, len(v) - 2)
        o = np.argsort(idx, kind="stable"); i_s, q_s, x_s = idx[o], q[o], x[o]
        t = np.searchsorted(i_s, np.arange(len(v)))
        for a_, b_ in zip(t[:-1], t[1:]):
            if b_ - a_ >= 3000:
                out.append((float(np.median(x_s[a_:b_])), float(np.median(q_s[a_:b_])),
                            int(b_ - a_), nom))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parells", nargs="+", required=True, help="curt:llarg …")
    ap.add_argument("--x0", type=float, default=0.55)
    # ⛔ terra de nivell: per sota, el senyal amb el cel restat del fotograma CURT
    # és gairebé zero i el quocient explota. Sense això l'ajust donava
    # a₁ = +1,48 —o sigui +148 % de correcció al pou— amb residu del 13,5 %.
    ap.add_argument("--x-min", type=float, default=0.15)
    ap.add_argument("--x-max", type=float, default=0.88)
    ap.add_argument("--ordre", type=int, choices=[1, 2], default=1)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    fg = {f.nom: f for f in C.llegeix_manifest()}
    PL.centres_finals(list(fg.values()))
    dades = []
    for par in a.parells:
        c, l = par.split(":")
        fc, fl = fg[c], fg[l]
        pts = punts_del_parell(fc, fl, x_min=a.x_min, x_max=a.x_max)
        if not pts:
            print(f"  {c}→{l}: sense mostra"); continue
        xs = [p[0] for p in pts]
        print(f"  {fc.exp_s:.5g}→{fl.exp_s:<9.5g}  {len(pts):3d} punts, "
              f"x de {min(xs):.3f} a {max(xs):.3f}  (Δt {fl.t_rel_c2-fc.t_rel_c2:+.1f} s)")
        dades.append((fc, fl, pts))
    if not dades:
        raise SystemExit("cap parell utilitzable")

    def u(x):
        # ⚠️ Amb `x0 = 0` no hi ha genoll: la mesura diu que la compressió ja
        # baixa des de x = 0,15, o sigui que forçar identitat per sota d'un
        # genoll no descriu la dada.
        return (np.maximum(0.0, (x - a.x0) / (1.0 - a.x0)) if a.x0 > 0 else x)

    def residu(par):
        coef = par[:a.ordre]
        res = []
        for i, (fc, fl, pts) in enumerate(dades):
            R = par[a.ordre + i]
            x = np.array([p[0] for p in pts]); q = np.array([p[1] for p in pts])
            xs_ = x * (fc.exp_s / fl.exp_s)
            def cfun(z):
                uu = u(z); s = np.ones_like(z)
                for k, ak in enumerate(coef):
                    s = s + ak * uu ** (k + 1)
                return s
            mod = R * cfun(xs_) / cfun(x)
            # ⛔ pes per mostra: un calaix amb tres mil píxels no val el mateix
            # que un amb tres-cents mil
            pes = np.sqrt(np.array([pp[2] for pp in pts], float))
            res.append(pes * (q - mod) / np.maximum(q, 1e-9))
        return np.concatenate(res)

    from scipy.optimize import least_squares
    p0 = [0.0] * a.ordre + [float(np.median([p[1] for p in d[2]])) for d in dades]
    # ⛔ pèrdua ROBUSTA: els parells tenen punts atípics on el registre
    # sub-píxel no s'ha pogut corregir, i un mínim quadrats pur els segueix.
    sol = least_squares(residu, p0, loss="soft_l1", f_scale=1.0, max_nfev=20000)
    coef = sol.x[:a.ordre]
    print(f"\n  genoll x₀ = {a.x0}  ·  ordre {a.ordre}")
    for k, ak in enumerate(coef):
        print(f"    a{k+1} = {ak:+.6f}")
    for k, ak in enumerate(coef):
        pass
    cmax = 1.0 + sum(ak * 1.0 ** (k + 1) for k, ak in enumerate(coef))
    print(f"    → correcció al POU ple: {100*(cmax-1):+.3f} %")
    print(f"    → al sostre actual (x={C.SOSTRE/POU:.3f}): "
          f"{100*(sum(ak*((C.SOSTRE/POU-a.x0)/(1-a.x0))**(k+1) for k,ak in enumerate(coef))):+.3f} %")
    # ⚠️ `sol.fun` porta el pes sqrt(n) a dins: dividir-lo per tornar a %
    _pw = np.sqrt(np.mean([pp[2] for d in dades for pp in d[2]]))
    print(f"  residu rms {100*np.sqrt(np.mean(sol.fun**2))/_pw:.4f} %  ({sol.fun.size} punts)")
    # ⛔ GUARDA: la mesura directa diu ~0,3 % de compressió al 84 % del pou.
    # Una correcció de més de l'1 % al sostre vol dir ajust degenerat.
    _s = C.SOSTRE / POU
    _c = sum(ak * ((_s - a.x0) / (1 - a.x0)) ** (k + 1) for k, ak in enumerate(coef))
    if abs(_c) > 0.01:
        print(f"  ⛔ GUARDA: {100*_c:+.2f} % al sostre és massa. Ajust DEGENERAT, "
              f"no fer-lo servir.")
    if a.json:
        a.json.write_text(json.dumps(
            {"model": "x_true = x*(1 + a1*u + a2*u^2), u = max(0,(x-x0)/(1-x0))",
             "x0": a.x0, "coeficients": [float(c_) for c_ in coef],
             "residu_rms": float(np.sqrt(np.mean(sol.fun ** 2))),
             "n_punts": int(sol.fun.size),
             "parells": [f"{d[0].nom}:{d[1].nom}" for d in dades]},
            ensure_ascii=False, indent=1))
        print(f"  → {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
