"""Reconstrueix CapesInteriorsV4.psb amb la filosofia de V3: ORDRE DE V3 (la 1/3200 a baix, sense màscara; les llargues a sobre),
màscares = les de Pere promitjades per anell (radials pures) × disc lunar × cascada de protecció (on la 1/125 o la 1/500 estan
cremades manen les capes de sota), 04 i 03 ocultes com a V3, cap capa de guany. Geometria del 18-08 (tot a −1,−1 de V3)."""
import os, json, time, numpy as np
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, finalize_lr16, set_merged
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:5.0f} s]', *a, flush=True)
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
OUT = D + 'CapesInteriorsV4.psb'
meta = json.load(open('v3/meta.json')); nL = len(meta['layers'])
files = sorted(__import__('glob').glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
V3 = PSDImage.open(D + 'CapesInteriorsV3.psb')
W, H = 7648, 5353
psd = new_psb(W, H, resources_from=V3)
FRAME = (457, 463)
NOMS = {1: 'Capa 4 = 11_1-500s_572A2968.CR3', 2: 'Capa 5 = 10_1-125s_572A2969.CR3'}
# compost per a la fusionada: 12 + capes visibles amb les màscares V5
h, w = 4640, 6960
masks = {i: np.load(f'v5/masks/{i:02d}_mask.npy', mmap_mode='r') for i in range(1, nL)}
for i in range(nL):                      # ordre de V3: 0 (12) a baix, després 1..9
    info = meta['layers'][i]; name = NOMS.get(i, info['name'])
    a = np.load(files[i], mmap_mode='r')
    if i == 0:
        rgb = np.asarray(a); top, left = 462, 456; mask = None
    else:
        l0, t0_ = info['bbox'][:2]
        rgb = np.ascontiguousarray(a[464 - t0_:5104 - t0_, 458 - l0:7418 - l0])
        top, left = FRAME[1], FRAME[0]
        mask = np.asarray(masks[i])
    layer = add_pixel_layer(psd, rgb, name, top=top, left=left, mask8=None, blend=BlendMode.NORMAL, opacity=255,
                            visible=info['visible'], compression=Compression.ZIP)
    if mask is not None:
        add_mask16(layer, mask, top=top, left=left, compression=Compression.ZIP_WITH_PREDICTION)
    log('capa', i, name[:44], 'vis', info['visible'], 'màscara' if mask is not None else 'sense màscara (base, com a V3)')
finalize_lr16(psd)
merged = np.full((H, W, 3), 65535, np.uint16)
merged[FRAME[1]:FRAME[1] + h, FRAME[0]:FRAME[0] + w] = np.load('v5/compost_rgb16.npy', mmap_mode='r')
set_merged(psd, merged, compression=Compression.RAW)
psd._record.header.channels = 3
if os.path.exists(OUT):
    os.replace(OUT, OUT + '.anterior-disseny-claude')   # conservem el disseny refusat fins que Pere digui
    log('anterior →', OUT + '.anterior-disseny-claude')
psd.save(OUT)
log('desat', OUT, os.path.getsize(OUT) / 1e9, 'GB')
