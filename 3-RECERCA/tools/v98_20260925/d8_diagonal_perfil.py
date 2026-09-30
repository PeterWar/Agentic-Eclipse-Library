"""d8 (V98) · La banda diagonal fosca de dalt a l'esquerra (WOW bilateral de la V97, a ~1.000 px de la vora del camp, paral·lela; Artefactes_V95
§4 era un graó a ~430 px). Perfil de ln base_G perpendicular a la vora del camp, mitjana al llarg de la vora, amb el gradient de la corona
tret (polinomi de grau 4 en s): V97 (fusió b3 amb el residu A→B que s'esvaeix) contra el control V85 (graó a 430 px).
Ús: d8_diagonal_perfil.py <sortida.json> nom=<base_G.npy> ..."""
import sys, json
from pathlib import Path
import numpy as np, cv2
H, W = 7506, 10551
E0 = np.array([0.0, 1725.0]); E1 = np.array([1200.0, 600.0]); tau = (E1 - E0) / np.linalg.norm(E1 - E0); n = np.array([tau[1], -tau[0]])
if n[1] < 0: n = -n                         # cap endins (cap avall-dreta)
S = np.arange(0, 2600, 2.0); T = np.arange(-600, 1400, 4.0)
out = {}
for arg in sys.argv[2:]:
    nom, p = arg.split('='); G = np.load(p, mmap_mode='r')
    X = (E0[0] + S[:, None] * n[0] + T[None, :] * tau[0]).astype(np.float32); Y = (E0[1] + S[:, None] * n[1] + T[None, :] * tau[1]).astype(np.float32)
    ok = (X >= 0) & (X < W - 1) & (Y >= 0) & (Y < H - 1); v = np.full(X.shape, np.nan, np.float32)
    xi, yi = np.round(X[ok]).astype(int), np.round(Y[ok]).astype(int); v[ok] = np.asarray(G[yi, xi])
    lv = np.log(np.where(v > 0, v, np.nan)); prof = np.nanmedian(lv, axis=1); f = np.isfinite(prof)
    c = np.polyfit(S[f], prof[f], 4); res = prof - np.polyval(c, S)
    out[nom] = {f'{int(s)}': round(float(r) * 1000, 2) for s, r in zip(S[::10], res[::10]) if np.isfinite(r)}
    print(nom, ' '.join(f'{int(s)}:{r*1000:+.1f}' for s, r in zip(S[::15], res[::15]) if np.isfinite(r)))
Path(sys.argv[1]).write_text(json.dumps(dict(unitats='‰ (ln × 1000)', s='px des de la vora del camp cap endins', perfils=out), indent=1))
