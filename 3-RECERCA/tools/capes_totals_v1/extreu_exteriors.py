"""Extreu les 8 capes de CapesExteriors.psb (RGB uint16 + màscara uint16 + metadades) a npy."""
import os, sys, json, time, numpy as np
from psd_tools import PSDImage
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
SRC = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/CapesExteriors.psb')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ext')
psd = PSDImage.open(SRC)
meta = []
for i, l in enumerate(psd):
    nom = l.name
    log(f'capa {i}: {nom[:60]}')
    arr = l.numpy('color')  # float32 0..1, (H,W,3)
    np.save(os.path.join(OUT, f'capa{i:02d}_rgb.npy'), np.clip(np.rint(arr*65535),0,65535).astype(np.uint16))
    m = l.mask
    mrec = None
    if m is not None:
        marr = l.numpy('mask')
        if marr is not None:
            np.save(os.path.join(OUT, f'capa{i:02d}_mask.npy'), np.clip(np.rint(marr[...,0]*65535),0,65535).astype(np.uint16))
            mrec = dict(left=m.left, top=m.top, right=m.right, bottom=m.bottom, bg=m.background_color)
    meta.append(dict(i=i, nom=nom, left=l.left, top=l.top, right=l.right, bottom=l.bottom,
                     blend=str(l.blend_mode), opacity=l.opacity, visible=l.visible, mask=mrec))
    log(f'  bbox=({l.left},{l.top},{l.right},{l.bottom}) desada')
with open(os.path.join(OUT, 'meta.json'), 'w') as f:
    json.dump(meta, f, indent=1, ensure_ascii=False)
log('FET')
