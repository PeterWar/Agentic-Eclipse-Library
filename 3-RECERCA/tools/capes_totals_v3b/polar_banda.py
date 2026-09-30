"""Desplegat polar al voltant de la Lluna (x = azimut 0..360 a 0,5°, y = píxels fora del limbe 0..90) amb la tendència radial
treta (dividit per la mediana en un anell de ±12 px i, a més, per la mediana azimutal de cada fila), per veure si hi ha un arc
que segueixi la frontera de la banda (vermell)."""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from geom import *
for i in [int(s) for s in sys.argv[1:]] or [7, 8, 9]:
    G = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')
    e = ELL[str(i)]; cx, cy = e['cx'], e['cy']; Rm = R_moon(i)
    az = np.radians(np.arange(0, 360, 0.5)); rr = Rm + np.arange(0, 90, 0.5)
    X = cx + rr[None, :]*np.cos(az[:, None]); Y = cy - rr[None, :]*np.sin(az[:, None])
    S = 1200; x0, y0 = int(cx-S//2), int(cy-S//2)
    a = np.asarray(G[y0:y0+S, x0:x0+S], np.float32)/65535.
    P = ndi.map_coordinates(a, [(Y-y0).ravel(), (X-x0).ravel()], order=1).reshape(len(az), len(rr)).T  # files = radi
    F, N = ref_fraction(i, X.astype(np.float32), Y.astype(np.float32)); F = F.T
    # tendència radial per azimut: suavitzat 1-D al llarg del radi (σ = 8 px = 16 mostres) i divisió
    sm = ndi.gaussian_filter1d(P, 16, axis=0, mode='nearest')
    rel = P/np.maximum(sm, 1e-3)
    img = np.clip((rel-1)/0.06+0.5, 0, 1)
    img = np.repeat(img, 2, axis=0)  # 1 px de radi = 2 files → 0,5 px/fila ja; fem 4 files per px
    im = Image.fromarray((img*255).astype(np.uint8)).convert('RGB'); dr = ImageDraw.Draw(im)
    banda = F > 1.0/N+1e-3
    edge = ndi.binary_dilation(banda) & ~banda
    ys, xs = np.nonzero(edge)
    for yv, xv in zip(ys, xs): dr.point((int(xv), int(yv)*2), fill=(255, 0, 0))
    # línia del final de zona_ref pura (F==1): contorn de F>0.999
    e2 = ndi.binary_dilation(F > 0.999) & ~(F > 0.999); ys, xs = np.nonzero(e2)
    for yv, xv in zip(ys, xs): dr.point((int(xv), int(yv)*2), fill=(0, 160, 255))
    im.save(f'polar_id{i}.png'); print('polar_id%d.png' % i, im.size)
