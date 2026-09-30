"""m1e (V106, Claude: m1d de «LOLA fi» amb sectors i franges per variables d'entorn M1E_SECTORS i M1E_BANDES) · La prova m1 (fracció lunar, mètode del verificador) AGREGADA per franges de d: les correlacions creuades A–B i
l'autocorrelació de B de cada d de la franja (pas 0,25 px) es sumen ponderades pel nombre de mostres abans d'ajustar a·ACF + b·ACF(desplaçada).
Menys soroll que una sola d. Referència de soroll: la mateixa estimació amb desfasaments falsos (−p, ±1,6p, ±2,2p).
Ús: m1d_agregat.py <DELTA.npz> [...]"""
import sys, json, numpy as np
def analitza(path):
    Z = np.load(path); dg = Z['dgrid']; nth = int(Z['nth']); dth = np.degrees(np.linspace(0, 2 * np.pi, nth, endpoint=False))
    C = {int(r[0]): (r[1], r[2]) for r in Z['centres']}; A = [j for j in C if j <= 10]; B = [j for j in C if 13 <= j <= 18]
    dx = np.mean([C[j][0] for j in B]) - np.mean([C[j][0] for j in A]); dy = np.mean([C[j][1] for j in B]) - np.mean([C[j][1] for j in A])
    XA, PA, XB, PB = np.nan_to_num(Z['hA']), Z['pA'], np.nan_to_num(Z['hB']), Z['pB']
    lags = np.arange(-24, 25)
    def xc(X, PX, Y, PY, i, s):
        out = []; n = 0
        for L in lags:
            y = np.roll(Y[i], -L); py = np.roll(PY[i], -L); m = s & (PX[i] > 0) & (py > 0)
            out.append(np.corrcoef(X[i][m], y[m])[0, 1] if m.sum() > 150 and X[i][m].std() > 0 and y[m].std() > 0 else np.nan)
            if L == 0: n = int(m.sum())
        return np.array(out), n
    def frac(cc, ac, sh):
        acs = lambda s_: np.interp(lags - s_, lags, ac); M = np.stack([acs(0), acs(sh)], 1); ok = np.isfinite(cc) & np.isfinite(M).all(1) & (np.abs(lags) <= 16)
        if ok.sum() < 10: return np.nan
        (a, b), *_ = np.linalg.lstsq(M[ok], cc[ok], rcond=None); return b / (a + b) if (a + b) > 0 else np.nan
    res = {}
    import os
    SECT = json.loads(os.environ.get('M1E_SECTORS', '[[60,100],[100,140],[200,240],[240,280],[280,320]]')); BAN = json.loads(os.environ.get('M1E_BANDES', '[[0.5,1.5],[1.0,4.0],[2.0,4.0]]'))
    for lo, hi in SECT:
        tc = np.radians((lo + hi) / 2); pred = (dx * (-np.sin(tc)) + dy * (-np.cos(tc))) / 0.5; s = (dth >= lo) & (dth < hi)
        if hi - lo > 40:   # sector ampli: prediccions diferents a cada meitat → es fa per subsectors i se sumen les fraccions ponderades
            pass
        for dlo, dhi in BAN:
            CC = np.zeros(lags.size); AC = np.zeros(lags.size); NW = 0
            for d in np.arange(dlo, dhi + 1e-6, 0.25):
                i = int(np.argmin(np.abs(dg - d))); cc, n = xc(XA, PA, XB, PB, i, s); ac, _ = xc(XB, PB, XB, PB, i, s)
                if n < 150 or np.isnan(cc).all() or np.isnan(ac).all(): continue
                CC += n * np.nan_to_num(cc); AC += n * np.nan_to_num(ac); NW += n
            if NW == 0: res[(lo, hi, dlo, dhi)] = (np.nan, np.nan, 0); continue
            CC /= NW; AC /= NW; f = frac(CC, AC, pred)
            fk = np.array([frac(CC, AC, sh) for sh in (-pred, 1.6 * pred, -1.6 * pred, 2.2 * pred, -2.2 * pred)])
            res[(lo, hi, dlo, dhi)] = (f, float(np.sqrt(np.nanmean(fk ** 2))), NW)
    return res
if __name__ == '__main__':
    rows = {}
    for p in sys.argv[1:]:
        rows[p] = analitza(p)
    keys = list(next(iter(rows.values())).keys())
    print('sector  franja d | ' + ' | '.join(p.split('/')[-2][:18] for p in rows))
    for k in keys:
        lo, hi, dlo, dhi = k
        print(f'{lo:3d}-{hi:<3d} {dlo:g}–{dhi:g}  | ' + ' | '.join(f'{rows[p][k][0]:+.2f} (±{rows[p][k][1]:.2f})' if np.isfinite(rows[p][k][0]) else '   —          ' for p in rows))
