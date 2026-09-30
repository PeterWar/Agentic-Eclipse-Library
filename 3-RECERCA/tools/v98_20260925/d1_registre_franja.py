"""d1 (V98) · Diagnosi de la «lupa» (marques P04/P03 de Pere): la dada d'un instant de la franja (E, fotogrames t ≤ 22,3 s, caixa limb_frames)
i la fusió (base_G) tenen la mateixa geometria? Correlació de fase per blocs a l'anell 12–45 px del limbe de presentació, 24 sectors:
desplaçament (dx, dy) de E respecte de la fusió i la seva component radial. També l'escala del gra (amplada d'autocorrelació del pas alt) per distància."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'; O = ARREL / '4-RESULTATS/v98_20260925'
Q = np.load(RES / 'lineal_v97_franja/A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
G = np.load(RES / 'cadena_v97/d4/products/sources/base_G.npy', mmap_mode='r') if (RES / 'cadena_v97/d4/products/sources/base_G.npy').exists() else None
if G is None:
    import glob; print(glob.glob(str(RES / 'cadena_v97/d4/**'), recursive=True)[:20]); sys.exit(1)
Gb = np.asarray(G[by0:by1, bx0:bx1]).astype(np.float32); E = Q['E'][..., 1].astype(np.float32)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; dL = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
def hp(x, s=4.0):
    l = np.log(np.maximum(x, 1e-6)); return l - cv2.GaussianBlur(l, (0, 0), s)
hG, hE = hp(Gb), hp(E)
ok = (Gb > 0) & (E > 0)
rep = dict(caixa=[by0, by1, bx0, bx1], centre=[cx, cy, R], sectors=[])
for a0 in range(0, 360, 15):
    s = ok & (dL >= 12) & (dL <= 45) & (((th - a0) % 360) < 15)
    if s.sum() < 2000: continue
    ys, xs = np.nonzero(s); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    w = s[y0:y1, x0:x1].astype(np.float32); w = cv2.GaussianBlur(w, (0, 0), 2)
    a = (hG[y0:y1, x0:x1] * w).astype(np.float32); b = (hE[y0:y1, x0:x1] * w).astype(np.float32)
    H_, W_ = a.shape; P = cv2.getOptimalDFTSize(max(H_, W_) + 16)
    A_ = np.zeros((P, P), np.float32); B_ = np.zeros((P, P), np.float32); A_[:H_, :W_] = a; B_[:H_, :W_] = b
    (dx, dy), resp = cv2.phaseCorrelate(A_, B_)
    am = np.radians(a0 + 7.5); radial = dx * np.cos(am) - dy * np.sin(am)   # component cap enfora (y cap avall)
    cc = float(np.corrcoef(hG[s], hE[s])[0, 1])
    rep['sectors'].append(dict(az=a0 + 7.5, dx_E_resp_G=round(dx, 3), dy=round(dy, 3), radial_cap_enfora=round(radial, 3), resposta=round(resp, 3), corr_hp=round(cc, 3), n=int(s.sum())))
    print(rep['sectors'][-1], flush=True)
(O / 'D1_REGISTRE_FRANJA.json').write_text(json.dumps(rep, indent=1))
