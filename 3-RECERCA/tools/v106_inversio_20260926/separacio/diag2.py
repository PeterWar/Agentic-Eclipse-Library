import numpy as np
from scipy.ndimage import gaussian_filter1d
from inversio import Inversio
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig, verbose=False)
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
I.prepara(fr); I.construeix(fr); C = I.resol()
print('fotograma exp | χ² reduït per franja de D: [0.6,1) [1,2) [2,3) [3,4) [4,6) [6,10) | fracció suau (σ 8 px) del residu a D<2')
for j in fr:
    c = I.cache[j]; ok = c['ok']; lamv = np.where(ok, I.A[j] * I.avalua_lam(c['a'], c['D']), 0)
    r = np.where(ok, c['d'] - C - lamv, 0); w = (1 / I.sigma(j) ** 2)[:, None]
    out = []
    for lo, hi in [(0.6, 1), (1, 2), (2, 3), (3, 4), (4, 6), (6, 10)]:
        m = ok & (c['D'] >= lo) & (c['D'] < hi)
        # correcció de palanca aproximada
        h = np.where(m, w / np.maximum(I.Wt.reshape(C.shape), 1e-30), 0)
        out.append(float(np.sum((w * r * r)[m] / np.maximum(1 - h[m], 0.05)) / max(m.sum(), 1)) if m.sum() > 500 else np.nan)
    m = ok & (c['D'] < 2)
    rs = gaussian_filter1d(np.where(ok, r, 0), 16, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ok.astype(float), 16, axis=1, mode='wrap'), 1e-6)
    fs = float(np.sum(rs[m] ** 2) / max(np.sum(r[m] ** 2), 1e-30)) if m.sum() > 500 else np.nan
    print(j, f'{I.S.e[j]:.5f}', ' '.join(f'{v:6.1f}' for v in out), f'| suau {fs:.2f}')
