"""⛔ CONTROL SINTÈTIC: el compositor, sobre dades PERFECTAMENT LINEALS.

Idea de Codex (contrast del 25-08-2026), i és la que faltava. Abans de declarar
que una corba mesurada és **del sensor**, cal comprovar que el compositor no la
fabrica ell tot sol. Aquí es genera una corona sintètica **exactament lineal**,
s'hi apliquen soroll de Poisson i de lectura i el pedestal reals, es composa amb
**la mateixa lògica de pesos, taper i censura dura** que la fase 2, i es mira si
apareix un clot a les isofotes de fusió.

Si n'apareix, el que hi ha és **biaix de selecció de l'algorisme** i s'ha de
corregir això primer; la «no-linealitat del sensor» quedaria contaminada.

Les tres coses que es proven alhora, i totes són del compositor, no del cos:

1. `w = t²/(S/g + RN²)` amb `S` **mesurat**: el pes anticorrelaciona amb el
   soroll i la mitjana ponderada surt esbiaixada cap avall;
2. el `taper`, que depèn del valor **mesurat** i per tant també del soroll;
3. ⛔ la **censura dura** `w[brut > SOSTRE] = 0`: just per sota del sostre,
   els píxels que fluctuen amunt es descarten i **només sobreviuen els que
   fluctuen avall**. És el biaix de truncament clàssic.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-px", type=int, default=400000)
    ap.add_argument("--llavor", type=int, default=20260825)
    ap.add_argument("--sense-censura", action="store_true",
                    help="prova de control: sense el tall dur w[brut>SOSTRE]=0")
    ap.add_argument("--pes-verdader", action="store_true",
                    help="prova de control: pes i taper amb el senyal VERITABLE")
    a = ap.parse_args()
    rng = np.random.default_rng(a.llavor)
    exps = [0.0003076, 0.00048828, 0.00097656, 0.0019531, 0.0039062, 0.0078125,
            0.015625, 0.03125, 0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 10.079]
    n_fot = {e: 4 for e in exps}
    g = C.GUANY["G1"]
    rn_c, rn_l = C.RN_CURT, C.RN_LLARG

    # ⛔ taxa VERITABLE, exactament lineal, repartida en log per cobrir tot el rang
    taxa = np.exp(rng.uniform(np.log(20.0), np.log(3.0e5), a.n_px))
    num = np.zeros(a.n_px); den = np.zeros(a.n_px)
    for t in exps:
        rn = rn_c if t < C.LLINDAR_MODE_S else rn_l
        for _ in range(n_fot[t]):
            senyal = taxa * t                      # ADU sobre el fosc, LINEAL
            e = senyal * g
            brut = rng.poisson(np.minimum(e, 1e12)) / g + rng.normal(0, rn, a.n_px)
            usat = senyal if a.pes_verdader else np.maximum(brut, 0.0)
            var = usat / g + rn * rn
            w = (t * t) / var
            w = w * C.rampa((C.SOSTRE - usat) / (C.RAMPA_SOSTRE * C.SOSTRE))
            if not a.sense_censura:
                w = np.where(brut > C.SOSTRE, 0.0, w)
            else:
                w = np.where(senyal > C.SOSTRE, 0.0, w)
            num += w * (brut / t); den += w
    comp = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
    biaix = comp / taxa - 1.0
    bo = np.isfinite(biaix)

    vores = np.exp(np.linspace(np.log(taxa.min()), np.log(taxa.max()), 240))
    idx = np.clip(np.digitize(taxa, vores) - 1, 0, len(vores) - 2)
    xr, br = [], []
    for k in range(len(vores) - 1):
        m = bo & (idx == k)
        if m.sum() >= 300:
            xr.append(float(np.log(np.median(taxa[m])))); br.append(float(np.median(biaix[m])))
    xr, br = np.array(xr), np.array(br)
    # ⛔ El que fa costura NO és el biaix mitjà —un biaix uniforme el treu el
    # passa-alt— sinó la seva VARIACIÓ amb el nivell. Es treu la tendència suau
    # i es mira el residu, exactament com fa `detecta_costures.py` amb la dada.
    from scipy.signal import savgol_filter
    fin = min(41, (len(br) // 2) * 2 - 1)
    res = br - savgol_filter(br, fin, 2, mode="interp")
    fronteres = np.array(sorted({C.SOSTRE / t for t in exps}
                                | {0.2 * C.SOSTRE / t for t in exps}))
    prop = np.array([np.min(np.abs(np.log(np.exp(x) / fronteres))) for x in xr])
    a_front = np.abs(res[prop < 0.06]); a_lluny = np.abs(res[prop > 0.15])
    print(f"censura dura: {'NO' if a.sense_censura else 'SÍ'}  ·  "
          f"pes amb senyal {'VERITABLE' if a.pes_verdader else 'MESURAT'}")
    print(f"  biaix mitjà del compositor      : {100*np.median(br):+.4f} %")
    print(f"  residu |·| A LES fronteres      : {100*np.median(a_front):.4f} %  (n={a_front.size})")
    print(f"  residu |·| LLUNY de fronteres   : {100*np.median(a_lluny):.4f} %  (n={a_lluny.size})")
    q = np.median(a_front) / max(np.median(a_lluny), 1e-12)
    print(f"  ⛔ quocient frontera/lluny      : ×{q:.2f}"
          + ("   → el compositor SÍ fabrica costura" if q > 1.5 else
             "   → el compositor NO fabrica costura"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
