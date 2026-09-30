"""Pas 1: la geometria del llenç (Sol conegut; Lluna ajustada al limbe de la fusió lineal)."""
import json, numpy as np
from comu import *
from ael.geometry import fit_limb

F = np.load(LINEAL / 'fusion_starless.npy', mmap_mode='r')
S = np.load(LINEAL / 'support.npy', mmap_mode='r')
y0, y1, x0, x1 = 3100, 4460, 4700, 6060          # caixa al voltant de la Lluna
G = np.array(F[y0:y1, x0:x1, 1], np.float32)
V = np.asarray(S[y0:y1, x0:x1]).astype(bool)
G[~V] = 0.0                                        # fora del suport: fosc (només per trobar la vora)
res = fit_limb(G, (SOL[0] + 14 - x0, SOL[1] - y0), 462.0, n_rays=2880, search_frac=0.05, valid=None,
               north_deg=NORD)
lx, ly = res['xy'][0] + x0, res['xy'][1] + y0
geo = geometria_llenc((lx, ly), res['r'])
geo.to_json(RES / 'GEOMETRIA_LLENC_V120.json')
out = dict(lluna_xy=(lx, ly), r_lluna=res['r'], rms=res['rms'], n=res['n_used'],
           lluna_menys_sol=(lx - SOL[0], ly - SOL[1]), r_lluna_rsun=res['r'] / RS)
json.dump(out, open(RES / 'P1_LLUNA.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
