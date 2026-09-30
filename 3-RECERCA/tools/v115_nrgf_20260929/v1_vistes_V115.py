"""v1 (V115, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER:
  V115_V114_llenc_sencer.png    la V114 de Pere (compost desat, sense la 414) i la V115 (render natiu), sRGB, 1/4 cadascuna, una al costat de l'altra
  V115_estructura_V114_V115_Brno.png   estructura de 8–300 px (±3 σ de la textura de cada imatge) de V114, V115 i Brno 200 mm, amb les marques de Pere
  V115_canvi_V115_sobre_V114.png  on canvia la imatge: V115/V114 − 1 (lluminància, suavitzat σ 8 px), ±6 %, vermell = més clar a la V115
Ús: v1_vistes_V115.py <render_V115.tif> <carpeta_vistes>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; MQ = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
T115 = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
U114 = np.load(MQ / 'U_compost_sense_414_u16.npy', mmap_mode='r'); U115 = tifffile.memmap(T115, mode='r')
lab = np.load(MQ / 'marques_414_etiquetes.npy'); M = json.load(open(MQ / 'MARQUES_414.json'))['marques']; H, W = lab.shape
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])); TM = MS @ MA
def srgb(u16):
    lin = (np.asarray(u16, np.float32) / 65535) ** 2.19921875; s = np.clip(lin @ TM.T, 0, 1)
    return ((np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)) * 255 + 0.5).astype(np.uint8)
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4, *x.shape[2:]).mean((1, 3))
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 40)
except Exception: F = ImageFont.load_default()
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; ed4 = (lab4 != ndi.grey_erosion(lab4, size=(3, 3))) & (lab4 > 0)
def titol(img, t, marques=False):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); d.text((20, 16), t, fill=(255, 255, 255), font=F, stroke_width=3, stroke_fill=(0, 0, 0))
    if marques:
        for m in M: d.text((m['caixa'][2] / 4 + 6, max(m['caixa'][1] / 4 - 4, 2)), str(m['marca']), fill=(255, 64, 0), font=F, stroke_width=3, stroke_fill=(0, 0, 0))
    return np.asarray(im)
A4 = quart(np.asarray(U114, np.float32)).astype(np.float32); B4 = quart(np.asarray(U115, np.float32)).astype(np.float32)
sa, sb = srgb(A4), srgb(B4)
Image.fromarray(np.concatenate([titol(sa, 'V114 de Pere'), np.full((sa.shape[0], 12, 3), 255, np.uint8), titol(sb, 'V115')], 1)).save(OUT / 'V115_V114_llenc_sencer.png')
SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4; yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def D(L):
    v = L > 0.004; num = ndi.gaussian_filter(np.where(v, L, 0), 75); den = ndi.gaussian_filter(v.astype(np.float32), 75)
    s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-6); ok = v & (den > 0.5)
    return np.where(ok, np.log(np.maximum(s, 1e-6)) - np.log(np.maximum(num / np.maximum(den, 1e-6), 1e-6)), 0), ok
pan = []
for nom, L in (('V114 de Pere', A4.mean(2) / 65535), ('V115', B4.mean(2) / 65535), ('Brno 200 mm (jutge)', np.load(MQ / 'estadis_1a4/brno_230_L.npy'))):
    d, ok = D(L); sd = np.std(d[ok & (rr > 4.5) & (rr < 9.5) & (lab4 == 0)])
    g = np.clip(128 + d / (3 * sd) * 127, 0, 255).astype(np.uint8); g = np.stack([g] * 3, 2); g[~ok] = (40, 40, 40); g[ed4] = (255, 64, 0)
    pan.append(titol(g, f'{nom} · estructura 8–300 px, ±3 σ (σ {sd * 100:.2f} %)', True))
h = min(p.shape[0] for p in pan); sep = np.full((h, 12, 3), 255, np.uint8)
im = Image.fromarray(np.concatenate([pan[0][:h], sep, pan[1][:h], sep, pan[2][:h]], 1)); im.resize((im.width * 2 // 3, im.height * 2 // 3)).save(OUT / 'V115_estructura_V114_V115_Brno.png')
LA = ndi.gaussian_filter(np.asarray(U114, np.float32).mean(2) / 65535, 8)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(U115, np.float32).mean(2) / 65535, 8)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0); x = np.clip(r / 0.06, -1, 1)
c = np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255; c[LA <= 0.004] = 40
c = c.astype(np.uint8); c[ed4[:c.shape[0], :c.shape[1]]] = (0, 0, 0)
Image.fromarray(titol(c, 'V115 / V114 − 1 (lluminància): vermell = més clar a la V115, blau = més fosc; ±6 % = saturat', True)).save(OUT / 'V115_canvi_V115_sobre_V114.png')
print(json.dumps(dict(canvi_pct=dict(p1=float(np.percentile(r[LA > 0.004], 1) * 100), p50=float(np.median(r[LA > 0.004]) * 100), p99=float(np.percentile(r[LA > 0.004], 99) * 100)))))
