"""t1 (V95) · Prova de wow_completesa a la caixa de 2400 px al voltant de la Lluna, contra la V94 (wow_domini + neutralitza) i la V93.
Mesures: nivell per distància i sector (sense cap correcció posterior), estructura en arc del nivell a 10–150 px (σ al llarg de l'arc del nivell
suavitzat 2°), textura (LoG) a 1–9 px, mitjana local lluny. Sortida: T4.json i vista a 1:1 amb les marques de Pere."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
from PIL import Image
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v95_20260924'; SORT.mkdir(exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent)); from wow_parells import wow_parells as wow_completesa
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85 / 'd4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
B = 1200; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
a = np.asarray(np.load(FONTS / 'base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32).copy(); m = (np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[by0:by1, bx0:bx1]) & np.isfinite(a) & (a > 0))
sy, sx = slice(qy0 - by0, qy1 - by0), slice(qx0 - bx0, qx1 - bx0); a[sy, sx] = Q['G']; m[sy, sx] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
t0 = time.time(); q, pesos = wow_completesa(a, m, 8, True); print(f'WOW bilateral (completesa) {time.time() - t0:.0f} s', flush=True); np.save(SORT / 't4_q.npy', q)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
old93 = np.load(ARREL / '4-RESULTATS/v93_20260924/filtres_v93/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
v94 = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
ref = (d > 200) & (d < 600) & m; hp = lambda X: X - cv2.GaussianBlur(X, (0, 0), 8); qz = np.nan_to_num(q)
k = float(np.std(hp(old93)[ref]) / np.std(hp(qz)[ref])); off = 0.0
new = np.where(m, 0.5 + k * (qz - off), 0.5).astype(np.float32); np.save(SORT / 't4_display.npy', new); print('k', round(k, 4), 'desplaçament global (mediana) restat', round(off * k, 4))
DT, DR = 0.1, 1.0; NT = int(360 / DT); DS = np.arange(0, 250, DR); TS = np.radians((np.arange(NT) + 0.5) * DT); TT, DD = np.meshgrid(TS, DS)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32); t = np.arange(NT) * DT
rep = {}
for nom, X, dom in (('V93', old93, np.ones_like(m)), ('V94', v94, m), ('V95_parells', new, m)):
    P = cv2.remap(X, MX, MY, cv2.INTER_LINEAR); V = cv2.remap(dom.astype(np.float32), MX, MY, cv2.INTER_NEAREST) > 0.5
    Ps = np.where(V, P, np.nan); nivell_arc = np.array([gaussian_filter1d(np.nan_to_num(Ps[i], nan=0.5), 2 / DT, mode='wrap') for i in range(len(DS))])
    arcs = {f'{a0}-{a1}px': round(float(np.std(nivell_arc[a0:a1].mean(0))), 4) for a0, a1 in ((5, 30), (30, 60), (60, 90), (90, 130), (130, 200))}
    perfil = {f'{s0}-{s1}': [round(float(np.nanmean(Ps[dd, (t >= s0) & (t < s1)])), 3) for dd in (2, 5, 10, 20, 40, 60, 90, 110, 130, 160, 200)] for s0, s1 in ((345, 360), (276, 288), (140, 170), (200, 230), (60, 90))}
    lap = cv2.Laplacian(cv2.GaussianBlur(X, (0, 0), 1.0), cv2.CV_32F) ** 2
    tex = {s: [round(float(np.sqrt(lap[(th >= a0) & (th < a1) & dom & (d >= b0) & (d < b1)].mean() / lap[(th >= a0) & (th < a1) & dom & (d >= 40) & (d < 70)].mean())), 2) for b0, b1 in ((1, 3), (3, 6), (6, 9), (9, 14))] for s, (a0, a1) in {'63_93': (63, 93), '208_253': (208, 253), '329_351': (329, 351)}.items()}
    rep[nom] = dict(arcs_sigma_nivell=arcs, perfil_nivell=perfil, textura_1_14=tex); print(nom, json.dumps(rep[nom]), flush=True)
rep['pes_escales_a_d'] = {f'escala {s}': [round(float(pesos[s][(np.abs(d - dd) < 0.5) & m].mean()), 2) for dd in (2, 5, 10, 20, 40, 80, 160)] for s in range(8)}; print(json.dumps(rep['pes_escales_a_d']))
(SORT / 'T4.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
