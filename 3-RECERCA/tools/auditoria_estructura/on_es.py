"""On és l'excés de contrast de la corona interior, en azimut i en radi."""
from __future__ import annotations
import json, os
import numpy as np
import nucli as N
from mapes import fraccio_tapada

NTH = 720
lum, pes, LL, S = N.carrega_nostre()
cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
radis = np.array([1.030, 1.045, 1.060, 1.070, 1.085, 1.100, 1.130, 1.170, 1.250])
pol = N.mostreja(lum, cy, cx, LL["R_sol_px"], radis, NTH)
wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], radis, NTH)
tap, nfr = fraccio_tapada(S, LL, radis, NTH)

print("brillantor / mediana de l'anell, per sectors de 10° (θ=0 a la dreta,"
      " creix cap avall; nord amunt)\n")
hdr = "  ".join(f"{k*10:3d}" for k in range(0, 36, 2))
print(f"{'R☉':>6s}  {hdr}")
for i, r in enumerate(radis):
    k = (tap[i] < 0.02) & np.isfinite(pol[i]) & (wp[i] > 0)
    if k.sum() < 50:
        print(f"{r:6.3f}  (només {k.sum()*360//NTH}° útils)"); continue
    med = np.median(pol[i][k])
    v = np.where(k, pol[i] / med, np.nan)
    sec = [np.nanmean(v[j*20:(j+1)*20]) for j in range(36)]
    print(f"{r:6.3f}  " + "  ".join("  ." if not np.isfinite(s) else f"{s:3.0f}"
                                    for s in sec[::2]))

print("\nel màxim de cada anell:")
for i, r in enumerate(radis):
    k = (tap[i] < 0.02) & np.isfinite(pol[i]) & (wp[i] > 0)
    if k.sum() < 50:
        continue
    med = np.median(pol[i][k]); v = np.where(k, pol[i] / med, np.nan)
    j = int(np.nanargmax(v))
    print(f"  r={r:.3f}  màxim ×{v[j]:6.2f} a θ={j*360/NTH:6.1f}°"
          f"   (p99 ×{np.nanpercentile(v,99):5.2f}, p90 ×{np.nanpercentile(v,90):4.2f})")
