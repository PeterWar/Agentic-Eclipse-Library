"""c2 · Quina capa porta l'estirament radial arran del limbe (índex de lent de c1) a la V91: la base (3), cada filtre (41–56, ràster sol),
les fotos de Pere (76, 266, 96), la 224 i la Lluna (258), llegides de 1-PHOTOSHOP/V91.psb a la caixa de la Lluna. Mateix mètode que c1.
Sortida: C2_PER_CAPA.json."""
from pathlib import Path
import json, sys, time
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; BX = (4600, 3000, 6150, 4550)
cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; near = (DS >= 2.5) & (DS <= 10); far = (DS >= 16) & (DS <= 30)
def index(Y):
    P = cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR); T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    W = int(5 / DT); f = lambda E, m: uniform_filter1d(E[m].mean(0), W, mode='wrap'); L = (f(Ed, far) / f(Es, far)) / (f(Ed, near) / f(Es, near))
    amp = np.sqrt(uniform_filter1d((T[near] ** 2).mean(0), W, mode='wrap')) / np.maximum(np.sqrt(uniform_filter1d((T[far] ** 2).mean(0), W, mode='wrap')), 1e-9)
    return L, amp
sect = [(60, 100), (100, 135), (135, 228), (240, 270), (270, 300), (300, 330)]
q = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); rep = {}
for lid in [3, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 76, 266, 96, 224, 258]:
    L_ = q.layer(lid); ch = [c for c in (0, 1, 2) if c in L_['chans']]
    if not ch or L_['right'] <= L_['left']: continue
    A = np.stack([q.channel_box(lid, c, BX) for c in ch], -1).astype(np.float32) / 65535
    Y = A[..., 0] if len(ch) == 1 else 0.2126 * A[..., 0] + 0.7152 * A[..., 1] + 0.0722 * A[..., 2]
    L, amp = index(Y); t = np.arange(NT) * DT
    rep[lid] = dict(nom=L_['name'], mode=str(L_['blend']), visible=L_['visible'], opacitat=L_['opacity'],
                    index_lent={f'{a}-{b}': round(float(L[(t >= a) & (t < b)].mean()), 2) for a, b in sect},
                    amplitud_textura_prop_sobre_lluny={f'{a}-{b}': round(float(amp[(t >= a) & (t < b)].mean()), 2) for a, b in sect})
    print(lid, L_['name'][:30], L_['blend'], L_['visible'], json.dumps(rep[lid]['index_lent']), json.dumps(rep[lid]['amplitud_textura_prop_sobre_lluny']), flush=True)
(SORT / 'C2_PER_CAPA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str) + '\n')
