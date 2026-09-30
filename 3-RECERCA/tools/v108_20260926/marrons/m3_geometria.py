"""m3 · Geometria FINA de cada traç, mesurada on el traç és més fort: el ràster de la P04 WOW (capa 55; V93: −16…−27 %), amb la P05 (56) de control.
Filtre adaptat a una línia estreta: DoG (σ4 − σ40) del ràster; per a cada angle (±4°, pas 0,05°) i desplaçament (±150 px, pas 1 px) respecte de la
marca de Pere, la mitjana del DoG al llarg del traç. El mínim del mapa (θ, t) és la recta; se n'anota el contrast respecte del soroll del mapa (z).
Sortida: M3_GEOMETRIA.json (centre, direcció, extrems, z) i M3_mapes.npz."""
import sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
E = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'
res = {}; mapes = {}
TH = np.arange(-4.0, 4.001, 0.05); TT = np.arange(-150, 151, 1.0)
for tr in TRACOS:
    x0, y0, x1, y1 = caixa(tr, 400); out = {}
    for lid in (55, 56):
        img = np.asarray(np.load(E / f'L{lid}_G.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32) / 65535
        dog = cv2.GaussianBlur(img, (0, 0), 4) - cv2.GaussianBlur(img, (0, 0), 40)
        M = np.zeros((len(TH), len(TT)), np.float32)
        for i, dth in enumerate(TH):
            s, t, X, Y = graella(tr, tmax=150, dt=1, ds=3, dtheta=dth)
            P = mostreja(dog, X, Y, (x0, y0)); M[i] = np.nanmean(P, 0)
        z = (M - np.median(M)) / (1.4826 * np.median(np.abs(M - np.median(M))) + 1e-12)
        i, j = np.unravel_index(np.argmin(M), M.shape)
        out[lid] = dict(dtheta=float(TH[i]), t0=float(TT[j]), dog_min=float(M[i, j]), z=float(z[i, j]))
        mapes[f'T{tr["k"]}_L{lid}'] = M
    g = out[55]; d = tr['d']; a = np.radians(g['dtheta']); d2 = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)]); n2 = np.array([-d2[1], d2[0]])
    c2 = tr['centre'] + g['t0'] * n2
    acord = abs(out[55]['dtheta'] - out[56]['dtheta']) <= 0.3 and abs(out[55]['t0'] - out[56]['t0']) <= 6
    res[tr['k']] = dict(nom=tr['nom'], P04=out[55], P05=out[56], acord_55_56=acord, centre=c2.round(2).tolist(), direccio=d2.round(6).tolist(),
                        angle_graus=float(np.degrees(np.arctan2(d2[1], d2[0])) % 180), llarg=tr['llarg'],
                        extrems=[(c2 - d2 * tr['llarg'] / 2).round(1).tolist(), (c2 + d2 * tr['llarg'] / 2).round(1).tolist()])
    print(f"T{tr['k']}", 'P04', {k: round(v, 4) for k, v in out[55].items()}, 'P05', {k: round(v, 4) for k, v in out[56].items()}, 'acord', acord, 'angle', round(res[tr['k']]['angle_graus'], 2), 'centre', res[tr['k']]['centre'], flush=True)
desa(OUT / 'M3_GEOMETRIA.json', res); np.savez_compressed(OUT / 'M3_mapes.npz', TH=TH, TT=TT, **mapes)
