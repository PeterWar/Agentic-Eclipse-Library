"""e5 (V106, «LOLA fi») · Validació creuada de la vora fina: LOLA-64 (θN i σ_arc ajustats) contra la vora EMPÍRICA (mitjana dels altres
fotogrames en coordenades lunars) i la combinació. Es reserva un grup de fotogrames; amb la resta s'ajusten els comuns (i la vora empírica);
al grup reservat només s'ajusten el radi i el centre per fotograma (3 paràmetres) i es mesura el residu per banda d'escala i sector.
També: correlació LOLA↔observat per bandes i sectors amb la geometria final, i residus robustos."""
import numpy as np, os
from pathlib import Path
from e4_ajust import *
if __name__ == '__main__':
    A4 = np.load(H / 'E4_AJUST_LDEM64.npz'); thN = float(A4['thN']); sig = float(A4['sig_arc'])
    hl = hlola(thN, sig)
    grups = {'A 0–8': range(0, 9), 'A2 9–17': range(9, 18), 'C1 26–35': range(26, 36), 'C2 38–48': range(38, 49), 'B1 50–58': range(50, 59), 'B2 59–66': range(59, 67)}
    SECT = [(0, 45), (45, 90), (90, 135), (135, 180), (180, 225), (225, 270), (270, 315), (315, 360)]
    def ajusta_reservat(i, ypred_common):
        w = Wt[i]; y = Y[i] - ypred_common; Hw = Hf * w[:, None]; p = np.linalg.solve(Hf.T @ Hw + 1e-9 * np.eye(3), Hw.T @ y); return y - Hf @ p
    tot = {m: {b: [0.0, 0.0] for b in ('gran', 'mitjana', 'fina', 'tot')} for m in ('cap', 'LOLA', 'EMP', 'EMP_s', 'LOLA+EMP_s')}
    per_sect = {m: np.zeros((len(SECT), 2)) for m in tot}
    for nom, gr in grups.items():
        train = [i for i, j in enumerate(J) if j not in gr]; test = [i for i, j in enumerate(J) if j in gr]
        if not test: continue
        _, _, pc, pf, res, _ = solve(hl, train, return_all=True)
        # vora empírica: mitjana ponderada dels residus del train SENSE el terme LOLA (= relleu observat)
        Cb = common_basis((2, 3)); S = np.zeros(nb); Wsum = np.zeros(nb)
        for i in train:
            X_c = np.concatenate([Cb, Cb * TJ[i], hl[:, None]], 1); r_noL = res[i] + pc[-1] * hl        # obs − (harmònics) = relleu + soroll
            S += Wt[i] * r_noL; Wsum += Wt[i]
        emp = np.where(Wsum > 0, S / np.maximum(Wsum, 1e-30), 0.0)
        emp_s = gsm(emp, (Wsum > 0).astype(float), 0.15)                                               # vora empírica suavitzada (σ 0,15°)
        resL = np.where(Wsum > 0, emp - pc[-1] * hl, 0.0); resL_s = gsm(resL, (Wsum > 0).astype(float), 0.5)
        for i in test:
            X_c0 = np.concatenate([Cb, Cb * TJ[i]], 1); comm = X_c0 @ pc[:-1]
            preds = {'cap': comm, 'LOLA': comm + pc[-1] * hl, 'EMP': comm + emp, 'EMP_s': comm + emp_s, 'LOLA+EMP_s': comm + pc[-1] * hl + resL_s}
            w = Wt[i]; m = w > 0
            for mname, yp in preds.items():
                r = ajusta_reservat(i, yp); B = bandes(r, m.astype(float)); B['tot'] = r
                for b in B:
                    tot[mname][b][0] += np.sum(w[m] * B[b][m] ** 2); tot[mname][b][1] += np.sum(w[m])
                for k, (lo, hi) in enumerate(SECT):
                    ms = m & (th >= lo) & (th < hi); per_sect[mname][k] += (np.sum(w[ms] * r[ms] ** 2), np.sum(w[ms]))
    print('Validació creuada (6 grups reservats per torn): rms ponderat del residu al grup reservat (px)')
    print('model         ' + ' '.join(f'{b:>8s}' for b in ('gran', 'mitjana', 'fina', 'tot')))
    for mname in tot:
        print(f'{mname:12s}  ' + ' '.join(f'{np.sqrt(tot[mname][b][0] / tot[mname][b][1]):8.4f}' for b in ('gran', 'mitjana', 'fina', 'tot')))
    print('per sectors (tot):')
    for mname in tot:
        print(f'{mname:12s}  ' + ' '.join(f'{lo}-{hi}:{np.sqrt(per_sect[mname][k, 0] / per_sect[mname][k, 1]):.3f}' for k, (lo, hi) in enumerate(SECT)))
    # correlació final per bandes i sectors (mitjana de tots els fotogrames sense els harmònics ajustats)
    _, _, pc, pf, res, _ = solve(hl, return_all=True)
    S = np.zeros(nb); Wsum = np.zeros(nb)
    for i in range(nJ): S += Wt[i] * (res[i] + pc[-1] * hl); Wsum += Wt[i]
    obs = np.where(Wsum > 0, S / np.maximum(Wsum, 1e-30), 0.0); m = Wsum > 0; w = m.astype(float)
    Bo = bandes(obs, w); Bl = bandes(pc[-1] * hl, w)
    print(f'\nθN {thN:.4f}°, σ_arc {sig} px, k {pc[-1]:.3f}: correlació LOLA-64 ↔ observat (mitjana de {nJ} fotogrames)')
    for b in ('gran', 'mitjana', 'fina'):
        print(f'  {b:8s}: ρ {corr(Bl[b], Bo[b], m):+.3f} | ' + ' '.join(f'{lo}-{hi}:{corr(Bl[b], Bo[b], m & (th >= lo) & (th < hi)):+.2f}' for lo, hi in SECT) +
              f' | rms LOLA {np.std(Bl[b][m]):.3f} obs {np.std(Bo[b][m]):.3f} resid {np.std((Bo[b] - Bl[b])[m]):.3f}')
    # residu robust per fotograma i on són els atípics
    rr = np.array([res[i] for i in range(nJ)]); ww = np.array([Wt[i] for i in range(nJ)])
    rob_f = [1.4826 * np.median(np.abs(rr[i][ww[i] > 0])) for i in range(nJ)]
    print('residu robust per fotograma (px):', ' '.join(f'{J[i]}:{rob_f[i]:.3f}' for i in range(nJ)))
    mres = np.where(Wsum > 0, (S - Wsum * pc[-1] * hl) / np.maximum(Wsum, 1e-30), np.nan)
    big = np.argsort(-np.abs(np.nan_to_num(mres)))[:25]
    print('calaixos amb residu mitjà més gran (θ: px):', ' '.join(f'{th[k]:.2f}:{mres[k]:+.2f}' for k in sorted(big)))
    np.savez_compressed(H / 'E5_OBS_I_LOLA.npz', obs=obs, lola=pc[-1] * hl, W=Wsum, theta=th, resid_mitja=mres)
