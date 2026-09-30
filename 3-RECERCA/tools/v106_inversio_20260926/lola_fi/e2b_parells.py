import numpy as np
from e2_repro import *
res = {}
def prep(j):
    u = U[j]; e = E[j]; w = np.where(np.isfinite(u) & np.isfinite(e), 1/np.maximum(e,0.02)**2, 0)
    r,_ = treu_harm(np.nan_to_num(u), w); return bandes(r, w), w
P = {j: prep(j) for j in range(nF) if np.isfinite(U[j]).sum() > 1000}
def cc(j, k, band):
    (Bj, wj), (Bk, wk) = P[j], P[k]; m = (wj>0)&(wk>0)
    x = sum(Bj[b] for b in band); y = sum(Bk[b] for b in band); return corr(x, y, m)
for band in (['fina'], ['mitjana'], ['gran']):
    print('banda', band)
    for pairs in [[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7)], [(9,10),(10,11),(14,15),(15,16),(16,17),(9,15),(10,16)], [(27,28),(28,29),(33,34),(39,40),(40,41),(45,46),(46,47)], [(50,51),(51,52),(52,53),(55,56),(60,61),(63,64)], [(0,50),(1,51),(5,55),(10,28),(15,40),(16,46)]]:
        print('   ', ' '.join(f'{j}-{k}:{cc(j,k,band):+.2f}' for j,k in pairs))
    # rms per fotograma
print('rms per fotograma (fina, mitjana, gran):')
for j in sorted(P):
    B,w = P[j]; m = w>0
    print(f'  {j:2d} exp {EXPO[j] if False else 0:} ' if False else f'  {j:2d}', ' '.join(f'{np.std(B[b][m]):.3f}' for b in ('fina','mitjana','gran')), f'err med {np.nanmedian(E[j]):.3f}')
