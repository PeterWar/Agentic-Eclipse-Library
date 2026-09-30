"""a2 (29-09-2026) · Vistes de NIVELL per veure artefactes foscos amples i febles (1–3 %), al llenç sencer.
Sobre el compost sense la 414 (a1): lluminància L; D = L suavitzada (σ 8 px, normalitzada a la dada) dividida per un fons (i) radial (mediana per
anells de 4 px al voltant del Sol) o (ii) gran (σ 300 px). Es mostra ±EXC (%) al voltant del gris, amb els contorns de les marques.
Sortides: vistes/V4_nivell_radial_marques.png, V5_nivell_fons300_marques.png (1/4) i detall_nivell_marca_NN.png (1:2); nivell_radial_f32.npy."""
import json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
U = np.load(OUT / 'U_compost_sense_414_u16.npy', mmap_mode='r'); lab = np.load(OUT / 'marques_414_etiquetes.npy')
M = json.load(open(OUT / 'MARQUES_414.json'))['marques']
SOL = (5361.768, 3775.748); RSOL = 440.603; H, W = lab.shape
L = U.astype(np.float32).mean(2) / 65535
dada = L > 0.004                                           # fora del llenç amb dada el compost és negre
def suau(x, s):
    num = ndi.gaussian_filter(np.where(dada, x, 0).astype(np.float32), s); den = ndi.gaussian_filter(dada.astype(np.float32), s)
    return np.where(den > 0.2, num / np.maximum(den, 1e-6), 0)
Ls = suau(L, 8)
yy, xx = np.mgrid[0:H, 0:W]; rr = np.hypot(xx - SOL[0], yy - SOL[1]); rb = (rr / 4).astype(np.int32)
v = dada & (rr > 1.05 * RSOL)
med = np.zeros(rb.max() + 1, np.float32)
ordre = np.argsort(rb[v]); rbs = rb[v][ordre]; Lv = Ls[v][ordre]
tall = np.flatnonzero(np.diff(rbs)) + 1
for grup, b in zip(np.split(Lv, tall), rbs[np.r_[0, tall]]): med[b] = np.median(grup)
med = ndi.median_filter(med, 5)
Drad = np.where(v, Ls / np.maximum(med[rb], 1e-6) - 1, 0).astype(np.float32)
np.save(OUT / 'nivell_radial_f32.npy', Drad)
Dfons = np.where(v, Ls / np.maximum(suau(L, 300), 1e-6) - 1, 0).astype(np.float32)
try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 44)
except Exception: FONT = ImageFont.load_default()
def vista(D, exc, f, mv=None):
    mv = v if mv is None else mv
    g = np.clip(128 + D[::f, ::f] / exc * 127, 0, 255).astype(np.uint8); g = np.stack([g] * 3, 2)
    g[~mv[::f, ::f]] = (40, 40, 40); return g
def contorns(img, lb, f):
    ed = (lb != ndi.grey_erosion(lb, size=(3, 3))) & (lb > 0); ys, xs = np.nonzero(ed)
    img[(ys // f).clip(0, img.shape[0] - 1), (xs // f).clip(0, img.shape[1] - 1)] = (255, 64, 0); return img
for nom, D, exc in (('V4_nivell_radial_marques', Drad, 0.04), ('V5_nivell_fons300_marques', Dfons, 0.03)):
    im = Image.fromarray(contorns(vista(D, exc, 4), lab, 4)); d = ImageDraw.Draw(im)
    for m in M: d.text((m['caixa'][2] / 4 + 6, max(m['caixa'][1] / 4 - 4, 2)), str(m['marca']), fill=(255, 64, 0), font=FONT, stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((20, H / 4 - 60), f'nivell: ±{exc * 100:.0f} % = negre/blanc', fill=(255, 255, 255), font=FONT, stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(OUT / f'vistes/{nom}.png')
for m in M:
    x0, y0, x1, y1 = m['caixa']; mg = max(300, (x1 - x0) // 3)
    X0, Y0, X1, Y1 = max(0, x0 - mg), max(0, y0 - mg), min(W, x1 + mg), min(H, y1 + mg)
    sub = np.where(lab[Y0:Y1, X0:X1] == m['marca'], m['marca'], 0)
    mv = v[Y0:Y1, X0:X1]
    a = contorns(vista(Dfons[Y0:Y1, X0:X1], 0.03, 2, mv), sub, 2); b = contorns(vista(Drad[Y0:Y1, X0:X1], 0.04, 2, mv), sub, 2)
    Image.fromarray(np.concatenate([a, np.full((a.shape[0], 8, 3), 255, np.uint8), b], 1)).save(OUT / f"vistes/detall_nivell_marca_{m['marca']:02d}.png")
print('fet')
