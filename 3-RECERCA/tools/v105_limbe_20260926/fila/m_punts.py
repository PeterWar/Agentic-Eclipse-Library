"""m_punts · mètrica directa de la filera de punts foscos: a la franja de l'inici, fracció de mostres amb pas alt fi (1–3 px d'arc) de ln L
per sota de −2,5·σ_fora (σ_fora = la del mateix sector a la finestra de fora) i percentil 1, contra la finestra de fora."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
from m_mesura import PIC, FORA, CP, L4
def hp(L): lp = np.log(np.maximum(pol(L), 1e-4)); return lp - gaussian_filter1d(lp, 3, axis=1, mode='wrap')
res = {}
for nom in ['V104'] + sys.argv[1:]:
    L = L4 if nom == 'V104' else lum(np.load(OUT / nom / 'COMP_emul.npy')); h = hp(L); res[nom] = {}
    for nm in ['dalt', 'dalt_esq', 'baix_esq']:
        s = sec(nm); ib = (DG >= PIC[nm][0]) & (DG <= PIC[nm][1]); io = (DG >= FORA[nm][0]) & (DG <= FORA[nm][1])
        hb = h[ib][:, s]; ho = h[io][:, s]; so = ho.std()
        res[nom][nm] = dict(foscos_franja=round(float((hb < -2.5 * so).mean() * 100), 2), foscos_fora=round(float((ho < -2.5 * so).mean() * 100), 2), p1_franja_sobre_fora=round(float(np.percentile(hb, 1) / np.percentile(ho, 1)), 3))
    print(f'{nom:14s} ' + ' | '.join(f"{nm}: foscos {q['foscos_franja']:.2f} % (fora {q['foscos_fora']:.2f} %) p1 {q['p1_franja_sobre_fora']:.2f}" for nm, q in res[nom].items()))
desa(OUT / 'M_PUNTS.json', res)
