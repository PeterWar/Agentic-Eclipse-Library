"""v2 (29-09-2026) · Vista per a Pere: la marca taronja a la V115 i a Brno (només control), a 1:1 i amb el mateix estirament relatiu (detall de
8–60 px, ±3 σ de la textura de cada imatge a la finestra), sense i amb el traç; i el LLENÇ SENCER amb la finestra marcada (norma: mai només el retall).
Sortida: 4-RESULTATS/v116_20260929/vistes/V117_marca_taronja_V115_i_Brno.png i _llenc.png"""
import sys, numpy as np, cv2, tifffile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; V = O / 'vistes'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
X0, X1, Y0, Y1 = 5850, 7150, 4380, 4680
lab = np.asarray(np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')[Y0:Y1, X0:X1]) == 11
p = PSB(str(R / '1-PHOTOSHOP/V115.psb'))
def capa(lid):
    a, (x, y) = p.channel(lid, 1); z = np.full((Y1 - Y0, X1 - X0), np.nan, np.float32); h, w = a.shape
    ya, yb, xa, xb = max(Y0, y), min(Y1, y + h), max(X0, x), min(X1, x + w); z[ya - Y0:yb - Y0, xa - X0:xb - X0] = a[ya - y:yb - y, xa - x:xb - x] / 65535; return z
T = tifffile.memmap(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r')
S = {'V115 (compost desat)': np.asarray(T[Y0:Y1, X0:X1, 1], np.float32) / 65535, 'Brno 200 mm (control)': capa(230), 'Brno 400 mm (control)': capa(231)}
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)
except Exception: F = ImageFont.load_default()
ed = lab & ~cv2.erode(lab.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
fil = []
for nom, s in S.items():
    m = np.isfinite(s) & (s > 0); mf = m.astype(np.float32); x = np.where(m, np.log(np.where(m, s, 1)), 0).astype(np.float32)
    d = np.where(m, cv2.GaussianBlur(x, (0, 0), 1.2) - cv2.GaussianBlur(x, (0, 0), 20) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 20), 1e-6), 0)
    sd = np.std(d[m]); g = np.clip(128 + d / (3 * sd) * 127, 0, 255).astype(np.uint8); g = np.stack([g] * 3, 2); g2 = g.copy(); g2[ed] = (255, 140, 0)
    im = Image.fromarray(np.concatenate([g, np.full((g.shape[0], 8, 3), 255, np.uint8), g2], 1)); ImageDraw.Draw(im).text((8, 6), f'{nom} · detall 1:1, ±3 σ de la seva textura', fill=(255, 255, 0), font=F, stroke_width=2, stroke_fill=(0, 0, 0))
    fil.append(np.asarray(im)); fil.append(np.full((8, im.width, 3), 255, np.uint8))
Image.fromarray(np.concatenate(fil[:-1], 0)).save(V / 'V117_marca_taronja_V115_i_Brno.png')
L = tifffile.imread(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/llenc_sencer.tif').astype(np.float32); f = L.shape[1] / 10551
g = np.clip(L / 65535, 0, 1) ** (1 / 1.0); g8 = (np.clip(g / np.percentile(g, 99.7), 0, 1) ** 0.6 * 255).astype(np.uint8)
im = Image.fromarray(g8); dr = ImageDraw.Draw(im); dr.rectangle([X0 * f, Y0 * f, X1 * f, Y1 * f], outline=(255, 140, 0), width=3)
dr.text((X1 * f + 6, Y0 * f - 4), 'marca taronja', fill=(255, 140, 0), font=F, stroke_width=2, stroke_fill=(0, 0, 0)); im.save(V / 'V117_marca_taronja_llenc.png')
print('fet')
