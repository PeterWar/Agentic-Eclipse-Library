"""t14 · Tolerància de la regla «mateixa distància del limbe» (iso) a la vora difuminada: (0,5–1,5) contra (0,25–0,75), per a P04 i P05;
i la P04 amb centratge local a totes les escales (σ = max(32, 4·2^s)). Mesures: nivell a d 1–30 per sector, textura relativa (LoG) a 1–3/3–6/6–9 px per
blocs de 15° d'azimut (anisotropia: la dispersió entre blocs), i correlació amb la V94 lluny."""
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
LOC = dict(local_des=0, sig_local=lambda s: max(32.0, 4.0 * 2 ** s))
CASOS = [('P05_WOW_bilateral', True, 'iso_0.5_1.5', {}), ('P05_WOW_bilateral', True, 'iso_0.25_0.75', dict(iso=(0.25, 0.75))),
         ('P04_WOW', False, 'iso_0.5_1.5+local', LOC), ('P04_WOW', False, 'iso_0.25_0.75+local', dict(iso=(0.25, 0.75), **LOC))]
for tag, bil, nom, kw in CASOS:
    k = W1[tag]['k']; mus = W1[tag]['mitjanes_escala']; v94 = np.load(ARREL / f'4-RESULTATS/v94_20260924/wow/{tag}_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
    q, _, _ = wow_v95(a, m, dm, 8, bil, log=lambda *x: None, mus=mus, **kw); X = np.where(m, 0.5 + k * np.nan_to_num(q), 0.5).astype(np.float32); np.save(S / f't14_{tag}_{nom}.npy', X)
    niv = {f'{s0}-{s1}': [round(float(X[m & (th >= s0) & (th < s1) & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30)] for s0, s1 in ((345, 360), (276, 288), (200, 230), (60, 90), (0, 360))}
    lap = cv2.Laplacian(cv2.GaussianBlur(X, (0, 0), 1.0), cv2.CV_32F) ** 2; tx = []
    for b0 in range(0, 360, 15):
        sb = (th >= b0) & (th < b0 + 15) & m; r0 = lap[sb & (d >= 40) & (d < 70)].mean(); tx.append([float(np.sqrt(lap[sb & (d >= e0) & (d < e1)].mean() / r0)) for e0, e1 in ((1, 3), (3, 6), (6, 9))])
    tx = np.array(tx); cor = {f'{s1}-{s2}': round(float(np.corrcoef(band(X, s1, s2)[ref], band(v94, s1, s2)[ref])[0, 1]), 4) for s1, s2 in ((.5, 1.5), (4, 12), (12, 40))}
    print(tag, nom, '| correlació V94 lluny', cor); print('   nivell d 1,2,3,4,5,6,8,10,15,20,30:', json.dumps(niv))
    print('   textura 1–3/3–6/6–9 px: mitjana', np.round(tx.mean(0), 2).tolist(), '· mín', np.round(tx.min(0), 2).tolist(), '· dispersió entre blocs de 15°', np.round(tx.std(0), 2).tolist(), flush=True)
