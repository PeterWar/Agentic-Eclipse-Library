"""s8 (V106 · Separació, Claude, 26-09-2026) · INJECCIÓ als δ_j REALS: un patró fix al Sol, C_inj = a_C·cos(2πs/λ_C + ψ), i un patró fix a
la Lluna, Λ_inj = a_L·h(D)·cos(2πs_φ/λ_L), a la vegada (λ_L ≠ λ_C per poder-los separar per demodulació). Es passa TOTA la cadena real
(IRLS amb el soroll re-estimat) i es resta la solució sense injecció. Mesures per sector i d:
  · fracció i fase de C_inj recuperada a Ĉ;  · amplitud de Λ_inj que queda a Ĉ, relativa a la que queda a la mitjana ingènua."""
import numpy as np, sys, json, time
from pipeline import Pipeline
cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
TAG = sys.argv[2] if len(sys.argv) > 2 else 'base'
P = Pipeline(cfg); t0 = time.time()
Ib = P.inverteix(P.fr); S = Ib.S; nd, nth = len(S.dg), S.nth; Cb = Ib.C.copy(); Wt = Ib.Wt.reshape(nd, nth); vt_base = Ib.var_tab
L = Ib.Lam(); Dn = Ib.D0 + Ib.dD * np.arange(Ib.nD); hD = np.array([np.sqrt(np.mean(L[k][Ib.lam_obs[k]] ** 2)) for k in range(Ib.nD)]); hD /= hD[np.argmin(abs(Dn - P.cfg['LO']))]
def h(D): return np.where(D < P.cfg['DMAX'], np.interp(D, np.r_[Dn, P.cfg['DMAX']], np.r_[hD, 0.0]), 0.0)
BASE = {j: Ib.cache[j]['d'].copy() for j in P.fr}
ith = np.arange(nth); dth = S.dth
SECT = [(60, 100), (100, 140), (200, 220), (220, 240), (240, 260), (260, 280), (280, 320)]
DS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]; rows = {d: int(np.argmin(abs(S.dg - d))) for d in DS}
def demod(X, w_, W):
    out = {}
    for lo, hi in SECT:
        s = (dth >= lo) & (dth < hi)
        for d, i in rows.items():
            m = s & (W[i] > 0)
            if m.sum() < 60: continue
            out[(lo, hi, d)] = np.sum(X[i][m] * np.exp(-1j * w_ * ith[m])) / m.sum()
    return out
aC, aL = 0.03, 0.15
res = {'cfg': P.cfg, 'aC': aC, 'aL': aL, 'parells': {}}
for lamC, lamL in [(4, 5), (8, 10), (16, 20)]:
    wC = 2 * np.pi * 0.5 / lamC; wL = 2 * np.pi * 0.5 / lamL
    Cinj = aC * np.cos(wC * ith + 0.7)[None, :] * np.ones((nd, 1))
    INJ = {}
    for j in P.fr:
        c = Ib.cache[j]; INJ[j] = (BASE[j] + np.where(c['ok'], Cinj + aL * h(c['D']) * np.cos(wL * c['a'] / 360.0 * nth), 0.0)).astype(np.float32)
    I = P.nova(); I.cache = Ib.cache                                                     # mateixa geometria
    for jj in P.fr: I.cache[jj]['d'] = INJ[jj]
    I.var_tab = None; I.frames = P.fr
    for it in range(P.cfg['irls'] + 1):                                                  # IRLS complet sobre la dada injectada
        I.construeix(P.fr); I.resol(ridge=P.cfg['ridge'], regD=P.cfg['regD'])
        if it < P.cfg['irls']: I.reestima_soroll()
    dC = I.C - Cb
    # mitjana ingènua de la part lunar injectada (pesos de la inversió injectada)
    sw = np.zeros((nd, nth)); sy = np.zeros_like(sw)
    for j in P.fr:
        c = I.cache[j]; w = I.pes(j) * c['ok']; sw += w; sy += w * np.where(c['ok'], aL * h(c['D']) * np.cos(wL * c['a'] / 360.0 * nth), 0)
    naiv = np.where(sw > 0, sy / np.maximum(sw, 1e-300), 0)
    zc = demod(dC, wC, Wt); zt = demod(Cinj, wC, Wt); zl = demod(dC, wL, Wt); zn = demod(naiv, wL, Wt)
    out = {}
    for k in zc:
        out[f'{k[0]}-{k[1]} d{k[2]}'] = dict(C_frac=float(abs(zc[k] / zt[k])), C_fase=float(np.degrees(np.angle(zc[k] / zt[k]))),
                                              lluna_a_C=float(2 * abs(zl[k])), lluna_ingenu=float(2 * abs(zn[k])), fuita=float(abs(zl[k]) / max(abs(zn[k]), 1e-9)))
    res['parells'][f'{lamC}/{lamL}'] = out
    for jj in P.fr: Ib.cache[jj]['d'] = BASE[jj]
    print(f'λ_C {lamC} / λ_L {lamL}', round(time.time() - t0), 's', flush=True)
json.dump(res, open(f'INJECCIO_{TAG}.json', 'w'), indent=1)
print('clau: C = fracció recuperada (fase°) | fuita = Λ_inj que queda a Ĉ / la que queda a la mitjana ingènua (amplitud a Ĉ)')
for sec in SECT:
    print('==', f'{sec[0]}-{sec[1]}')
    for d in DS:
        k = f'{sec[0]}-{sec[1]} d{d}'
        if k not in res['parells']['8/10']: continue
        print(f'  d{d:3.1f} ' + ' | '.join(f"{p}: C {res['parells'][p][k]['C_frac']:.2f}({res['parells'][p][k]['C_fase']:+.0f}°) fuita {res['parells'][p][k]['fuita']:.2f} ({res['parells'][p][k]['lluna_a_C']:.3f})" for p in res['parells'] if k in res['parells'][p]))
