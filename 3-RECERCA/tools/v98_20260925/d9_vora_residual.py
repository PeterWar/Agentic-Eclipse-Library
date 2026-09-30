"""d9 (V98) · Dèficit residual a les primeres files de la dada neta (A3B): per azimut (1°), ln G de les files dv = d − vora ∈ [0,1), [1,2), [2,3)
contra la recta ajustada a dv ∈ [4, 15); mediana per sector de 30°. Ús: d9_vora_residual.py <A3B.npz> <base_G.npy>"""
import sys, numpy as np
Q = np.load(sys.argv[1]); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; dom = Q['domini']; DMIN = np.maximum(Q['DMIN'], 0)
G = np.load(sys.argv[2], mmap_mode='r')[by0:by1, bx0:bx1]; lg = np.log(np.maximum(np.asarray(G, np.float32), 1e-6))
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
dv = d - DMIN[(th / 360 * len(DMIN)).astype(int) % len(DMIN)]; tb = th.astype(int)
res = {}
for k in range(360):
    s = dom & (tb == k) & (dv >= 0) & (dv < 15)
    if s.sum() < 30: continue
    x = dv[s]; y = lg[s]; f = x >= 4
    if f.sum() < 10: continue
    c = np.polyfit(x[f], y[f], 1); r = y - np.polyval(c, x)
    res[k] = [float(np.median(r[(x >= a) & (x < a + 1)])) if ((x >= a) & (x < a + 1)).sum() > 2 else np.nan for a in (0, 1, 2, 3)]
for a0 in range(0, 360, 30):
    v = np.array([res[k] for k in range(a0, a0 + 30) if k in res])
    if len(v): print(f'{a0:3d}-{a0+30:3d}', ' '.join(f'fila{i}:{np.nanmedian(v[:, i])*100:+.2f}%' for i in range(4)))
