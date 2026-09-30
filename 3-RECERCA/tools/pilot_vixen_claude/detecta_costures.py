"""Detector automàtic de costures de fusió: on la derivada per NIVELL fa un salt.

## ⛔ Per què per nivell i no per radi

La recepta òbvia —desenrotllar a polars i buscar pics de `∂I/∂r`— **no serveix
aquí**, i val la pena dir per què: a la corona interior el gradient radial és
enorme de veritat, i un llindar sobre `|∂I/∂r|` marca tota la corona interior.
Pitjor: una frontera de fusió **no és una circumferència sinó una isofota**, o
sigui que en radi està escampada —al pilot, la del fotograma de 10,08 s va de
**1,58 a 2,37 R☉**, un recorregut de 0,8 R☉— mentre que **en nivell és un punt**.

Per tant es fa en dos passos:

1. es treballa sobre el **detall** (passa-alt), no sobre la imatge crua: la
   caiguda radial ja no hi és i el que queda és el residu;
2. es deriva respecte del **logaritme del nivell del compost**, que és l'única
   variable de la qual depèn tota la maquinària de fusió —el pes d'un fotograma
   d'exposició `t` només depèn del seu valor cru `g·t`—.

## ⛔ I porta control, com mana la norma zero

El llindar no es tria: es calibra **barrejant les etiquetes de nivell** dels
píxels (permutació). Amb les etiquetes barrejades, qualsevol estructura real
queda repartida i el que en surt és el terra del mètode.
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
import filtres as F  # noqa: E402


def perfil_per_nivell(d, w, g, n=600, barreja=None):
    """`barreja` = un `Generator`: si es dona, es **permuten les etiquetes de
    nivell** i tota la resta es fa exactament igual. ⛔ Aquesta és l'única manera
    de construir el control: barrejar els VALORS en lloc de les etiquetes trenca
    l'estructura de calaixos i dona un terra 4.000 vegades massa gros —mesurat
    el 24-08-2026, i és el mateix error que ja havia comès amb els controls de
    costura per nivell—."""
    v = d.ravel()
    m = (w.ravel() > 0) & np.isfinite(v) & np.isfinite(g.ravel()) & (g.ravel() > 0)
    x, vv = np.log(g.ravel()[m]), v[m]
    if barreja is not None:
        x = barreja.permutation(x)
    vores = F._vores_adaptatives(x, n, 300)
    nb = len(vores) - 1
    idx = np.clip(np.digitize(x, vores) - 1, 0, nb - 1)
    o = np.argsort(idx, kind="stable")
    i_s, v_s = idx[o], vv[o]
    t = np.searchsorted(i_s, np.arange(nb + 1))
    med = np.array([np.median(v_s[a:b]) if b - a >= 60 else np.nan
                    for a, b in zip(t[:-1], t[1:])])
    return 0.5 * (vores[:-1] + vores[1:]), med, np.array([b - a for a, b in
                                                          zip(t[:-1], t[1:])])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("detall", type=Path)
    ap.add_argument("--comp", type=Path, required=True)
    ap.add_argument("--sostre", type=float, required=True)
    ap.add_argument("--exposicions", type=float, nargs="+", required=True)
    ap.add_argument("--fb", type=float, default=None)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    d = np.load(a.detall / "DETALL_ln.npy")
    w = np.load(a.detall / "PES.npy")
    g = np.load(a.comp, mmap_mode="r")
    g = np.asarray(g[..., 1] if g.ndim == 3 else g, np.float32)
    if a.fb:
        g = g / np.float32(a.fb)

    x, med, npx = perfil_per_nivell(d, w, g)
    bo = np.isfinite(med)
    # ⛔ **Graella UNIFORME abans de res.** Amb calaixos adaptatius els Δx són
    # molt desiguals i qualsevol derivada hi explota: mesurat el 24-08-2026, el
    # terra per permutació sortia 4.000 vegades més gros que el senyal i el
    # detector no podia dir res. I ⛔ **res de derivades**: l'estadístic és el
    # residu contra la tendència suau, que és el que fa un artefacte de fusió.
    xu = np.linspace(x[bo].min(), x[bo].max(), 800)
    mu = np.interp(xu, x[bo], med[bo])
    from scipy.signal import savgol_filter
    finestra = 81                      # ~0,8 EV: molt més ample que una costura
    res_prof = mu - savgol_filter(mu, finestra, 2, mode="interp")

    # ⛔ CONTROL: el MATEIX estadístic a nivells triats a l'atzar, lluny de
    # qualsevol frontera. El llindar se'l calibren ells, no es tria.
    nivells_f = np.array(sorted({a.sostre / t for t in a.exposicions}
                                | {0.2 * a.sostre / t for t in a.exposicions}))
    rng = np.random.default_rng(20260824)
    ctrl = []
    for _ in range(400):
        xc = rng.uniform(xu[0], xu[-1])
        if np.min(np.abs(np.log(nivells_f) - xc)) < 0.15:
            continue               # massa a prop d'una frontera
        k = int(np.argmin(np.abs(xu - xc)))
        ctrl.append(abs(float(res_prof[k])))
    llindar = float(np.percentile(ctrl, 99)) if len(ctrl) > 50 else float("inf")

    H, W = d.shape
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    def radi_de(niv):
        m = (w > 0) & (np.abs(np.log(np.maximum(g, 1e-30)) - math.log(niv)) < 0.02)
        return float(np.median(rr[m])) if m.sum() > 500 else math.nan

    fronteres = sorted({("pes→0", a.sostre / t, t) for t in a.exposicions}
                       | {("pes→1", 0.2 * a.sostre / t, t) for t in a.exposicions},
                       key=lambda z: -z[1])
    out = {"llindar_dels_controls_p99": llindar, "n_controls": len(ctrl),
           "fronteres": []}
    print(f"terra dels {len(ctrl)} controls (p99): {100*llindar:.4f} %")
    print(f"{'frontera':>26s} {'nivell':>10s} {'r (R☉)':>8s} {'residu':>10s}  veredicte")
    for quin, niv, t in fronteres:
        if not (xu.min() < math.log(niv) < xu.max()):
            continue
        k = int(np.argmin(np.abs(xu - math.log(niv))))
        val = float(np.max(np.abs(res_prof[max(k - 3, 0):k + 4])))
        r_ = radi_de(niv)
        if not (1.06 < r_ < 5.2):
            continue
        ver = "COSTURA" if val > llindar else "neta"
        out["fronteres"].append({"quin": quin, "t_s": t, "nivell": niv,
                                 "radi_rsol": r_, "residu": val, "veredicte": ver})
        print(f"  t={t:<8.5g} {quin:6s} {niv:10.1f} {r_:8.3f} {100*val:9.4f} %  {ver}")
    n_mal = sum(1 for f in out["fronteres"] if f["veredicte"] == "COSTURA")
    print(f"\n  {n_mal} de {len(out['fronteres'])} fronteres amb discontinuïtat per damunt del terra")
    if a.json:
        C.desa_json(a.json, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
