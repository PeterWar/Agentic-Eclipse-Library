"""t1 · Prova de wow_domini en una caixa de 2400 px al voltant de la Lluna (la vora de la caixa fa de vora de domini; s'avalua a d < 600 px):
textura (LoG σ 1) per distància al limbe i per sector contra la V93, perfil del nivell arran del limbe (anell clar/fosc?) i mitjana local."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_domini import wow_domini
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85 / 'd4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(FONTS / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
sy, sx = slice(qy0 - by0, qy1 - by0), slice(qx0 - bx0, qx1 - bx0); a[sy, sx] = Q['G']; m[sy, sx] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
t0 = time.time(); q = wow_domini(a, m, 8, True); print(f'WOW bilateral domini (caixa) en {time.time() - t0:.0f} s', flush=True)
np.save(SORT / 't1_wow_bil_caixa.npy', q)
old = np.load(ARREL / '4-RESULTATS/v93_20260924/filtres_v93/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
ref = (d > 100) & (d < 600) & m
hp_old = old - cv2.GaussianBlur(old, (0, 0), 8); hp_new = np.nan_to_num(q) - cv2.GaussianBlur(np.nan_to_num(q), (0, 0), 8)
k = float(np.std(hp_old[ref]) / np.std(hp_new[ref])); new = np.where(m, 0.5 + k * np.nan_to_num(q), 0.5).astype(np.float32); print('escala k', round(k, 4), flush=True)
np.save(SORT / 't1_wow_bil_caixa_display.npy', new)
BINS = [(0, 1), (1, 3), (3, 6), (6, 9), (9, 14), (14, 25), (40, 70)]; SECT = {'taronja_63_93': (63, 93), 'taronja_208_253': (208, 253), 'taronja_329_351': (329, 351), 'esquerra_120_200': (120, 200)}
def tex(X, dom):
    lap = cv2.Laplacian(cv2.GaussianBlur(X, (0, 0), 1.0), cv2.CV_32F) ** 2; out = {}
    for s, (a0, a1) in SECT.items():
        az = (th >= a0) & (th < a1); row = [float(np.sqrt(lap[az & dom & (d >= b0) & (d < b1)].mean())) if (az & dom & (d >= b0) & (d < b1)).any() else float('nan') for b0, b1 in BINS]
        out[s] = [round(v / row[-1], 2) for v in row]
    return out
print('textura V93 (ref 40–70 px):', json.dumps(tex(old, np.ones_like(m))), flush=True)
print('textura nova:', json.dumps(tex(new, m)), flush=True)
for s, (a0, a1) in SECT.items():
    az = (th >= a0) & (th < a1)
    prof_o = [round(float(old[az & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in (1, 2, 3, 4, 6, 8, 10, 15, 25, 50)]
    prof_n = [round(float(new[az & m & (np.abs(d - dd) < 0.5)].mean()), 3) if (az & m & (np.abs(d - dd) < 0.5)).any() else None for dd in (1, 2, 3, 4, 6, 8, 10, 15, 25, 50)]
    print(f'nivell {s}: V93 {prof_o}\n            nou {prof_n}', flush=True)
lm = cv2.GaussianBlur(new, (0, 0), 150); print('mitjana local nova (σ150) a d 300–1000:', np.percentile(lm[(d > 300) & (d < 1000) & m], [5, 50, 95]).round(3), ' V93:', np.percentile(cv2.GaussianBlur(old, (0, 0), 150)[(d > 300) & (d < 1000)], [5, 50, 95]).round(3))
print('primer píxel amb dada (d) per sector:', {s: round(float(d[(th >= a0) & (th < a1) & m & (d > -5)].min()), 2) for s, (a0, a1) in SECT.items()})
