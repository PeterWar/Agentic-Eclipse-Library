import numpy as np, json, glob
from scipy import ndimage as ndi
meta = json.load(open('v3/meta.json')); files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15
def disp(a, b, s=6):
    A = a - ndi.gaussian_filter(a, s); B = b - ndi.gaussian_filter(b, s); A /= (A.std() + 1e-9); B /= (B.std() + 1e-9)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B)); F /= np.abs(F) + 1e-9; pc = np.real(np.fft.ifft2(F))
    iy, ix = np.unravel_index(np.argmax(pc), pc.shape)
    dy = iy if iy <= pc.shape[0] // 2 else iy - pc.shape[0]; dx = ix if ix <= pc.shape[1] // 2 else ix - pc.shape[1]
    ys, xs = np.mgrid[-1:2, -1:2]; w = np.array([[pc[(iy + i) % pc.shape[0], (ix + j) % pc.shape[1]] for j in (-1, 0, 1)] for i in (-1, 0, 1)]); w = np.clip(w - w.min(), 0, None)
    return -(dx + (w * xs).sum() / w.sum()), -(dy + (w * ys).sum() / w.sum()), pc.max()
def layer_patch(i, x0, y0, S, chan=None):
    info = meta['layers'][i]; l0, t0 = info['bbox'][:2]; a = np.load(files[i], mmap_mode='r')
    sub = np.asarray(a[y0 - t0:y0 + S - t0, x0 - l0:x0 + S - l0], np.float32) / 65535.
    return sub.mean(-1) if chan is None else sub[..., chan]
a12 = np.load(files[0], mmap_mode='r'); l0, t0 = meta['layers'][0]['bbox'][:2]
sub = np.asarray(a12[1800:3700, 3000:5000], np.float32) / 65535.
ha = sub[..., 0] - 0.81 * sub[..., 1]
yy, xx = np.mgrid[1800:3700, 3000:5000]; rr_ = np.hypot(xx + l0 - SUN[0], yy + t0 - SUN[1]) / RS
ha[(rr_ < 0.99) | (rr_ > 1.2)] = 0; ha = ndi.gaussian_filter(ha, 3)
iy, ix = np.unravel_index(np.argmax(ha), ha.shape); px, py = ix + 3000 + l0, iy + 1800 + t0
print('protuberància més brillant (doc):', px, py, 'θ =', round(float(np.degrees(np.arctan2(-(py - SUN[1]), px - SUN[0]))), 1), 'r =', round(float(np.hypot(px - SUN[0], py - SUN[1]) / RS), 3), flush=True)
for S in (192, 320):
    x0, y0 = int(px - S / 2), int(py - S / 2)
    for j in (1, 2, 3):
        a = np.log(np.maximum(layer_patch(0, x0, y0, S, 0), 1e-4)); b = np.log(np.maximum(layer_patch(j, x0, y0, S, 0), 1e-4))
        pa = layer_patch(0, x0, y0, S, 0) - 0.81 * layer_patch(0, x0, y0, S, 1); pb = layer_patch(j, x0, y0, S, 0) - 0.81 * layer_patch(j, x0, y0, S, 1)
        print(f'  S={S} 12 vs {meta["layers"][j]["name"][:8]}: log R → ({disp(a, b)[0]:+.2f},{disp(a, b)[1]:+.2f}|{disp(a, b)[2]:.2f}); Hα → ({disp(pa, pb)[0]:+.2f},{disp(pa, pb)[1]:+.2f}|{disp(pa, pb)[2]:.2f})   (positiu = la segona més a la dreta/avall)', flush=True)
