"""t13 · P04 (WOW lineal) i P05 a la caixa: centratge local a partir de l'escala 3 (com la V95 muntada) contra a TOTES les escales amb σ = max(32, 4·2^s).
Mesures: nivell per distància i sector; correlació per bandes amb la V94 lluny de la Lluna (100–600 px... 200–600)."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; S = ARREL / '4-RESULTATS/v95_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_v95 import wow_v95, desplacament_cresta, dmap_vora
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(V85 / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(V85 / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
a[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['G']; m[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yb, xb = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xb - cx, yb - cy) - R).astype(np.float32); th = (np.degrees(np.arctan2(-(yb - cy), xb - cx)) + 360) % 360
off, _ = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dm = dmap_vora(d, xb, yb, cx, cy, off)
W1 = json.loads((S / 'W1_WOW.json').read_text())['capes']; ref = m & (d > 200) & (d < 600)
band = lambda X, s1, s2: cv2.GaussianBlur(X, (0, 0), s1) - cv2.GaussianBlur(X, (0, 0), s2)
for tag, bil in (('P04_WOW', False), ('P05_WOW_bilateral', True)):
    v94 = np.load(ARREL / f'4-RESULTATS/v94_20260924/wow/{tag}_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535; k = W1[tag]['k']; mus = W1[tag]['mitjanes_escala']
    for nom, kw in (('local_des_3', dict(local_des=3)), ('local_totes_s32', dict(local_des=0, sig_local=lambda s: max(32.0, 4.0 * 2 ** s)))):
        q, _, _ = wow_v95(a, m, dm, 8, bil, log=lambda *x: None, mus=mus, **kw); X = np.where(m, 0.5 + k * np.nan_to_num(q), 0.5).astype(np.float32); np.save(S / f't13_{tag}_{nom}.npy', X)
        prof = {f'{s0}-{s1}': [round(float(X[m & (th >= s0) & (th < s1) & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in (2, 5, 10, 20, 40, 60, 90, 130, 200, 300)] for s0, s1 in ((345, 360), (276, 288), (200, 230), (0, 360))}
        cor = {f'{s1}-{s2}': round(float(np.corrcoef(band(X, s1, s2)[ref], band(v94, s1, s2)[ref])[0, 1]), 4) for s1, s2 in ((.5, 1.5), (1.5, 4), (4, 12), (12, 40))}
        print(tag, nom, 'mitjana lluny', round(float(X[ref].mean()), 4), '| correlació amb V94 per bandes', cor); print('   nivell d 2,5,10,20,40,60,90,130,200,300:', json.dumps(prof)); print(flush=True)
