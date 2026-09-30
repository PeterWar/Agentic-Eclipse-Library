"""d6 (V98) · Compara dues linealitzades arran del limbe: (1) perfil de ln G per distància al limbe de presentació i sector (clots/anells) i
(2) retalls del pas alt (ln G − gauss σ 6, estirat igual) a 4:1 als llocs de les marques de Pere (dalt, dreta, esquerra, baix).
Ús: d6_compara_lineal.py <linA> <linB> <prefix_sortida>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
A, B, pref = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
QA, QB = (np.load(sys.argv[4]), np.load(sys.argv[5])) if len(sys.argv) > 5 else (None, None)   # npz de franja (domini de la caixa) per a A i B
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
box = (4800, 3200, 5960, 4360); x0, y0, x1, y1 = box
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
def domini(Q):
    if Q is None: return None
    by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; return np.asarray(Q['domini'][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0])
def carrega(p, Q=None):
    g = np.load(p / 'base_G.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32); ok = np.isfinite(g) & (g > 0)
    Dm = domini(Q); ok = ok & (Dm & (d >= 0)) if Dm is not None else ok
    l = np.where(ok, np.log(np.maximum(g, 1e-6)), 0).astype(np.float32); w = ok.astype(np.float32)
    hp = l - cv2.GaussianBlur(l, (0, 0), 6) / np.maximum(cv2.GaussianBlur(w, (0, 0), 6), 1e-6); return l, np.where(ok, hp, 0), ok
lA, hA, okA = carrega(A, QA); lB, hB, okB = carrega(B, QB)
nb = np.floor(d / 0.5).astype(int)
out = {}
for a0 in range(0, 360, 30):
    s = ((th - a0) % 360) < 30
    row = {}
    for nom, l, ok in (('A', lA, okA), ('B', lB, okB)):
        k = s & ok & (d >= -10) & (d < 30); c = np.bincount(nb[k] + 20, weights=l[k], minlength=80); n = np.bincount(nb[k] + 20, minlength=80)
        row[nom] = [None if n[i] < 30 else round(float(c[i] / n[i]), 3) for i in range(80)]
    out[f'{a0}-{a0+30}'] = row
Path(pref + '_perfils.json').write_text(json.dumps(dict(d_calaixos=[-10 + 0.5 * i + 0.25 for i in range(80)], sectors=out)))
s = np.percentile(np.abs(hB[okB & (d > 20) & (d < 60)]), 99)
for nom, (cx0, cy0, cx1, cy1) in dict(dalt=(5300, 3240, 5460, 3330), dreta=(5790, 3700, 5870, 3860), esquerra=(4905, 3600, 4985, 3760), baix=(5300, 4215, 5460, 4305), dalt_dreta=(5600, 3330, 5720, 3450)).items():
    pa = hA[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]; pb = hB[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    ma = okA[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]; mb = okB[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    def u8(p, m): v = np.clip(0.5 + 0.5 * p / s, 0, 1); v[~m] = 0.25; return cv2.resize((v * 255).astype(np.uint8), None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    sep = np.full((u8(pa, ma).shape[0], 12), 255, np.uint8); cv2.imwrite(f'{pref}_{nom}.png', np.hstack([u8(pa, ma), sep, u8(pb, mb)]))
print('fet', pref)
