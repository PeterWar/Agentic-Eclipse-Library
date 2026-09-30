"""d11 (V98) · Hi ha graons de ln G lligats a una brillantor (canvis d'exposició de l'LDIC) a la Vixen? Pas alt de ln G (σ 3 − σ 25) agrupat
per nivell d'isofota (brillantor suavitzada σ 6), a d = 60–900 px del limbe; nul: les mateixes isofotes girades al voltant del Sol.
Els pics del perfil (i on cauen en radi a dalt) diuen si l'arc de ~640 px de la capa 47 (marca 307 de Pere, el «teulat») és un graó d'isofota.
Ús: d11_graons_isofota_G.py <vixen_starless.npy o base_G.npy> [canal]"""
import sys, numpy as np, cv2
p = sys.argv[1]; ch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
A = np.load(p, mmap_mode='r'); CX, CY = 5361.768, 3775.748; LX, LY, RL = 5375.787, 3775.977, 452.979
x0, y0, x1, y1 = int(LX - 1300), int(LY - 1300), int(LX + 1300), int(LY + 1300)
G = np.asarray(A[y0:y1, x0:x1, ch] if A.ndim == 3 else A[y0:y1, x0:x1], np.float32); ok = np.isfinite(G) & (G > 0)
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - LX, yy - LY) - RL; r = np.hypot(xx - CX, yy - CY)
L = np.where(ok, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32); w = ok.astype(np.float32)
def ng(a, s): return cv2.GaussianBlur(a * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
hp = ng(L, 3) - ng(L, 25); q = ng(L, 6); zona = ok & (d > 60) & (d < 900)
def perfil(qm, nb=240):
    v = qm[zona]; e = np.quantile(v, np.linspace(0, 1, nb + 1)); idx = np.clip(np.searchsorted(e, v) - 1, 0, nb - 1)
    P = np.bincount(idx, hp[zona], nb) / np.maximum(np.bincount(idx, None, nb), 1); return P, e
P, e = perfil(q)
nuls = []
for ang in (60, 135, 200):
    M = cv2.getRotationMatrix2D((CX - x0, CY - y0), ang, 1.0); qr = cv2.warpAffine(q, M, (q.shape[1], q.shape[0]), borderValue=float(np.median(q[zona]))); nuls.append(perfil(qr)[0])
sd_nul = float(np.std(np.concatenate(nuls))); print('DE perfil', round(float(np.std(P)), 5), 'DE nul', round(sd_nul, 5), 'ràtio', round(float(np.std(P) / sd_nul), 2))
# on cauen els pics a dalt (azimut 80–100°): radi solar de cada nivell d'isofota
th = (np.degrees(np.arctan2(-(yy - CY), xx - CX)) + 360) % 360; top = zona & (th > 80) & (th < 100)
for k in np.argsort(-np.abs(P))[:8]:
    lv = 0.5 * (e[k] + e[k + 1]); s = top & (np.abs(q - lv) < 0.01)
    print(f'nivell {k:3d}: pas alt {P[k]*1000:+.2f} ‰ (nul DE {sd_nul*1000:.2f}) · a dalt, radi solar p50 = {np.median(r[s]) if s.sum() > 5 else float("nan"):.0f} px')
