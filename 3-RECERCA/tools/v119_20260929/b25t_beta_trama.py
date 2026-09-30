"""b25t (V119, 29-09-2026) · κ(r) de la TRAMA: el β del b9 (pendent del detall tangencial del compost de la V115 contra la trama de tres
testimonis), només als anells on és fiable: r < 3,6 R☉ i β > 0. Més enfora la trama és feble (rms < 0,2 %) i el detall tangencial del compost
hi és dominat pels anells del seu processat (els testimonis no els confirmen): el pendent salta (−1,2 a 10). Aquests anells, sense dada (null):
el b3t hi manté el darrer valor fiable. L'original queda a BETA_V115_brut.json. Ús: b25t_beta_trama.py <carpeta_b9>"""
import sys, json, shutil
from pathlib import Path
B9 = Path(sys.argv[1]).resolve()
if not (B9 / 'BETA_V115_brut.json').exists(): shutil.copy(B9 / 'BETA_V115.json', B9 / 'BETA_V115_brut.json')
b = json.load(open(B9 / 'BETA_V115_brut.json'))
beta = [v if (v is not None and v > 0 and r < 3.6) else None for r, v in zip(b['r_centres'], b['beta'])]
json.dump(dict(r_centres=b['r_centres'], beta=beta, beta_brut=b['beta'], nota='β de la trama; null a r ≥ 3,6 R☉ o β ≤ 0 (el b3t hi manté el darrer valor fiable)'),
          open(B9 / 'BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
print(' '.join(f'{r:.1f}:{("—" if v is None else f"{v:.2f}")}' for r, v in zip(b['r_centres'], beta)))
