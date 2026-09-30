"""Exploració: soroll de δ_j per fotograma (residu contra la mediana dels altres fotogrames on tots veuen a D ≥ 6)."""
import numpy as np, time
from nucli import Dades
S = Dades(); t0 = time.time()
DEL = np.zeros((S.nF, len(S.dg), S.nth), np.float32); VAL = np.zeros(DEL.shape, bool); DD = np.zeros(DEL.shape, np.float32)
for j in range(S.nF):
    a, D, *_ = S.geom(j); d, ok = S.delta(j, D); DEL[j] = d; VAL[j] = ok; DD[j] = D
print('δ', time.time() - t0)
net = VAL & (DD >= 6)
M = np.where(net, DEL, np.nan)
med = np.nanmedian(M, axis=0); n = net.sum(0)
bins = [(-32, -10), (-10, 0), (0, 6), (6, 12), (12, 20), (20, 40)]
print('fotograma exp | rms del residu contra la mediana (només D≥6, n≥8) per franja de d')
SIG = {}
for j in range(S.nF):
    out = []
    for lo, hi in bins:
        rows = (S.dg >= lo) & (S.dg < hi)
        m = net[j][rows] & (n[rows] >= 8)
        if m.sum() < 5000: out.append('   -  '); continue
        r = (DEL[j][rows] - med[rows])[m]; s = 1.4826 * np.median(np.abs(r - np.median(r)))
        out.append(f'{s:.4f}')
    print(j, f'{S.e[j]:.5f}', ' '.join(out))
