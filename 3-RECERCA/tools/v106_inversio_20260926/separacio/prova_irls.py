import numpy as np, sys, json
from inversio import Inversio
from proves import m1, taula
kw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig, verbose=False, **{k: v for k, v in kw.items() if k in ('DMAX', 'dphi', 'LO', 'D0')})
reg = {k: v for k, v in kw.items() if k in ('ridge', 'regD')}
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
i4 = I.S.i4; dg = I.S.dg[i4:]; nth = I.S.nth
A = [j for j in fr if j <= 10]; B = [j for j in fr if 13 <= j <= 18]
def avalua(tag):
    cA = I.S.C0[A].mean(0) + I.dxy[A].mean(0); cB = I.S.C0[B].mean(0) + I.dxy[B].mean(0)
    hA, pA = I.grup(A); hB, pB = I.grup(B)
    r = m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB); print('---', tag); print(taula(r))
    L = I.L; res = L['y'] - I.C.ravel()[L['p']] - I.pred_lun
    print('   χ² reduït a la vora:', round(float(np.mean(L['w'] * res ** 2)), 2))
I.prepara(fr)
for it in range(3):
    I.construeix(fr); I.resol(**reg); avalua(f'IRLS {it}')
    vt = I.reestima_soroll()
    if it == 0:
        for j in fr: print(j, 'σ(D):', ' '.join(f'{np.sqrt(v):.3f}' for v in vt[j]['vD']), '| σ(d):', ' '.join(f'{np.sqrt(v):.3f}' for v in vt[j]['vd'][4:14]))
np.save('C_irls.npy', I.C.astype(np.float32))
import pickle; pickle.dump(I.var_tab, open('VAR_irls.pkl', 'wb'))
