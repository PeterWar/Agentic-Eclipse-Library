"""Limbe lunar per gradient radial màxim (capes 12, Capa 4, Capa 5, 09) i ajust de cercle; i vora de la màscara de Capa 4."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta = json.load(open('v3/meta.json')); files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15
rr = np.arange(0.90, 1.10, 0.00025); th = np.deg2rad(np.arange(0, 360, 0.5))
R, T = np.meshgrid(rr, th, indexing='ij'); X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
def samp(arr, l0, t0): return ndi.map_coordinates(arr, [Y - t0, X - l0], order=1, mode='nearest')
def limb_of(i, chan=1):
    info = meta['layers'][i]; l0, t0 = info['bbox'][:2]
    a = np.load(files[i], mmap_mode='r'); g = np.asarray(a[..., chan], np.float32) / 65535.
    P = samp(g, l0, t0)                      # (nr, nth)
    # log per comprimir; gradient radial; màxim entre 0,93 i 1,06
    Lg = np.log(np.maximum(P, 1e-4)); G = np.gradient(ndi.gaussian_filter1d(Lg, 4, axis=0), axis=0)
    j0, j1 = int((0.93 - 0.9) / 0.00025), int((1.06 - 0.9) / 0.00025)
    jm = j0 + np.argmax(G[j0:j1], axis=0)
    return rr[jm], G[jm, np.arange(G.shape[1])]
def fit_circle(rl, w=None):
    x = SUN[0] + rl * RS * np.cos(th); y = SUN[1] - rl * RS * np.sin(th)
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]; b = x ** 2 + y ** 2
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + cx ** 2 + cy ** 2)
    res = np.hypot(x - cx, y - cy) - r
    return cx, cy, r, res
for i in (0, 1, 2, 3):
    rl, gmax = limb_of(i)
    cx, cy, r, res = fit_circle(rl)
    ok = np.abs(res) < 3 * np.std(res)
    cx, cy, r, res2 = fit_circle(rl[ok]) if False else (cx, cy, r, res)
    print(f'{meta["layers"][i]["name"][:16]:16s} limbe: centre ({cx:.2f}, {cy:.2f}) = Sol + ({cx - SUN[0]:+.1f}, {cy - SUN[1]:+.1f}) px, radi {r:.1f} px = {r / RS:.4f} R☉, residu rms {res.std():.2f} px, p99 {np.percentile(np.abs(res), 99):.1f}')
# vora de la màscara de Capa 4 pel mateix mètode (0,5)
m = np.load('v3/01_Capa_4_mask.npy', mmap_mode='r'); P = samp(np.asarray(m, np.float32) / 65535., 0, 0)
cross = np.array([rr[np.argmax(P[:, j] > 0.5)] if (P[:, j] > 0.5).any() else np.nan for j in range(P.shape[1])])
ok = np.isfinite(cross) & (cross > 0.901)
x = SUN[0] + cross[ok] * RS * np.cos(th[ok]); y = SUN[1] - cross[ok] * RS * np.sin(th[ok])
A = np.c_[2 * x, 2 * y, np.ones_like(x)]; b = x ** 2 + y ** 2; cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + cx ** 2 + cy ** 2)
print(f'màscara Capa 4 (0,5): centre ({cx:.1f}, {cy:.1f}) = Sol + ({cx - SUN[0]:+.1f}, {cy - SUN[1]:+.1f}), radi {r:.1f} px; punts usats {ok.sum()}/{len(ok)} (la resta de θ: vora dins de 0,90 R☉)')
# distància mínima entre la vora de la màscara i el limbe de Capa 4, per θ
rl4, _ = limb_of(1)
d = (rl4 - cross) * RS
print('limbe Capa4 − vora màscara (px): min', np.nanmin(d), 'mediana', np.nanmedian(d), 'max', np.nanmax(d))
