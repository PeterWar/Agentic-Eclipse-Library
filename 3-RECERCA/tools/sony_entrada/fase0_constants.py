"""Pedestal i saturació de l'A7RIIIA, MESURATS. No es poden copiar de la R6 III.

El pedestal es mesura al marge emmascarat (píxels que mai veuen llum) i la
saturació al valor on el histograma dels fotogrames llargs s'acumula.
"""
from __future__ import annotations
import glob, os
import numpy as np
import rawpy

DIR = os.path.expanduser("~/Desktop/Eclipse determinista/0-ENTRADES/SONY-A7RIIIA")

print(f"{'fitxer':>13s} {'declarat libraw':>28s} {'MESURAT al marge (RGGB)':>34s} "
      f"{'blanc':>7s} {'màx':>7s} {'cim':>7s}")
peds, sats = [], []
for f in sorted(glob.glob(os.path.join(DIR, "totalitat", "*.ARW")))[:6] + \
         sorted(glob.glob(os.path.join(DIR, "darks", "*.ARW")))[:3]:
    with rawpy.imread(f) as r:
        raw = r.raw_image.astype(np.float64)
        vis = r.raw_image_visible
        pat = np.asarray(r.raw_pattern)
        tm, lm = r.sizes.top_margin, r.sizes.left_margin
        decl = list(np.asarray(r.black_level_per_channel))
        blanc = float(r.white_level)
    if lm >= 16:
        fosc = raw[tm:tm + vis.shape[0], 4:lm - 4]
        p = [float(np.median(fosc[i::2, j::2])) for i in range(2) for j in range(2)]
    else:
        p = [np.nan] * 4
    mx = float(raw.max())
    h = np.bincount(raw.astype(np.int64).ravel(), minlength=int(mx) + 1)
    cim = int(np.argmax(h[int(0.9 * mx):]) + 0.9 * mx) if mx > 100 else 0
    peds.append(p); sats.append((blanc, mx, cim))
    print(f"{os.path.basename(f):>13s} {str(decl):>28s} "
          f"{str([round(x,1) for x in p]):>34s} {blanc:7.0f} {mx:7.0f} {cim:7.0f}")

P = np.array(peds)
print(f"\nPEDESTAL mesurat: mediana per canal {np.nanmedian(P, axis=0).round(2).tolist()}"
      f"  ·  pla? dispersió entre canals {np.nanstd(np.nanmedian(P,axis=0)):.2f} DN")
print(f"SATURACIÓ: blanc declarat {sats[0][0]:.0f} · màxim vist "
      f"{max(s[1] for s in sats):.0f} · cim d'acumulació {max(s[2] for s in sats)}")
print(f"\n(el marge esquerre té {lm} px; el de la R6 III en tenia prou i aquest també)")
