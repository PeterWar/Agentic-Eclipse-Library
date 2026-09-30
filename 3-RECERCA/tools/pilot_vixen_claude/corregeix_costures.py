"""Correcció de costures amb la forma DICTADA pels mapes de pes de la fusió.

## ⛔ Per què aquesta i no una resta lliure

El 24-08-2026 una resta del detall **per nivell i sector azimutal** esborrava les
costures i el jutge extern la va refusar: feia caure l'acord amb l'altre tren de
**0,930 a 0,849**. Tenia centenars de paràmetres lliures per sector i el que
absorbia era **corona**.

Aquí el model no és lliure. Si l'esglaó d'exposició `k` porta un error
multiplicatiu `δ_k`, l'error del compost a cada píxel és **exactament**

    error(píxel) = Σ_k f_k(píxel) · δ_k

on `f_k = w_k / Σ_j w_j` és la **fracció de pes** d'aquell esglaó, que **no és un
paràmetre: està mesurada** i surt de la mateixa fase 2. O sigui **un escalar per
exposició** —quinze al pilot— contra trenta milions de píxels.

⛔ **I això no pot menjar corona.** La variació azimutal, que és el que la resta
per sector necessitava paràmetres per seguir, aquí **surt sola**: `f_k` ja depèn
de la brillantor local, perquè el pes d'un fotograma depèn del seu valor cru. I
perquè l'ajust absorbís estructura real, la corona hauria de semblar-se a una
combinació lineal dels mapes de pes — i el passa-alt d'un mapa de pes està
concentrat **només a les fronteres**, que és on el mapa canvia.

⚠️ Igualment, **la decisió no és d'aquest fitxer**: el resultat passa pel
`jutge_creuat.py` com qualsevol altre candidat. Si l'acord amb l'altre tren no
puja, la correcció es llença.

## Ús

Cal haver desat els mapes per esglaó de la fase 2:

    PILOT_ESGLAONS_SEPARATS=<dir> ... f2 ...
    corregeix_costures.py <filtres_dir> --esglaons <dir> --sortida <dir nou>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import math

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import filtres as F  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("filtres", type=Path)
    ap.add_argument("--esglaons", type=Path, required=True)
    ap.add_argument("--sortida", type=Path, required=True)
    ap.add_argument("--sigmes", type=float, nargs="+", default=[8.0, 16.0, 32.0])
    ap.add_argument("--sigma-prior", type=float, default=0.003,
                    help="desviació típica esperada de δ; ve de la mesura de "
                         "coherència, no es tria a ull")
    a = ap.parse_args()

    d = np.load(a.filtres / "DETALL_ln.npy")
    w = np.load(a.filtres / "PES.npy")
    bo = w > 0
    exps = {int(k): v for k, v in
            json.loads((a.esglaons / "exposicions.json").read_text()).items()}
    ids = sorted(exps)

    # Σw per píxel, per normalitzar les fraccions
    tot = np.zeros(d.shape, np.float32)
    hi_ha = []
    for i in ids:
        f = a.esglaons / f"den_{i:02d}.npy"
        if f.exists():
            tot += np.load(f, mmap_mode="r")
            hi_ha.append(i)
    tot = np.maximum(tot, 1e-30)
    print(f"{len(hi_ha)} esglaons amb mapa de pes")

    # ⛔ El regressor és el mapa de pes PASSAT PEL MATEIX PASSA-ALT que el
    # detall: una `f_k` suau no contribueix al detall, només ho fa el seu salt.
    n = len(hi_ha)
    ATA = np.zeros((n, n)); ATb = np.zeros(n)
    regs = []
    for j, i in enumerate(hi_ha):
        fk = (np.load(a.esglaons / f"den_{i:02d}.npy", mmap_mode="r") / tot).astype(np.float32)
        Fk, _ = F.achf(np.where(bo, fk, 0.0), w.astype(np.float32), a.sigmes)
        Fk = np.where(bo, Fk, 0.0).astype(np.float32)
        regs.append(Fk)
        print(f"  esglaó {i:2d} ({exps[i]:.5g} s): rms del regressor {np.std(Fk[bo]):.5f}")
    v = d[bo]
    M = np.stack([r[bo] for r in regs], axis=1)
    # ⛔ gauge: Σf_k = 1 a tot píxel, o sigui que els regressors són col·lineals.
    # Es fixa Σδ = 0, que és el mateix que dir que l'escala global no es toca.
    M = M - M.mean(axis=1, keepdims=True)
    ATA = M.T @ M; ATb = M.T @ v
    # ⛔ **REGULARITZACIÓ, i el prior NO és inventat.** Els regressors sumen 1 a
    # cada píxel i uns quants esglaons tenen pes gairebé nul: el sistema és mal
    # condicionat i sense prior l'ajust se'n va per direccions degenerades.
    # Mesurat el 24-08-2026, l'ajust lliure demanava δ de **+954 %, −3182 % i
    # −1963 %**, que és físicament impossible i la guarda ho va aturar.
    # El prior surt de la MESURA independent de coherència: després de corregir
    # la transparència, el desacord entre esglaons veïns queda en **±0,3 %**, o
    # sigui que δ ha de ser d'aquest ordre. `sigma_prior` ho posa a l'ajust en
    # lloc de deixar-ho a la sort del condicionament.
    # ⛔ **λ = σ_soroll² / σ_prior², PERÒ amb el nombre EFECTIU de mostres.** El
    # detall està correlat espacialment a l'escala de les σ de l'ACHF, o sigui
    # que trenta milions de píxels no són trenta milions de mesures
    # independents: n'hi ha `N / (2π σ_max²)`. Mesurat el 24-08-2026, escalant
    # λ amb el soroll per píxel el prior no mossegava gens i l'ajust encara
    # demanava δ de **+32 % i −32 %**.
    area = 2.0 * math.pi * (max(a.sigmes) ** 2)
    lam = float(np.var(v)) / (a.sigma_prior ** 2) * area
    delta = np.linalg.solve(ATA + lam * np.eye(len(hi_ha)), ATb)
    print(f"\n  prior σ(δ) = {100*a.sigma_prior:.3f} %  ·  λ = {lam:.4g}  "
          f"(àrea de correlació {area:.0f} px)")
    print("  δ per esglaó (error multiplicatiu ajustat):")
    for j, i in enumerate(hi_ha):
        print(f"    {exps[i]:>10.5g} s   {100*delta[j]:+8.4f} %")
    model = np.zeros(d.shape, np.float32)
    for j, r in enumerate(regs):
        model += np.float32(delta[j]) * r
    model -= np.float32(np.mean(delta)) * np.float32(0.0)
    net = (d - np.where(bo, model, 0.0)).astype(np.float32)
    _pitjor = float(np.max(np.abs(delta)))
    if _pitjor > 0.01:
        print(f"\n  ⛔ GUARDA: |δ| màxim {100*_pitjor:.2f} % > 1 %. L'ajust és "
              f"DEGENERAT i el model no s'ha de fer servir.")
    print(f"\n  rms del model {np.std(model[bo]):.6f}  ({100*np.std(model[bo])/np.std(d[bo]):.1f} % del detall)")
    print(f"  detall {np.std(d[bo]):.6f} → {np.std(net[bo]):.6f}")
    a.sortida.mkdir(parents=True, exist_ok=True)
    np.save(a.sortida / "DETALL_ln.npy", net)
    np.save(a.sortida / "PES.npy", w)
    (a.sortida / "correccio_costures.json").write_text(json.dumps(
        {"model": "error = Σ_k f_k · δ_k, un escalar per esglaó",
         "delta_per_exposicio": {f"{exps[i]:.9g}": float(delta[j])
                                 for j, i in enumerate(hi_ha)},
         "rms_del_model": float(np.std(model[bo])),
         "guarda": ("⛔ si algun |δ| passa de l'1 %, el model és degenerat i "
                    "s'ha de llençar: la mesura de coherència diu ±0,3 %"),
         "gauge": "Σδ = 0 (els regressors sumen 1 a cada píxel)",
         "sigma_prior": float(a.sigma_prior), "lambda": float(lam),
         "area_de_correlacio_px": float(area)},
        ensure_ascii=False, indent=1))
    print(f"→ {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
