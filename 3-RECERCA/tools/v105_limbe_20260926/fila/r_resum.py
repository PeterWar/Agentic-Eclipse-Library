"""r_resum · taula resum de totes les variants (MESURA.json, VOLTANT.json, M_PUNTS.json) → RESUM_FILA.json i text."""
import sys, json; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import OUT, desa
V = sys.argv[1:]; P = json.loads((OUT / 'M_PUNTS.json').read_text()); R = {}
for v in V:
    M = json.loads((OUT / v / 'MESURA.json').read_text()); T = json.loads((OUT / v / 'VOLTANT.json').read_text())
    R[v] = dict(ratio={k: M[k]['ratio'] for k in ('dalt', 'dalt_esq', 'baix_esq')}, anell_sector={k: M[k]['anell_max_pct'] for k in ('dalt', 'dalt_esq', 'baix_esq')},
                anell_pitjor_10graus=T['pitjor_anell_pct'], sectors_10graus_sobre_05=T['sectors_anell_sobre_05'], lupa_dalt=M['dalt']['lupa_escales_banda_sobre_fora'],
                punts_foscos={k: (P[v][k]['foscos_franja'], P[v][k]['foscos_fora']) for k in ('dalt', 'dalt_esq', 'baix_esq')}, fora=M['fora'])
    r = R[v]; print(f"{v:14s} ràtio {r['ratio']['dalt']:.2f}/{r['ratio']['dalt_esq']:.2f}/{r['ratio']['baix_esq']:.2f} · anell sect {max(r['anell_sector'].values()):.2f} % · pitjor 10° {r['anell_pitjor_10graus']:.2f} % · punts dalt {r['punts_foscos']['dalt'][0]:.2f}/{r['punts_foscos']['dalt'][1]:.2f} % · fora 12-40 rms {r['fora']['12-40']['rms_pct']:.3f} % 40-200 màx {r['fora']['40-200']['max_pct']:.3f} %")
R['V104_referencia'] = dict(punts_foscos={k: (P['V104'][k]['foscos_franja'], P['V104'][k]['foscos_fora']) for k in ('dalt', 'dalt_esq', 'baix_esq')})
desa(OUT / 'RESUM_FILA.json', R)
