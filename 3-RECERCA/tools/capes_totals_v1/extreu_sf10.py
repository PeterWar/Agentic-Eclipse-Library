"""Extreu les capes 1..15 de FiltresSEMIFINAL10.psb (RGB uint16 + màscara + metadades)."""
import os, json, time, numpy as np
from psd_tools import PSDImage
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL10.psb')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sf10')
psd = PSDImage.open(SRC)
meta = []
for i, l in enumerate(psd):
    if i == 0:
        meta.append(dict(i=0, nom=l.name, left=l.left, top=l.top, right=l.right, bottom=l.bottom,
                         blend=str(l.blend_mode), opacity=l.opacity, visible=l.visible, mask=None))
        log('capa 0 (base) saltada — ja la tenim com a TIF'); continue
    log(f'capa {i}: {l.name[:50]}')
    arr = l.numpy('color')
    np.save(os.path.join(OUT, f'f{i:02d}_rgb.npy'), np.clip(np.rint(arr*65535),0,65535).astype(np.uint16))
    mrec = None
    if l.mask is not None:
        marr = l.numpy('mask')
        if marr is not None:
            np.save(os.path.join(OUT, f'f{i:02d}_mask.npy'), np.clip(np.rint(marr[...,0]*65535),0,65535).astype(np.uint16))
            mrec = dict(left=l.mask.left, top=l.mask.top, right=l.mask.right, bottom=l.mask.bottom, bg=l.mask.background_color)
    meta.append(dict(i=i, nom=l.name, left=l.left, top=l.top, right=l.right, bottom=l.bottom,
                     blend=str(l.blend_mode), opacity=l.opacity, visible=l.visible, mask=mrec))
with open(os.path.join(OUT, 'meta.json'), 'w') as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)
log('FET')
