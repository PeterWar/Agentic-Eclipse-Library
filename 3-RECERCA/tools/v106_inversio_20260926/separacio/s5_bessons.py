"""s5 (V106 · Separació) · BESSONS SINTÈTICS: veritat C* = Ĉ real i Λ* = Λ̂ real (el model exacte), soroll = residus reals de cada
fotograma amb signe aleatori per fotograma (conserva l'estructura espacial i l'amplitud del soroll real, trenca l'ortogonalitat amb l'ajust)
i inflats per la palanca. Es passa tota la cadena (IRLS, inversions S1/S2, m1, ρ). Si el model rígid fos cert, això és el que veuríem."""
import numpy as np, sys, json, time
from pipeline import Pipeline
from proves import m1, rho, taula
cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
TAG = sys.argv[2] if len(sys.argv) > 2 else 'base'; SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
P = Pipeline(cfg); t0 = time.time()
IR = P.inverteix(P.fr)                                 # ajust real (veritat del bessó)
S = IR.S; nd, nth = len(S.dg), S.nth; Wt = IR.Wt.reshape(nd, nth); Cst = IR.C.copy()
rng = np.random.default_rng(SEED); sgn = {j: rng.choice([-1.0, 1.0]) for j in P.fr}
Y = {}
for j in P.fr:
    c = IR.cache[j]; w = IR.pes(j); hh = np.clip(w / np.maximum(Wt, 1e-300), 0, 0.9)
    lamj = IR.A[j] * IR.avalua_lam(c['a'], c['D'])
    r = np.where(c['ok'], (c['d'] - Cst - lamj) / np.sqrt(1 - hh), 0.0)
    Y[j] = np.where(c['ok'], Cst + lamj + sgn[j] * r, 0.0).astype(np.float32)
print('bessó construït', round(time.time() - t0), 's', flush=True)
R = P.proves(ydelta=lambda j: Y[j])
i4 = S.i4; IT = R['IT']
# error real de Ĉ contra la veritat i fuita del terme lunar
err = IT.C - Cst; W = IT.Wt.reshape(nd, nth); dth = S.dth
print('--- error de Ĉ contra la veritat (rms) i rms de la veritat ---')
for lo, hi in [(60, 100), (200, 220), (220, 240), (240, 260), (260, 280), (280, 320)]:
    s = (dth >= lo) & (dth < hi)
    print(f'{lo}-{hi}: ' + ' '.join(f'd{d:g}:{np.std(err[int(np.argmin(abs(S.dg-d)))][s & (W[int(np.argmin(abs(S.dg-d)))]>0)]):.3f}/{np.std(Cst[int(np.argmin(abs(S.dg-d)))][s & (W[int(np.argmin(abs(S.dg-d)))]>0)]):.3f}' for d in [0.5, 1, 1.5, 2, 3, 4, 6] if (s & (W[int(np.argmin(abs(S.dg-d)))]>0)).sum() > 60))
json.dump(dict(cfg=P.cfg, m1={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['m1'].items()}, rho={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['rho'].items()}), open(f'BESSONS_{TAG}_s{SEED}.json', 'w'), indent=1)
print('fet', round(time.time() - t0), 's')
