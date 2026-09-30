"""Construeix CapesInteriorsV4.psb des de zero amb psd-tools (psb_utils): les mateixes capes de V3 (píxels intactes, Capa 4/5 retallades
al marc), totes desplaçades (−1,−1) per tornar a la geometria del 18-08 (= CapesExteriors), màscares radials noves a 16 bits,
una capa de guany radial (Color Dodge) a dalt, i la imatge fusionada nova."""
import os, sys, json, time, numpy as np
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, add_mask16, finalize_lr16, set_merged
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:5.0f} s]', *a, flush=True)
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
OUT = D + 'CapesInteriorsV4.psb'
assert not os.path.exists(OUT), 'ja existeix ' + OUT
meta = json.load(open('v3/meta.json')); nL = len(meta['layers'])
files = sorted(__import__('glob').glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
V3 = PSDImage.open(D + 'CapesInteriorsV3.psb')
W, H = 7648, 5353
psd = new_psb(W, H, resources_from=V3)
FRAME = (457, 463)          # origen del marc 6960×4640 a V4 (DNG, Capa 4/5 retallades)
NOMS = {1: '11_1-500s_572A2968.CR3 (era «Capa 4» a V3)', 2: '10_1-125s_572A2969.CR3 (era «Capa 5» a V3)'}
ORDRE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]          # de baix a dalt: Capa 4 (base), Capa 5, 09…03, i la 12 (perles) a dalt
NOMS[1] = NOMS[1] + ' · BASE (màscara blanca: capa de fons; on es veu ho decideixen les màscares de sobre)'
NOMS[0] = '12_1-3200s_572A2956.CR3 · PERLES (màscara: interior de la Lluna + nuclis saturats del creixent i la protuberància)'
for i in ORDRE:
    info = meta['layers'][i]; name = NOMS.get(i, info['name'])
    a = np.load(files[i], mmap_mode='r')
    if i == 0:
        rgb = np.asarray(a); top, left = info['bbox'][1] - 1, info['bbox'][0] - 1       # (456, 462)
        mask = np.load('v4/masks/00_mask.npy'); assert mask.shape == rgb.shape[:2]
    else:
        l0, t0_ = info['bbox'][:2]
        rgb = np.ascontiguousarray(a[464 - t0_:5104 - t0_, 458 - l0:7418 - l0])        # el marc (6960×4640)
        top, left = FRAME[1], FRAME[0]
        mask = np.load(f'v4/masks/{i:02d}_mask.npy')
        assert mask.shape == rgb.shape[:2] == (4640, 6960)
    layer = add_pixel_layer(psd, rgb, name, top=top, left=left, mask8=None, blend=BlendMode.NORMAL, opacity=255, visible=True, compression=Compression.ZIP)
    if mask is not None:
        add_mask16(layer, mask, top=top, left=left, compression=Compression.ZIP_WITH_PREDICTION)
    log('capa', i, name[:40], 'bbox', (left, top, left + rgb.shape[1], top + rgb.shape[0]), 'visible', True, 'màscara' if mask is not None else 'sense màscara')
# capa de guany radial (Color Dodge)
G = np.load('v4/gain_raster.npz'); V = G['V']; gx0, gy0 = int(G['x0']), int(G['y0'])
rgbg = np.repeat(np.clip(np.round(V * 65535), 0, 65535).astype(np.uint16)[..., None], 3, axis=2)
layer = add_pixel_layer(psd, np.ascontiguousarray(rgbg), 'GUANY RADIAL · Color Dodge · perfil de V3 (apaga-la per veure la fusió nua)', top=gy0, left=gx0, mask8=None,
                        blend=BlendMode.COLOR_DODGE, opacity=255, visible=True, compression=Compression.ZIP)
log('capa de guany', (gx0, gy0, gx0 + V.shape[1], gy0 + V.shape[0]), 'v màx', float(V.max()))
finalize_lr16(psd)
# fusionada: blanc fora del marc (com la de V3), el compost amb guany dins
merged = np.full((H, W, 3), 65535, np.uint16)
cg = np.load('v4/compost_gain_rgb16.npy', mmap_mode='r')
merged[FRAME[1]:FRAME[1] + 4640, FRAME[0]:FRAME[0] + 6960] = cg
set_merged(psd, merged, compression=Compression.RAW)
psd._record.header.channels = 3
log('desant', OUT)
psd.save(OUT)
log('desat', os.path.getsize(OUT) / 1e9, 'GB')
