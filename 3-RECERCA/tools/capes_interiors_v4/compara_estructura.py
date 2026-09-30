"""Compara l'estructura azimutal (imatge / mediana azimutal per radi) de V3, V4 i capes soles, a resolució 1/2, finestra al voltant del Sol."""
import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
SUN3 = (4021.89, 2738.66); RS = 446.15
mer = np.load('v3/merged_rgb.npy', mmap_mode='r'); V4 = np.load('v4/compost_rgb16.npy', mmap_mode='r')
L8 = np.load('v3/04_08_1-30s_572A2970_apilat4.dng_rgb.npy', mmap_mode='r'); L7 = np.load('v3/05_07_1-15s_572A2976_apilat2.dng_rgb.npy', mmap_mode='r'); L6 = np.load('v3/06_06_1-8s_572A2971_apilat4.dng_rgb.npy', mmap_mode='r'); L5c = np.load('v3/02_Capa_5_rgb.npy', mmap_mode='r')
S = int(2.1 * RS)
def getG(arr, ox, oy, sunx, suny):
    x0, y0 = int(round(sunx - S)) - ox, int(round(suny - S)) - oy
    return np.asarray(arr[y0:y0 + 2 * S, x0:x0 + 2 * S, 1], np.float32) / 65535.
def norm(G):
    yy, xx = np.mgrid[0:2 * S, 0:2 * S]; r = np.hypot(xx - S + 0.5, yy - S + 0.5) / RS
    rb = np.round(r / 0.01).astype(int)
    med = np.zeros(rb.max() + 1)
    for k in range(rb.max() + 1):
        m = rb == k
        if m.sum(): med[k] = np.median(G[m])
    prof = med[rb]
    Q = G / np.maximum(prof, 1e-4)
    Q[(r < 1.0) | (r > 2.05)] = 1.0
    return Q
def tile(Q, lab, sat_mask=None):
    img = np.clip(Q / 2.0, 0, 1)[::2, ::2]
    im = Image.fromarray((img * 255).astype(np.uint8)).convert('RGB'); ImageDraw.Draw(im).text((6, 4), lab, fill=(255, 255, 0)); return im
tiles = [tile(norm(getG(mer, 0, 0, *SUN3)), 'V3 / mediana anell'), tile(norm(getG(V4, 457, 463, SUN3[0] - 1, SUN3[1] - 1)), 'V4 / mediana anell'),
         tile(norm(getG(L5c, 0, 0, *SUN3)), 'Capa 5 (1/125) / mediana'), tile(norm(getG(L8, 458, 464, *SUN3)), 'capa 08 (1/30) / mediana'),
         tile(norm(getG(L7, 458, 464, *SUN3)), 'capa 07 (1/15) / mediana'), tile(norm(getG(L6, 458, 464, *SUN3)), 'capa 06 (1/8) / mediana')]
w = tiles[0].width
out = Image.new('RGB', (3 * w + 20, 2 * w + 20), (30, 30, 30))
for k, t in enumerate(tiles):
    out.paste(t, ((k % 3) * (w + 10), (k // 3) * (w + 10)))
out.save('v4/comparativa_estructura.png'); print(out.size)
