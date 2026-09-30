# -*- coding: utf-8 -*-
"""Exploració ràpida: estadístiques de capes i màscara abans de mesurar."""
import numpy as np, json, os

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
c1 = np.load(os.path.join(BASE, "capa1_rgb16.npy"), mmap_mode="r")
c2 = np.load(os.path.join(BASE, "capa2_rgb16.npy"), mmap_mode="r")
m2 = np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")
geo = json.load(open(os.path.join(BASE, "geometria.json")))
H, W = c1.shape[:2]
xc, yc = geo["sol_crop"]; rs = geo["rs"]

yy = np.arange(H, dtype=np.float32)[:, None]
xx = np.arange(W, dtype=np.float32)[None, :]
# radi en R☉ a una graella ::8 per anar de pressa
r8 = np.sqrt((xx[:, ::8] - xc) ** 2 + (yy[::8] - yc) ** 2) / rs

m8 = np.asarray(m2[::8, ::8], dtype=np.float32) / 65535.0
g1_8 = np.asarray(c1[::8, ::8, 1], dtype=np.float32)
g2_8 = np.asarray(c2[::8, ::8, 1], dtype=np.float32)

print("mida", c1.shape, c2.shape, m2.shape)
print("mask: mitjana %.4f  p1 %.4f p50 %.4f p99 %.4f" % (m8.mean(), *np.percentile(m8, [1, 50, 99])))
for lo, hi in [(0, 1), (1, 2), (2, 2.5), (2.5, 3), (3, 4), (4, 6), (6, 8), (8, 12)]:
    sel = (r8 >= lo) & (r8 < hi)
    if sel.sum() == 0:
        continue
    print("r %4.1f-%4.1f R☉: n=%7d mask mitjana %.3f  G1 med %6.0f  G2 med %6.0f" %
          (lo, hi, sel.sum(), m8[sel].mean(), np.median(g1_8[sel]), np.median(g2_8[sel])))

# quant s'assemblen capa1 i capa2 globalment
d = g2_8 - g1_8
print("G2-G1 ::8  p1 %.0f p50 %.0f p99 %.0f  rms %.0f" % (*np.percentile(d, [1, 50, 99]), np.sqrt((d**2).mean())))
# fraccions de màscara
print("mask<60000/65535 fracció:", float((m8 < 60000/65535).mean()), " mask==1 fracció:", float((m8 > 0.999).mean()))
