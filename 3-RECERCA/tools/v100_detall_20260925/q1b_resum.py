"""q1b · resum llegible de dada/Q1_MEITATS.json (taules per sector i calaix). Sortida: dada/Q1_resum.txt"""
import json, sys
from pathlib import Path
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'
R = json.loads((O / 'Q1_MEITATS.json').read_text())['resultats']; SORT = O / 'Q1_resum.txt'; assert not SORT.exists()
L = []
for x in R:
    n = x['nul'] or dict(r_mitjana=float('nan'), r_sd=float('nan'))
    L.append(f"r{x['rampa']} {x['meitats']:>14} {x['hp']} σ{x['sigma']} PA{x['sector']} {x['calaix']:>9} {x['rang'][0]:>4}-{x['rang'][1]:<5} n{x['n']:>6} "
             f"r {x['r']:+.3f} (nul {n['r_mitjana']:+.3f}±{n['r_sd']:.3f}, z {x.get('z', float('nan')):6.1f}) detall {x['rms_detall_pc']:.2f}% "
             f"soroll_apilat {x['rms_soroll_apilat_pc']:.2f}% S/N_apilat {x['sn_apilat']:.2f}")
SORT.write_text('\n'.join(L)); print(len(L), 'files')
