"""t3 · Quina escala fa la vall de nivell a 20–40 px (t2): contribució mitjana de cada escala per distància al limbe, abans i després de fer-la
de mitjana nul·la, a la caixa de la Lluna."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v95_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_completesa import conv_pla, nconv, b3conv, smoothstep, ng_pes
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85 / 'd4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(FONTS / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
sy, sx = slice(qy0 - by0, qy1 - by0), slice(qx0 - bx0, qx1 - bx0); a[sy, sx] = Q['G']; m[sy, sx] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; BINS = [(1, 5), (5, 10), (10, 20), (20, 30), (30, 45), (45, 70), (70, 110), (110, 160), (160, 250), (300, 600)]
c = np.where(m, a, 0).astype(np.float32); mf = m.astype(np.float32); k = 0.0233
for s in range(8):
    nxt, _ = conv_pla(c, m, s, True); nxt = np.where(m, nxt, 0).astype(np.float32); wave = np.where(m, c - nxt, 0).astype(np.float32)
    amp = np.sqrt(np.maximum(nconv(wave * wave, m, s), 1e-20)); g = np.where(m, wave / amp, 0).astype(np.float32)
    w = (smoothstep(b3conv(mf, s), 0.45 + 0.05 * s, 0.75 + 0.03 * s) * mf).astype(np.float32); gn = g - ng_pes(g, w, max(8.0, 4.0 * 2 ** s))
    row = lambda X: [round(float(k * (X * w)[m & (d >= b0) & (d < b1)].mean()), 4) for b0, b1 in BINS]
    print(f'escala {s}: brut ', row(g), '\n          neutre', row(gn), flush=True); c = nxt
print('bins d:', BINS)
