"""v1 (V117, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER (els detalls, a més, mai en lloc seu):
  V117_V115_llenc_sencer.png       la V115 de Pere (compost desat, sense la 414) i la V117 (render natiu), sRGB, 1/4 cadascuna
  V117_canvi_V117_sobre_V115.png   el que hi posa el filtre: V117/V115 − 1 (lluminància, σ 1 px a 1/4), ±1,5 %, vermell = més clar a la V117
  V117_capa415.png                 el ràster de la capa 415 (u − ½, ±1,5 %): el detall que veuen TOTS DOS apuntaments de la Sony
  V117_detall_1a1.png              DETALL (a més del llenç): una finestra de raigs a 1:1, V115 i V117 amb el mateix estirament
Ús: v1_vistes_V117.py <render_V117.tif> <carpeta_vistes>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; O6 = ARREL / '4-RESULTATS/v116_20260929'; O7 = ARREL / '4-RESULTATS/v117_20260929'
T117, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
U115 = tifffile.memmap(ARREL / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r'); U117 = tifffile.memmap(T117, mode='r')
lab = np.load(O6 / 'marques_V115_etiquetes.npy'); M = json.load(open(O6 / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])); TM = MS @ MA
def srgb(u16):
    lin = (np.asarray(u16, np.float32) / 65535) ** 2.19921875; s = np.clip(lin @ TM.T, 0, 1)
    return ((np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)) * 255 + 0.5).astype(np.uint8)
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4, *x.shape[2:]).mean((1, 3))
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 40); FP = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
except Exception: F = FP = ImageFont.load_default()
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; ed4 = (lab4 != ndi.grey_erosion(lab4, size=(3, 3))) & (lab4 > 0)
def titol(img, t, marques=False):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); d.text((20, 16), t, fill=(255, 255, 255), font=F, stroke_width=3, stroke_fill=(0, 0, 0))
    if marques:
        for m in M: d.text((m['caixa'][2] / 4 + 6, max(m['caixa'][1] / 4 - 4, 2)), str(m['marca']), fill=(255, 140, 0) if m['marca'] == 11 else (255, 64, 0), font=F, stroke_width=3, stroke_fill=(0, 0, 0))
    return np.asarray(im)
A4 = quart(np.asarray(U115, np.float32)).astype(np.float32); B4 = quart(np.asarray(U117, np.float32)).astype(np.float32)
sa, sb = srgb(A4), srgb(B4)
Image.fromarray(np.concatenate([titol(sa, 'V115 de Pere (sense la 414)'), np.full((sa.shape[0], 12, 3), 255, np.uint8), titol(sb, 'V117 = V115 + filtre A·B (25 %)')], 1)).save(OUT / 'V117_V115_llenc_sencer.png')
def mapa_div(r, exc, fons):
    x = np.clip(r / exc, -1, 1); c = (np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255).astype(np.uint8); c[fons] = 40; return c
LA = ndi.gaussian_filter(np.asarray(U115, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(U117, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0); c = mapa_div(r, 0.015, LA <= 0.004); c[ed4[:c.shape[0], :c.shape[1]]] = (0, 0, 0)
Image.fromarray(titol(c, 'El que hi posa el filtre: V117 / V115 − 1, ±1,5 % (vermell = més clar, blau = més fosc)', True)).save(OUT / 'V117_canvi_V117_sobre_V115.png')
k = LA > 0.004; rep = dict(efecte_pct=dict(p1=round(float(np.percentile(r[k], 1) * 100), 3), p50=round(float(np.median(r[k]) * 100), 3), p99=round(float(np.percentile(r[k], 99) * 100), 3)))
G = np.load(O7 / 'AB/capa415/L415_G.npy', mmap_mode='r'); g4 = quart(np.asarray(G, np.float32) / 65535 - 0.5)
Image.fromarray(titol(mapa_div(g4, 0.015, np.abs(g4) < 1e-6), 'Capa 415: detall que veuen TOTS DOS apuntaments de la Sony (u − ½, ±1,5 %); gris = neutre o fora del camp comú')).save(OUT / 'V117_capa415.png')
# DETALL a 1:1: la finestra de la corona interior amb més detall confirmat (energia de la capa), a 1,6–3 R☉
e = ndi.uniform_filter(np.abs(g4), 150); yy, xx = np.mgrid[0:e.shape[0], 0:e.shape[1]]; rr = np.hypot(xx * 4 - 5361.768, yy * 4 - 3775.748) / 440.603
e[(rr < 1.6) | (rr > 3.0)] = 0; iy, ix = np.unravel_index(np.argmax(e), e.shape); cx, cy = ix * 4, iy * 4; wx, wy = 700, 420
x0, y0 = int(np.clip(cx - wx // 2, 0, W - wx)), int(np.clip(cy - wy // 2, 0, H - wy))
cr = [srgb(np.asarray(U[y0:y0 + wy, x0:x0 + wx])) for U in (U115, U117)]; lo, hi = np.percentile(np.concatenate([c_.ravel() for c_ in cr]), [1, 99.5])
fil = []
for nom, c_ in zip(('V115', 'V117 (filtre al 25 %)'), cr):
    q = np.clip((c_.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8); im = Image.fromarray(q).resize((wx * 2, wy * 2), Image.NEAREST)
    ImageDraw.Draw(im).text((10, 8), f'{nom} · 1:1 ampliat ×2, mateix estirament · x {x0}–{x0 + wx}, y {y0}–{y0 + wy}', fill=(255, 255, 0), font=FP, stroke_width=2, stroke_fill=(0, 0, 0)); fil.append(np.asarray(im))
Image.fromarray(np.concatenate([fil[0], np.full((10, fil[0].shape[1], 3), 255, np.uint8), fil[1]], 0)).save(OUT / 'V117_detall_1a1.png')
rep['finestra_detall'] = [x0, y0, x0 + wx, y0 + wy]
(OUT / 'V1_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))
