"""j11 (V97) · Rebut del cost de la finestra LDIC comuna: soroll (MAD del pas alt σ1,2 en ln) i nivell per canal i per anell de R☉,
apilat Vixen amb finestra comuna contra finestra per canal (la mateixa calibració i els mateixos fotogrames). Ús: j11_soroll_finestra.py <canal.npy> <comuna.npy> <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import *
A = np.load(sys.argv[1], mmap_mode='r'); B = np.load(sys.argv[2], mmap_mode='r'); out = {}
box = (int(SOL[0] - 2600), max(int(SOL[1] - 2600), 0), int(SOL[0] + 2600), min(int(SOL[1] + 2600), H)); x0, y0, x1, y1 = box
rs = radi_sol(box); dl = dist_limbe(box)
for c, nom in ((0, 'R'), (1, 'G'), (2, 'B')):
    a = np.asarray(A[y0:y1, x0:x1, c], np.float32); b = np.asarray(B[y0:y1, x0:x1, c], np.float32); ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    la = np.log(np.where(ok, a, 1)); lb = np.log(np.where(ok, b, 1)); na = la - cv2.GaussianBlur(la, (0, 0), 1.2); nb = lb - cv2.GaussianBlur(lb, (0, 0), 1.2); out[nom] = {}
    for r0, r1 in ((1.03, 1.1), (1.1, 1.3), (1.3, 1.6), (1.6, 2.0), (2.0, 3.0), (3.0, 5.0)):
        m = ok & (rs >= r0) & (rs < r1) & (dl > 8); sa = 1.4826 * np.median(np.abs(na[m])); sb = 1.4826 * np.median(np.abs(nb[m]))
        out[nom][f'{r0}-{r1}'] = dict(soroll_comuna_sobre_canal=float(sb / sa), nivell_ln_comuna_menys_canal=float(np.median((lb - la)[m])))
desa(sys.argv[3], dict(canal=sys.argv[1], comuna=sys.argv[2], nota='el pas alt σ1,2 inclou una mica de senyal fi: és una cota del soroll, no el soroll pur', resultats=out)); print(json.dumps(out, indent=0)[:1500])
