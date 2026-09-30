"""j15 (V98) · El compost emulat (jutge_comu: pila visible per sota de la 234, sense les capes d'ajust) de dos estats a la caixa de la Lluna:
(1) vistes a 4:1 dels llocs de les marques de Pere (dalt, dreta, esquerra, baix, dalt-dreta, dalt-esquerra), costat a costat;
(2) anells: perfil de ln(lluminància) per distància al limbe i azimut, residu contra una recta a 12–30 px, mediana per sectors de 30°
    (la part coherent al llarg de l'arc); clot = mínim a 1–9 px.
Ús: j15_compost_limbe.py <estatA> <estatB> <prefix_sortida>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, LLUNA, RLLUNA
A, B, pref = Estat(sys.argv[1]), Estat(sys.argv[2]), sys.argv[3]
box = (4780, 3180, 5980, 4380); x0, y0, x1, y1 = box
yy, xx = np.mgrid[y0:y1, x0:x1]; d = (np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA).astype(np.float32); th = ((np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) + 360) % 360).astype(np.float32)
CA, _ = A.compost(box=box); CB, _ = B.compost(box=box)
np.save(pref + '_compostA.npy', CA); np.save(pref + '_compostB.npy', CB)
def lum(C): return np.log(np.maximum((C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4, 1e-4))
NB = 200; nb = np.clip((d / 0.5).astype(int), 0, NB - 1); NT = 180; tb = (th / 2).astype(int) % NT; dc = (np.arange(NB) + 0.5) * 0.5
def anells(L):
    ok = (d >= 0) & (d < 100); idx = tb[ok] * NB + nb[ok]; s = np.bincount(idx, weights=L[ok], minlength=NT * NB); n = np.bincount(idx, minlength=NT * NB)
    P = np.where(n >= 3, s / np.maximum(n, 1), np.nan).reshape(NT, NB); res = np.full_like(P, np.nan); fit = (dc >= 12) & (dc <= 30)
    for k in range(NT):
        f = fit & np.isfinite(P[k])
        if f.sum() > 10: c = np.polyfit(dc[f], P[k][f], 1); res[k] = P[k] - np.polyval(c, dc)
    out = {}
    for a0 in range(0, 360, 30):
        med = np.nanmedian(res[a0 // 2:(a0 + 30) // 2], axis=0); w = (dc >= 1) & (dc <= 9)
        out[f'{a0}-{a0+30}'] = dict(clot=round(float(np.nanmin(med[w])), 4), d=float(dc[w][np.nanargmin(med[w])]), perfil_0_12=[round(float(v), 4) for v in med[:24]])
    return out
rep = dict(A=sys.argv[1], B=sys.argv[2], anells_A=anells(lum(CA)), anells_B=anells(lum(CB)))
for k in rep['anells_A']: print(k, 'A', rep['anells_A'][k]['clot'], '@', rep['anells_A'][k]['d'], '| B', rep['anells_B'][k]['clot'], '@', rep['anells_B'][k]['d'])
Path(pref + '_ANELLS.json').write_text(json.dumps(rep, indent=1))
def u8(C): return (np.clip(C, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)[..., ::-1]
for nom, (cx0, cy0, cx1, cy1) in dict(dalt=(5280, 3250, 5480, 3350), dreta=(5780, 3690, 5880, 3890), esquerra=(4895, 3600, 4995, 3800), baix=(5280, 4200, 5480, 4300),
                                      dalt_dreta=(5600, 3340, 5740, 3480), dalt_esquerra=(5020, 3350, 5160, 3490)).items():
    a = CA[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]; b = CB[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    ia = cv2.resize(u8(a), None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST); ib = cv2.resize(u8(b), None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'{pref}_{nom}.png', np.hstack([ia, np.full((ia.shape[0], 10, 3), 255, np.uint8), ib]))
print('fet')
