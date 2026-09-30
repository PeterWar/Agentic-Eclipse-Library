"""m0 · Geometria dels traços marrons de Pere (capa 269 «Artefactes V92» de la V107, només lectura): components connexos de l'alfa,
recta per components principals (centre, direcció, llargada, gruix). Sortida: 4-RESULTATS/v108_20260926/marrons/M0_TRACOS_269.json + marques_269.npz"""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
OUT = ARREL / '4-RESULTATS/v108_20260926/marrons'; OUT.mkdir(parents=True, exist_ok=True)
p = PSB(str(ARREL / '1-PHOTOSHOP/V107.psb')); l = p.layer(269)
a, org = p.channel(269, -1); R, _ = p.channel(269, 0); G, _ = p.channel(269, 1); B, _ = p.channel(269, 2)
print('269', org, a.shape, 'alfa>0:', int((a > 0).sum()))
print("percentils alfa>0:", np.percentile(a[a > 0], [5, 25, 50, 75, 95]).tolist()); m = cv2.morphologyEx((a > 2000).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
tr = []
for k in range(1, n):
    if st[k, cv2.CC_STAT_AREA] < 2000: continue
    ys, xs = np.nonzero(lab == k); xs = xs + org[0]; ys = ys + org[1]
    c = np.array([xs.mean(), ys.mean()]); X = np.stack([xs - c[0], ys - c[1]], 1).astype(np.float64)
    ev, evec = np.linalg.eigh(X.T @ X / len(X)); d = evec[:, 1]; nrm = evec[:, 0]
    s = X @ d; t = X @ nrm
    col = [int(np.median(ch[lab == k])) for ch in (R, G, B)]
    tr.append(dict(area=int(st[k, cv2.CC_STAT_AREA]), centre=c.round(1).tolist(), direccio=d.round(4).tolist(), angle_deg=float(np.degrees(np.arctan2(d[1], d[0])) % 180),
                   llarg=float(s.max() - s.min()), gruix=float(np.percentile(t, 99) - np.percentile(t, 1)), s_min=float(s.min()), s_max=float(s.max()), color_mediana_u16=col))
tr.sort(key=lambda z: -z['area'])
for z in tr: print(z)
json.dump(dict(font='V107.psb capa 269 (alfa > 2000, tancament 15 px)', origen=org, tracos=tr), open(OUT / 'M0_TRACOS_269.json', 'w'), indent=1)
np.savez_compressed(OUT / 'marques_269.npz', alfa=a[::4, ::4], org=np.array(org))
