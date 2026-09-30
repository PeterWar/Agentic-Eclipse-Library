"""t3 (V96) · Opció B per al buit sense dada (d entre el limbe i DMIN, ~1–2 px) de la NRGF, que és en MULTIPLICAR (transparent = no enfosqueix = línia clara):
als píxels SENSE DADA, només el NIVELL de la NRGF nova als primers píxels de dada (d − DMIN entre 1 i 3 px), al llarg de l'arc (gaussiana d'azimut σ 3 px), sense
textura; els píxels AMB dada, intactes; alfa 1 (com la V95); dins del disc, rampa cap a 0,5 com la V93 (la màscara de Pere tapa el disc).
Compost emulat de V95, A (transparent) i B, 6:1. Sortida: t3_B_u16_caixa.npy i C3_OPCIONS_BUIT_6a1.png."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v90_marques_pere_20260923'))
from psb69 import PSB
from v86_compost import capa_box
from vm_compost import comp
from v86_operadors import smoothstep
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NB = len(DMIN)
B = 560; box = (int(cx) - B, int(cy) - B, int(cx) + B, int(cy) + B); x0, y0, x1, y1 = box; sl = (slice(y0, y1), slice(x0, x1))
u = np.asarray(np.load(SORT / 'P01_NRGF_u16.npy', mmap_mode='r')[sl]).astype(np.float32) / 65535; alA = np.asarray(np.load(SORT / 'P01_NRGF_alfa_u16.npy', mmap_mode='r')[sl]).astype(np.float32) / 65535
FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'; m = np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[sl]).copy()
qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; assert qy0 <= y0 and y1 <= qy1 and qx0 <= x0 and x1 <= qx1   # la caixa és dins la caixa A3A
m = (Q['domini'] & (Q['G'] > 0))[y0 - qy0:y1 - qy0, x0 - qx0:x1 - qx0].copy()
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dmin = DMIN[(th / 360 * NB).astype(int) % NB]; dist = d - dmin
# nivell al llarg de l'arc als primers píxels de dada (1 ≤ d − DMIN < 3), per calaixos d'azimut de 0,1° i gaussiana σ 3 px d'arc
NT = 3600; tb = (th / 360 * NT).astype(int) % NT; zona = m & (dist >= 1) & (dist < 3)
s = np.bincount(tb[zona], weights=u[zona], minlength=NT); n = np.bincount(tb[zona], minlength=NT).astype(float)
sig = 3.0 / (R * np.radians(360 / NT)); lev = gaussian_filter1d(s, sig, mode='wrap') / np.maximum(gaussian_filter1d(n, sig, mode='wrap'), 1e-9)
L = lev[tb].astype(np.float32); buit = (~m) & (d > -12) & (d < 40)
valB = np.where(m, u, np.where(d >= -4, L, np.where(d <= -10, 0.5, L + (0.5 - L) * (1 - smoothstep(d, -10, -4))))).astype(np.float32)
np.save(SORT / 't3_B_u16_caixa.npy', np.round(np.clip(valB, 0, 1) * 65535).astype(np.uint16)); print('píxels sense dada omplerts amb nivell (d −4…DMIN):', int(((~m) & (d >= -4) & (d < 5)).sum()), '· píxels amb dada tocats: 0')
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); capes = [Lr for Lr in p.layers if Lr['visible'] and Lr['right'] > Lr['left']]
def fer(val=None, alfa=None):
    ll = []
    for Lr in capes:
        mode, F, a = capa_box(p, Lr['id'], box)
        if val is not None and Lr['id'] == 41:
            F = np.repeat(val[..., None], 3, -1); msk = p.channel_box(41, -2, box, fill=0).astype(np.float32) / 65535; a = alfa * msk * (Lr['opacity'] / 255.0)
        ll.append((str(mode).split('.')[-1].upper(), F, a))
    return comp(ll, y1 - y0, x1 - x0)[0]
C5 = fer(); CA = fer(u, alA); CB = fer(valB, np.ones_like(u))
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
for nom, C in (('A transparent', CA), ('B nivell al buit', CB)):
    rat = lum(C) / np.maximum(lum(C5), 1e-4) - 1
    print(nom, 'canvi contra V95 (%) per d [−1, 0, 1, 2, 3, 6, 10, 15]:', {f'{a0}-{a1}': [round(float(np.mean(rat[(th >= a0) & (th < a1) & (np.abs(d - dd) < 0.25)])) * 100, 1) for dd in (-1, 0, 1, 2, 3, 6, 10, 15)] for a0, a1 in ((195, 295), (52, 108), (300, 360), (0, 360))})
LLOCS = [(245, 6), (85, 6), (60, 6), (330, 4), (215, 6), (160, 8)]; w, zf = 56, 6; F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
out = Image.new('RGB', (3 * (w * zf + 8), len(LLOCS) * (w * zf + 24) + 36), 'white'); dr = ImageDraw.Draw(out)
dr.text((6, 8), 'Compost EMULAT 6:1 · V95 (actual) · A: NRGF nova, buit transparent · B: NRGF nova, al buit NOMÉS el nivell (sense textura)', fill='black', font=F_)
for j, (az, dd) in enumerate(LLOCS):
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - x0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - y0; ref = C5[py - w // 2:py + w // 2, px - w // 2:px + w // 2]; lo, hi = np.percentile(ref, (1, 99.5))
    for i, C in enumerate((C5, CA, CB)):
        c = np.clip((C[py - w // 2:py + w // 2, px - w // 2:px + w // 2] - lo) / max(hi - lo, 1e-6), 0, 1); im = cv2.resize(np.uint8(c * 255), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        out.paste(Image.fromarray(im), (i * (w * zf + 8), 36 + j * (w * zf + 24) + 20)); dr.text((i * (w * zf + 8) + 4, 36 + j * (w * zf + 24) + 2), f'{az}° · {("V95", "A transparent", "B nivell al buit")[i]}', fill='black', font=F_)
out.save(SORT / 'C3_OPCIONS_BUIT_6a1.png'); print('fet')
