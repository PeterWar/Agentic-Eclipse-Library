"""r7 (V103) · Làmines 4:1 (log, mateixa escala) de la dada linealitzada G' arran del limbe: V103 (a3d) a l'esquerra, V99 (a3c) a la dreta, i el
règim net sol de la V103 al mig. Ús: r7_laminas_franja.py <A3C npz V103> <A3C npz V99> <carpeta>"""
import sys
from pathlib import Path
import numpy as np, cv2
A = np.load(sys.argv[1]); B = np.load(sys.argv[2]); O = Path(sys.argv[3]); O.mkdir(parents=True, exist_ok=True)
by0, by1, bx0, bx1 = [int(v) for v in A['box']]
EA = np.where(A['domini_E'], A['E'][..., 1], 0); EN = np.where(A['NCLEAN'] > 0.5, A['E_net'][..., 1], 0); EB = np.where(B['domini_E'], B['E'][..., 1], 0)
def crop(img, x0, y0, x1, y1): return img[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
def lam(img, lo, hi):
    l = np.log(np.maximum(img, 1e-6)); u = np.clip((l - lo) / (hi - lo), 0, 1); return np.where(img > 0, (u * 255).astype(np.uint8), 0)
caixes = {'dalt': (5150, 3290, 5600, 3400), 'dalt_esq': (4930, 3330, 5200, 3560), 'esquerra': (4900, 3650, 5060, 3900), 'baix_esq': (4930, 4000, 5250, 4240), 'baix': (5150, 4160, 5600, 4270), 'dreta': (5760, 3650, 5900, 3900)}
for nom, (x0, y0, x1, y1) in caixes.items():
    a, n, b = crop(EA, x0, y0, x1, y1), crop(EN, x0, y0, x1, y1), crop(EB, x0, y0, x1, y1); ok = b > 0; lo, hi = np.percentile(np.log(b[ok]), [1, 99.5])
    sep = np.full((a.shape[0], 4), 128, np.uint8); L = np.concatenate([lam(a, lo, hi), sep, lam(n, lo, hi), sep, lam(b, lo, hi)], axis=1)
    cv2.imwrite(str(O / f'LAM_{nom}_V103_net_V99_4a1.png'), cv2.resize(L, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))
print('fet', O)
