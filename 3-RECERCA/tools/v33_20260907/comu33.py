"""V33 · rutes i utilitats. Base: la fusió lineal V32 (no es toca). Només canvien els filtres."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907'))
from comu32 import *            # H, W, CX, CY, RS, coords, gauss, normgauss, CAUF, CAU32, V31P, sha, log, savejson, smooth
import f3
HERE33 = Path(__file__).resolve().parent
CAU33 = HERE33 / 'cau'; OUT33 = ROOT / 'output/v33_20260907'; VIS33 = OUT33 / 'lliurables/vistes'; REB33 = OUT33 / '4-rebuts'
IAOUT33 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v33_20260907')
for p in (CAU33, VIS33, REB33, IAOUT33):
    p.mkdir(parents=True, exist_ok=True)
T_SN = 0.18          # norma de Pere (27-08): el soroll blanc residual queda a t vegades l'estructura
SMAX = 32.0          # σ màxima declarada (px) allà on només hi ha gra (snmap)


sys.path.insert(0, str(HERE33)); from snmap import sn_v33, SMAX as SMAX_SN   # σ = max(mapa C0 λ/8, autocalibrada local)


def sigma_profile(sig, m, r):
    rows = []
    for a in (1.1, 1.3, 1.5, 1.7, 2.0, 2.3, 2.65, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 11.0):
        k = m & (r >= a * RS) & (r < (a + 0.3) * RS)
        rows.append({'r': a, 'sigma_p50': float(np.median(sig[k])) if k.sum() > 100 else None, 'sigma_p90': float(np.percentile(sig[k], 90)) if k.sum() > 100 else None, 'frac_smax': float(np.mean(sig[k] >= SMAX - 1e-3)) if k.sum() > 100 else None})
    return rows
