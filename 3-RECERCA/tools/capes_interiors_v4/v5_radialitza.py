"""V5 = la filosofia de V3: mateix ordre (1/3200 a baix), les màscares de Pere promitjades per anell (cap estructura azimutal),
cascada de protecció «manen les capes inferiors» allà on la 1/125 o la 1/500 estan cremades (perles, protuberàncies, cromosfera),
disc lunar → només la 1/3200, Capa 4/5 retallades al marc, geometria del 18-08. Escriu v5/masks/*.npy, compost i previews."""
import numpy as np, json, os, glob
from scipy import ndimage as ndi, special
from PIL import Image
os.makedirs('v5/masks', exist_ok=True)
meta = json.load(open('v3/meta.json')); nL = len(meta['layers'])
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
RS = 446.15
SUN3 = (4021.89, 2738.66)                       # Sol a V3 (coordenades de document V3)
SUN5 = (4020.89, 2737.66)                       # Sol a V5 (= V4: tot a −1,−1)
MOON5 = (4034.8, 2736.3); R_DISK = 451.5 - 14.0; SIG_DISK = 4.0
FRAME = (457, 463, 7417, 5103)
# ---- 1. perfil radial (mitjana azimutal) de cada màscara de V3, a resolució completa, en bins de 0,002 R☉
yy, xx = np.mgrid[0:5353, 0:7648].astype(np.float32)
r3 = np.hypot(xx - SUN3[0], yy - SUN3[1]) / RS
del yy, xx
bins = np.round(r3 / 0.002).astype(np.int32)
nb = int(bins.max()) + 1
cnt_all = np.bincount(bins.ravel(), minlength=nb).astype(np.float64)
prof = {}
for i in range(1, nL):
    info = meta['layers'][i]; mb = info['mask']['bbox']; m = np.load(files[i].replace('_rgb.npy', '_mask.npy'), mmap_mode='r')
    # màscara al llenç V3 (fora de la seva bbox: el color de fons)
    full = np.full((5353, 7648), info['mask']['bg'] / 255.0, np.float32)
    y0, y1 = max(mb[1], 0), min(mb[3], 5353); x0, x1 = max(mb[0], 0), min(mb[2], 7648)
    full[y0:y1, x0:x1] = np.asarray(m[y0 - mb[1]:y1 - mb[1], x0 - mb[0]:x1 - mb[0]], np.float32) / 65535.
    # només dins del marc de contingut (V3: files 464..5103, cols 458..7417): fora no compta
    inside = np.zeros((5353, 7648), bool); inside[464:5104, 458:7418] = True
    s = np.bincount(bins[inside].ravel(), weights=full[inside].ravel().astype(np.float64), minlength=nb)
    c = np.bincount(bins[inside].ravel(), minlength=nb).astype(np.float64)
    p = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    # omple buits i suavitza (σ = 0,02 R☉ = 10 bins)
    ok = np.isfinite(p); p[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), p[ok])
    p = ndi.gaussian_filter1d(p, 10.0, mode='nearest')
    prof[i] = p
    print('màscara', i, info['name'][:14], 'mitjana radial a r=1,0/1,2/1,5/2/3/5:', [round(float(p[int(round(r / 0.002))]), 3) for r in (1.0, 1.2, 1.5, 2.0, 3.0, 5.0)], flush=True)
rr_b = np.arange(nb) * 0.002
np.savez('v5/perfils_mascares_v3.npz', rr=rr_b, **{f'p{i}': prof[i] for i in prof})
del bins, r3
# ---- 2. raster al marc (coordenades V5)
yy, xx = np.mgrid[FRAME[1]:FRAME[3], FRAME[0]:FRAME[2]].astype(np.float32)
r_sun = np.hypot(xx - SUN5[0], yy - SUN5[1]) / RS
r_moon = np.hypot(xx - MOON5[0], yy - MOON5[1])
disk_out = 0.5 * (1 + special.erf((r_moon - R_DISK) / (SIG_DISK * np.sqrt(2)))).astype(np.float32)
del r_moon, yy, xx
def rad(i): return np.interp(r_sun, rr_b, prof[i]).astype(np.float32)
# cascada de protecció: cremat de la 1/125 (h5) i de la 1/500 (h4) al limbe (0,95–1,15 R☉)
def blown(i):
    a = np.load(files[i], mmap_mode='r'); l0, t0 = meta['layers'][i]['bbox'][:2]
    mx = np.asarray(a[464 - t0:5104 - t0, 458 - l0:7418 - l0], np.float32).max(-1) / 65535.
    h = np.clip((mx - 0.60) / 0.25, 0, 1); h = h * h * (3 - 2 * h)
    h *= ((r_sun > 0.95) & (r_sun < 1.15)).astype(np.float32)
    return ndi.gaussian_filter(h, 1.5).astype(np.float32)
h5 = blown(2); h4 = blown(1)
print('protecció: píxels h5>0,5:', int((h5 > 0.5).sum()), ' h4>0,5:', int((h4 > 0.5).sum()), flush=True)
masks = {}
masks[1] = disk_out * (1 - h4)
masks[2] = rad(2) * disk_out * (1 - h5)
for i in range(3, nL): masks[i] = rad(i) * disk_out * (1 - h5)
for i in range(1, nL):
    np.save(f'v5/masks/{i:02d}_mask.npy', np.clip(np.round(masks[i] * 65535), 0, 65535).astype(np.uint16))
    print('màscara V5', i, meta['layers'][i]['name'][:14], 'mitjana', float(masks[i].mean()), flush=True)
np.save('v5/masks/00_mask.npy', np.full(r_sun.shape, 65535, np.uint16))      # 12: base blanca (a la seva pròpia bbox: mateixa mida)
np.save('v5/h5.npy', h5); np.save('v5/h4.npy', h4)
# ---- 3. compost (12 base + capes visibles com a V3: 04 i 03 ocultes)
h, w = r_sun.shape
a12 = np.load(files[0], mmap_mode='r')
C = np.zeros((h, w, 3), np.float32); C[:h - 1, :w - 1] = np.asarray(a12[1:, 1:], np.float32) / 65535.; C[h - 1] = C[h - 2]; C[:, w - 1] = C[:, w - 2]
for i in range(1, nL):
    if not meta['layers'][i]['visible']: continue
    a = np.load(files[i], mmap_mode='r'); l0, t0 = meta['layers'][i]['bbox'][:2]
    sub = np.asarray(a[464 - t0:5104 - t0, 458 - l0:7418 - l0], np.float32) / 65535.
    m = masks[i][..., None]; C = C * (1 - m) + sub * m
    print('composta', i, flush=True)
np.save('v5/compost_rgb16.npy', np.clip(np.round(C * 65535), 0, 65535).astype(np.uint16))
def prev(arr16, name):
    a = np.asarray(arr16[::4, ::4], np.float32) / 65535.; Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(name)
prev(np.load('v5/compost_rgb16.npy', mmap_mode='r'), 'v5/prev_V5.png')
print('fet')
