"""a4 (29-09-2026) · Quan neix cada marca: el mateix contrast (marca / veïnat 60–300 px − 1) al compost desat de V111 (Pere), V112, V113 i V114,
traient-ne de manera exacta les capes de marques de Pere visibles (412 a V111–V113, 414 a V114): C = (1−a)·U + a·K ⇒ U = (C − a·K)/(1−a).
A més, la mateixa mesura als ràsters de la 45 i la 46 (factor de Multiplicar) de cada versió. Sortida: QUAN_NEIXEN.json."""
import sys, json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
lab = np.load(OUT / 'marques_414_etiquetes.npy'); M = json.load(open(OUT / 'MARQUES_414.json'))['marques']; H, W = lab.shape
VERS = {'V111 (Pere)': '4-RESULTATS/v110_torre_20260928/V111.psb', 'V112': '1-PHOTOSHOP/V112.psb', 'V113': '1-PHOTOSHOP/V113.psb', 'V114 (Pere, amb 414)': '1-PHOTOSHOP/V114.psb'}
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]
dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def contrast(L4, v4):
    o = {}
    for m in M:
        k = m['marca']; d = (lab4 == k) & v4; f = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & v4
        o[k] = round(float(L4[d].mean() / L4[f].mean() - 1), 4) if d.any() and f.any() else None
    return o
res = {}
for nom, rel in VERS.items():
    p = PSB(str(ARREL / rel)); C = p.composite()[..., :3].astype(np.float32) / 65535
    for mid in (412, 414):
        try: l = p.layer(mid)
        except StopIteration: continue
        if not l['visible']: continue
        A, (x0, y0) = p.channel(mid, -1); a = np.zeros((H, W), np.float32); a[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = A / 65535 * l['opacity'] / 255
        for c in range(3):
            K = np.zeros((H, W), np.float32); Kc, _ = p.channel(mid, c); K[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = Kc / 65535
            m = a > 0; C[..., c][m] = (C[..., c][m] - a[m] * K[m]) / (1 - a[m])
    L4 = quart(C.mean(2)); v4 = quart(C.mean(2) > 0.004) > 0.99
    res[nom] = {'compost': contrast(L4, v4)}
    for fid in (45, 46, 41):
        try: l = p.layer(fid)
        except StopIteration: continue
        F = np.mean([p.channel(fid, c)[0].astype(np.float32) / 65535 for c in range(3)], 0)
        res[nom][f'ràster {fid} ({l["opacity"]}/255)'] = contrast(quart(F), v4)
json.dump(dict(nota='contrast = marca / veïnat − 1 (lluminància), marques de la 414 de Pere; compost desat sense les capes de marques', versions=res), open(OUT / 'QUAN_NEIXEN.json', 'w'), ensure_ascii=False, indent=1)
print('versió · mesura'.ljust(40), ' '.join(f'{m["marca"]:>6d}' for m in M))
for nom, d in res.items():
    for k, v in d.items(): print(f'{nom} · {k}'[:40].ljust(40), ' '.join(f"{(v[m['marca']] or 0) * 100:6.2f}" for m in M))
