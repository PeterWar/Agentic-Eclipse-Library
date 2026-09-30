"""Comparació abans/després de les ombres: SUAU_v1 (la que Pere ha marcat) contra SUAU v4, mateix
estirat; més el camp llunyà a baixa freqüència de totes dues i de la referència Vixen."""
import os, numpy as np, tifffile
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

SP = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
r = np.load(os.path.join(SP, 'r_rsol.npy')); H, W = r.shape
old = tifffile.imread(os.path.join(D, '_anteriors_DoG', 'APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_SUAU_6748x4553.tif')).astype(np.float32) / 65535
new = tifffile.imread(os.path.join(D, 'APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_SUAU_6748x4553.tif')).astype(np.float32) / 65535
base = tifffile.imread(os.path.join(D, 'APILAT_Capa_Sony_encaixada_VORESNETES_6748x4553.tif')).astype(np.float32) / 65535
vref = np.load(os.path.join(SP, 'vix_ref_rgb.npy'))
def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

# 1) tal qual, a 1/4, una al costat de l'altra (com ho veu Pere)
def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)
sep = np.full((to8(old).shape[0], 10, 3), 255, np.uint8)
Image.fromarray(np.concatenate([to8(old), sep, to8(new)], 1)).save(os.path.join(D, 'APILAT_comparacio_ombres_SUAU_v1_vs_v4.jpg'), quality=92)
# 2) camp llunyà estirat igual per a totes (percentils de la nova a r>4,5)
L_old, L_new, L_base, L_ref = [ndi.gaussian_filter(lum(a), 10) for a in (old, new, base, vref)]
lo, hi = np.percentile(L_new[r > 4.5], [0.5, 99.5])
def st(Lx):
    v = np.clip((Lx - lo) / (hi - lo), 0, 1); v[r < 3.2] = 0.5
    return (v[::4, ::4] * 255).astype(np.uint8)
row1 = np.concatenate([st(L_old), st(L_new)], 1); row2 = np.concatenate([st(L_base), st(L_ref)], 1)
im = Image.fromarray(np.concatenate([row1, row2], 0)); d = ImageDraw.Draw(im)
for (x, y, t) in ((10, 10, 'REALCADA SUAU v1 (la de Pere)'), (W // 4 + 10, 10, 'REALCADA SUAU v4'), (10, H // 4 + 10, 'base v4'), (W // 4 + 10, H // 4 + 10, 'referencia Vixen (capa de Pere sense enfosquiment)')):
    d.text((x, y), t, fill=255)
im.save(os.path.join(D, 'APILAT_comparacio_ombres_camp_llunya_v1_v4.png'))
# 3) retalls dels quatre cantons i la punta del raig, tal qual (sense estirar), v1 | v4
crops = []
for (y0, x0) in ((0, 0), (0, W - 900), (H - 600, 0), (H - 600, W - 900), (0, 1400)):
    a = np.clip(old[y0:y0 + 600, x0:x0 + 900], 0, 1); b = np.clip(new[y0:y0 + 600, x0:x0 + 900], 0, 1)
    crops.append(np.concatenate([a, np.ones((600, 8, 3)), b], 1))
Image.fromarray((np.concatenate(crops, 0)[::2, ::2] * 255).astype(np.uint8)).save(os.path.join(D, 'APILAT_comparacio_ombres_cantons_v1_v4.jpg'), quality=92)
print('fet')
for tag, (y, x) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W - 150)), ('baix-esq', (H - 150, 150)), ('baix-dreta', (H - 150, W - 150)), ('punta raig', (200, 1840)), ('dalt', (150, W // 2)), ('esq', (H // 2, 150))):
    bx = (slice(y - 100, y + 100), slice(x - 100, x + 100))
    print(f'{tag:11s} v1 {65535*np.median(L_old[bx]):6.0f}  v4 {65535*np.median(L_new[bx]):6.0f}  base v4 {65535*np.median(L_base[bx]):6.0f}  ref {65535*np.median(L_ref[bx]):6.0f}')
