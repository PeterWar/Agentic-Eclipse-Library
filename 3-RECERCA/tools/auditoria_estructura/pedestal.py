"""Queda pedestal? Ho diu la parella d'exposicions.

Si la resta del pedestal és exacta i el sensor és lineal, el quocient entre dos
fotogrames de la mateixa escena i exposicions diferents ha de ser CONSTANT amb
la brillantor. Un romanent additiu `o` el fa dependre'n:
    llarg/curt = (B·t_l + o) / (B·t_c + o)  →  t_l/t_c on B és gran, 1 on és petit.
El pendent contra 1/B dona `o` directament.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402
from tancament_px import frame_al_llenc  # noqa: E402

PARELLES = [("572A2967.CR3", "572A2969.CR3"),   # 0,5 ms  vs 8 ms
            ("572A2968.CR3", "572A2970.CR3"),   # 2 ms    vs 33 ms
            ("572A2973.CR3", "572A2975.CR3"),   # 1 ms    vs 16,7 ms
            ("572A2985.CR3", "572A2987.CR3")]   # 0,5 ms  vs 8 ms (altre extrem)

S = json.load(open(os.path.join(N.RUN, "4-rebuts", "F1.2_sol_llenc.json")))
LL = S["llenc"]; fr = S["fotogrames"]
ped = comu.TRENS["VIXEN"]["pedestal_dn"]

print(f"pedestal declarat i restat: {ped:.0f} DN\n")
for nc, nl in PARELLES:
    vc, vl = fr[nc], fr[nl]
    ic, sc, n, rad = frame_al_llenc(nc, vc, LL, ped, 0, 0)
    il, sl, _, _ = frame_al_llenc(nl, vl, LL, ped, 0, 0)
    k = (np.isfinite(ic) & np.isfinite(il) & (sc < .01) & (sl < .01)
         & (rad > 1.05) & (rad < 1.60) & (ic > 3) & (il > 60))
    q = il[k] / ic[k]; b = ic[k]
    tr = vl["exp"] / vc["exp"]
    ta = np.percentile(b, [0, 20, 40, 60, 80, 100])
    print(f"{nc} ({vc['exp']*1000:g} ms) → {nl} ({vl['exp']*1000:g} ms)   "
          f"t_l/t_c = {tr:.1f}   {k.sum():,} px")
    ms, xs = [], []
    for i in range(5):
        m = (b >= ta[i]) & (b < ta[i + 1])
        if m.sum() < 500:
            continue
        ms.append(np.median(q[m])); xs.append(1.0 / np.median(b[m]))
        print(f"    curt ≈ {np.median(b[m]):7.1f} DN   quocient {ms[-1]:7.3f}"
              f"   ({ms[-1]/tr*100-100:+6.1f}% del nominal)")
    # quocient = t_l/t_c + o·(1 − t_l/t_c)/B  →  pendent contra 1/B
    A = np.column_stack([np.ones(len(xs)), np.array(xs)])
    c, *_ = np.linalg.lstsq(A, np.array(ms), rcond=None)
    o = c[1] / (1.0 - c[0]) if abs(1.0 - c[0]) > 1e-6 else np.nan
    print(f"    → asímptota {c[0]:.3f} (nominal {tr:.1f}, "
          f"{c[0]/tr*100-100:+.1f}%)   ROMANENT o = {o:+.2f} DN\n")
