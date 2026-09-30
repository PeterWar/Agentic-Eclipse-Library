"""t2 · Neutralització de la WOW de la caixa (t1): nivell i textura per distància i sector, contra la V93."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_domini import neutralitza
V88 = ARREL / '4-RESULTATS/v88_20260923'; Q = np.load(V88 / 'A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, by0 = int(cx) - B, int(cy) - B; q = np.load(SORT / 't1_wow_bil_caixa.npy'); m = np.isfinite(q)
qn = neutralitza(q, m, cx, cy, R, box=(bx0, by0)); old = np.load(ARREL / '4-RESULTATS/v93_20260924/filtres_v93/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by0 + 2 * B, bx0:bx0 + 2 * B].astype(np.float32) / 65535
yy, xx = np.mgrid[by0:by0 + 2 * B, bx0:bx0 + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; ref = (d > 100) & (d < 600) & m
hp = lambda X: X - cv2.GaussianBlur(X, (0, 0), 8); k = float(np.std(hp(old)[ref]) / np.std(hp(np.nan_to_num(qn))[ref])); new = np.where(m, 0.5 + k * np.nan_to_num(qn), 0.5).astype(np.float32)
np.save(SORT / 't2_wow_bil_caixa_neutre.npy', new); print('k', round(k, 4))
SECT = {'taronja_63_93': (63, 93), 'taronja_208_253': (208, 253), 'taronja_329_351': (329, 351), 'esquerra_120_200': (120, 200), 'tot': (0, 360)}
for s, (a0, a1) in SECT.items():
    az = (th >= a0) & (th < a1)
    print(s, 'nivell nou', [round(float(new[az & m & (np.abs(d - dd) < 0.5)].mean()), 3) if (az & m & (np.abs(d - dd) < 0.5)).any() else None for dd in (1, 2, 3, 4, 6, 8, 10, 15, 25, 50, 100, 300)])
BINS = [(1, 3), (3, 6), (6, 9), (9, 14), (14, 25), (40, 70)]; lap = cv2.Laplacian(cv2.GaussianBlur(new, (0, 0), 1.0), cv2.CV_32F) ** 2
print('textura nova', {s: [round(float(np.sqrt(lap[(th >= a0) & (th < a1) & m & (d >= b0) & (d < b1)].mean() / lap[(th >= a0) & (th < a1) & m & (d >= 40) & (d < 70)].mean())), 2) for b0, b1 in BINS] for s, (a0, a1) in SECT.items() if s != 'tot'})
lm = cv2.GaussianBlur(new, (0, 0), 150); print('mitjana local (σ150) d 300–1000', np.percentile(lm[(d > 300) & (d < 1000) & m], [5, 50, 95]).round(3))
