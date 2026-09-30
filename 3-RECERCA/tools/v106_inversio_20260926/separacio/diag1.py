import numpy as np
from inversio import Inversio
sig = dict(np.load('SIG.npz')); I = Inversio(sig_tab=sig, verbose=False)
fr = [j for j in range(I.S.nF) if sig['sig'][j].min() < 0.5]
I.prepara(fr); I.construeix(fr); C = I.resol()
z = np.load('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v105_limbe_20260926/claude/t2/DELTA_sigc32.npz'); c1 = z['delta']; P1 = z['pes']
dg = I.S.dg; dth = I.S.dth; i4 = I.S.i4
for lo, hi in [(200,220),(220,240),(240,260)]:
    s = (dth >= lo) & (dth < hi)
    for d in [1,2,3,4]:
        i = int(np.argmin(abs(dg-d))); ic = i - i4
        m1 = s & (P1[ic] > 0); 
        print(f'{lo}-{hi} d{d}: c1 rms {np.sqrt(np.mean(c1[ic][m1]**2)) if m1.any() else np.nan:.4f} (n {m1.sum()}) | C rms {np.sqrt(np.mean(C[i][s & (I.Wt.reshape(C.shape)[i]>0)]**2)):.4f}')
        # per fotograma: δ i Λ i residu
        out = []
        for j in fr:
            c = I.cache[j]; ok = c['ok'][i] & s
            if ok.sum() < 50: continue
            lamv = I.avalua_lam(c['a'][i][ok], c['D'][i][ok]); r = c['d'][i][ok] - C[i][ok] - lamv
            out.append(f"{j}:D{np.median(c['D'][i][ok]):.1f} δ{np.std(c['d'][i][ok]):.3f} Λ{np.std(lamv):.3f} r{np.std(r):.3f}")
        print('   ', ' '.join(out[:40]))
