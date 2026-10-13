"""Sensibilitat dels punts zero per canal. AFEGIT DESPRÉS de veure el primer resultat
(post hoc): no canvia cap valor adoptat de ZP_CANAL.json; només mesura com de fràgil és.

Motiu: a ZP_CANAL.json el jackknife per estrelles i la permutació del (B−V) (tots dos
predeclarats) mostren que el retall iteratiu a 2,5σ amb 20–21 estrelles fa saltar el
resultat quan es treu una sola estrella, i que la fórmula del jackknife no és vàlida per
a un estimador discontinu. Aquí es dona:
  1. deixar-ne-una-fora: el valor de m☉ per a cada estrella treta (quina el mou);
  2. bootstrap per estrelles (2.000 mostres, llavor 20261011), amb TOT l'ajust (retall
     inclòs), conjunt als tres canals: percentils de m☉, de fac i dels quocients F☉,c/F☉,G;
  3. sense retall (totes les estrelles amb fotometria, mínims quadrats simples);
  4. obertures fixes sense correcció d'obertura (r = 7, 10, 14 px);
  5. rèplica Sony (verd): permutació del (B−V), deixar-ne-una-fora i bootstrap.

Sortida: resultats/msb_calibrat_20261011/zp_canal/SENSIBILITAT_ZP.json
"""
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import zp_canal as Z  # noqa: E402  (reutilitza wls, minst_from_phot, airmass… sense executar main)
os.chdir(Z.comu.work("xmatch"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NBOOT = 2000


def m_sol_fit(y, BV, dX, ok0=None, clip=True):
    A = np.column_stack([np.ones(len(y)), -dX, -BV])
    if clip:
        s, e, ok, rms, cov = Z.wls(A, y)
    else:
        ok = np.ones(len(y), bool)
        s, cov, rms = Z.fit_fixed(A, y, ok)
    return float(s[0] - Z.BV_SOL*s[2]), s, ok, rms, cov


def fac_of(m, Rsun_px):
    return float(np.pi*Rsun_px**2/10**(0.4*(m - Z.M_SOL)))


def pct(v):
    v = np.asarray(v)
    v = v[np.isfinite(v)]
    return dict(p2_5=float(np.percentile(v, 2.5)), p16=float(np.percentile(v, 16)),
                p50=float(np.percentile(v, 50)), p84=float(np.percentile(v, 84)),
                p97_5=float(np.percentile(v, 97.5)), n=int(len(v)))


def main():
    t0 = time.time()
    tab = pd.read_csv('final_match_r6.csv')
    sol = json.load(open('final_solution.json'))
    Rsun_px = Z.RSUN_AS/sol['r6']['scale']
    alt, X, Xsun, salt = Z.airmass(tab)
    dX = X - Xsun
    BV = tab.BV.values.astype(float)
    out = dict(tasca='msb_calibrat_20261011/zp_canal', caracter='POST HOC: no canvia els valors adoptats',
               data=time.strftime('%Y-%m-%dT%H:%M:%S'), r6={}, sony_G={})
    ph = {ch: Z.minst_from_phot(Z.CANAL/f'phot_r6_{ch}_interp.npz', tab) for ch in 'RGB'}
    y = {ch: tab.V.values - ph[ch]['minst'] for ch in 'RGB'}
    fin = {ch: np.isfinite(y[ch]) for ch in 'RGB'}

    # 1. deixar-ne-una-fora (per canal, amb les estrelles amb fotometria del canal)
    for ch in 'RGB':
        f = fin[ch]
        m0, s0, ok0, _, _ = m_sol_fit(y[ch][f], BV[f], dX[f])
        loo = {}
        for j in np.where(f)[0]:
            keep = f.copy()
            keep[j] = False
            m, s, ok, rms, _ = m_sol_fit(y[ch][keep], BV[keep], dX[keep])
            loo[tab.det.values[j]] = dict(m_sol=m, dif_mag=m - m0, n=int(ok.sum()), rms=rms)
        difs = np.array([v['dif_mag'] for v in loo.values()])
        out['r6'][ch] = dict(m_sol=m0, fac=fac_of(m0, Rsun_px),
                             deixar_una_fora=dict(per_estrella=loo, dif_min=float(difs.min()), dif_max=float(difs.max()),
                                                  n_que_mouen_mes_de_0_02=int((np.abs(difs) > 0.02).sum())))
        # 3. sense retall
        m, s, ok, rms, cov = m_sol_fit(y[ch][f], BV[f], dX[f], clip=False)
        a = np.array([1.0, 0.0, -Z.BV_SOL])
        out['r6'][ch]['sense_retall'] = dict(n=int(ok.sum()), ZP=float(s[0]), k=float(s[1]), c=float(s[2]),
                                             rms=rms, m_sol=m, sigma_m_sol=float(np.sqrt(a@cov@a)),
                                             fac=fac_of(m, Rsun_px))
        # 4. obertures fixes sense correcció
        z = np.load(Z.CANAL/f'phot_r6_{ch}_interp.npz', allow_pickle=True)
        F = z['F']
        W = z['exp'][:, None, None]
        with np.errstate(invalid='ignore', divide='ignore'):
            Fc = np.nansum(F*W, axis=0)/np.nansum(np.where(np.isfinite(F), W, 0), axis=0)
        fixes = {}
        for r in (7, 10, 14):
            with np.errstate(invalid='ignore', divide='ignore'):
                mi = -2.5*np.log10(np.where(Fc[:, r-1] > 0, Fc[:, r-1], np.nan))
            yy = tab.V.values - mi
            ff = np.isfinite(yy)
            m, s, ok, rms, cov = m_sol_fit(yy[ff], BV[ff], dX[ff])
            fixes[f'r{r}'] = dict(n=int(ok.sum()), n_amb_fotometria=int(ff.sum()), c=float(s[2]), rms=rms,
                                  m_sol=m, fac=fac_of(m, Rsun_px))
        out['r6'][ch]['obertura_fixa_sense_correccio'] = fixes

    # 2. bootstrap conjunt (estrelles amb fotometria als tres canals)
    rng = np.random.default_rng(Z.SEED)
    fall = fin['R'] & fin['G'] & fin['B']
    idx = np.where(fall)[0]
    ms = {ch: [] for ch in 'RGB'}
    for _ in range(NBOOT):
        b = rng.choice(idx, size=len(idx), replace=True)
        for ch in 'RGB':
            try:
                m, *_ = m_sol_fit(y[ch][b], BV[b], dX[b])
            except np.linalg.LinAlgError:
                m = np.nan
            ms[ch].append(m)
    ms = {ch: np.array(v) for ch, v in ms.items()}
    boot = dict(n_mostres=NBOOT, llavor=Z.SEED, n_estrelles=int(len(idx)))
    for ch in 'RGB':
        boot[f'm_sol_{ch}'] = pct(ms[ch])
        boot[f'fac_{ch}'] = pct([fac_of(m, Rsun_px) for m in ms[ch] if np.isfinite(m)])
    for ch in 'RB':
        boot[f'F_sol_{ch}_sobre_G'] = pct(10**(0.4*(ms[ch] - ms['G'])))
    out['r6']['bootstrap_conjunt'] = boot

    # 5. rèplica Sony, verd (phot_sony.npz i zp_sony.csv de la cadena original regenerada)
    d = pd.read_csv('zp_sony.csv')
    zpj = json.load(open('zp.json'))
    Xs = zpj['sony']['Xsun']
    d = d[np.isfinite(d.minst)].reset_index(drop=True)
    ys = (d.V - d.minst).values
    BVs = np.where(np.isfinite(d.BV), d.BV, 0.0)
    dXs = d.X.values - Xs
    Rsun_s = Z.RSUN_AS/sol['sony']['scale']
    m0, s0, ok0, rms0, cov0 = m_sol_fit(ys, BVs, dXs)
    perm = Z.permutation_c(ys, BVs, dXs, s0[2], np.random.default_rng(Z.SEED))
    loo = []
    for j in range(len(ys)):
        keep = np.ones(len(ys), bool)
        keep[j] = False
        m, *_ = m_sol_fit(ys[keep], BVs[keep], dXs[keep])
        loo.append(m - m0)
    rng = np.random.default_rng(Z.SEED)
    mb = []
    for _ in range(NBOOT):
        b = rng.integers(0, len(ys), len(ys))
        try:
            m, *_ = m_sol_fit(ys[b], BVs[b], dXs[b])
        except np.linalg.LinAlgError:
            m = np.nan
        mb.append(m)
    a = np.array([1.0, 0.0, -Z.BV_SOL])
    ms0, ss0, oks0, rmss0, covs0 = m_sol_fit(ys, BVs, dXs)
    out['sony_G'] = dict(n=int(ok0.sum()), n_amb_fotometria=int(len(ys)), ZP=float(s0[0]), k=float(s0[1]),
                         c=float(s0[2]), rms=rms0, m_sol=m0, sigma_m_sol_cov=float(np.sqrt(a@cov0@a)),
                         fac=fac_of(m0, Rsun_s), fac_ref_17_08=1.1351916390017417e-11,
                         n_BV_absent_posat_a_0=int((~np.isfinite(d.BV)).sum()),
                         permutacio_terme_color=perm,
                         deixar_una_fora=dict(dif_min=float(np.min(loo)), dif_max=float(np.max(loo))),
                         bootstrap=dict(m_sol=pct(mb), fac=pct([fac_of(m, Rsun_s) for m in mb if np.isfinite(m)])))
    out['segons'] = round(time.time()-t0, 1)
    json.dump(out, open(Z.RES/'SENSIBILITAT_ZP.json', 'w'), indent=1, ensure_ascii=False)
    # resum a la pantalla
    for ch in 'RGB':
        r = out['r6'][ch]
        print(f"{ch}: m☉ {r['m_sol']:+.4f}  fac {r['fac']:.4e}  LOO {r['deixar_una_fora']['dif_min']:+.3f}…"
              f"{r['deixar_una_fora']['dif_max']:+.3f}  boot p16–p84 {boot[f'm_sol_{ch}']['p16']:+.3f}…"
              f"{boot[f'm_sol_{ch}']['p84']:+.3f}  sense retall {r['sense_retall']['m_sol']:+.4f} (n {r['sense_retall']['n']}, "
              f"rms {r['sense_retall']['rms']:.3f}, c {r['sense_retall']['c']:+.3f})  fixes "
              + ' '.join(f"{k}:{v['m_sol']:+.3f}" for k, v in r['obertura_fixa_sense_correccio'].items()))
    for ch in 'RB':
        print(f"F☉{ch}/F☉G boot: {boot[f'F_sol_{ch}_sobre_G']}")
    print('Sony G:', json.dumps({k: v for k, v in out['sony_G'].items() if k != 'bootstrap'}, indent=0))
    print('Sony G boot:', out['sony_G']['bootstrap'])


if __name__ == '__main__':
    main()
