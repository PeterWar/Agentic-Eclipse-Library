"""e7 · Reproductibilitat final de la vora (sense ordre ≤ 3 per fotograma: radi, centre i refracció) entre grups INDEPENDENTS (fons coronal i
seeing diferents): primerencs (t 15–30 s) contra tardans (t 82–118 s), i cada grup contra LOLA-64 (θN 45,253°, σ_arc 2,5 px). Per bandes."""
import numpy as np
from e4_ajust import *
A4 = np.load(H / 'E4_AJUST_LDEM64.npz'); hl = hlola(float(A4['thN']), float(A4['sig_arc']))
_, _, pc, pf, res, _ = solve(hl, return_all=True)
def mitjana(sel):
    S = np.zeros(nb); W = np.zeros(nb)
    for i, j in enumerate(J):
        if sel(j): S += Wt[i] * (res[i] + pc[-1] * hl); W += Wt[i]
    return np.where(W > 0, S / np.maximum(W, 1e-30), 0.0), W
E, WE = mitjana(lambda j: j <= 17); L, WL = mitjana(lambda j: j >= 26)
m = (WE > 0) & (WL > 0); w = m.astype(float)
BE = bandes(E, w); BL = bandes(L, w); BH = bandes(pc[-1] * hl, w)
SECT = [(0, 90), (90, 180), (180, 270), (270, 360)]
for b in ('gran', 'mitjana', 'fina'):
    print(f'{b:8s}: primerencs–tardans ρ {corr(BE[b], BL[b], m):+.2f} | primerencs–LOLA {corr(BE[b], BH[b], m):+.2f} | tardans–LOLA {corr(BL[b], BH[b], m):+.2f} | '
          f'rms E {np.std(BE[b][m]):.3f} L {np.std(BL[b][m]):.3f} LOLA {np.std(BH[b][m]):.3f} px | sectors E–L: ' + ' '.join(f'{lo}-{hi}:{corr(BE[b], BL[b], m & (th >= lo) & (th < hi)):+.2f}' for lo, hi in SECT))
