"""Perfils radials (p50, p95 del canal màxim i mediana de luminància) de cada capa de 4 a 11,5 R☉, per definir les màscares fins als cantons."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta = json.load(open('v3/meta.json')); files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15
rr = np.arange(3.9, 11.6, 0.05); th = np.deg2rad(np.arange(0, 360, 1.0))
R, T = np.meshgrid(rr, th, indexing='ij'); X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
out = {'rr': rr}
for i in range(len(files)):
    info = meta['layers'][i]; l0, t0, r0, b0 = info['bbox']
    a = np.load(files[i], mmap_mode='r')
    chans = []
    for c in range(3):
        v = ndi.map_coordinates(np.asarray(a[..., c], np.float32) / 65535., [Y - t0, X - l0], order=1, mode='constant', cval=np.nan)
        chans.append(v)
    P = np.stack(chans)
    # fora del marc (blanc o nan) → nan
    inside = (X >= 458) & (X < 7418) & (Y >= 464) & (Y < 5104)
    P[:, ~inside] = np.nan
    lum = 0.2126 * P[0] + 0.7152 * P[1] + 0.0722 * P[2]
    mx = np.nanmax(P, axis=0)
    out[f'p50_{i}'] = np.nanmedian(lum, axis=1); out[f'p95max_{i}'] = np.nanpercentile(mx, 95, axis=1); out[f'nvalid_{i}'] = np.isfinite(lum).sum(1)
    print(i, info['name'][:12], 'p50 lum a 4/6/8/10 R☉:', [round(float(out[f'p50_{i}'][int(round((r-3.9)/0.05))]), 4) for r in (4, 6, 8, 10)], 'punts vàlids a 10 R☉:', int(out[f'nvalid_{i}'][int(round((10-3.9)/0.05))]), flush=True)
np.savez('v3/perfils_ext.npz', **out)
