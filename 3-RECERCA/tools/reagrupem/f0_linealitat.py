#!/usr/bin/env python3
"""FASE 0 · pas 3 — on s'acaba la LINEALITAT, per canal.

Mètode: parells de fotogrames de la mateixa escena separats 1 o 2 EV i
propers en el temps. Amb el dark restat, el quocient entre tots dos ha de ser
CONSTANT amb el nivell si la resposta és lineal. On deixa de ser-ho, s'acaba
la linealitat, i aquell nivell és el sostre del pes `w` de la fase 2.

⛔ El quocient es mesura per canal CFA. La imatge final és en color.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

PARELLS = [  # (curt, llarg, EV nominals) triats propers en el temps
    ("572A2967.CR3", "572A2973.CR3", 1.0),   # 1/2000 -> 1/1000
    ("572A2968.CR3", "572A2974.CR3", 1.0),   # 1/500  -> 1/250
    ("572A2969.CR3", "572A2975.CR3", 1.0),   # 1/125  -> 1/60
    ("572A2970.CR3", "572A2976.CR3", 1.0),   # 1/30   -> 1/15
    ("572A2971.CR3", "572A2977.CR3", 1.0),   # 1/8    -> 1/4
    ("572A2972.CR3", "572A2978.CR3", 1.0),   # 1/2    -> 1 s
    ("572A2978.CR3", "572A2979.CR3", 1.0),   # 1 s    -> 2 s
    ("572A2981.CR3", "572A2982.CR3", 2.32),  # 2 s    -> 10 s
]


def calibra(nom: str) -> tuple[np.ndarray, float]:
    p = os.path.join(comu.VIXEN, nom)
    with rawpy.imread(p) as r:
        d = r.raw_image.astype(np.float32)
    import subprocess
    e = float(subprocess.run(["exiftool", "-q", "-n", "-T", "-ExposureTime", p],
                             capture_output=True, text=True).stdout.strip())
    md = os.path.join(comu.F0, "masters_dark", f"MD_R6III_E{e:.6g}s.fits")
    d -= fits.getdata(md).astype(np.float32)
    return d, e


def main() -> int:
    with rawpy.imread(os.path.join(comu.VIXEN, PARELLS[0][0])) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    vis = np.zeros((g.alt, g.ample), bool); vis[g.visible] = True
    sat = 16382.0

    res = {}
    print(f"{'parell':>28} | {'canal':>3} | {'raó EV':>7} | "
          + "  ".join(f"{q:>6}" for q in ("2k", "4k", "6k", "8k", "10k", "12k", "13k", "14k")))
    print("-" * 108)
    for na, nb, ev in PARELLS:
        A, ea = calibra(na); B, eb = calibra(nb)
        for i, cn in ((1, "G1"), (0, "R"), (2, "B")):
            sel = vis & (mc == i)
            a = A[sel]; b = B[sel]
            bo = (a > 40) & (b > 40) & (a < sat - 520) & (b < sat - 520)
            if bo.sum() < 5000:
                continue
            a, b = a[bo], b[bo]
            q_ref = np.median(b[(a > 100) & (a < 1500)] / a[(a > 100) & (a < 1500)])
            fila = []
            for lim in (2000, 4000, 6000, 8000, 10000, 12000, 13000, 14000):
                m = (a > lim * 0.9) & (a < lim * 1.1)
                fila.append(np.median(b[m] / a[m]) / q_ref if m.sum() > 300 else np.nan)
            res[f"{na[4:8]}-{nb[4:8]}-{cn}"] = {
                "q_ref": float(q_ref), "eb_ea": eb / ea,
                "norm": [None if not np.isfinite(x) else float(x) for x in fila],
            }
            print(f"{na[4:8]+'->'+nb[4:8]:>28} | {cn:>3} | {q_ref:7.3f} | "
                  + "  ".join("  ----" if not np.isfinite(x) else f"{x:6.4f}" for x in fila))
    with open(os.path.join(comu.REBUTS, "F0_linealitat.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
