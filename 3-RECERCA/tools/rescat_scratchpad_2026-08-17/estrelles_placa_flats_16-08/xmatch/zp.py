"""Punt zero fotometric de cada tren.
   V_cat - m_inst = ZP - k*X - c*(B-V)
   m_inst = -2.5 log10(flux total ADU/s, superficie verda)
Ajusta ZP, k (extincio) i c (terme de color) alhora, amb rebuig d'atipics."""
import numpy as np, pandas as pd, json
from skyfield.api import load, wgs84, Star

ts = load.timescale()
eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')
lloc = eph['earth'] + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
TEMP, PRES = 20.0, 930.0
EPOCHS = {'sony': (2026, 8, 12, 18, 29, 48.0), 'r6': (2026, 8, 12, 18, 29, 18.6)}
RAP = {'sony': 6, 'r6': 7}


def kasten_young(alt_deg):
    a = np.asarray(alt_deg, float)
    return 1.0/(np.sin(np.radians(a)) + 0.50572*(a + 6.07995)**(-1.6364))


def airmass_of(tag, tab):
    t = ts.utc(*EPOCHS[tag])
    cat = pd.read_csv(f'cat2_{tag}.csv')
    key = cat.set_index('TYC')
    alt = []
    for tyc in tab.TYC:
        r = key.loc[tyc]
        st = Star(ra_hours=float(r._RAJ2000)/15., dec_degrees=float(r._DEJ2000))
        ap = lloc.at(t).observe(st).apparent()
        a, _, _ = ap.altaz(temperature_C=TEMP, pressure_mbar=PRES)
        alt.append(a.degrees)
    alt = np.array(alt)
    return alt, kasten_young(alt)


def fit(y, X, BV, w=None, clip=2.5, fit_k=True, fit_c=True):
    ok = np.isfinite(y) & np.isfinite(X) & (np.isfinite(BV) | (not fit_c))
    bv = np.where(np.isfinite(BV), BV, 0.0)
    for _ in range(6):
        cols = [np.ones(ok.sum())]
        if fit_k:
            cols.append(-X[ok])
        if fit_c:
            cols.append(-bv[ok])
        A = np.column_stack(cols)
        sol, *_ = np.linalg.lstsq(A, y[ok], rcond=None)
        pred = A@sol
        r = y[ok]-pred
        s = 1.4826*np.median(np.abs(r-np.median(r)))
        bad = np.abs(r-np.median(r)) > clip*max(s, 0.02)
        idx = np.where(ok)[0]
        if not bad.any():
            break
        ok[idx[bad]] = False
    # residus finals
    cols = [np.ones(ok.sum())]
    if fit_k:
        cols.append(-X[ok])
    if fit_c:
        cols.append(-bv[ok])
    A = np.column_stack(cols)
    sol, *_ = np.linalg.lstsq(A, y[ok], rcond=None)
    res = y[ok]-A@sol
    n, p = ok.sum(), A.shape[1]
    s2 = (res**2).sum()/max(n-p, 1)
    cov = s2*np.linalg.inv(A.T@A)
    return sol, np.sqrt(np.diag(cov)), ok, float(np.sqrt(s2))


out = {}
for tag in ('sony', 'r6'):
    tab = pd.read_csv(f'final_match_{tag}.csv')
    z = np.load(f'phot_{tag}.npz', allow_pickle=True)
    F = z['F']; exp = z['exp']
    W = exp[:, None, None]
    Fc = np.nansum(F*W, axis=0)/np.nansum(np.where(np.isfinite(F), W, 0), axis=0)
    cg = np.load(f'cogf_{tag}.npz')
    rap = RAP[tag]
    corr = cg['ref'][rap-1]/np.nanmedian(cg['ref'][13:18])   # r_ap -> total
    flux = Fc[:, rap-1]/corr
    tab['flux_tot'] = flux
    minst = -2.5*np.log10(np.where(flux > 0, flux, np.nan))
    tab['minst'] = minst
    alt, X = airmass_of(tag, tab)
    tab['alt'] = alt; tab['X'] = X
    y = tab.V.values - minst

    print(f'================ {tag} ================')
    print(f'  obertura r={rap} px, correccio d\'obertura {1/corr:.4f} '
          f'({-2.5*np.log10(corr):+.3f} mag)')
    print(f'  altura de les estrelles: {alt.min():.2f} a {alt.max():.2f} deg  '
          f'-> massa d\'aire {X.min():.2f} a {X.max():.2f}')

    for label, fk, fc in (('ZP + k + color', True, True),
                          ('ZP + k        ', True, False),
                          ('ZP nomes      ', False, False)):
        sol, err, ok, rms = fit(y, X, tab.BV.values, fit_k=fk, fit_c=fc)
        s = f'  {label}: n={ok.sum():2d}/{len(y)}  rms={rms:.3f} mag  ZP={sol[0]:+.3f}+-{err[0]:.3f}'
        i = 1
        if fk:
            s += f'  k={sol[i]:+.4f}+-{err[i]:.4f}'; i += 1
        if fc:
            s += f'  c={sol[i]:+.3f}+-{err[i]:.3f}'
        print(s)
    sol, err, ok, rms = fit(y, X, tab.BV.values, fit_k=True, fit_c=True)
    ZP, k, c = sol
    # ZP a massa d'aire 0 i el ZP "efectiu" a X del Sol
    tsun = ts.utc(*EPOCHS[tag])
    aps = lloc.at(tsun).observe(eph['sun']).apparent()
    salt, _, _ = aps.altaz(temperature_C=TEMP, pressure_mbar=PRES)
    Xsun = kasten_young(salt.degrees)
    print(f'  Sol: altura refractada {salt.degrees:.3f} deg -> X={Xsun:.3f}')
    print(f'  ZP fora de l\'atmosfera = {ZP:+.3f} +- {err[0]:.3f} mag')
    print(f'  extincio al Sol A_V = k*X = {k*Xsun:.3f} mag')
    print(f'  ZP efectiu al Sol (ZP - k*X) = {ZP-k*Xsun:+.3f} mag')
    tab['resid_zp'] = y - (ZP - k*tab.X.values - c*np.where(np.isfinite(tab.BV), tab.BV, 0))
    tab['usat'] = ok
    tab.to_csv(f'zp_{tag}.csv', index=False)
    out[tag] = dict(ZP=float(ZP), eZP=float(err[0]), k=float(k), ek=float(err[1]),
                    c=float(c), ec=float(err[2]), rms=float(rms), n=int(ok.sum()),
                    Xsun=float(Xsun), rap=rap, apcorr=float(1/corr),
                    ZPeff=float(ZP-k*Xsun))
    print()
json.dump(out, open('zp.json', 'w'), indent=1)
