import numpy as np
from e2_repro import *
UU = Z['u0']; EE = Z['err']
def prepc(c, j):
    u = UU[c, j]; e = EE[c, j]; w = np.where(np.isfinite(u) & np.isfinite(e), 1/np.maximum(e,0.02)**2, 0)
    r,_ = treu_harm(np.nan_to_num(u), w); return bandes(r, w), w
def rob(x): return 1.4826*np.median(np.abs(x-np.median(x)))
print('j  exp   | ρ R–G, B–G, R–B (fina) | (mitjana) | rms robust fina G | rms robust mitjana G')
for j in [0,1,4,5,8,9,10,11,14,15,16,17,27,28,29,33,34,40,41,46,47,50,55,60,65]:
    if not np.isfinite(UU[1,j]).sum(): continue
    P = [prepc(c, j) for c in range(3)]
    m = (P[0][1]>0)&(P[1][1]>0)&(P[2][1]>0)
    out=[]
    for b in ('fina','mitjana'):
        out.append(' '.join(f'{corr(P[a][0][b], P[c][0][b], m):+.2f}' for a,c in ((0,1),(2,1),(0,2))))
    print(f'{j:2d} {EXPO[j]:.5f} | {out[0]} | {out[1]} | {rob(P[1][0]["fina"][m]):.3f} | {rob(P[1][0]["mitjana"][m]):.3f}')
