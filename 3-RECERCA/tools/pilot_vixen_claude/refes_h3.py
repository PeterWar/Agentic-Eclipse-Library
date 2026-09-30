"""Recalcula la porta H3 des dels perfils desats, sense refer-los.

⛔ Els perfils de coherència costen tres minuts i **no depenen de l'estadístic**.
Aquesta eina els llegeix del `.npz` que deixa `fase_coherencia` i torna a
avaluar H3, de manera que corregir com es mesura no obliga a rellegir 68 RAW.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import pilot  # noqa: E402
import portes as P  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("npz", type=Path)
    ap.add_argument("json_coherencia", type=Path)
    ap.add_argument("--escriu", action="store_true",
                    help="reescriu els camps porta_h3_* del JSON")
    a = ap.parse_args()
    z = np.load(a.npz)
    d = json.loads(a.json_coherencia.read_text())
    noms = [x["nom"] for x in d["per_fotograma"]]
    exps = {x["nom"]: float(x["exposicio_s"]) for x in d["per_fotograma"]}
    cels = {x["nom"]: x["cel_adu_s"] for x in d["per_fotograma"]}
    fac = d["factors"]
    perfils = {n: {q: (z[f"{n}|{q}"], None) for q in ("R", "G1", "G2", "B")}
               for n in noms}
    d0 = pilot.desacord_entre_esglaons(perfils, noms, exps, cels, fac, False)
    d1 = pilot.desacord_entre_esglaons(perfils, noms, exps, cels, fac, True)
    h0 = P.porta_h_esglaons_px(d0["ratios"], d0["sigmes"])
    h1 = P.porta_h_esglaons_px(d1["ratios"], d1["sigmes"])
    print("parell                    abans        ara")
    for k in d0["ratios"]:
        print(f"  {k:22s} {100*d0['ratios'][k]:+7.3f} %  {100*d1['ratios'].get(k, float('nan')):+7.3f} %")
    print(f"\n  H3 abans {h0['estat']} pitjor {100*h0['pitjor_desacord']:+.3f} %"
          f"   →   ara {h1['estat']} pitjor {100*h1['pitjor_desacord']:+.3f} %")
    if a.escriu:
        d["porta_h3_abans"], d["porta_h3_despres"] = h0, h1
        C.desa_json(a.json_coherencia, d)
        print(f"  → {a.json_coherencia} actualitzat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
