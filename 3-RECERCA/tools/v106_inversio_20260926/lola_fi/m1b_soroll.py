"""m1b (V106, «LOLA fi») · La prova m1 (fracció lunar) amb referència de soroll: la mateixa estimació amb desfasaments FALSOS (−pred, ±pred/2
girats, 1,5·pred…) on no hi ha res lunar ni solar; la dispersió d'aquestes fraccions falses és l'error de la prova en aquell sector i d."""
import sys, json, numpy as np
Z = np.load(sys.argv[1]); dg = Z['dgrid']; nth = int(Z['nth']); th = np.linspace(0, 2*np.pi, nth, endpoint=False); dth = np.degrees(th)
C = {int(r[0]): (r[1], r[2]) for r in Z['centres']}
A = [j for j in C if j <= 10]; B = [j for j in C if 13 <= j <= 18]
dx = np.mean([C[j][0] for j in B]) - np.mean([C[j][0] for j in A]); dy = np.mean([C[j][1] for j in B]) - np.mean([C[j][1] for j in A])
XA, PA, XB, PB = np.nan_to_num(Z['hA']), Z['pA'], np.nan_to_num(Z['hB']), Z['pB']
lags = np.arange(-24, 25)
def xc(X, PX, Y, PY, i, s):
    out = []
    for L in lags:
        y = np.roll(Y[i], -L); py = np.roll(PY[i], -L); m = s & (PX[i] > 0) & (py > 0)
        out.append(np.corrcoef(X[i][m], y[m])[0, 1] if m.sum() > 150 and X[i][m].std() > 0 and y[m].std() > 0 else np.nan)
    return np.array(out)
def frac(cc, ac, sh):
    acs = lambda s_: np.interp(lags - s_, lags, ac); M = np.stack([acs(0), acs(sh)], 1); ok = np.isfinite(cc) & np.isfinite(M).all(1) & (np.abs(lags) <= 16)
    if ok.sum() < 10: return np.nan
    (a, b), *_ = np.linalg.lstsq(M[ok], cc[ok], rcond=None); return b / (a + b) if (a + b) > 0 else np.nan
res = []
for lo, hi in [(60, 100), (100, 140), (200, 240), (240, 280), (280, 320)]:
    tc = np.radians((lo + hi) / 2); pred = (dx * (-np.sin(tc)) + dy * (-np.cos(tc))) / 0.5; s = (dth >= lo) & (dth < hi)
    for d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        i = int(np.argmin(np.abs(dg - d))); cc = xc(XA, PA, XB, PB, i, s); ac = xc(XB, PB, XB, PB, i, s)
        if np.isnan(cc).all() or np.isnan(ac).all(): continue
        f = frac(cc, ac, pred)
        fakes = [frac(cc, ac, sh) for sh in (-pred, 1.6 * pred, -1.6 * pred, 2.2 * pred, -2.2 * pred) if abs(sh) >= 2]
        fakes = np.array([x for x in fakes if np.isfinite(x)])
        res.append(dict(sector=f'{lo}-{hi}', d=d, f=float(f), fals_mitjana=float(np.mean(fakes)) if fakes.size else None, fals_rms=float(np.sqrt(np.mean(fakes**2))) if fakes.size else None))
        print(f'{lo:3d}-{hi:3d} d {d:3.1f} | fracció lunar {f:+.2f} | falses (−p, ±1,6p, ±2,2p): ' + ' '.join(f'{x:+.2f}' for x in fakes) + f'  rms {np.sqrt(np.mean(fakes**2)) if fakes.size else np.nan:.2f}')
if len(sys.argv) > 2: open(sys.argv[2], 'w').write(json.dumps(res, indent=1))
