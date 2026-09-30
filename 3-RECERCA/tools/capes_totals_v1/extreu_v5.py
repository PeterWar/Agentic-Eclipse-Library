"""Extreu les 12 capes de CapesInteriorsV5.psb (RGB uint16 + màscares 16 bits + meta)."""
import os, json, time, numpy as np
from psd_tools import PSDImage
t0=time.time()
def log(*a): print(f'[{time.time()-t0:5.0f} s]', *a, flush=True)
SRC='/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/CapesInteriorsV5.psb'
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'v5')
psd=PSDImage.open(SRC); meta=[]
for i,l in enumerate(psd):
    arr=l.numpy('color')
    np.save(os.path.join(OUT,f'v{i:02d}_rgb.npy'), np.clip(np.rint(arr*65535),0,65535).astype(np.uint16))
    mrec=None
    if l.mask is not None:
        marr=l.numpy('mask')
        np.save(os.path.join(OUT,f'v{i:02d}_mask.npy'), np.clip(np.rint(marr[...,0]*65535),0,65535).astype(np.uint16))
        mrec=dict(left=l.mask.left,top=l.mask.top,right=l.mask.right,bottom=l.mask.bottom,bg=l.mask.background_color)
    meta.append(dict(i=i,nom=l.name,left=l.left,top=l.top,right=l.right,bottom=l.bottom,
                     blend=str(l.blend_mode),opacity=l.opacity,visible=l.visible,mask=mrec))
    log(i,l.name[:40])
json.dump(meta,open(os.path.join(OUT,'meta.json'),'w'),indent=1,ensure_ascii=False)
log('FET')
