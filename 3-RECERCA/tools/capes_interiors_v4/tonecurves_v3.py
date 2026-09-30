"""Relació entre cada capa (valors codificats) i la luminància lineal calibrada de l'HDR (ADU/s): corba de to de cada capa,
on comença a comprimir (roll-off) i a quin radi (màxim sobre θ) cada capa deixa de ser vàlida."""
import numpy as np, json, os
from scipy import ndimage as ndi
d = np.load('v3/polar.npz'); meta = json.load(open('v3/meta.json'))
rr = d['rr']; th = np.deg2rad(d['th']); nL = len(meta['layers'])
HDR = np.load(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_countss.npy'), mmap_mode='r')
HSUN = (3479.0, 2319.0); RS = 446.15
R, T = np.meshgrid(rr, th, indexing='ij'); X = HSUN[0] + R * RS * np.cos(T); Y = HSUN[1] - R * RS * np.sin(T)
S = np.stack([ndi.map_coordinates(np.asarray(HDR[..., c], np.float32), [Y, X], order=1, mode='constant', cval=np.nan) for c in range(3)])
np.save('v3/polar_hdr_lineal.npy', S)
exp = {0: 1/3200, 1: 1/500, 2: 1/125, 3: 1/60, 4: 1/30, 5: 1/15, 6: 1/8, 7: 1/4, 8: 1/2, 9: 1.0}
print('capa | exposició | per al canal G: mediana de e per bins de ln(s·t) (s en ADU/s de l\'HDR) — si les corbes coincideixen, el revelat és el mateix')
bins = np.arange(-1.0, 10.5, 0.5)   # ln(s*t) en ADU
print('ln(s·t):'.ljust(26) + ''.join(f'{b:6.1f}' for b in bins[:-1]))
curves = {}
for i in range(nL):
    e = d[f'L{i}'][1]; s = S[1] * exp[i]
    ok = np.isfinite(s) & (s > 0) & (R > 1.0)
    ls = np.log(s[ok]); ee = e[ok]
    row = []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        m = (ls >= b0) & (ls < b1)
        row.append(np.median(ee[m]) if m.sum() > 50 else np.nan)
    curves[i] = row
    print(f'{meta["layers"][i]["name"][:14]:14s} t={exp[i]:7.5f} ' + ''.join(f'{v:6.3f}' if np.isfinite(v) else '     -' for v in row))
# pendent local (gamma local) de la corba conjunta: d ln e / d ln s
print('\nPendent local d(ln e)/d(ln s) per bins (capes 3..9 juntes):')
allls, alle = [], []
for i in range(3, 10):
    e = d[f'L{i}'][1]; s = S[1] * exp[i]; ok = np.isfinite(s) & (s > 0) & (R > 1.0) & (e > 0.002) & (e < 0.995)
    allls.append(np.log(s[ok])); alle.append(np.log(e[ok]))
allls = np.concatenate(allls); alle = np.concatenate(alle)
b2 = np.arange(-1, 10.1, 0.25)
med = [np.median(alle[(allls >= a) & (allls < b)]) if ((allls >= a) & (allls < b)).sum() > 100 else np.nan for a, b in zip(b2[:-1], b2[1:])]
med = np.array(med); cen = 0.5 * (b2[:-1] + b2[1:])
for j in range(1, len(med) - 1):
    if np.isfinite(med[j - 1]) and np.isfinite(med[j + 1]):
        print(f'  ln s={cen[j]:5.2f}  e={np.exp(med[j]):6.3f}  gamma_local={(med[j + 1] - med[j - 1]) / 0.5:5.2f}')
