"""a2 · per escala de la WOW bilateral: energia fina de g·w i relació ⟨wave²⟩ al llarg de l'arc / potència isòtropa (nconv) a la mateixa d."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
nom = sys.argv[1] if len(sys.argv) > 1 else 'base_iso'
D = np.load(OUT / nom / 'DIAG_ESCALES.npz'); S = Estat(E / 'estat_v103'); al = S.dada(56, BOXL); dom = pol((al > 0).astype(np.float32))
def fa(A, s): p = pol(A); hp = p - gaussian_filter1d(p, 3, axis=1, mode='wrap'); return np.std(hp[:, s], axis=1)
for nm in (sys.argv[2:] or ['dalt']):
    s = sec(nm); print('##', nm, nom)
    cols = {}
    for k in range(8):
        cols[f'E{k}'] = fa(D[f'gw{k}'].astype(np.float32), s)
    for k in range(3):
        w2 = pol(D[f'wave{k}'] ** 2); p = pol(D[f'pot{k}']); cols[f'r{k}'] = (w2[:, s].mean(1) / np.maximum(p[:, s].mean(1), 1e-30))
    print('    d  ' + ' '.join(f'{k:>6}' for k in cols) + '   (Ek = energia fina de g·w a l\'escala k; rk = ⟨wave²⟩_arc / ⟨pot⟩_arc)')
    for i, d in enumerate(DG):
        if d < 1 or d > 14: continue
        print(f'{d:6.2f} ' + ' '.join(f'{cols[k][i]:6.3f}' for k in cols))
