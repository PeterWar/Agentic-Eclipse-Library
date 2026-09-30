"""Desplegat polar del COMPOST (merged V2b o un altre RGBA/RGB npy) al voltant de la Lluna (centre d'ID7), canal G,
detrended per azimut (gaussiana 1-D σ=8 px al llarg del radi) i mostrat a ±3 %; frontera de la banda d'ID7 en vermell,
final de la zona F=1 en blau. Mitjana per sectors del residu alineat a la frontera."""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from geom import *
path = sys.argv[1]; tag = sys.argv[2]; i = int(sys.argv[3]) if len(sys.argv) > 3 else 7
M = np.load(path, mmap_mode='r')
e = ELL[str(i)]; cx, cy = e['cx']+OFF[0], e['cy']+OFF[1]; Rm = R_moon(i)
azs = np.arange(0, 360, 0.5); az = np.radians(azs); rr = Rm + np.arange(0, 100, 0.5)
X = cx + rr[None, :]*np.cos(az[:, None]); Y = cy - rr[None, :]*np.sin(az[:, None])
S = 1200; x0, y0 = int(cx-S//2), int(cy-S//2)
a = np.asarray(M[y0:y0+S, x0:x0+S, 1], np.float32)/65535.
P = ndi.map_coordinates(a, [(Y-y0).ravel(), (X-x0).ravel()], order=1).reshape(len(az), len(rr)).T
F, N = ref_fraction(i, (X-OFF[0]).astype(np.float32), (Y-OFF[1]).astype(np.float32)); F = F.T
sm = ndi.gaussian_filter1d(P, 16, axis=0, mode='nearest'); rel = P/np.maximum(sm, 1e-3)
img = np.clip((rel-1)/0.06+0.5, 0, 1); img = np.repeat(img, 2, axis=0)
im = Image.fromarray((img*255).astype(np.uint8)).convert('RGB'); dr = ImageDraw.Draw(im)
banda = F > 1.0/N+1e-3
for mask, col in ((banda, (255, 0, 0)), (F > 0.999, (0, 160, 255))):
    ed = ndi.binary_dilation(mask) & ~mask; ys, xs = np.nonzero(ed)
    for yv, xv in zip(ys, xs): dr.point((int(xv), int(yv)*2), fill=col)
im.save(f'polar_merged_{tag}.png')
# residu alineat a la frontera: per azimut, rel(u) amb u = d - frontera; mitjana per sector de 30°
print(f'{tag}: residu relatiu (%) del compost, mitjana per sector, en u = px respecte a la frontera de la banda (files: u=-20..+20 pas 4)')
us = np.arange(-20, 21, 4)
for s0 in range(0, 360, 30):
    rows = []
    for j in np.where((azs >= s0) & (azs < s0+30))[0]:
        if not banda[:, j].any(): continue
        fr = rr[banda[:, j]].max()
        prof = np.interp(fr+us, rr, rel[:, j]); rows.append(prof)
    if not rows: continue
    m = 100*(np.median(np.array(rows), axis=0)-1)
    print(f'  {s0:3d}: ' + ' '.join(f'{v:+5.2f}' for v in m))
