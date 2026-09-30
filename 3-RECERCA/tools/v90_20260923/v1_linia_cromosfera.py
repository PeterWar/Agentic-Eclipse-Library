"""v1 · On és la línia vermella de la cromosfera a la vora de la Lluna (compost natiu desat de la V88 de Pere, 18:50), per azimut (0,25°).
Vermellor = (R − G) / (R + G + B) al compost (el que veu Pere); perfil radial de d = −4 a +10 px des del limbe de presentació (R 453), suavitzat
0,5° en azimut; la línia = màxim de vermellor a −2..+8 px, si destaca prou de la vermellor de la corona (+8 px..+14 px) al mateix azimut.
Sortida: V1_CROMOSFERA.json (d de la línia i contrast per azimut) i LAMINA_V1_cromosfera.png (polars: vermellor, línia trobada, contorns de
l'alfa de Pere 0,95 / 0,5 / 0,05)."""
from v90_comu import *
from psb69 import PSB
import tifffile, cv2
from scipy.ndimage import gaussian_filter1d
from PIL import Image, ImageDraw, ImageFont
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']
VM = ARREL / '4-RESULTATS/v88_marques_pere_20260923'; B0 = (4600, 3000)
C = tifffile.imread(VM / 'compost_lluna.tif')[..., :3].astype(np.float32) / 65535
cx, cy, R = GEO['cx'] - B0[0], GEO['cy'] - B0[1], GEO['R']
red = (C[..., 0] - C[..., 1]) / np.maximum(C.sum(-1), 1e-4)
NBZ = 1440; TS = (np.arange(NBZ) + 0.5) * 360 / NBZ; DS = np.arange(-4, 14.01, 0.25); TT, DD = np.meshgrid(np.radians(TS), DS)
MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
P = cv2.remap(red, MX, MY, cv2.INTER_LINEAR); P = gaussian_filter1d(P, 2, axis=1, mode='wrap')     # 0,5° en azimut
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); a, (ox, oy) = p.channel(258, -1); a = a.astype(np.float32) / 65535
A = cv2.remap(a, MX + B0[0] - ox, MY + B0[1] - oy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def contorn(lv):
    out = np.full(NBZ, np.nan)
    for k in range(NBZ):
        j = np.flatnonzero(A[:, k] >= lv); out[k] = DS[j[-1]] if j.size else np.nan
    return out
c95, c50, c05 = contorn(0.95), contorn(0.5), contorn(0.05)
sel = (DS >= -2) & (DS <= 8); ref = (DS >= 8) & (DS <= 14)
dline = np.full(NBZ, np.nan); contr = np.zeros(NBZ)
for k in range(NBZ):
    col = P[:, k]; j = np.flatnonzero(sel); jm = j[np.nanargmax(col[j])]; base = np.nanmedian(col[ref]); contr[k] = col[jm] - base
    if contr[k] > 0.06: dline[k] = DS[jm]
res = dict(llindar_contrast=0.06, d_linia=[None if not np.isfinite(v) else round(float(v), 2) for v in dline], contrast=np.round(contr, 3).tolist(),
           alfa_c95=np.round(c95, 2).tolist(), alfa_c50=np.round(c50, 2).tolist(), alfa_c05=np.round(c05, 2).tolist())
for a0, a1 in [(100, 120), (120, 150), (150, 170), (170, 190), (190, 210), (210, 230), (230, 260), (300, 360), (0, 60)]:
    s = slice(a0 * 4, a1 * 4); f = np.isfinite(dline[s])
    res[f'resum_{a0}_{a1}'] = dict(fraccio_amb_linia=round(float(f.mean()), 2), d_linia_mediana=(round(float(np.median(dline[s][f])), 2) if f.any() else None), alfa05_mediana=round(float(np.nanmedian(c50[s])), 2), alfa005_mediana=round(float(np.nanmedian(c05[s])), 2))
desa_json('V1_CROMOSFERA.json', res)
for k, v in res.items():
    if k.startswith('resum'): print(k, v)
# làmina en polars (95°–245°)
k0, k1 = 95 * 4, 245 * 4; img = np.clip((P[:, k0:k1] + 0.05) / 0.35, 0, 1)
zx, zy = 2, 8; pil = Image.fromarray(np.uint8(img * 255)).resize(((k1 - k0) * zx, len(DS) * zy), Image.NEAREST).convert('RGB'); di = ImageDraw.Draw(pil)
def corba(v, col):
    pts = [((k - k0) * zx + 1, int((v[k] - DS[0]) / 0.25 * zy + zy / 2)) for k in range(k0, k1) if np.isfinite(v[k])]; di.point(pts, fill=col)
corba(c95, (0, 160, 255)); corba(c50, (0, 90, 255)); corba(c05, (120, 120, 255)); corba(dline, (255, 60, 60))
yl = int((0 - DS[0]) / 0.25 * zy); di.line([(0, yl), (pil.width, yl)], fill=(255, 255, 0))
for az in range(100, 245, 10): xl = (az * 4 - k0) * zx; di.line([(xl, 0), (xl, 10)], fill=(255, 255, 0)); di.text((xl + 2, 0), str(az), fill=(255, 255, 0))
S = Image.new('RGB', (pil.width, pil.height + 30), 'white'); S.paste(pil, (0, 30))
ImageDraw.Draw(S).text((4, 6), 'Vermellor del compost natiu (V88) en polars: 95°→245°, d −4..+14 px (×8). Vermell: línia de cromosfera trobada; blaus: alfa de Pere 0,95 / 0,5 / 0,05; groc: d = 0', fill='black', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16))
S.save(SORT / 'LAMINA_V1_cromosfera.png'); log('fet')
