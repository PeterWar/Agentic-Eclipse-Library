"""e4 (V106, «LOLA fi») · Ajust conjunt de la vora observada de tots els fotogrames mesurables contra LOLA (64 o 16):
u0_j(θ) = a_j + b_j·cos θ + c_j·sin θ (radi i centre per fotograma) + Σ_{n=2,3} [p_n + q_n·(t_j − t0)]·(cos nθ, sin nθ) (refracció, comuna i lenta)
          + k · h_LOLA(θ − θN; suavitzat al llarg de l'arc amb σ_arc)
θN (angle del nord celeste al llenç), σ_arc i k: quadrícula + mínims quadrats; la resta lineal. Pes per fotograma: 1/σ_fina² (soroll + seeing,
robust) i rebuig de calaixos atípics. Incertesa de θN: corba de χ² reescalada i ganiveta (jackknife) per grups de fotogrames."""
import numpy as np, json, sys, os
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
from e2_repro import U, E, th, nF, nb, treu_harm, bandes, gsm, corr, Z
H = Path(__file__).parent; R0 = Path.home() / 'Desktop/Eclipse 2026'
R = float(Z['R']); PXKM = R / 1737.4; T = Z['t']; t0 = 18.43
PERFIL = os.environ.get('E4_PERFIL', 'PERFIL_LDEM64_182849.npz')
def rob(x): return 1.4826 * np.median(np.abs(x - np.median(x)))
_L = np.load(PERFIL if PERFIL.startswith('/') else R0 / f'4-RESULTATS/v106_inversio_20260926/lola/{PERFIL}'); _pa = _L['pa']; _h = _L['h_km'] * PXKM
def hlola(thN, sig_px, parit=1, nsub=25):
    ang = (thN + parit * _pa) % 360; o = np.argsort(ang); g = np.arange(0, 360, 0.01)
    hl = np.interp(g, ang[o], _h[o], period=360)
    if sig_px > 0: hl = gaussian_filter1d(hl, sig_px / (R * np.pi / 180) / 0.01, mode='wrap')
    return hl.reshape(nb, nsub).mean(1)
# dades
FJ = [j for j in range(nF) if np.isfinite(U[j]).sum() >= 600]
Y = []; Wt = []; J = []
for j in FJ:
    u = U[j]; w0 = np.isfinite(u) & np.isfinite(E[j])
    r, _ = treu_harm(np.nan_to_num(u), w0.astype(float)); B = bandes(r, w0.astype(float)); s = rob(B['fina'][w0])
    loc = gsm(r, w0.astype(float), 0.5); bad = np.abs(r - loc) > 9 * max(s, 0.03)
    w = np.where(w0 & ~bad, 1 / s ** 2, 0.0)
    Y.append(np.nan_to_num(u)); Wt.append(w); J.append(j)
Y = np.array(Y); Wt = np.array(Wt); nJ = len(J); TJ = T[J] - t0
thr = np.radians(th)
Hf = np.stack([np.ones(nb), np.cos(thr), np.sin(thr)], 1)                         # per fotograma
def common_basis(orders=(2, 3), temps=True):
    cols = []
    for n in orders:
        cols += [np.cos(n * thr), np.sin(n * thr)]
    return np.array(cols).T                                                         # (nb, m)
def solve(hl, js=None, orders=(2, 3), temps=True, return_all=False):
    """Mínims quadrats: per fotograma (3) + comuns (2·len(orders)) (+ derivada temporal) + k. Retorna χ², paràmetres."""
    idx = range(nJ) if js is None else js
    Cb = common_basis(orders)                                                       # (nb, m)
    m = Cb.shape[1]; npar_c = m * (2 if temps else 1) + 1
    # eliminem els paràmetres per fotograma per projecció (complement de Schur)
    A_cc = np.zeros((npar_c, npar_c)); b_c = np.zeros(npar_c); proj = {}
    for i in idx:
        w = Wt[i]; X_c = np.concatenate([Cb] + ([Cb * TJ[i]] if temps else []) + [hl[:, None]], 1)   # (nb, npar_c)
        Hw = Hf * w[:, None]; Aff = Hf.T @ Hw; Afc = Hw.T @ X_c; bf = Hw.T @ Y[i]
        Aff_i = np.linalg.inv(Aff + 1e-9 * np.eye(3))
        A_cc += (X_c * w[:, None]).T @ X_c - Afc.T @ Aff_i @ Afc; b_c += (X_c * w[:, None]).T @ Y[i] - Afc.T @ Aff_i @ bf
        proj[i] = (Aff_i, Afc, bf, X_c)
    pc = np.linalg.solve(A_cc + 1e-9 * np.eye(npar_c), b_c)
    chi2 = 0.0; n = 0; pf = {}; res = {}
    for i in idx:
        Aff_i, Afc, bf, X_c = proj[i]; p_f = Aff_i @ (bf - Afc @ pc); pf[i] = p_f
        r = Y[i] - Hf @ p_f - X_c @ pc; res[i] = r; chi2 += np.sum(Wt[i] * r * r); n += (Wt[i] > 0).sum()
    if return_all: return chi2, n, pc, pf, res, np.linalg.inv(A_cc + 1e-9 * np.eye(npar_c))
    return chi2, n, pc
if __name__ == '__main__':
    print(f'perfil {PERFIL}; fotogrames {nJ}: {J}')
    # 1) quadrícula θN × σ_arc
    best = None; tab = {}
    for sig in [0.0, 0.8, 1.25, 1.8, 2.5, 3.5]:
        for thN in np.arange(44.6, 46.0, 0.02):
            c2, n, pc = solve(hlola(thN, sig)); tab[(sig, round(thN, 3))] = (c2, pc[-1])
            if best is None or c2 < best[0]: best = (c2, thN, sig, pc[-1], n)
    c2b, thNb, sigb, kb, nb_ = best
    print(f'millor: θN {thNb:.3f}°, σ_arc {sigb} px, k {kb:.3f}, χ²/n {c2b / nb_:.4f} (n {nb_})')
    for sig in [0.0, 0.8, 1.25, 1.8, 2.5, 3.5]:
        row = [(t, tab[(sig, round(t, 3))]) for t in np.arange(44.6, 46.0, 0.02)]
        tm, (cm, km) = min(row, key=lambda r: r[1][0])
        print(f'   σ_arc {sig:4.2f}: θN {tm:.2f}  χ²/n {cm / nb_:.5f}  k {km:.3f}')
    # 2) afinament de θN a 0,002° amb σ_arc òptim, i corba de χ²
    ts = np.arange(thNb - 0.2, thNb + 0.2001, 0.005); cs = np.array([solve(hlola(t, sigb))[0] for t in ts])
    i0 = np.argmin(cs); a, b, c = np.polyfit(ts[max(i0 - 8, 0):i0 + 9], cs[max(i0 - 8, 0):i0 + 9], 2); tf = -b / (2 * a)
    s2 = cs.min() / nb_                                                            # χ² reduït: reescala
    err_formal = np.sqrt(s2 / a) if a > 0 else np.nan
    print(f'θN fi: {tf:.4f}°  error formal (χ² reescalat) ±{err_formal:.4f}°')
    # 3) ganiveta per grups de fotogrames (6 grups)
    grups = {'A 0–8': range(0, 9), 'A2 9–17': range(9, 18), 'C1 26–35': range(26, 36), 'C2 38–48': range(38, 49), 'B1 50–58': range(50, 59), 'B2 59–66': range(59, 67)}
    jk = []
    for nom, gr in grups.items():
        keep = [i for i, j in enumerate(J) if j not in gr]
        cs_ = np.array([solve(hlola(t, sigb), keep)[0] for t in ts]); i0 = np.argmin(cs_)
        a_, b_, c_ = np.polyfit(ts[max(i0 - 8, 0):i0 + 9], cs_[max(i0 - 8, 0):i0 + 9], 2); jk.append(-b_ / (2 * a_))
        only = [i for i, j in enumerate(J) if j in gr]
        cs_o = np.array([solve(hlola(t, sigb), only)[0] for t in ts]); i1 = np.argmin(cs_o)
        a_, b_, c_ = np.polyfit(ts[max(i1 - 8, 0):i1 + 9], cs_o[max(i1 - 8, 0):i1 + 9], 2)
        print(f'   sense {nom:9s}: θN {jk[-1]:.4f}° | només aquest grup: θN {-b_ / (2 * a_):.4f}°')
    jk = np.array(jk); njk = len(jk); err_jk = np.sqrt((njk - 1) / njk * np.sum((jk - jk.mean()) ** 2))
    print(f'θN = {tf:.4f}° ± {err_jk:.4f}° (ganiveta per grups)')
    # 4) paràmetres finals
    c2, n, pc, pf, res, cov = solve(hlola(tf, sigb), return_all=True)
    names = ['c2', 's2', 'c3', 's3', 'dc2/dt', 'ds2/dt', 'dc3/dt', 'ds3/dt', 'k']
    print('comuns:', ' '.join(f'{nm} {v:+.4f}±{np.sqrt(cov[i, i] * c2 / n):.4f}' for i, (nm, v) in enumerate(zip(names, pc))))
    C = Z['centres']
    out = dict(thN=tf, thN_err_jk=err_jk, thN_err_formal=err_formal, sig_arc=sigb, k=pc[-1], comuns=pc, noms_comuns=np.array(names), t0=t0, J=np.array(J),
               pf=np.array([pf[i] for i in range(nJ)]), perfil=PERFIL, jk=jk)
    nom_out = 'E4_AJUST_LDEM64.npz' if PERFIL == 'PERFIL_LDEM64_182849.npz' else f'E4_AJUST_{Path(PERFIL).stem.split("_", 1)[1]}.npz'
    np.savez_compressed(H / nom_out, **out)
    print('per fotograma (radi a, centre b,c en px; t):')
    for i, j in enumerate(J):
        print(f'   {j:2d} t {T[j]:6.2f}  a {pf[i][0]:+.3f}  b {pf[i][1]:+.3f}  c {pf[i][2]:+.3f}   rms res {np.sqrt(np.sum(Wt[i] * res[i] ** 2) / np.sum(Wt[i])) if Wt[i].sum() else 0:.3f}')
