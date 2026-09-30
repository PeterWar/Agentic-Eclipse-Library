"""c8 · Marques lila de Pere a la WOW V95 (capa 270 sobre la 56): on s'engeguen les escales gruixudes (pes de completesa de wow_v95) i com canvia el contrast
del ràster amb la distància, als azimuts de les marques. Caixa de 2400 px al voltant de la Lluna, paràmetres finals de la V95. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924')); from wow_v95 import wow_v95, desplacament_cresta, dmap_vora
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(V85 / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(V85 / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
a[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['G']; m[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yb, xb = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xb - cx, yb - cy) - R).astype(np.float32); th = (np.degrees(np.arctan2(-(yb - cy), xb - cx)) + 360) % 360
off, _ = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dm = dmap_vora(d, xb, yb, cx, cy, off)
W1 = json.loads((ARREL / '4-RESULTATS/v95_20260924/W1_WOW.json').read_text())['capes']['P05_WOW_bilateral']; SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s))
_, pesos, _ = wow_v95(a, m, dm, 8, True, log=lambda *x: None, mus=W1['mitjanes_escala'], centra_rad=True, iso=(0.5, 1.5), sig_rad=SIG)
X = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')).channel(56, 0)[0][by0:by1, bx0:bx1].astype(np.float32) / 65535
bp = lambda Y, s1, s2: cv2.GaussianBlur(Y, (0, 0), s1) - cv2.GaussianBlur(Y, (0, 0), s2)
E = {'8-32': bp(X, 8, 32) ** 2, '32-96': bp(X, 32, 96) ** 2}
DD = list(range(40, 200, 10))
for s0, s1, et in ((65, 106, 'marca lila dalt (d 130–154)'), (233, 262, 'marques lila baix (d 79–88 i 141–156)'), (300, 340, 'control sense marca')):
    sel = m & (th >= s0) & (th < s1); print(f'--- {s0}-{s1}° · {et}')
    for s in (4, 5, 6): print(f'   pes escala {s}:', [round(float(pesos[s][sel & (np.abs(d - dd) < 3)].mean()), 2) for dd in DD])
    for k, e in E.items(): print(f'   contrast {k} px:', [round(float(np.sqrt(e[sel & (np.abs(d - dd) < 3)].mean())) * 100, 2) for dd in DD])
print('d:', DD)
