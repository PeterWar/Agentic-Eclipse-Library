"""Validesa radial de cada capa: percentils azimutals (50, 90, 95, 99) del canal màxim; soroll per capa a uns quants radis."""
import numpy as np, json
from scipy import ndimage as ndi
d = np.load('v3/polar.npz'); meta = json.load(open('v3/meta.json'))
rr = d['rr']; th = d['th']; nL = len(meta['layers'])
print('percentil 95 (i 50 / 99) del canal màxim per radi; la protuberància (θ 160–178°) i r<1,0 exclosos')
thmask = ~((th > 160) & (th < 178))
rsel = [1.00, 1.02, 1.04, 1.06, 1.08, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.45, 1.50, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.5, 3.0]
idx = [int(round((r - 0.9) / 0.005)) for r in rsel]
print('capa'.ljust(10) + ''.join(f'{r:>6.2f}' for r in rsel))
prof = {}
for i in range(1, nL):
    L = d[f'L{i}']; mx = np.max(L, axis=0)[:, thmask]
    p95 = np.percentile(mx, 95, axis=1); p50 = np.percentile(mx, 50, axis=1); p99 = np.percentile(mx, 99, axis=1)
    prof[i] = (p50, p95, p99)
    nm = meta['layers'][i]['name'][:9]
    print(nm.ljust(10) + ''.join(f'{p95[j]:6.3f}' for j in idx) + '  p95')
    print(''.ljust(10) + ''.join(f'{p50[j]:6.3f}' for j in idx) + '  p50')
np.savez('v3/validesa_perfils.npz', rr=rr, **{f'p50_{i}': prof[i][0] for i in prof}, **{f'p95_{i}': prof[i][1] for i in prof}, **{f'p99_{i}': prof[i][2] for i in prof})
# soroll: desviació del residu passa-alt (σ=2 px) del canal G en finestres 64×64 a uns radis (direcció θ=60°, zona sense estructura forta?)
print('\nsoroll (desv. del residu passa-alt del canal G, finestres 96×96 a 8 azimuts; valor codificat ×1000) i senyal mitjà ×1000:')
import glob
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15
for i in range(1, nL):
    info = meta['layers'][i]; l0, t0 = info['bbox'][:2]; a = np.load(files[i], mmap_mode='r')
    row = []
    for r in (1.05, 1.15, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0):
        ns, ss = [], []
        for ang in range(15, 360, 45):
            cx = SUN[0] + r * RS * np.cos(np.radians(ang)); cy = SUN[1] - r * RS * np.sin(np.radians(ang)); x0 = int(cx - 48 - l0); y0 = int(cy - 48 - t0)
            g = np.asarray(a[y0:y0 + 96, x0:x0 + 96, 1], np.float32) / 65535.
            if g.max() > 0.98: continue
            hp = g - ndi.gaussian_filter(g, 2.0)
            ns.append(hp.std() / 0.74); ss.append(g.mean())   # /0.74: la gaussiana σ=2 treu part del soroll; aproximació
        row.append(f'{r:4.2f}: {np.median(ns)*1000:5.2f}/{np.median(ss)*1000:6.1f}' if ns else f'{r:4.2f}:   sat ')
    print(meta['layers'][i]['name'][:9].ljust(10) + '  '.join(row))
