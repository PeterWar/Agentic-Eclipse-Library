"""c3 · L'octàgon de les marques de Pere a l'ACHF 01 (capa 50): ràster del filtre a 1:2 a la caixa de 1800 px al voltant de la Lluna, el mapa de resolució σ
(nivells), el domini dels filtres (suport fora de la caixa A3A, domini A3A dins) i les marques. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
V85D = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85D / 'd4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 900; y0, x0 = int(cy) - B, int(cx) - B; sl = (slice(y0, y0 + 2 * B), slice(x0, x0 + 2 * B))
sig = np.asarray(np.load(V85D / 'fixed_inputs/resolution_sigma.npy', mmap_mode='r')[sl], np.float32)
sup = np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[sl]); dom = sup.copy(); dom[qy0 - y0:qy1 - y0, qx0 - x0:qx1 - x0] = Q['domini']
print('σ a la caixa: mín', round(float(sig.min()), 2), 'màx', round(float(sig.max()), 2)); print('suport ≠ domini dins la caixa (px):', int((sup[qy0 - y0:qy1 - y0, qx0 - x0:qx1 - x0] != Q['domini']).sum()))
yy, xx = np.mgrid[y0:y0 + 2 * B, x0:x0 + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R
for dd in (100, 200, 250, 300, 350, 400, 450, 500): print(f'  σ a d {dd}: {np.round(np.percentile(sig[np.abs(d - dd) < 2], (5, 50, 95)), 2).tolist()}')
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); X = p.channel(50, 0)[0][sl].astype(np.float32) / 65535
Z = np.load(SORT / 'marques.npz'); mk = np.zeros((7506, 10551), bool); ox, oy = Z['283_origen']; g = Z['283_to_50_60']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] = g; mk = mk[sl]
def vista(A, lo, hi): return np.stack([np.uint8(np.clip((A - lo) / (hi - lo), 0, 1) * 255)] * 3, -1)
a1 = vista(X, *np.percentile(X, (1, 99))); a2 = cv2.applyColorMap(np.uint8(np.clip((sig - sig.min()) / (np.percentile(sig, 99) - sig.min() + 1e-6), 0, 1) * 255), cv2.COLORMAP_VIRIDIS)[..., ::-1].copy()
L = cv2.GaussianBlur(X, (0, 0), 12); a3 = vista(L - cv2.GaussianBlur(X, (0, 0), 60), -0.02, 0.02)   # nivell a mida mitjana (12–60 px)
for im in (a1, a2, a3):
    cs, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(im, cs, -1, (255, 200, 0), 3)
    cv2.rectangle(im, (qx0 - x0, qy0 - y0), (qx1 - x0, qy1 - y0), (255, 255, 255), 2)
    for lv in (1.0, 1.5, 2.0, 3.0): c2, _ = cv2.findContours((sig >= lv).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); cv2.drawContours(im, c2, -1, (255, 0, 255), 1)
out = Image.new('RGB', (3 * 900 + 16, 900 + 34), 'white'); dr = ImageDraw.Draw(out); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 17)
for i, (im, t) in enumerate(((a1, 'ACHF 01 (capa 50) · ràster'), (a2, 'mapa de resolució σ (fixed_inputs/resolution_sigma)'), (a3, 'ACHF 01 · nivell a 12–60 px (±2 %)'))):
    out.paste(Image.fromarray(cv2.resize(im, (900, 900), interpolation=cv2.INTER_AREA)), (i * 908, 34)); dr.text((i * 908 + 6, 8), t + ' · marques de Pere (groc), caixa A3A (blanc), σ ≥1/1,5/2/3 (magenta) · 1:2', fill='black', font=F)
out.save(SORT / 'OCTAGON_ACHF01.png'); print('fet')
