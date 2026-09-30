"""x7 (verificador adversari, 27-09) · Retalls a resolució plena (pas 1) de V107 | V108 | ln(V108/V107) ±15 % a les zones on el mapa del
genoll té vores marcades: la «lent» de la dreta (~−20°, 3–4,3 R☉), la de l'esquerra (~200°) i la «muntanya» de sota la Lluna (sud).
Estirament: el mateix per a V107 i V108 (percentils de la V107 al retall), sobre ln L menys el seu fons σ200 (per veure l'estructura).
Sortida: vistes/X7_<nom>.png"""
from pathlib import Path
import numpy as np, cv2
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026'); O = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; CO = O / 'composts'
L7 = np.load(CO / 'L_V107.npy', mmap_mode='r'); L8 = np.load(CO / 'L_V108.npy', mmap_mode='r')
def div(v, s):
    v = np.clip(v / s, -1, 1); return (np.stack([np.clip(1 - np.maximum(v, 0), 0, 1), 1 - np.abs(v), np.clip(1 + np.minimum(v, 0), 0, 1)], -1) * 255).astype(np.uint8)
for nom, (x0, y0, x1, y1) in {'lent_dreta': (6300, 3900, 7700, 4800), 'lent_esquerra': (3000, 4000, 4400, 4900), 'sud_muntanya': (4200, 4200, 6600, 5600)}.items():
    a7 = np.log(np.maximum(np.asarray(L7[y0:y1, x0:x1], np.float32), 1e-4)); a8 = np.log(np.maximum(np.asarray(L8[y0:y1, x0:x1], np.float32), 1e-4))
    # estirament global (el mateix per a les dues), sense treure fons: el que veuria Pere
    lo, hi = np.percentile(a7, [1, 99.5]); g = lambda l: cv2.cvtColor((np.clip((l - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    # i cada una amb el seu propi estirament
    def own(l):
        lo_, hi_ = np.percentile(l, [1, 99.5]); return cv2.cvtColor((np.clip((l - lo_) / (hi_ - lo_), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    sep = np.full((a7.shape[0], 12, 3), 255, np.uint8)
    top = np.concatenate([g(a7), sep, g(a8), sep, div(a8 - a7, 0.15)], 1); bot = np.concatenate([own(a7), sep, own(a8), sep, div(cv2.GaussianBlur(a8 - a7, (0, 0), 1) - cv2.GaussianBlur(a8 - a7, (0, 0), 20), 0.03)], 1)
    cv2.imwrite(str(O / 'vistes' / f'X7_{nom}.png'), np.concatenate([top, np.full((12, top.shape[1], 3), 255, np.uint8), bot], 0))
print('fet')
