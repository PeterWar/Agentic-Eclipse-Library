"""Diagnòstic de les ombres que Pere marca a REALCADA_SUAU (cantons i un punt a dalt).
Només lectura. Treu un PNG amb el camp llunyà estirat i uns perfils per zones.
"""
import os, sys, numpy as np, tifffile
import scipy.ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
FILES = {
    'SUAU_v1': os.path.join(D, '_anteriors_DoG', 'APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_SUAU_6748x4553.tif'),
    'BASE_v2': os.path.join(D, 'APILAT_Capa_Sony_encaixada_VORESNETES_6748x4553.tif'),
    'TANG_SUAU_v2': os.path.join(D, 'APILAT_Capa_Sony_encaixada_VORESNETES_TANGENCIAL_SUAU_6748x4553.tif'),
}
r = np.load(os.path.join(SP, 'r_rsol.npy'))
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy')).astype(np.float32)
H, W = r.shape

def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def low(a, s=25):
    return ndi.gaussian_filter(a, s)

imgs = {}
for k, f in FILES.items():
    a = tifffile.imread(f).astype(np.float32)
    imgs[k] = a
    print(k, a.shape, a.dtype, a.min(), a.max())

# Camp llunyà: r > 4. Estirem la luminància a baixa freqüència entre percentils
panels = []
for k, a in imgs.items():
    L = low(lum(a), 12)
    far = L[r > 4.5]
    lo, hi = np.percentile(far, [1, 99])
    print(k, 'far lum p1/p99', lo, hi, 'median', np.median(far))
    v = np.clip((L - lo) / (hi - lo), 0, 1)
    v[r < 3.0] = 0.5
    panels.append((v[::4, ::4] * 255).astype(np.uint8))
Lv = low(lum(vix), 12)
far = Lv[r > 4.5]
lo, hi = np.percentile(far, [1, 99])
v = np.clip((Lv - lo) / (hi - lo), 0, 1); v[r < 3.0] = 0.5
panels.append((v[::4, ::4] * 255).astype(np.uint8))
row1 = np.concatenate(panels[:2], axis=1)
row2 = np.concatenate(panels[2:], axis=1)
Image.fromarray(np.concatenate([row1, row2], axis=0)).save(os.path.join(SP, 'ombres_camp_llunya.png'))
print('SUAU_v1 | BASE_v2 / TANG_SUAU_v2 | VIXEN')

# Diferència SUAU_v1 - BASE_v2 (baixa freq) i SUAU_v1 - VIXEN als cantons
for k in ['SUAU_v1', 'BASE_v2', 'TANG_SUAU_v2']:
    d = low(lum(imgs[k]) - lum(vix), 12)
    lo, hi = np.percentile(d[r > 3.5], [1, 99])
    print(k, '- VIXEN: p1/p99', lo, hi)
    v = np.clip((d - lo) / (hi - lo), 0, 1); v[r < 3.0] = 0.5
    Image.fromarray((v[::4, ::4] * 255).astype(np.uint8)).save(os.path.join(SP, f'ombres_diff_{k}_vixen.png'))

# Zones marcades (coordenades aprox. del llenç a partir de la captura de Pere)
zones = {'dalt-esq (1850,207)': (1850, 207), 'dalt-dreta (6695,86)': (6695, 86),
         'baix-esq (86,4416)': (86, 4416), 'baix-dreta (6643,4416)': (6643, 4416),
         'centre-esq (300,2200)': (300, 2200), 'centre-dalt (3400,150)': (3400, 150),
         'centre-baix (3400,4400)': (3400, 4400), 'centre-dreta (6600,2200)': (6600, 2200)}
for k, a in imgs.items():
    L = lum(a)
    print('==', k)
    for zn, (x, y) in zones.items():
        x0, x1 = max(0, x - 120), min(W, x + 120); y0, y1 = max(0, y - 120), min(H, y + 120)
        print(f'  {zn:26s} L={np.median(L[y0:y1, x0:x1]):8.1f}  vix={np.median(lum(vix)[y0:y1, x0:x1]):8.1f}  '
              f'RGB={np.median(a[y0:y1, x0:x1].reshape(-1,3),axis=0).round(0)}')
