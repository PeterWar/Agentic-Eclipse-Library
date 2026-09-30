"""w2 (V96) · Ràster final de la capa 41 (P01 NRGF): parteix de la 41 de la V95 i en canvia NOMÉS el ràster:
  - on hi ha dada: la NRGF V96 (w1: la V88 amb els anells interiors parcials completats);
  - al buit sense dada tocant la Lluna (decisió de Pere, 24-09: opció B): NOMÉS el nivell de la NRGF nova als primers píxels de dada (1 ≤ d − DMIN < 3)
    al llarg de l'arc (gaussiana σ 3 px d'arc), sense textura; dins del disc, rampa cap a 0,5 (−10…−4 px), com la V93;
  - la resta (fora del suport, tapat per la màscara de Pere), com a la V95.
Alfa i màscara: les de la V95 (byte a byte, al muntatge). Sortida: P01_NRGF_V96_u16.npy i W2_CAPA41.json."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from psb69 import PSB
from v86_operadors import smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); c0, c1, c2 = [p.channel(41, c)[0] for c in range(3)]; assert np.array_equal(c0, c1) and np.array_equal(c0, c2), 'la 41 no és grisa'
FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'; Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]
a = np.load(FONTS / 'base_G.npy', mmap_mode='r'); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0); m[qy0:qy1, qx0:qx1] = Q['domini'] & (Q['G'] > 0)
nou = np.load(SORT / 'P01_NRGF_u16.npy'); out = c0.copy()
yA, xA = np.ogrid[:7506, :10551]; rS = np.hypot(yA - 3775.747534140857, xA - 5361.768111973117); aprop = m & (rS < 520)   # més enllà la V96 = V88 = V95 (±1 DN d'arrodoniment): es deixa la V95 byte a byte
out[aprop] = nou[aprop]
cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NB = len(DMIN)
yy, xx = np.mgrid[qy0:qy1, qx0:qx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; dist = d - DMIN[(th / 360 * NB).astype(int) % NB]
mb = m[qy0:qy1, qx0:qx1]; ub = out[qy0:qy1, qx0:qx1].astype(np.float32) / 65535
NT = 3600; tb = (th / 360 * NT).astype(int) % NT; zona = mb & (dist >= 1) & (dist < 3)
s = np.bincount(tb[zona], weights=ub[zona], minlength=NT); n = np.bincount(tb[zona], minlength=NT).astype(float); sig = 3.0 / (R * np.radians(360 / NT))
L = (gaussian_filter1d(s, sig, mode='wrap') / np.maximum(gaussian_filter1d(n, sig, mode='wrap'), 1e-9))[tb].astype(np.float32)
buit = (~mb) & (d < 5); val = np.where(d >= -4, L, np.where(d <= -10, 0.5, L + (0.5 - L) * (1 - smoothstep(d, -10, -4))))
ub = np.where(buit, val, ub); out[qy0:qy1, qx0:qx1] = np.round(np.clip(ub, 0, 1) * 65535).astype(np.uint16)
assert not ((~mb) & (d >= 5)).any(), 'hi ha píxels sense dada lluny del limbe dins la caixa'
np.save(SORT / 'P01_NRGF_V96_u16.npy', out)
canvi = out != c0
rep = dict(px_canviats=int(canvi.sum()), r_sol_max_canvi=round(float(rS[canvi].max()), 1), px_buit_nivell=int((buit & (d >= -4)).sum()), px_dada_canviats=int((canvi & m).sum()),
           diferencia_max_lluny_r_gt_520=int(np.abs(out.astype(np.int32) - c0.astype(np.int32))[rS > 520].max()), sha256=sha(SORT / 'P01_NRGF_V96_u16.npy'))
(SORT / 'W2_CAPA41.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); print(json.dumps(rep, ensure_ascii=False))
