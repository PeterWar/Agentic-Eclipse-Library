"""Retalla la capa Sony al llenç, reconstrueix el compost i el compara amb l'aplanat del TIFF."""
import json
import numpy as np
from PIL import Image

idx = json.load(open('layers_index.json'))
r1 = idx[1]
top, left, bottom, right = r1['bbox']
H, W = 4553, 6748
r0, c0 = -top, -left            # fila/columna del llenç (0,0) dins de la capa
print('llenç dins la capa a fila', r0, 'col', c0)
m = r1['mask']
mr0, mc0 = -m['top'], -m['left']
print('llenç dins la màscara a fila', mr0, 'col', mc0)

def load_crop(name, rr, cc):
    a = np.load(name, mmap_mode='r')
    return np.array(a[rr:rr+H, cc:cc+W], dtype=np.float32)

sony = np.stack([load_crop(f'sony_{c}.npy', r0, c0) for c in 'RGB'], -1) / 65535.
alpha = load_crop('sony_alpha.npy', r0, c0) / 65535.
mask = load_crop('sony_mask.npy', mr0, mc0) / 65535.
vix = np.stack([np.load(f'vixen_{c}.npy').astype(np.float32) for c in 'RGB'], -1) / 65535.
np.save('sony_canvas_rgb.npy', sony)
np.save('sony_canvas_alpha.npy', alpha)
np.save('sony_canvas_mask.npy', mask)
np.save('vixen_canvas_rgb.npy', vix)

comp = np.load('composite_u16.npy').astype(np.float32) / 65535.
a = (alpha * mask)[..., None]
recon = vix * (1 - a) + sony * a
d = recon - comp
print('alpha min/max al llenç', alpha.min(), alpha.max(), ' màscara min/max', mask.min(), mask.max())
print('diferència recon−compost: mediana abs', np.median(np.abs(d)), 'p99', np.percentile(np.abs(d), 99), 'màx', np.abs(d).max())
print('per canal, mitjana signada', d.reshape(-1, 3).mean(0))
# on hi ha les diferències grans
big = np.abs(d).max(-1) > 0.02
print('fracció de píxels amb |d|>0.02:', big.mean())
Image.fromarray((np.clip(np.abs(d).max(-1) * 20, 0, 1) * 255).astype(np.uint8)[::4, ::4]).save('recon_diff_ds4.png')
Image.fromarray((np.clip(recon, 0, 1) * 255).astype(np.uint8)[::4, ::4]).save('recon_ds4.png')
