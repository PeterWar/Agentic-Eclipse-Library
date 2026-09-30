"""Mapa de diferències entre dos renders natius (TIFF RGB16): log L(B) − log L(A), en blocs 6×6, i estadístiques per zones
(disc lunar, limbe 0–40 px, corona interior 40–500 px, 1–3 R, >3 R, marques 412, màscara 234). Ús: v1_diferencia.py A.tif B.tif SORTIDA_prefix"""
import sys, json
from pathlib import Path
import numpy as np, tifffile
from scipy import ndimage as ndi
from PIL import Image
R = Path(__file__).resolve().parents[3]; C = R / '4-RESULTATS/v112_20260928'
A = tifffile.memmap(sys.argv[1]); Bm = tifffile.memmap(sys.argv[2]); out = sys.argv[3]
H, W = A.shape[:2]; cx, cy, Rl = 5375.786804312011, 3775.9774911631, 452.9785129274736
res = {}; B = 6; h, w = H // B, W // B
Lb = {}
for nm, im in (('A', A), ('B', Bm)):
    L = np.zeros((h, w)); 
    for c, k in ((0, 1), (1, 2), (2, 1)):
        L += k * np.asarray(im[:h*B, :w*B, c], np.float64).reshape(h, B, w, B).mean((1, 3))
    Lb[nm] = L / 4
val = (Lb['A'] > 300) & (Lb['B'] > 300)
d = np.where(val, np.log(np.maximum(Lb['B'], 1)) - np.log(np.maximum(Lb['A'], 1)), 0)
np.save(out + '_dlog.npy', d.astype(np.float32))
s = 0.05
g = np.clip((d / s + 1) * 127.5, 0, 255).astype(np.uint8); g[~val] = 0
Image.fromarray(g).save(out + '_dlog_pm5pct.png')
# estadístiques a resolució completa per franges (per files, per no carregar tot)
yy, xx = np.mgrid[0:h, 0:w]; rr = np.hypot(xx*B + B/2 - cx, yy*B + B/2 - cy) / Rl
zones = {'disc': rr < 0.98, 'limbe_0_40px': (rr >= 1) & (rr < 1 + 40/Rl), 'r_1_09_2': (rr >= 1 + 40/Rl) & (rr < 2),
         'r_2_3': (rr >= 2) & (rr < 3), 'r_3_6': (rr >= 3) & (rr < 6), 'r_6_mes': rr >= 6}
for k, m in zones.items():
    v = d[m & val]
    res[k] = dict(n_blocs=int(v.size), mediana=float(np.median(v)), p01=float(np.percentile(v, 1)), p99=float(np.percentile(v, 99)), abs_p99=float(np.percentile(np.abs(v), 99)))
Path(out + '_zones.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
