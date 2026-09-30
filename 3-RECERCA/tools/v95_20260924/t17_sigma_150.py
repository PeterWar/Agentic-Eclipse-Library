"""t17 · Anell fosc ample (0,48–0,49 a 150–500 px) de la P05 V95: centratge local de les escales gruixudes massa ample (σ 256/512). Prova σ ≤ 150 px
(la mateixa escala de nivell que treia la V94 de la suma). Caixa de 3200 px (d fins a ~1150 als costats). P05 i P04 amb els paràmetres finals."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; S = ARREL / '4-RESULTATS/v95_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from wow_v95 import wow_v95, desplacament_cresta, dmap_vora
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1600; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(V85 / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(V85 / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
a[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['G']; m[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yb, xb = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xb - cx, yb - cy) - R).astype(np.float32); th = (np.degrees(np.arctan2(-(yb - cy), xb - cx)) + 360) % 360
off, _ = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dm = dmap_vora(d, xb, yb, cx, cy, off)
W1 = json.loads((S / 'W1_WOW.json').read_text())['capes']; ref = m & (d > 200) & (d < 1100)
band = lambda X, s1, s2: cv2.GaussianBlur(X, (0, 0), s1) - cv2.GaussianBlur(X, (0, 0), s2)
bins = [0, 5, 10, 20, 60, 100, 150, 200, 250, 300, 350, 400, 500, 600, 800, 1000]
PAR = {'P05_WOW_bilateral': (True, dict(centra_rad=True, iso=(0.5, 1.5))), 'P04_WOW': (False, dict(centra_rad=True, iso=(0.25, 0.75)))}
for tag, (bil, kw) in PAR.items():
    k = W1[tag]['k']; mus = W1[tag]['mitjanes_escala']; v94 = np.load(ARREL / f'4-RESULTATS/v94_20260924/wow/{tag}_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
    print(tag, 'V94   ', [round(float(v94[m & (d >= p) & (d < q_)].mean()), 3) for p, q_ in zip(bins[:-1], bins[1:])])
    for nom, sr in (('σ ≤ 512 (muntada)', lambda s: max(32.0, 4.0 * 2 ** s)), ('σ ≤ 150', lambda s: min(150.0, max(32.0, 4.0 * 2 ** s)))):
        q, _, _ = wow_v95(a, m, dm, 8, bil, log=lambda *x: None, mus=mus, sig_rad=sr, **kw); X = np.where(m, 0.5 + k * np.nan_to_num(q), 0.5).astype(np.float32)
        if '150' in nom: np.save(S / f't17_{tag}_sigma150.npy', X)
        cor = {f'{s1}-{s2}': round(float(np.corrcoef(band(X, s1, s2)[ref], band(v94, s1, s2)[ref])[0, 1]), 4) for s1, s2 in ((.5, 1.5), (4, 12), (12, 40), (40, 150))}
        sd = {f'{s1}-{s2}': round(float(band(X, s1, s2)[ref].std() / band(v94, s1, s2)[ref].std()), 3) for s1, s2 in ((4, 12), (12, 40), (40, 150))}
        print(tag, f'{nom:18s}', [round(float(X[m & (d >= p) & (d < q_)].mean()), 3) for p, q_ in zip(bins[:-1], bins[1:])], '| corr V94', cor, '| amplitud/V94', sd, flush=True)
    print('d:', [f'{p}-{q_}' for p, q_ in zip(bins[:-1], bins[1:])])
