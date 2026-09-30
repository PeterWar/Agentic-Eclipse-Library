"""El mateix bony, mesurat al COMPOST amb la MATEIXA obertura que als fotogrames.

Si el compost en diu molt més que els fotogrames, el compost l'amplifica i això
sí que és un defecte. Si en diu el mateix, la diferència era la meva obertura.
"""
from __future__ import annotations
import math, os
import numpy as np
import nucli as N

TH0, R0 = 133.5, 1.070
CTRL = [(40.0, 1.070), (220.0, 1.070), (300.0, 1.070)]
RAD_PX = 9.0 / 2.0 * 2.0    # el disc de bony.py era de 9 px de sensor;
                            # al llenç l'escala és la mateixa (1 px = 1 px)

lum, pes, LL, S = N.carrega_nostre()
cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
RS = LL["R_sol_px"]


def disc(a, th, r, rad):
    X = cx + r * RS * math.cos(math.radians(th))
    Y = cy + r * RS * math.sin(math.radians(th))
    y0, y1 = int(Y - rad - 1), int(Y + rad + 2)
    x0, x1 = int(X - rad - 1), int(X + rad + 2)
    sub = a[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    k = np.hypot(xx - X, yy - Y) <= rad
    return float(np.median(sub[k])), float(np.mean(sub[k]))


for rad in (2.0, 4.5, 9.0, 18.0):
    b = disc(lum, TH0, R0, rad)
    cs = [disc(lum, t, r, rad) for t, r in CTRL]
    cm = np.median([c[0] for c in cs])
    print(f"obertura r={rad:4.1f} px:  bony {b[0]:10.4g}   controls "
          + " ".join(f"{c[0]:9.4g}" for c in cs)
          + f"   →  ×{b[0]/cm:5.2f}")

# i el màxim absolut de l'anell, que és el que deia ×10,8
th = np.linspace(0, 2 * np.pi, 3600, endpoint=False)
v = N.mostreja(lum, cy, cx, RS, [R0], 3600)[0]
w = N.mostreja(pes, cy, cx, RS, [R0], 3600)[0]
k = np.isfinite(v) & (w > 0)
med = np.median(v[k])
print(f"\nanell r={R0}: mediana {med:.4g}, màxim ×{np.nanmax(v[k]/med):.2f} "
      f"a θ={np.degrees(th[k][np.nanargmax(v[k]/med)]):.1f}°")
print(f"  p99 ×{np.nanpercentile(v[k]/med,99):.2f}  p95 ×{np.nanpercentile(v[k]/med,95):.2f}")
print(f"\n⏭️ als fotogrames el bony valia ×4,4 amb obertura de 9 px "
      f"(mediana de 34 fotogrames)")
