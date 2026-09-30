"""m1c · Desfasament del màxim de la correlació creuada A–B lluny del limbe (d 6–30 px, T = 1): si no és 0, els grups A i B no estan registrats
igual al llarg de l'arc (això contamina la prova m1 prop del limbe). Ajust parabòlic del màxim, en px d'arc."""
import sys, numpy as np
Z = np.load(sys.argv[1]); dg = Z['dgrid']; nth = int(Z['nth']); dth = np.degrees(np.linspace(0, 2*np.pi, nth, endpoint=False))
XA, PA, XB, PB = np.nan_to_num(Z['hA']), Z['pA'], np.nan_to_num(Z['hB']), Z['pB']
C = {int(r[0]): (r[1], r[2]) for r in Z['centres']}; A = [j for j in C if j <= 10]; B = [j for j in C if 13 <= j <= 18]
dx = np.mean([C[j][0] for j in B]) - np.mean([C[j][0] for j in A]); dy = np.mean([C[j][1] for j in B]) - np.mean([C[j][1] for j in A])
lags = np.arange(-10, 11)
for lo, hi in [(60, 100), (100, 140), (140, 180), (200, 240), (240, 280), (280, 320), (320, 360), (0, 40)]:
    s = (dth >= lo) & (dth < hi); tc = np.radians((lo + hi) / 2); pred = (dx * (-np.sin(tc)) + dy * (-np.cos(tc)))
    out = []
    for d in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0]:
        i = int(np.argmin(np.abs(dg - d))); cc = []
        for L in lags:
            y = np.roll(XB[i], -L); py = np.roll(PB[i], -L); m = s & (PA[i] > 0) & (py > 0)
            cc.append(np.corrcoef(XA[i][m], y[m])[0, 1] if m.sum() > 150 else np.nan)
        cc = np.array(cc)
        if np.isnan(cc).all(): out.append(f'd{d:g}: —'); continue
        k = np.nanargmax(cc)
        if 0 < k < len(lags) - 1 and np.isfinite(cc[k - 1:k + 2]).all():
            y0, y1, y2 = cc[k - 1:k + 2]; off = lags[k] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
        else: off = lags[k]
        out.append(f'd{d:g}: {off * 0.5:+.2f} ({cc[k]:.2f})')
    print(f'{lo:3d}-{hi:3d} (Lluna {pred:+.2f} px d\'arc): ' + '  '.join(out))
