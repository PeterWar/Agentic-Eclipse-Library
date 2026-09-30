import numpy as np, time
from inversio import Inversio
t0 = time.time()
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig)
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
I.prepara(fr); print('prepara', time.time() - t0, flush=True)
I.construeix(fr); print('construeix', time.time() - t0, flush=True)
C = I.resol(); print('resol', time.time() - t0, flush=True)
lam = I.Lam(); dD = I.D0 + I.dD * np.arange(I.nD)
for k in range(I.nD): print(f'D {dD[k]:.2f}: rms Λ {np.sqrt(np.mean(lam[k][I.lam_obs[k]]**2)):.4f}  observats {I.lam_obs[k].mean():.2f}')
dg = I.S.dg; dth = I.S.dth; Wt = I.Wt.reshape(C.shape)
for lo, hi in [(60,100),(100,140),(200,240),(240,280),(280,320)]:
    s = (dth >= lo) & (dth < hi)
    print(lo, hi, ' '.join(f'd{d:g}:{np.sqrt(np.mean(C[int(np.argmin(abs(dg-d)))][s & (Wt[int(np.argmin(abs(dg-d)))]>0)]**2)):.4f}' for d in [-2,0,0.5,1,1.5,2,3,4,6,10]))
np.save('C_prova.npy', C.astype(np.float32)); np.save('LAM_prova.npy', lam.astype(np.float32))
