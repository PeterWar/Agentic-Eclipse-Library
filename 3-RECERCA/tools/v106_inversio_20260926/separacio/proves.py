"""proves (V106 · Separació) · La prova «Lluna o corona» (còpia fidel de m1_fraccio_lunar.py, en memòria) i la reproductibilitat ρ."""
import numpy as np
from scipy.ndimage import gaussian_filter1d
SECTORS = [(60, 100), (100, 140), (140, 180), (200, 240), (240, 280), (280, 320)]
DS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
def m1(dg, nth, hA, pA, hB, pB, cA, cB, verbose=False):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); dth = np.degrees(th)
    dx = cB[0] - cA[0]; dy = cB[1] - cA[1]
    XA, PA, XB, PB = np.nan_to_num(hA), pA, np.nan_to_num(hB), pB; lags = np.arange(-16, 17)
    def xc(X, PX, Y, PY, i, s):
        out = []
        for L in lags:
            y = np.roll(Y[i], -L); py = np.roll(PY[i], -L); m = s & (PX[i] > 0) & (py > 0)
            out.append(np.corrcoef(X[i][m], y[m])[0, 1] if m.sum() > 150 and X[i][m].std() > 0 and y[m].std() > 0 else np.nan)
        return np.array(out)
    res = {}
    for lo, hi in SECTORS:
        tc = np.radians((lo + hi) / 2); pred = (dx * (-np.sin(tc)) + dy * (-np.cos(tc))) / 0.5; s = (dth >= lo) & (dth < hi)
        for d in DS:
            i = int(np.argmin(np.abs(dg - d))); cc = xc(XA, PA, XB, PB, i, s); ac = xc(XB, PB, XB, PB, i, s)
            if np.isnan(cc).all() or np.isnan(ac).all(): continue
            acs = lambda sh: np.interp(lags - sh, lags, ac); M = np.stack([acs(0), acs(pred)], 1); ok = np.isfinite(cc) & np.isfinite(M).all(1)
            if ok.sum() < 10: continue
            (a, b), *_ = np.linalg.lstsq(M[ok], cc[ok], rcond=None); f = b / (a + b) if (a + b) > 0 else np.nan
            res[(lo, hi, d)] = dict(f=float(f), a=float(a), b=float(b), cc0=float(cc[16]), n=int((s & (PA[i] > 0) & (PB[i] > 0)).sum()))
            if verbose: print(f'{lo:3d}-{hi:3d} d {d:3.1f} | fracció lunar {f:+.2f} | corona {a:+.2f} Lluna {b:+.2f} | n {res[(lo, hi, d)]["n"]}')
    return res
def rho(dg, nth, X, PX, Y, PY, sectors=SECTORS, ds=DS):
    """ρ entre dues estimacions independents, per sector i d (correlació de Pearson al llarg de l'arc, desfasament 0)."""
    dth = np.degrees(np.linspace(0, 2 * np.pi, nth, endpoint=False)); out = {}
    for lo, hi in sectors:
        s = (dth >= lo) & (dth < hi)
        for d in ds:
            i = int(np.argmin(np.abs(dg - d))); m = s & (PX[i] > 0) & (PY[i] > 0)
            if m.sum() > 150 and X[i][m].std() > 0 and Y[i][m].std() > 0: out[(lo, hi, d)] = (float(np.corrcoef(X[i][m], Y[i][m])[0, 1]), int(m.sum()))
    return out
def taula(res, clau='f', fmt='{:+.2f}'):
    secs = sorted(set((k[0], k[1]) for k in res)); lines = []
    for s in secs:
        lines.append(f'{s[0]:3d}-{s[1]:3d}: ' + ' '.join(f'd{d:g}:' + fmt.format(res[(s[0], s[1], d)][clau] if isinstance(res[(s[0], s[1], d)], dict) else res[(s[0], s[1], d)][0]) for d in DS if (s[0], s[1], d) in res))
    return '\n'.join(lines)
