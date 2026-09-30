import numpy as np
from e2_repro import treu_harm, HARM2, gsm, bandes, corr
Z = np.load('E1_VORES.npz'); U = Z['u0']; th = Z['theta']; thr = np.radians(th)
Hm = np.stack([np.ones_like(thr), np.cos(thr), np.sin(thr), np.cos(2*thr), np.sin(2*thr)], 1)
rows = []
for j in range(U.shape[1]):
    if np.isfinite(U[1, j]).sum() < 1000: continue
    cs = []
    for c in range(3):
        u = U[c, j]; ok = np.isfinite(u)
        cf, *_ = np.linalg.lstsq(Hm[ok], u[ok], rcond=None); cs.append(cf)
    cs = np.array(cs); rows.append((j, cs[0] - cs[1], cs[2] - cs[1]))
R_G = np.array([r[1] for r in rows]); B_G = np.array([r[2] for r in rows])
print('R − G (a0, cos, sin, cos2, sin2): mediana', np.round(np.median(R_G, 0), 3), ' dispersió', np.round(1.4826*np.median(np.abs(R_G - np.median(R_G,0)),0), 3))
print('B − G                          : mediana', np.round(np.median(B_G, 0), 3), ' dispersió', np.round(1.4826*np.median(np.abs(B_G - np.median(B_G,0)),0), 3))
# relleu fi per canal: correlació de la mitjana de tots els fotogrames R vs G vs B (banda mitjana)
M = []
for c in range(3):
    S = np.zeros(th.size); W = np.zeros(th.size)
    for j in range(U.shape[1]):
        u = U[c, j]; ok = np.isfinite(u)
        if ok.sum() < 1000: continue
        r, _ = treu_harm(np.nan_to_num(u), ok.astype(float)); S += np.where(ok, r, 0); W += ok
    M.append(np.where(W > 0, S / np.maximum(W, 1), 0))
w = np.ones(th.size)
B = [bandes(m, w) for m in M]
for b in ('gran', 'mitjana', 'fina'):
    print(b, 'ρ R–G', round(corr(B[0][b], B[1][b], w > 0), 3), 'B–G', round(corr(B[2][b], B[1][b], w > 0), 3), 'rms', [round(np.std(B[c][b]), 3) for c in range(3)])
