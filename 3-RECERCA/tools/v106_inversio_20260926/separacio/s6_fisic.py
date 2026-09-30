"""s6 (V106 · Separació) · Prova FÍSICA del model: fotogrames sintètics generats a nivell de ln L (abans del pas alt), amb la geometria i
les màscares reals: ln L_j = C*(θ,d) + ln T(D_j − r(φ_j)), T = PSF gaussiana (σ = 1,2 px) + halo (f = 0,3, σ_a = 2,5 px), r = relleu
sintètic (camp aleatori de banda limitada, rms 0,8 px, fix a la Lluna), C* = detall real Ĉ. Després el MATEIX pas alt per fotograma de
la c1 i la inversió conjunta. Sense soroll: mesura el biaix del mètode (el pas alt de cada fotograma talla la vora lunar en angles diferents)."""
import numpy as np, sys, json, time
from scipy.ndimage import gaussian_filter1d
from scipy.special import erf
from pipeline import Pipeline
cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
TAG = sys.argv[2] if len(sys.argv) > 2 else 'base'
SOROLL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
P = Pipeline(cfg); t0 = time.time()
IR = P.inverteix(P.fr); S = IR.S; nd, nth = len(S.dg), S.nth; Cst = IR.C.copy(); Wt = IR.Wt.reshape(nd, nth)
rng = np.random.default_rng(7)
# relleu sintètic fix a la Lluna: soroll blanc suavitzat (σ 1,5 px d'arc) normalitzat a rms 0,8 px
nphi = 5760; r = gaussian_filter1d(rng.standard_normal(nphi), 1.5 / (2 * np.pi * S.R / nphi), mode='wrap'); r *= 0.8 / r.std()
def rel(a): return np.interp(a, np.arange(nphi) * 360.0 / nphi, r, period=360)
def lnT(D): return np.log(np.maximum(0.7 * 0.5 * (1 + erf(D / (np.sqrt(2) * 1.2))) + 0.3 * 0.5 * (1 + erf(D / (np.sqrt(2) * 2.5))), 1e-6))
def hp(j, X, D):
    v = np.asarray(S.OK[j]) & (D >= P.cfg['LO']); lL = np.where(v, X, 0.0); vf = v.astype(float); sc = 32.0 / 0.5
    cw = gaussian_filter1d(vf, sc, axis=1, mode='wrap'); cm = gaussian_filter1d(lL, sc, axis=1, mode='wrap') / np.maximum(cw, 1e-12)
    fw = gaussian_filter1d(vf, 1.0, axis=1, mode='wrap'); fm = gaussian_filter1d(lL, 1.0, axis=1, mode='wrap') / np.maximum(fw, 1e-12)
    return np.where(v & (cw >= 0.9), fm - cm, 0.0)
Y = {}; Ytrue_lun = {}
for j in P.fr:
    c = IR.cache[j]; D = c['D'].astype(float); a = c['a'].astype(float)
    Y[j] = hp(j, Cst + lnT(D - rel(a)), D).astype(np.float32)
    if SOROLL > 0: Y[j] += (SOROLL * rng.standard_normal(Y[j].shape) * c['ok']).astype(np.float32)
# referència: el detall de C* passat pel mateix pas alt (sense Lluna) → és el que hauríem de recuperar
Cref = {}
print('sintètics', round(time.time() - t0), 's', flush=True)
R = P.proves(ydelta=lambda j: Y[j], var_tab=IR.var_tab if SOROLL == 0 else None)
IT = R['IT']; dth = S.dth; W = IT.Wt.reshape(nd, nth)
# mitjana ingènua (c1 amb pesos IRLS, sense Λ)
lam0 = IT.lam.copy(); IT.lam[:] = 0; Cn, _ = IT.grup(P.fr, lambda j: Y[j]); IT.lam[:] = lam0
print('--- rms de (Ĉ − C*) | rms de (ingenu − C*) | rms C* ---')
for lo, hi in [(60, 100), (100, 140), (200, 220), (220, 240), (240, 260), (260, 280), (280, 320)]:
    s = (dth >= lo) & (dth < hi); txt = []
    for d in [0.5, 1, 1.5, 2, 3, 4, 6]:
        i = int(np.argmin(abs(S.dg - d))); m = s & (W[i] > 0)
        if m.sum() > 60: txt.append(f'd{d:g}:{np.std(IT.C[i][m]-Cst[i][m]):.3f}|{np.std(Cn[i][m]-Cst[i][m]):.3f}|{np.std(Cst[i][m]):.3f}')
    print(f'{lo}-{hi}: ' + ' '.join(txt))
json.dump(dict(cfg=P.cfg, soroll=SOROLL, m1={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['m1'].items()}, rho={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['rho'].items()}), open(f'FISIC_{TAG}_n{SOROLL:g}.json', 'w'), indent=1)
print('fet', round(time.time() - t0), 's')
