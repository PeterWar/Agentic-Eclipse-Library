"""s4 (V106 · Separació, Claude, 26-09-2026) · IDENTIFICABILITAT amb simulacions: la geometria real (centres lunars dels 59 fotogrames útils,
silueta d'ordre 2, validesa i pesos IRLS reals) i el SOROLL REAL (residus de l'ajust real, inflats per la palanca). Per a cada longitud
d'ona λ al llarg de l'arc:
  (a) només C sintètic (cos 2πs/λ, fix al Sol)  → fracció recuperada i fase a Ĉ;
  (b) només Λ sintètic (cos 2πs_φ/λ · h(D), fix a la Lluna, h = perfil real de Λ̂ en D, 0 a D ≥ DMAX) → el que se'n filtra a Ĉ,
      comparat amb el que en queda a la mitjana ingènua (la c1 sense rampa);
  (c) només soroll real → rms del soroll a Ĉ i a la mitjana ingènua. El soroll real són els residus de l'ajust real de cada fotograma,
      inflats per la palanca i amb un SIGNE ALEATORI per fotograma (3 realitzacions): conserva l'amplitud i l'estructura espacial del soroll
      de cada fotograma i trenca l'ortogonalitat amb l'ajust (els residus tal qual donarien Ĉ = 0 per construcció).
Tot lineal amb pesos fixos: Ĉ(dada) = Ĉ(C) + Ĉ(Λ) + Ĉ(soroll)."""
import numpy as np, sys, json, time, pickle
from scipy.ndimage import gaussian_filter
from inversio import Inversio
cfg = dict(DMAX=4.0, dphi=0.125, LO=0.6, regD=0.05, ridge=1e-4, irls=2)
if len(sys.argv) > 1: cfg.update(json.loads(sys.argv[1]))
TAG = sys.argv[2] if len(sys.argv) > 2 else 'base'
sig = dict(np.load('SIG.npz')); t0 = time.time()
I = Inversio(sig_tab=sig, verbose=False, DMAX=cfg['DMAX'], dphi=cfg['dphi'], LO=cfg['LO'])
fr = [j for j in range(67) if sig['sig'][j].min() < 0.5]
I.prepara(fr)
for it in range(cfg['irls'] + 1):
    I.construeix(fr); I.resol(ridge=cfg['ridge'], regD=cfg['regD'])
    if it < cfg['irls']: I.reestima_soroll()
S = I.S; nd, nth = len(S.dg), S.nth; Wt = I.Wt.reshape(nd, nth); Creal = I.C.copy(); lam_real = I.lam.copy()
# perfil h(D) de la Λ real
L = I.Lam(); Dn = I.D0 + I.dD * np.arange(I.nD); hD = np.array([np.sqrt(np.mean(L[k][I.lam_obs[k]] ** 2)) for k in range(I.nD)]); hD /= hD[np.argmin(abs(Dn - cfg['LO']))]
def h(D): return np.where(D < cfg['DMAX'], np.interp(D, np.r_[Dn, cfg['DMAX']], np.r_[hD, 0.0]), 0.0)
# soroll real: residus inflats per la palanca
RES = {}
for j in fr:
    c = I.cache[j]; w = I.pes(j); hh = np.clip(w / np.maximum(Wt, 1e-300), 0, 0.9)
    RES[j] = np.where(c['ok'], (c['d'] - Creal - I.A[j] * I.avalua_lam(c['a'], c['D'])) / np.sqrt(1 - hh), 0.0).astype(np.float32)
print('ajust real i residus', round(time.time() - t0), 's', flush=True)
ith = np.arange(nth)
def naive(ydelta):
    sw = np.zeros((nd, nth)); sy = np.zeros_like(sw)
    for j in fr:
        c = I.cache[j]; w = I.pes(j) * c['ok']; sw += w; sy += w * ydelta(j)
    return np.where(sw > 0, sy / np.maximum(sw, 1e-300), 0)
def solve(ydelta):
    I.construeix(fr, ydelta=ydelta); I.resol(ridge=cfg['ridge'], regD=cfg['regD']); return I.C.copy()
SECT = [(60, 100), (100, 140), (140, 180), (180, 200), (200, 220), (220, 240), (240, 260), (260, 280), (280, 320), (320, 360), (0, 60)]
DS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
dth = S.dth; rows = {d: int(np.argmin(abs(S.dg - d))) for d in DS}
def demod(X, w_):
    out = {}
    for lo, hi in SECT:
        s = (dth >= lo) & (dth < hi)
        for d, i in rows.items():
            m = s & (Wt[i] > 0)
            if m.sum() < 60: continue
            out[(lo, hi, d)] = np.sum(X[i][m] * np.exp(-1j * w_ * ith[m])) / m.sum()
    return out
# pres: geometria de la Lluna de presentació (centre de presentació + silueta o2)
e_pres = np.interp(dth, S.SPA, S.SE, period=360); Dpres = S.dg[:, None] - e_pres[None, :]
res = {'cfg': cfg, 'lambdes': {}}
# (c) soroll real amb signe aleatori per fotograma
LAMS = [2, 3, 4, 6, 8, 12, 16, 24, 32]
rng = np.random.default_rng(11); acc = {}; accz = {l: {} for l in LAMS}
for rea in range(3):
    sg = {j: rng.choice([-1.0, 1.0]) for j in fr}
    Cn = solve(lambda j: sg[j] * RES[j]); Nn = naive(lambda j: sg[j] * RES[j])
    for lo, hi in SECT:
        s = (dth >= lo) & (dth < hi)
        for d, i in rows.items():
            m = s & (Wt[i] > 0)
            if m.sum() < 60: continue
            k = f'{lo}-{hi} d{d}'; a = acc.setdefault(k, [0.0, 0.0, 0])
            a[0] += np.var(Cn[i][m]); a[1] += np.var(Nn[i][m]); a[2] += 1
    for l in LAMS:
        z = demod(Cn, 2 * np.pi * 0.5 / l)
        for kk, v in z.items(): accz[l].setdefault(f'{kk[0]}-{kk[1]} d{kk[2]}', []).append(2 * abs(v))
noise = {}
for k, a in acc.items():
    lo, rest = k.split('-', 1); hi = rest.split(' ')[0]; d = float(k.split(' d')[1]); i = rows[d]; s = (dth >= float(lo)) & (dth < float(hi)); m = s & (Wt[i] > 0)
    noise[k] = dict(rms_C=float(np.sqrt(a[0] / a[2])), rms_ingenu=float(np.sqrt(a[1] / a[2])), rms_Creal=float(np.std(Creal[i][m])))
res['soroll'] = noise
print('soroll', round(time.time() - t0), 's', flush=True)
for lam_px in LAMS:
    w_ = 2 * np.pi * 0.5 / lam_px                  # rad per mostra (0,5 px)
    Csyn = np.cos(w_ * ith)[None, :] * np.ones((nd, 1))
    Chat = solve(lambda j: Csyn)
    zt = demod(Csyn, w_); zc = demod(Chat, w_)
    def Lsyn(j):
        c = I.cache[j]; return np.cos(w_ * c['a'] / 360.0 * nth) * h(c['D'])
    Lhat = solve(Lsyn); Lnai = naive(Lsyn)
    Lpres = np.cos(w_ * ith)[None, :] * h(Dpres) * (Dpres >= cfg['LO'])
    zl = demod(Lhat, w_); zn = demod(Lnai, w_); zp = demod(Lpres, w_); zr = demod(Creal, w_)
    out = {}
    for k in zt:
        out[f'{k[0]}-{k[1]} d{k[2]}'] = dict(C_frac=float(abs(zc[k] / zt[k])), C_fase=float(np.degrees(np.angle(zc[k] / zt[k]))),
            lluna_a_C=float(2 * abs(zl[k])), lluna_ingenu=float(2 * abs(zn[k])), lluna_pres=float(2 * abs(zp[k])),
            fuita=float(abs(zl[k]) / max(abs(zn[k]), 1e-6)), soroll_lambda=float(np.sqrt(np.mean(np.square(accz[lam_px].get(f'{k[0]}-{k[1]} d{k[2]}', [np.nan]))))),
            real_lambda=float(2 * abs(zr[k])) if k in zr else np.nan)
    res['lambdes'][lam_px] = out
    print('λ', lam_px, round(time.time() - t0), 's', flush=True)
json.dump(res, open(f'IDENT_{TAG}.json', 'w'), indent=1)
# resum
print('\nclau: fuita = amplitud lunar que queda a Ĉ / la que queda a la mitjana ingènua (sense soroll) | S/N = amplitud de Ĉ real a λ / amplitud del soroll de Ĉ a λ. La C sintètica es recupera sempre sencera (fracció 1,00, fase 0°).')
for sec in ['200-220', '220-240', '240-260', '260-280', '60-100', '280-320']:
    print('==', sec)
    for d in DS:
        k = f'{sec} d{d}'
        if k not in res['lambdes'][8]: continue
        print(f'  d{d:3.1f} soroll {noise[k]["rms_C"]:.3f} (ingenu {noise[k]["rms_ingenu"]:.3f}, Ĉ real {noise[k]["rms_Creal"]:.3f}) | ' + ' '.join(
            f'λ{l}: fuita {res["lambdes"][l][k]["fuita"]:.2f} S/N {res["lambdes"][l][k]["real_lambda"]/max(res["lambdes"][l][k]["soroll_lambda"],1e-9):.1f}' for l in [2, 4, 8, 16, 32] if k in res['lambdes'][l]))
