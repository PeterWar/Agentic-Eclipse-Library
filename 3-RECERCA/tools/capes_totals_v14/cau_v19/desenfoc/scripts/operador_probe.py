# -*- coding: utf-8 -*-
"""Sonda ràpida de dades per al prototip de l'operador formalitzat (només lectura)."""
import numpy as np, json

B = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
c1 = np.load(B + "/capa1_rgb16.npy", mmap_mode="r")
c2 = np.load(B + "/capa2_rgb16.npy", mmap_mode="r")
mk = np.load(B + "/capa2_mask16.npy", mmap_mode="r")
H, W = c1.shape[:2]
cx, cy, rs = 4273.2, 2633.6, 455.5

def patch(a, y, x, s=96):
    return np.asarray(a[y:y+s, x:x+s]).astype(np.float32)

print("== cantonades (mitjana per canal / max) ==")
for name, (y, x) in {"TL": (0, 0), "TR": (0, W-96), "BL": (H-96, 0), "BR": (H-96, W-96)}.items():
    p1, p2, pm = patch(c1, y, x), patch(c2, y, x), patch(mk, y, x)
    print(f"{name}: c1={p1.mean(axis=(0,1)).round(0)} max={p1.max():.0f} | "
          f"c2={p2.mean(axis=(0,1)).round(0)} | mask mitjana={pm.mean():.0f}")

s1 = np.asarray(c1[::8, ::8]).astype(np.float32)
sm = np.asarray(mk[::8, ::8]).astype(np.float32) / 65535.0
L = s1.mean(axis=2)
yy, xx = np.mgrid[0:H:8, 0:W:8]
r = np.hypot(xx - cx, yy - cy) / rs

print("\n== percentils de L (subm ::8) ==")
for q in [0.01, 0.1, 1, 2, 5, 10, 50, 99]:
    print(f"p{q}: {np.percentile(L, q):.0f}")
print("frac L==0:", float((L == 0).mean()))
print("frac L<2000:", float((L < 2000).mean()), " frac L<6000:", float((L < 6000).mean()),
      " frac L<12000:", float((L < 12000).mean()))

print("\n== mask segons radi ==")
for r0, r1 in [(0, 0.9), (0.9, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.5), (3.5, 5), (5, 8), (8, 12)]:
    sel = (r >= r0) & (r < r1)
    if sel.any():
        print(f"r {r0}-{r1}: mask mitjana={sm[sel].mean():.3f}  L mediana={np.median(L[sel]):.0f}  "
              f"L p1={np.percentile(L[sel],1):.0f}")

# on és L petita dins r>2? (candidats a sense-dada)
sel = (r > 2.0) & (L < 8000)
print("\nfrac (r>2 i L<8000):", float(sel.mean()))
if sel.any():
    ys, xs = np.where(sel)
    print("bbox y:", ys.min()*8, ys.max()*8, " x:", xs.min()*8, xs.max()*8)
print("\nmax r al llenç:", float(r.max()))
