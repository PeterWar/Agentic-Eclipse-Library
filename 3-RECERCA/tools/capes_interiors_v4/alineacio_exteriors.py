import numpy as np, json, glob, os, time
from scipy import ndimage as ndi
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
meta = json.load(open('v3/meta.json')); files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN = (4021.89, 2738.66); RS = 446.15
def disp(a, b, s=6):
    A = a - ndi.gaussian_filter(a, s); B = b - ndi.gaussian_filter(b, s); A /= (A.std() + 1e-9); B /= (B.std() + 1e-9)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B)); F /= np.abs(F) + 1e-9; pc = np.real(np.fft.ifft2(F))
    iy, ix = np.unravel_index(np.argmax(pc), pc.shape)
    dy = iy if iy <= pc.shape[0] // 2 else iy - pc.shape[0]; dx = ix if ix <= pc.shape[1] // 2 else ix - pc.shape[1]
    ys, xs = np.mgrid[-1:2, -1:2]; w = np.array([[pc[(iy + i) % pc.shape[0], (ix + j) % pc.shape[1]] for j in (-1, 0, 1)] for i in (-1, 0, 1)]); w = np.clip(w - w.min(), 0, None)
    return -(dx + (w * xs).sum() / w.sum()), -(dy + (w * ys).sum() / w.sum()), pc.max()
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/')
E = PSDImage.open(D + 'CapesExteriors.psb'); hdrE = E._record.header
print('CapesExteriors:', hdrE.width, hdrE.height, flush=True)
for l in E:
    print('   ', l.name[:70], l.bbox, 'vis', l.visible, 'op', l.opacity, l.blend_mode, flush=True)
def read_full(l, chan=1):
    rec = l._record; L0, T0, R0, B0 = l.bbox; h, w = B0 - T0, R0 - L0
    chans = {ci.id: cd for ci, cd in zip(rec.channel_info, l._channels)}
    full = np.frombuffer(chans[ChannelID(chan)].get_data(w, h, hdrE.depth, hdrE.version), dtype='>u2').reshape(h, w).astype(np.float32) / 65535.
    return full, (L0, T0)
a05 = np.load(files[7], mmap_mode='r'); l05 = meta['layers'][7]['bbox'][:2]
a07 = np.load(files[5], mmap_mode='r'); l07 = meta['layers'][5]['bbox'][:2]
for l in E:
    if not (l.name.startswith('EDITAT') or l.name.startswith('01_10.3') or l.name.startswith('02_2s') or l.name.startswith('03_1s') or l.name.startswith('Capa')):
        continue
    t = time.time(); G, (L0, T0) = read_full(l); print('llegida', l.name[:30], G.shape, f'{time.time()-t:.0f} s', flush=True)
    for (src, lsrc, nm, rads) in ((a05, l05, '05 (1/4 s)', (1.8, 2.4)), (a07, l07, '07 (1/15 s)', (1.4, 1.7))):
        res = []
        for ang in range(0, 360, 30):
            for rrad in rads:
                cx = SUN[0] + rrad * RS * np.cos(np.radians(ang)); cy = SUN[1] - rrad * RS * np.sin(np.radians(ang)); x0 = int(cx - 256); y0 = int(cy - 256)
                a = np.asarray(src[y0 - lsrc[1]:y0 + 512 - lsrc[1], x0 - lsrc[0]:x0 + 512 - lsrc[0], 1], np.float32) / 65535.
                b = G[y0 - T0:y0 + 512 - T0, x0 - L0:x0 + 512 - L0]
                if a.shape != (512, 512) or b.shape != (512, 512): continue
                if (b <= 0).mean() > 0.2: continue
                res.append(disp(np.log(np.maximum(a, 1e-4)), np.log(np.maximum(b, 1e-4))))
        good = [r for r in res if r[2] > 0.08]
        if good:
            print(f'   V3/{nm} → {l.name[:24]}: {len(good)}/{len(res)} pics; mediana ({np.median([g[0] for g in good]):+.2f}, {np.median([g[1] for g in good]):+.2f}) px; pic màx {max(g[2] for g in good):.2f}  [' + ' '.join(f'({r[0]:+.1f},{r[1]:+.1f}|{r[2]:.2f})' for r in res[:12]) + ']', flush=True)
        else:
            print(f'   V3/{nm} → {l.name[:24]}: cap pic fiable', [tuple(round(float(v), 2) for v in r) for r in res[:6]], flush=True)
