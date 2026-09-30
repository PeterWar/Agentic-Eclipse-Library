"""a1 · perfils radials a dalt/dalt-esq/baix-esq: pesos del règim de banda i net, soroll fi de la linealitzada i energia fina de les capes 51 i 56."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
Q = np.load(FR)
def fin_lin(A, s):   # energia fina (1–3 px d'arc) de ln A (A > 0) al sector
    p = pol(A); lp = np.log(np.maximum(p, 1e-12)); hp = lp - gaussian_filter1d(lp, 3, axis=1, mode='wrap'); return np.std(hp[:, s], axis=1)
def fin_abs(A, s):
    p = pol(A); hp = p - gaussian_filter1d(p, 3, axis=1, mode='wrap'); return np.std(hp[:, s], axis=1)
S = Estat(E / 'estat_v103')
L56 = S.rgb(56, BOXL); L51 = S.rgb(51, BOXL); A56 = S.dada(56, BOXL); A51 = S.dada(51, BOXL)
G = Q['G'].astype(np.float32); Fl = Q['F']; Lm = (Fl[..., 0] + 2 * Fl[..., 1] + Fl[..., 2]) / 4
dom = Q['domini'].astype(np.float32)
for nm in ['dalt', 'dalt_esq', 'baix_esq']:
    s = sec(nm); print(f'## {nm}  DMIN mitjà {np.mean(Q["DMIN"][((np.arange(1440)/4 >= SECTORS[nm][0]) & (np.arange(1440)/4 < SECTORS[nm][1]))]):.2f}')
    cols = dict(dom=pol(dom)[:, s].mean(1), Wnet=pol(Q['W_net'])[:, s].mean(1), Wb=pol(Q['W_banda'])[:, s].mean(1), porta=pol(Q['porta_banda'])[:, s].mean(1),
                NEFFb=pol(Q['NEFF_banda'])[:, s].mean(1), NCLEAN=pol(Q['NCLEAN'])[:, s].mean(1), NF=pol(Q['NF'].astype(np.float32))[:, s].mean(1),
                fG=fin_lin(G, s), fL=fin_lin(Lm, s), f56=fin_abs(L56, s), f51=fin_abs(L51, s), a56=pol(A56)[:, s].mean(1), a51=pol(A51)[:, s].mean(1))
    print('    d  ' + ' '.join(f'{k:>7}' for k in cols))
    for i, d in enumerate(DG):
        if d < -0.5 or d > 12: continue
        print(f'{d:6.2f} ' + ' '.join(f'{cols[k][i]:7.4f}' if cols[k][i] < 100 else f'{cols[k][i]:7.1f}' for k in cols))
