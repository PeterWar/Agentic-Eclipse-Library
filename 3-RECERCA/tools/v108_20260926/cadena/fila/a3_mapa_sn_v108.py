# CÒPIA per a la cadena V108 (Claude, 26-09-2026) de 3-RECERCA/tools/v105_limbe_20260926/fila/a3_mapa_sn.py: només canvien el camí d'importació (comu_fila_v108).
"""a3 · mapa de resolució que segueix el S/N a la franja de banda (caixa lunar), MESURAT a la dada (linealitzada G de la V104):
  n_σ(d, θ) = rms fi (1–3 px d'arc) de ln(G promitjada amb σ) al llarg de l'arc (finestra gaussiana σ_θ);
  ref(θ)    = n_0 als primers 4 px del règim net (on la porta de banda ja és < 0,02), la mediana;
  σ(d, θ)   = la σ mínima tal que n_σ ≤ ref (interpolada entre nivells), NOMÉS on hi ha règim de banda (porta > 0) o a 1 px d'ell;
  rho       = n_0 / ref (≥ 1) per a la variant (iii).
Sortida: SN_MAPA.npz (sigma, rho a la caixa lunar; perfils per sector)."""
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from comu_fila_v108 import *
from scipy.ndimage import map_coordinates
Q = np.load(FR); G = Q['G'].astype(np.float32); dom = Q['domini'] & (G > 0); por = Q['porta_banda']
LV = [0.0, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]; STH = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0   # σ_θ en mostres de 0,5 px (20 px d'arc)
w = dom.astype(np.float32); pd = pol(w); ok = pd > 0.999
def nsig(s):
    Gs = G if s == 0 else cv2.GaussianBlur(np.where(dom, G, 0), (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-8)
    lp = np.where(ok, np.log(np.maximum(pol(np.where(dom, Gs, 0)), 1e-12)), 0); okf_ = ok.astype(np.float32)
    mu = gaussian_filter1d(lp, 3, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(okf_, 3, axis=1, mode='wrap'), 1e-6); hp = np.where(ok, lp - mu, 0)   # pas alt només amb mostres amb dada
    return np.sqrt(gaussian_filter1d(hp * hp, STH, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ok.astype(np.float32), STH, axis=1, mode='wrap'), 1e-6))
N = np.stack([nsig(s) for s in LV]); okf = gaussian_filter1d(ok.astype(np.float32), STH, axis=1, mode='wrap') > 0.5
pp = gaussian_filter1d(pol(por), STH, axis=1, mode='wrap'); pp = np.where(okf, pp, 1.0)
nd, nt = N.shape[1:]; ref = np.zeros(nt); dcl = np.zeros(nt)
for j in range(nt):
    cand = np.flatnonzero((pp[:, j] < 0.02) & okf[:, j] & (DG > 0))
    k0 = cand[0] if cand.size else nd - 17; dcl[j] = DG[k0]; ref[j] = np.median(N[0, k0:k0 + 17, j])      # 4 px de règim net
ref = gaussian_filter1d(ref, STH, mode='wrap')
zona = (pp > 0.0) | (DG[:, None] < dcl[None, :] + 1.0)       # banda (porta > 0) i el primer píxel net
zona &= okf
SIG = np.zeros((nd, nt), np.float32)
for i in range(nd):
    for j in np.flatnonzero(zona[i]):
        v = N[:, i, j]; r = ref[j]
        if v[0] <= r: continue
        k = np.flatnonzero(v <= r)
        if not k.size: SIG[i, j] = LV[-1]; continue
        k = k[0]; SIG[i, j] = LV[k - 1] + (LV[k] - LV[k - 1]) * (v[k - 1] - r) / max(v[k - 1] - v[k], 1e-12)
SIG = gaussian_filter1d(SIG, STH / 2, axis=1, mode='wrap')
RHO = np.where(zona, np.maximum(N[0] / ref[None, :], 1.0), 1.0).astype(np.float32); RHO = gaussian_filter1d(RHO, STH / 2, axis=1, mode='wrap')
# de la graella polar (d, θ) als píxels de la caixa lunar
dd, th = dist_theta(BOXL); fi = (dd - DG[0]) / 0.25; fj = np.radians(th) / (2 * np.pi) * NTH
def back(P, fill):
    Pp = np.concatenate([P, P[:, :1]], axis=1); v = map_coordinates(Pp, [fi.ravel(), fj.ravel()], order=1, mode='nearest').reshape(dd.shape)
    return np.where((dd >= DG[0]) & (dd <= DG[-1]), v, fill).astype(np.float32)
sigma = back(SIG, 0.0) * dom; rho = back(RHO, 1.0)
out = dict(sigma=sigma, rho=rho, SIG=SIG, RHO=RHO, ref=ref, dcl=dcl, N=N.astype(np.float32), LV=np.array(LV))
np.savez(OUT / 'SN_MAPA.npz', **out)
for nm in ['dalt', 'dalt_esq', 'baix_esq', 'dreta']:
    s = sec(nm); print(f'## {nm}: ref {ref[s].mean():.4f} · d_net {dcl[s].mean():.2f}')
    for d in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0]:
        i = id_(d); print(f'   d {d:4.1f}  n0 {N[0, i, s].mean():.4f}  ρ {RHO[i, s].mean():.2f}  σ {SIG[i, s].mean():.2f}  (n a σ: ' + ' '.join(f'{N[k, i, s].mean():.4f}' for k in range(len(LV))) + ')')
