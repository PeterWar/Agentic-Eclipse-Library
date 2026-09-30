"""m2 (V106, «LOLA fi») · Prova d'EMPREMTA LUNAR del detall tangencial, grup per grup (complementa m1, que necessita dos grups i té un soroll
de ±0,2–0,4 en molts calaixos). Per a cada grup g (A = 0–10, B = 13–18) i cada d: correlació (i pendent) entre el detall del grup i el RELLEU
LUNAR vist des del centre lunar mitjà del grup (LOLA-64 a θN 45,25°, suavitzat σ 2,5 px, passat pel mateix filtre que el detall: menys la
mitjana gaussiana de 32 px d'arc). Sense divisió per T (V105) el pendent és negatiu (limbe més alt → menys llum); amb una T perfecta, 0;
sobrecorrecció → positiu. Error: ±1/√N_ef amb N_ef = mostres / longitud de correlació (mesurada). Ús: m2_empremta.py <DELTA.npz> [sortida.json]"""
import sys, json, numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
H = Path(__file__).parent; sys.path.insert(0, str(H))
from geom_fina import Geometria
G = Geometria(H / 'GEOMETRIA_FINA.npz')
Z = np.load(sys.argv[1]); dg = Z['dgrid']; nth = int(Z['nth']); th = np.linspace(0, 2 * np.pi, nth, endpoint=False); dth = np.degrees(th)
cx, cy, R = Z['centre']; C = {int(r[0]): (r[1], r[2]) for r in Z['centres']}
SIGC = 32.0 / 0.5
hrel = G.relleu(2.5)                                                                     # px, graella 0,01° (angle del llenç al voltant del centre lunar)
def relleu_grup(js, d):
    """Relleu lunar a cada mostra polar (d, θ) vist des del centre mitjà del grup (angle al voltant del centre lunar)."""
    mx = np.mean([C[j][0] for j in js]); my = np.mean([C[j][1] for j in js])
    X = cx + np.cos(th) * (R + d); Y = cy - np.sin(th) * (R + d)
    a = np.degrees(np.arctan2(-(Y - my), X - mx)) % 360
    h = np.interp(a, G.g001, hrel, period=360)
    return h - gaussian_filter1d(h, SIGC, mode='wrap')                                   # mateix filtre que el detall (sense la part > 4°)
out = []
grups = {'A': ('hA', 'pA', [j for j in C if j <= 10]), 'B': ('hB', 'pB', [j for j in C if 13 <= j <= 18])}
SECT = [(0, 360), (60, 100), (100, 140), (200, 240), (240, 280), (280, 320)]
print('grup  sector   ' + ' '.join(f'   d{d:<4g}' for d in [0.5, 1, 1.5, 2, 2.5, 3, 4, 5]))
for g, (kx, kp, js) in grups.items():
    X = np.nan_to_num(Z[kx]); P = Z[kp]
    for lo, hi in SECT:
        s = (dth >= lo) & (dth < hi); row = []
        for d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            i = int(np.argmin(np.abs(dg - d))); m = s & (P[i] > 0)
            if m.sum() < 60: row.append('     —   '); continue
            h = relleu_grup(js, float(dg[i])); x = X[i][m]; y = h[m]
            if y.std() == 0 or x.std() == 0: row.append('     —   '); continue
            rho = np.corrcoef(x, y)[0, 1]; beta = np.dot(x - x.mean(), y - y.mean()) / np.dot(y - y.mean(), y - y.mean())
            # longitud de correlació (mostres) del producte, per a l'error
            xc = (x - x.mean()) / x.std(); yc = (y - y.mean()) / y.std()
            def lc(v):
                ac = [np.mean(v[:-k] * v[k:]) if k else 1.0 for k in range(0, 40)]
                return 1 + 2 * sum(a for a in ac[1:] if a > 0)
            neff = m.sum() / max(np.sqrt(lc(xc) * lc(yc)), 1.0); err = 1 / np.sqrt(max(neff, 1))
            out.append(dict(grup=g, sector=f'{lo}-{hi}', d=d, rho=float(rho), err=float(err), pendent=float(beta), n=int(m.sum())))
            row.append(f'{rho:+.2f}±{err:.2f}')
        print(f'{g:4s} {lo:3d}-{hi:<3d}  ' + ' '.join(row))
if len(sys.argv) > 2: Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
