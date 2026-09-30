"""b2 · Comprovació de l'encaix per estrelles de les capes de Brno: per a cada estrella del S22 dins de la capa, centroide del pic de Brno
(lluminància − mediana local 61 px, pes positiu, finestra ±R px) i desplaçament Brno − nostre. Ús: b2_comprova_brno.py [vell|nou]"""
import sys, json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
S22 = json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text())['stars']
mode = sys.argv[1] if len(sys.argv) > 1 else 'nou'; p = PSB(str(R / '1-PHOTOSHOP/V113.psb')); out = {}
for lid, RAD in ((230, 45), (231, 30), (232, 25)):
    if mode == 'nou':
        z = np.load(R / f'4-RESULTATS/v113_estrelles_20260928/brno/L{lid}.npz'); x0, y0, x1, y1 = z['bbox']; G = z['G'].astype(np.float32); A = z['A']
    else:
        G, (x0, y0) = p.channel(lid, 1); A, _ = p.channel(lid, -1); G = G.astype(np.float32)
    d = []
    for s in S22:
        cx, cy = s['x'] - x0, s['y'] - y0; ix, iy = int(round(cx)), int(round(cy))
        if not (RAD + 40 <= ix < G.shape[1] - RAD - 40 and RAD + 40 <= iy < G.shape[0] - RAD - 40): continue
        if A[iy, ix] < 65000: continue
        w = G[iy - RAD - 30:iy + RAD + 31, ix - RAD - 30:ix + RAD + 31]
        bg = np.median(w); c = w[30:-30, 30:-30] - bg; mad = 1.4826 * np.median(np.abs(w - bg)) + 1e-6
        if c.max() < 6 * mad: continue
        m = c > 0.5 * c.max(); lab, _ = ndi.label(m); k = lab[np.unravel_index(np.argmax(c), c.shape)]; mm = lab == k
        yy, xx = np.nonzero(mm); wt = c[mm]
        bx = (xx * wt).sum() / wt.sum() - RAD + ix; by = (yy * wt).sum() / wt.sum() - RAD + iy
        d.append((s['id'], bx - cx, by - cy))
    v = np.array([[a, b] for _, a, b in d]); r = np.hypot(v[:, 0], v[:, 1])
    out[lid] = dict(n=len(d), mitjana=v.mean(0).round(2).tolist(), RMS=round(float(np.sqrt((r ** 2).mean())), 2), mediana=round(float(np.median(r)), 2), maxim=round(float(r.max()), 2))
    print(mode, lid, out[lid], flush=True)
