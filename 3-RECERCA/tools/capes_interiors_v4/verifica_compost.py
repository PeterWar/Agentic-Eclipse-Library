"""Reprodueix el compost de V3 (a l'espai codificat, ordre de baix a dalt, màscares com a alfa, capes ocultes fora) sobre una
finestra i el compara amb la imatge fusionada del PSB."""
import numpy as np, json, glob
meta = json.load(open('v3/meta.json'))
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
merged = np.load('v3/merged_rgb.npy', mmap_mode='r')
y0, y1, x0, x1 = 2100, 3400, 3300, 4800   # finestra al voltant del Sol
C = np.zeros((y1 - y0, x1 - x0, 3), np.float64)
for i, f in enumerate(files):
    info = meta['layers'][i]
    if not info['visible']: continue
    l0, t0, r0, b0 = info['bbox']
    a = np.load(f, mmap_mode='r')
    # capa dins la finestra (assumim que la cobreix sencera)
    sub = np.asarray(a[y0 - t0:y1 - t0, x0 - l0:x1 - l0], np.float64) / 65535.
    if info['mask'] is None:
        alpha = np.ones(sub.shape[:2])
    else:
        ml, mt, mr, mb = info['mask']['bbox']
        m = np.load(f.replace('_rgb.npy', '_mask.npy'), mmap_mode='r')
        alpha = np.asarray(m[y0 - mt:y1 - mt, x0 - ml:x1 - ml], np.float64) / 65535.
    C = C * (1 - alpha[..., None]) + sub * alpha[..., None]
M = np.asarray(merged[y0:y1, x0:x1], np.float64) / 65535.
diff = C - M
print('diferència compost reproduït − fusionada: mitjana', diff.mean(), 'abs mitjana', np.abs(diff).mean(), 'p99 abs', np.percentile(np.abs(diff), 99), 'max', np.abs(diff).max())
# on és més gran?
idx = np.unravel_index(np.argmax(np.abs(diff).max(-1)), diff.shape[:2]); print('màxim a (y,x) doc =', idx[0] + y0, idx[1] + x0, 'C', C[idx], 'M', M[idx])
# prova alternativa: barreja amb gamma 1.0 (lineal)
def lin(e): return np.where(e <= 0.04045, e / 12.92, ((e + 0.055) / 1.055) ** 2.4)
def enc(s): return np.where(s <= 0.0031308, s * 12.92, 1.055 * s ** (1 / 2.4) - 0.055)
C2 = np.zeros_like(C)
for i, f in enumerate(files):
    info = meta['layers'][i]
    if not info['visible']: continue
    l0, t0, r0, b0 = info['bbox']
    a = np.load(f, mmap_mode='r'); sub = lin(np.asarray(a[y0 - t0:y1 - t0, x0 - l0:x1 - l0], np.float64) / 65535.)
    if info['mask'] is None: alpha = np.ones(sub.shape[:2])
    else:
        ml, mt, mr, mb = info['mask']['bbox']; m = np.load(f.replace('_rgb.npy', '_mask.npy'), mmap_mode='r'); alpha = np.asarray(m[y0 - mt:y1 - mt, x0 - ml:x1 - ml], np.float64) / 65535.
    C2 = C2 * (1 - alpha[..., None]) + sub * alpha[..., None]
d2 = enc(C2) - M
print('(si es barregés en lineal) abs mitjana', np.abs(d2).mean(), 'p99', np.percentile(np.abs(d2), 99))
