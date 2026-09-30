"""b25b (V118, 29-09-2026) · κ(r) de la capa nova: el β del b25 (V117) calculat contra el detall de TRES testimonis, però només als anells on el
tercer testimoni hi és. Fora del camp de la Vixen no hi ha detall de tres, i als anells on la Vixen cobreix menys del 90 % del que cobreixen A i B
la regressió surt de poques mostres i salta (a la V118: 11–53 més enllà de 6 R☉). Aquests anells es marquen sense dada (null) i el b3 hi manté el
darrer valor fiable (np.interp s'atura a l'extrem). L'original queda a BETA_V115_brut.json.
Ús: b25b_beta_fiable.py <carpeta_b5>"""
import sys, json, shutil, numpy as np
from pathlib import Path
B5 = Path(sys.argv[1]).resolve(); H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603; f = 2
if not (B5 / 'BETA_V115_brut.json').exists(): shutil.copy(B5 / 'BETA_V115.json', B5 / 'BETA_V115_brut.json')
b = json.load(open(B5 / 'BETA_V115_brut.json'))
DA = np.asarray(np.load(B5 / 'DA_f16.npy', mmap_mode='r')[::f, ::f]); D3 = np.asarray(np.load(B5 / 'D_minim_f32.npy', mmap_mode='r')[::f, ::f])
R = Path(__file__).resolve().parents[2].parent
DAB = np.asarray(np.load(R / '4-RESULTATS/v117_20260929/AB/b1/DA_f16.npy', mmap_mode='r')[::f, ::f])
yy, xx = np.mgrid[0:H:f, 0:W:f]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
cob, beta = [], []
for rc, bt in zip(b['r_centres'], b['beta']):
    k = (rr >= rc - 0.2) & (rr < rc + 0.2); c = float(np.count_nonzero(DA[k]) / max(np.count_nonzero(DAB[k]), 1)); cob.append(round(c, 3))
    beta.append(bt if (bt is not None and c >= 0.9) else None)
json.dump(dict(r_centres=b['r_centres'], beta=beta, cobertura_tres_sobre_AB=cob, beta_brut=b['beta'],
               nota='β del b25 contra el detall de tres testimonis; null on la Vixen cobreix < 90 % del que cobreixen A i B (el b3 hi manté el darrer valor fiable)'),
          open(B5 / 'BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
print(' '.join(f'{r:.1f}:{("—" if v is None else f"{v:.1f}")}({c:.2f})' for r, v, c in zip(b['r_centres'], beta, cob)))
