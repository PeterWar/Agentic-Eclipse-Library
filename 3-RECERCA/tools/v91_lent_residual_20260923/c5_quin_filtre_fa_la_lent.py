"""c5 · Quin filtre porta la lent que queda (zones roses de la V90: 0–32°, 45–98°, 230–305°). Compost EMULAT (sense capes d'ajust) de la
V91 de Pere (00:14) a la caixa de la Lluna, amb totes les capes visibles i traient-ne una cada vegada; índex de lent de c1 per sector.
Sortida: C5_ATRIBUCIO.json."""
from pathlib import Path
import json, sys, time
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
from psb69 import PSB
from vm_compost import comp, capa_box
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]
cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; near = (DS >= 2.5) & (DS <= 10); far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
SECT = {'rosa_0_32': [(0, 32), (352, 360)], 'rosa_45_98': [(45, 98)], 'rosa_230_305': [(230, 305)], 'esquerra_120_220': [(120, 220)]}
def index(C):
    Y = 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]; P = cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR)
    T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    W = int(5 / DT); f = lambda E, m: uniform_filter1d(E[m].mean(0), W, mode='wrap'); L = (f(Ed, far) / f(Es, far)) / (f(Ed, near) / f(Es, near))
    return {k: round(float(np.mean(np.concatenate([L[(t >= a) & (t < b)] for a, b in v]))), 2) for k, v in SECT.items()}
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244)]
print('capes visibles (de baix a dalt):', vis, flush=True); CAPES = {i: capa_box(p, i, BX) for i in vis}
rep = {'totes': index(comp([CAPES[i] for i in vis], H_, W_)[0])}; print('totes', rep['totes'], flush=True)
FIL = [41, 42, 47, 49, 51, 45, 46, 55, 56]
for k in FIL + ['tots_els_filtres']:
    sense = [i for i in vis if (i not in FIL if k == 'tots_els_filtres' else i != k)]
    rep[f'sense_{k}'] = index(comp([CAPES[i] for i in sense], H_, W_)[0]); print(f'sense {k} ({p.layer(k)["name"][:28] if k != "tots_els_filtres" else ""})', rep[f'sense_{k}'], flush=True)
(SORT / 'C5_ATRIBUCIO.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
