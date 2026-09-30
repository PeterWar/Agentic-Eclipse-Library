"""t5 · wow_parells (t4) + treu_anell_coherent: nivell per distància i sector, arcs, textura. Contra V93/V94."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v95_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_parells import treu_anell_coherent
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]; B = 1200; bx0, by0 = int(cx) - B, int(cy) - B
q = np.load(SORT / 't4_q.npy'); m = np.isfinite(q); X = np.load(SORT / 't4_display.npy'); Xn = treu_anell_coherent(X, m, cx, cy, R, box=(bx0, by0)); np.save(SORT / 't5_display.npy', Xn)
yy, xx = np.mgrid[by0:by0 + 2 * B, bx0:bx0 + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
DT, DR = 0.1, 1.0; NT = int(360 / DT); DS = np.arange(0, 250, DR); TS = np.radians((np.arange(NT) + 0.5) * DT); TT, DD = np.meshgrid(TS, DS)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32); t = np.arange(NT) * DT
for nom, Y in (('abans', X), ('després', Xn)):
    P = cv2.remap(Y, MX, MY, cv2.INTER_LINEAR); V = cv2.remap(m.astype(np.float32), MX, MY, cv2.INTER_NEAREST) > 0.5; Ps = np.where(V, P, np.nan)
    arc = np.array([gaussian_filter1d(np.nan_to_num(Ps[i], nan=0.5), 2 / DT, mode='wrap') for i in range(len(DS))])
    print(nom, 'arcs', {f'{a0}-{a1}': round(float(np.std(arc[a0:a1].mean(0))), 4) for a0, a1 in ((2, 16), (5, 30), (30, 60), (60, 130))})
    print('   tot (mitjana a tots els azimuts) d 2,4,6,8,10,12,15,20,30:', [round(float(np.nanmean(Ps[dd])), 3) for dd in (2, 4, 6, 8, 10, 12, 15, 20, 30)])
    for s0, s1 in ((345, 360), (276, 288), (140, 170), (200, 230), (60, 90)): print(f'   {s0}-{s1}', [round(float(np.nanmean(Ps[dd, (t >= s0) & (t < s1)])), 3) for dd in (2, 4, 6, 8, 10, 12, 15, 20, 40)])
    lap = cv2.Laplacian(cv2.GaussianBlur(Y, (0, 0), 1.0), cv2.CV_32F) ** 2
    print('   textura 1-3,3-6,6-9,9-14:', {s: [round(float(np.sqrt(lap[(th >= a0) & (th < a1) & m & (d >= b0) & (d < b1)].mean() / lap[(th >= a0) & (th < a1) & m & (d >= 40) & (d < 70)].mean())), 2) for b0, b1 in ((1, 3), (3, 6), (6, 9), (9, 14))] for s, (a0, a1) in {'63_93': (63, 93), '208_253': (208, 253), '329_351': (329, 351)}.items()})
