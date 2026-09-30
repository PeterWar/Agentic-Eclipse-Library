"""Corba de resposta del sensor, mesurada dels SOLAPAMENTS entre exposicions.

## ⛔ La idea, i per què es pot fer

Dues exposicions veïnes miren la mateixa corona. Si el sensor fos perfectament
lineal, el quocient de les seves taxes seria **constant** a tot el rang on totes
dues tenen dada. Si no ho és, el quocient **depèn del nivell**, i aquella
dependència **és** la corba de resposta.

Mesurat el 25-08-2026 al pilot, el parell 2 s → 10,079 s dona **+0,890 % a
senyal baix, −0,221 % al mig i −0,818 % a senyal alt**: una corba, no una
constant.

I lliga amb la prova del sostre: abaixant-lo de 0,85 a 0,60 del pou les costures
cauen de 2 a 3 vegades, perquè cap fotograma no arriba a la zona no lineal.
⛔ **Però abaixar el sostre costa senyal/soroll** —el jutge el penalitza tant com
partir la dada per la meitat—, mentre que **corregir la corba no costa res**.

## ⚠️ El que aquesta mesura NO pot separar tota sola

Un error de **pedestal** (fosc) també dona un quocient que depèn del nivell:
si a una exposició li sobra un pedestal `p`, la seva taxa és `(S+p)/t` i el
quocient contra la veïna varia com `1 + p/S`, o sigui **molt a senyal baix i
gens a senyal alt**. La no-linealitat de pou fa el contrari: **gens a senyal
baix i molt a senyal alt**. Per això la corba es mesura **en funció del senyal
CRU en ADU**, no de la taxa: així les dues signatures són distingibles per la
seva forma, i el mateix ajust les separa.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--esglaons", type=Path, required=True,
                    help="dir de PILOT_ESGLAONS_SEPARATS (num_XX/den_XX per esglaó)")
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--n-calaixos", type=int, default=24)
    a = ap.parse_args()
    exps = {int(k): v for k, v in
            json.loads((a.esglaons / "exposicions.json").read_text()).items()}
    ids = [i for i in sorted(exps) if (a.esglaons / f"den_{i:02d}.npy").exists()]

    def taxa(i):
        n = np.load(a.esglaons / f"num_{i:02d}.npy", mmap_mode="r")
        d = np.load(a.esglaons / f"den_{i:02d}.npy", mmap_mode="r")
        d = np.asarray(d); n = np.asarray(n)
        bo = d > 0
        return np.where(bo, n / np.maximum(d, 1e-30), np.nan), bo

    files = []
    print(f"{'parell':>22s} {'n px':>9s}   quocient per calaix de senyal CRU (ADU)")
    for A, B in zip(ids[:-1], ids[1:]):
        gA, bA = taxa(A); gB, bB = taxa(B)
        tA, tB = exps[A], exps[B]
        m = bA & bB & np.isfinite(gA) & np.isfinite(gB) & (gA > 0) & (gB > 0)
        if m.sum() < 20000:
            continue
        # ⛔ el senyal CRU de l'exposició LLARGA: és la que s'acosta al pou
        crua = gB[m] * tB
        q = gB[m] / gA[m] - 1.0
        vores = np.quantile(crua, np.linspace(0, 1, a.n_calaixos + 1))
        vores = np.unique(vores)
        idx = np.clip(np.digitize(crua, vores) - 1, 0, len(vores) - 2)
        o = np.argsort(idx, kind="stable")
        i_s, q_s, c_s = idx[o], q[o], crua[o]
        t = np.searchsorted(i_s, np.arange(len(vores)))
        punts = []
        for k in range(len(vores) - 1):
            lo, hi = t[k], t[k + 1]
            if hi - lo >= 2000:
                punts.append((float(np.median(c_s[lo:hi])), float(np.median(q_s[lo:hi])),
                              int(hi - lo)))
        if len(punts) < 5:
            continue
        files.append({"a": tA, "b": tB, "n": int(m.sum()),
                      "punts": [{"adu": p[0], "quocient": p[1], "n": p[2]} for p in punts]})
        s = "  ".join(f"{p[0]:6.0f}:{100*p[1]:+6.2f}" for p in punts[::max(len(punts)//6, 1)])
        print(f"  {tA:.5g}→{tB:<10.5g} {m.sum():9d}   {s}")
    if a.json:
        C.desa_json(a.json, {"parells": files})
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
