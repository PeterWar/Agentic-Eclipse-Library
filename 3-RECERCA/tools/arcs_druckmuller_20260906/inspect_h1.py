"""View the exact stored H1 contribution. Diagnostic only, no source edits.

Original 01 is V29/V30; V31 is its subsequent normalized sigma3 smoothing.
The H1 difference includes final uint16 quantization/clipping, explicitly.
All panels have fixed gain and retain a whole-canvas view alongside 1:1.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/arcs_druckmuller_20260906'
C=ROOT/'research/tools/v29/cau_final'
pre=np.load(C/'achf_smoothed.npy',mmap_mode='r')
post=np.load(C/'achf_u16.npy',mmap_mode='r')
v31=np.load(ROOT/'research/tools/v31/cau/01_final_u16.npy',mmap_mode='r')
mask=np.load(C/'fusion_support.npy',mmap_mode='r')
def values(sl):
    a=np.asarray(pre[sl],np.float32)+.5
    b=np.asarray(post[sl],np.float32)/65535
    c=np.asarray(v31[sl],np.float32)/65535
    delta=b-a
    return [a,b,c,.5+10*delta]
names=['01 abans H1 (V29)','01 despres H1 (V29/V30)','01 actual V31','Canvi H1 x10 + quantitzacio']
def panel(arrs,path):
    h,w=arrs[0].shape
    im=Image.new('RGB',(2*w,2*(h+32)),(25,25,25));d=ImageDraw.Draw(im)
    for k,(a,label) in enumerate(zip(arrs,names)):
        x=(k%2)*w;y=(k//2)*(h+32)
        im.paste(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('RGB'),(x,y+32))
        d.text((x+8,y+8),label,fill='white')
    im.save(path)
sl=(slice(None,None,7),slice(None,None,7))
arrs=values(sl)
for a in arrs:a[~mask[sl]]=.5
panel(arrs,OUT/'H1_01_LLENC_SENCER.png')
for tag,(x,y) in {'N':(5715,2200),'S':(5130,5160),'interior':(5810,3260)}.items():
    panel(values((slice(y-256,y+256),slice(x-256,x+256))),OUT/f'H1_01_{tag}_100.png')
print('H1 before/after views complete; source caches unchanged.')
