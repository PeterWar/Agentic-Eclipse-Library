"""Perfils radials (per canal, valors codificats 0..1) de cada capa de V3 i de cada màscara; saturació; estructura azimutal de les màscares.
Tot en coordenades de document, Sol a SUN, R☉ = 446,15 px. Treballa sobre una quadrícula polar (r en R☉, θ en graus)."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta = json.load(open('v3/meta.json'))
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
mfiles = {i: f.replace('_rgb.npy', '_mask.npy') for i, f in enumerate(files)}
import os
SUN = (4021.89, 2738.66); RS = 446.15
# quadrícula polar: r de 0,90 a 4,0 R☉ cada 0,005 (2,2 px); θ cada 0,5°
rr = np.arange(0.90, 4.0, 0.005); th = np.deg2rad(np.arange(0, 360, 0.5))
R, T = np.meshgrid(rr, th, indexing='ij')           # (nr, nth)
X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
def sample_doc(arr, l0, t0, order=1, fill=np.nan):
    # arr (h,w) en coordenades de capa; mostreig a (X,Y) de document
    return ndi.map_coordinates(arr, [Y - t0, X - l0], order=order, mode='constant', cval=fill)
out = {'rr': rr, 'th': np.rad2deg(th)}
for i, f in enumerate(files):
    info = meta['layers'][i]; l0, t0, r0, b0 = info['bbox']
    a = np.load(f, mmap_mode='r')
    pol = np.zeros((3,) + R.shape, np.float32)
    for c in range(3):
        pol[c] = sample_doc(np.asarray(a[..., c], dtype=np.float32) / 65535., l0, t0)
    out[f'L{i}'] = pol
    if info['mask'] is not None:
        ml, mt, mr, mb = info['mask']['bbox']
        m = np.load(mfiles[i], mmap_mode='r')
        out[f'M{i}'] = sample_doc(np.asarray(m, dtype=np.float32) / 65535., ml, mt, fill=info['mask']['bg'] / 255.)
    print('capa', i, info['name'][:20], 'feta', flush=True)
np.savez_compressed('v3/polar.npz', **out)
# resum textual
print('\n== perfils radials (mediana azimutal de la luminància codificada L=0.2126R+0.7152G+0.0722B) i fracció saturada (>0.995) per radi')
rsel = [0.95, 1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.30, 1.40, 1.50, 1.70, 2.0, 2.5, 3.0, 3.5]
idx = [int(round((r - 0.90) / 0.005)) for r in rsel]
hdr = 'capa'.ljust(18) + ''.join(f'{r:>7.2f}' for r in rsel)
print(hdr)
for i in range(len(files)):
    L = out[f'L{i}']; lum = 0.2126 * L[0] + 0.7152 * L[1] + 0.0722 * L[2]
    med = np.nanmedian(lum, axis=1); sat = np.nanmean((np.nanmax(L, axis=0) > 0.995), axis=1)
    print(meta['layers'][i]['name'][:18].ljust(18) + ''.join(f'{med[j]:7.3f}' for j in idx) + '   L')
    print(''.ljust(18) + ''.join(f'{sat[j]:7.2f}' for j in idx) + '   frac sat')
print('\n== màscares: mitjana azimutal i desviació azimutal per radi')
for i in range(len(files)):
    if f'M{i}' not in out: continue
    M = out[f'M{i}']; mean = np.nanmean(M, axis=1); std = np.nanstd(M, axis=1)
    print(meta['layers'][i]['name'][:18].ljust(18) + ''.join(f'{mean[j]:7.3f}' for j in idx) + '   mitjana')
    print(''.ljust(18) + ''.join(f'{std[j]:7.3f}' for j in idx) + '   desv az')
