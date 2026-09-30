import numpy as np, sys, json
from inversio import Inversio
from proves import m1, taula
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig, verbose=False, DMAX=float(sys.argv[1]) if len(sys.argv) > 1 else 4.0)
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
i4 = I.S.i4; dg = I.S.dg[i4:]; nth = I.S.nth
A = [j for j in fr if j <= 10]; B = [j for j in fr if 13 <= j <= 18]
def avalua(tag):
    cA = I.S.C0[A].mean(0) + I.dxy[A].mean(0); cB = I.S.C0[B].mean(0) + I.dxy[B].mean(0)
    hA, pA = I.grup(A); hB, pB = I.grup(B)
    r = m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB); print('---', tag); print(taula(r))
    # residu ponderat a la vora
    L = I.L; res = L['y'] - I.C.ravel()[L['p']] - I.pred_lun
    print('   χ² reduït a la vora:', round(float(np.mean(L['w'] * res ** 2)), 2))
for it in range(4):
    I.prepara(fr); I.construeix(fr); I.resol()
    avalua(f'iteració {it}')
    amp = it >= 2
    out = I.autocalibra(amplitud=amp)
    print('   desplaçaments:', ' '.join(f'{j}:{v[0]:+.2f},{v[1]:+.2f}' + (f',A{v[2]:.2f}' if amp else '') for j, v in out.items()))
I.prepara(fr); I.construeix(fr); I.resol(); avalua('final')
np.savez('AUTOCAL.npz', dxy=I.dxy, A=I.A)
