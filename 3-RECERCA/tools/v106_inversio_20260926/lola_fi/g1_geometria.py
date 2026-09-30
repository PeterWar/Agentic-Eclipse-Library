"""g1 (V106, «LOLA fi») · Construeix GEOMETRIA_FINA.npz (la vora fina de cada fotograma) a partir de l'ajust conjunt e4 (LOLA-64).
Fotogrames no mesurables (llargs saturats fora de la Lluna, < 600 calaixos vàlids): centre i radi NO mesurats; es deixen amb correcció zero
respecte del model (+ comuns + LOLA) i marcats mesurat = False (cap dada inventada: la geometria és la del model)."""
import numpy as np, sys
from pathlib import Path
from e4_ajust import *
from e4_ajust import _pa, _h
SIG_PROPI = float(os.environ.get('G1_SIG_PROPI', '1.0'))
if __name__ == '__main__':
    A4 = np.load(H / 'E4_AJUST_LDEM64.npz'); thN = float(A4['thN']); sig = float(A4['sig_arc'])
    hl = hlola(thN, sig)
    c2, n, pc, pf, res, cov = solve(hl, return_all=True)
    kfit = pc[-1]
    PF = np.zeros((nF, 3)); mes = np.zeros(nF, bool); EPS = np.zeros((nF, nb), np.float32)
    for i, j in enumerate(J):
        PF[j] = pf[i]; mes[j] = True
        w = (Wt[i] > 0).astype(float); EPS[j] = gsm(np.where(w > 0, res[i], 0.0), w, SIG_PROPI)
    # relleu LOLA-64 al llenç, graella 0,01°, sense suavitzar (km → px amb R/1737,4; k = 1: l'ajust dona k = %.3f)
    g = np.arange(0, 360, 0.01)
    ang = (thN + _pa) % 360; o = np.argsort(ang); h001 = np.interp(g, ang[o], _h[o], period=360)
    from vora_lib import SPA, SE, centre_model
    CM = np.array([centre_model(j) for j in range(nF)])
    CF = CM + np.stack([PF[:, 1], -PF[:, 2]], 1)
    np.savez_compressed(H / os.environ.get('G1_OUT', 'GEOMETRIA_FINA.npz'), R=R, thN=thN, thN_err=float(A4['thN_err_jk']), k=1.0, k_ajust=kfit, sig_arc_ajust=sig, t0=t0,
                        comuns=pc[:-1], noms_comuns=np.array(['c2', 's2', 'c3', 's3', 'dc2/dt', 'ds2/dt', 'dc3/dt', 'ds3/dt']),
                        pf=PF, mesurat=mes, centres_model=CM, centres_fins=CF, t=T, exp=Z['exp'], eo2_pa=SPA, eo2_e=SE,
                        g001=g, h_lola_001=h001.astype(np.float32), perfil='PERFIL_LDEM64_182849.npz (LOLA LDEM_64, 18:28:49 UTC)',
                        theta_b=th, eps_propi=EPS, sig_propi=SIG_PROPI,
                        nota='r_L,j(θ) = R + e_o2(θ) + a_j + b_j cos θ + c_j sin θ + Σ_{n=2,3}[p_n + q_n (t_j − t0)](cos nθ, sin nθ) + h_LOLA64(θ−θN)⊗g(σ); '
                             'θ al voltant del centre del model; centres_fins = centre del model + (b_j, −c_j). Vegeu geom_fina.py')
    print(f'θN {thN:.4f} ± {float(A4["thN_err_jk"]):.4f}°; k ajustat {kfit:.3f} (es desa k = 1); mesurats {mes.sum()} de {nF}')
    print('comuns', np.round(pc[:-1], 4))
