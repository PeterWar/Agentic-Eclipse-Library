import numpy as np, sys
from inversio import Inversio
from proves import m1, taula
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig, verbose=True)
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
I.prepara(fr); I.construeix(fr); C = I.resol()
i4 = I.S.i4; dg = I.S.dg[i4:]; nth = I.S.nth
A = [j for j in fr if j <= 10]; B = [j for j in fr if 13 <= j <= 18]
cA = I.S.C0[A].mean(0) + I.dxy[A].mean(0); cB = I.S.C0[B].mean(0) + I.dxy[B].mean(0)
# (1) cru (sense Λ): ha de reproduir la c1 amb pesos diferents
lam0 = I.lam.copy(); I.lam[:] = 0
hA, pA = I.grup(A); hB, pB = I.grup(B)
print('--- δ cru (pesos 1/σ², sense rampa) ---'); print(taula(m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB)))
I.lam[:] = lam0
hA, pA = I.grup(A); hB, pB = I.grup(B)
print('--- netejat amb Λ (tots els fotogrames) ---'); print(taula(m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB)))
