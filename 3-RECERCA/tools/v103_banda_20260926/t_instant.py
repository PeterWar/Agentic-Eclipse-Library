"""T del conjunt de l'instant (11 fotogrames, guarda 0,75→1,75) contra la veritat a3c a la DRETA, per calaix de 0,5 px de D_pres i per subsector;
i el mateix per a un conjunt més estret (|Δt| ≤ 2,5 s)."""
import json, sys
from pathlib import Path
import numpy as np
D = Path(sys.argv[1]); ARREL = Path.home() / 'Desktop/Eclipse 2026'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
Z = np.load(D / 'E_instant.npz'); E = Z['E']; NF = Z['NF']; by0, by1, bx0, bx1 = Z['box']
A = np.load(R9 / 'B/lineal_v99_franja/A3C_franja_silueta.npz'); Ea = A['E']; dom = A['domini_E']
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
yy, xx = np.mgrid[by0:by1, bx0:bx1]; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
dp = np.hypot(xx - LX, yy - LY) - RL - np.interp(th.ravel(), pag, eg, period=360).reshape(th.shape)
ok = (NF >= 3) & dom & (E[..., 1] > 0) & (Ea[..., 1] > 0)
sect = {'300-330': (300, 330), '330-360': (330, 360), '0-30': (0, 30), '30-60': (30, 60), 'tot 300-60': None}
res = {}
for nom, s in sect.items():
    m = ok if s is None else ok & (th >= s[0]) & (th < s[1])
    if s is None: m = ok & ((th >= 300) | (th < 60))
    row = {}
    for lo in np.arange(1.5, 8.0, 0.5):
        z = m & (dp >= lo) & (dp < lo + 0.5)
        if z.sum() < 100: row[f'{lo:.1f}'] = None; continue
        q = np.log(E[..., 1][z] / Ea[..., 1][z]); row[f'{lo:.1f}'] = round(float(np.median(q)) * 100, 2)
    res[nom] = row
for nom, row in res.items(): print(nom.ljust(11), ' '.join(f"{k}:{v:+.1f}%" if v is not None else f"{k}:--" for k, v in row.items()))
json.dump(res, open(D / 'T_INSTANT_DRETA.json', 'w'), indent=1)
