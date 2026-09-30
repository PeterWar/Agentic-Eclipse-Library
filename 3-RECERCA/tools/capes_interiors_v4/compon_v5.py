"""Compost final de V5 al llenç sencer: capes 0..9 del V4 editat (píxels + màscares seves) + 04/03 amb les màscares noves."""
import numpy as np, json
meta = json.load(open('v5in/meta.json'))
W, H = 7648, 5353
C = np.zeros((H, W, 3), np.float32)
A = np.zeros((H, W, 1), np.float32)      # alfa acumulada (per detectar zones sense res)
for i in range(12):
    info = meta['layers'][i]
    l0, t0, r0, b0 = info['bbox']
    rgb = np.load(f'v5in/{i:02d}_rgb.npy', mmap_mode='r')
    if i == 10: m = np.load('v5out/mask_04.npy', mmap_mode='r'); mb = (457, 463)
    elif i == 11: m = np.load('v5out/mask_03.npy', mmap_mode='r'); mb = (457, 463)
    elif info['mask'] is not None:
        m = np.load(f'v5in/{i:02d}_mask.npy', mmap_mode='r'); mb = tuple(info['mask']['bbox'][:2])
    else: m = None
    sub = np.asarray(rgb, np.float32) / 65535.
    if m is None:
        alpha = np.ones(sub.shape[:2], np.float32)
    else:
        alpha = np.zeros(sub.shape[:2], np.float32)
        # màscara al doc: bbox mb; capa al doc: (l0,t0)
        y0 = t0 - mb[1]; x0 = l0 - mb[0]
        mm = np.asarray(m, np.float32) / 65535.
        hh, ww = sub.shape[:2]
        ys0, xs0 = max(0, -y0), max(0, -x0)
        ye = min(hh, mm.shape[0] - y0); xe = min(ww, mm.shape[1] - x0)
        alpha[ys0:ye, xs0:xe] = mm[y0 + ys0:y0 + ye, x0 + xs0:x0 + xe]
    C[t0:b0, l0:r0] = C[t0:b0, l0:r0] * (1 - alpha[..., None]) + sub * alpha[..., None]
    A[t0:b0, l0:r0] = np.maximum(A[t0:b0, l0:r0], alpha[..., None])
    print('composta', i, info['name'][:30], flush=True)
# fora de tota capa: blanc (com el fusionat de sempre)
C = np.where(A > 0, C, 1.0)
np.save('v5out/compost_rgb16.npy', np.clip(np.round(C * 65535), 0, 65535).astype(np.uint16))
from PIL import Image
Image.fromarray((np.clip(C[::4, ::4], 0, 1) * 255).astype(np.uint8)).save('v5out/prev_V5.png')
print('fet')
