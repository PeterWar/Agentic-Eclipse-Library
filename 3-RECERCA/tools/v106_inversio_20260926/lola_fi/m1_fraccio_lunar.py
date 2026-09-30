"""m1 (V105) · Prova «Lluna o corona» (mètode del verificador, v8b): el detall tangencial del grup A (fotogrames 0–10, t 15–22 s) i del grup B
(13–18, t 25–30 s) es correlacionen en funció del desfasament al llarg de l'arc. La corona és fixa en coordenades solars (desfasament 0); el relleu
del limbe es mou amb la Lluna (desfasament previst pel desplaçament mitjà dels centres lunars B − A). Model: C_AB(l) = a·ACF_B(l) + b·ACF_B(l − l_Lluna);
fracció lunar = b/(a+b). Ús: m1_fraccio_lunar.py <DELTA.npz> [<sortida.json>]"""
import sys, json, numpy as np
Z = np.load(sys.argv[1]); dg = Z['dgrid']; nth = int(Z['nth']); th = np.linspace(0, 2 * np.pi, nth, endpoint=False); dth = np.degrees(th)
C = {int(r[0]): (r[1], r[2]) for r in Z['centres']}
A = [j for j in C if j <= 10]; B = [j for j in C if 13 <= j <= 18]
dx = np.mean([C[j][0] for j in B]) - np.mean([C[j][0] for j in A]); dy = np.mean([C[j][1] for j in B]) - np.mean([C[j][1] for j in A])
XA, PA, XB, PB = np.nan_to_num(Z['hA']), Z['pA'], np.nan_to_num(Z['hB']), Z['pB']
lags = np.arange(-16, 17)
def xc(X, PX, Y, PY, i, s):
    out = []
    for L in lags:
        y = np.roll(Y[i], -L); py = np.roll(PY[i], -L); m = s & (PX[i] > 0) & (py > 0)
        out.append(np.corrcoef(X[i][m], y[m])[0, 1] if m.sum() > 150 and X[i][m].std() > 0 and y[m].std() > 0 else np.nan)
    return np.array(out)
res = []; print(f'desplaçament lunar B − A: ({dx:+.2f}, {dy:+.2f}) px')
for lo, hi in [(60, 100), (100, 140), (140, 180), (200, 240), (240, 280), (280, 320)]:
    tc = np.radians((lo + hi) / 2); pred = (dx * (-np.sin(tc)) + dy * (-np.cos(tc))) / 0.5; s = (dth >= lo) & (dth < hi)
    for d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]:
        i = int(np.argmin(np.abs(dg - d))); cc = xc(XA, PA, XB, PB, i, s); ac = xc(XB, PB, XB, PB, i, s)
        if np.isnan(cc).all() or np.isnan(ac).all(): continue
        acs = lambda sh: np.interp(lags - sh, lags, ac); M = np.stack([acs(0), acs(pred)], 1); ok = np.isfinite(cc) & np.isfinite(M).all(1)
        if ok.sum() < 10: continue
        (a, b), *_ = np.linalg.lstsq(M[ok], cc[ok], rcond=None); f = b / (a + b) if (a + b) > 0 else np.nan
        res.append(dict(sector=f'{lo}-{hi}', d=d, fraccio_lluna=float(f), a=float(a), b=float(b), pred=float(pred), n=int((s & (PA[i] > 0) & (PB[i] > 0)).sum())))
        print(f'{lo:3d}-{hi:3d} d {d:3.1f} | fracció lunar {f:+.2f} | corona {a:+.2f} Lluna {b:+.2f} | n {res[-1]["n"]}')
if len(sys.argv) > 2: open(sys.argv[2], 'w').write(json.dumps(dict(desplacament=[dx, dy], files=res), indent=1))
