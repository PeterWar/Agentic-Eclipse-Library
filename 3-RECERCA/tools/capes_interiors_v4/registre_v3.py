"""Registre entre capes de V3: correlació de fase del passa-alt de la luminància sobre retalls al voltant del Sol.
Coordenades de document. Positiu = la segona capa és més a la dreta/avall que la primera."""
import numpy as np, json, glob
from scipy import ndimage as ndi
meta = json.load(open('v3/meta.json'))
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15   # Sol al llenç per a les capes DNG a (458,464)
def lum_doc(i):
    info = meta['layers'][i]; l0, t0, r0, b0 = info['bbox']
    a = np.load(files[i], mmap_mode='r')
    return a, (l0, t0)
def patch(i, x0, y0, S):
    a, (l0, t0) = lum_doc(i)
    h, w = a.shape[:2]
    out = np.full((S, S), np.nan, np.float32)
    ix0, iy0, ix1, iy1 = max(x0, l0), max(y0, t0), min(x0 + S, l0 + w), min(y0 + S, t0 + h)
    if ix1 <= ix0 or iy1 <= iy0: return out
    sub = a[iy0 - t0:iy1 - t0, ix0 - l0:ix1 - l0].astype(np.float32)
    L = 0.2126 * sub[..., 0] + 0.7152 * sub[..., 1] + 0.0722 * sub[..., 2]
    out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = L
    return out
def disp(a, b, s=6):
    A = a - ndi.gaussian_filter(a, s); B = b - ndi.gaussian_filter(b, s)
    A /= (A.std() + 1e-9); B /= (B.std() + 1e-9)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B)); F /= np.abs(F) + 1e-9; pc = np.real(np.fft.ifft2(F))
    iy, ix = np.unravel_index(np.argmax(pc), pc.shape)
    dy = iy if iy <= pc.shape[0] // 2 else iy - pc.shape[0]; dx = ix if ix <= pc.shape[1] // 2 else ix - pc.shape[1]
    ys, xs = np.mgrid[-1:2, -1:2]
    w = np.array([[pc[(iy + i) % pc.shape[0], (ix + j) % pc.shape[1]] for j in (-1, 0, 1)] for i in (-1, 0, 1)]); w = np.clip(w - w.min(), 0, None)
    return -(dx + (w * xs).sum() / w.sum()), -(dy + (w * ys).sum() / w.sum()), pc.max()
def ring(iA, iB, rr, S, thr=0.08, sat_lim=60000):
    res = []
    for ang in range(0, 360, 30):
        cx = SUN[0] + rr * RS * np.cos(np.radians(ang)); cy = SUN[1] - rr * RS * np.sin(np.radians(ang))
        x0 = int(cx - S / 2); y0 = int(cy - S / 2)
        a = patch(iA, x0, y0, S); b = patch(iB, x0, y0, S)
        if np.isnan(a).any() or np.isnan(b).any(): continue
        # emmascara el disc lunar i la saturació
        yy, xx = np.mgrid[y0:y0 + S, x0:x0 + S]; r_ = np.hypot(xx - SUN[0], yy - SUN[1]) / RS
        m = ((r_ > 1.06) & (a < sat_lim) & (b < sat_lim)).astype(np.float32)
        m = ndi.gaussian_filter(m, 3)
        a = a * m + np.nanmedian(a) * (1 - m); b = b * m + np.nanmedian(b) * (1 - m)
        res.append(disp(a, b))
    good = [r for r in res if r[2] > thr]
    nA = meta['layers'][iA]['name'][:14]; nB = meta['layers'][iB]['name'][:14]
    print(f'{nB:14s} vs {nA:14s} r={rr} S={S}: pics>{thr}: {len(good)}/{len(res)}; ' +
          (f'mediana ({np.median([g[0] for g in good]):+.2f},{np.median([g[1] for g in good]):+.2f}) px, pic màx {max(g[2] for g in good):.2f}' if good else 'cap pic fiable')
          + '  [' + ' '.join(f'({r[0]:+.1f},{r[1]:+.1f}|{r[2]:.2f})' for r in res) + ']', flush=True)
# índexs: 0=12, 1=Capa4, 2=Capa5, 3=09, 4=08, 5=07, 6=06, 7=05, 8=04, 9=03
ring(3, 0, 1.08, 384); ring(3, 1, 1.08, 384); ring(3, 1, 1.2, 512); ring(3, 2, 1.2, 512); ring(3, 2, 1.4, 512)
ring(3, 4, 1.3, 512); ring(4, 5, 1.4, 512); ring(5, 6, 1.5, 512); ring(6, 7, 1.7, 512); ring(7, 8, 1.9, 512); ring(8, 9, 2.2, 512)
ring(1, 2, 1.2, 512); ring(0, 1, 1.08, 384)
