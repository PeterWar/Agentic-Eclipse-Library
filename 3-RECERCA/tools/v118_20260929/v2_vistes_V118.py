"""v2 (V118, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER (els detalls, a més, mai en lloc seu). Adaptat de v117/v1.
  V118_V117_llenc_sencer.png      la V117 i la V118 (renders natius), sRGB, 1/4 cadascuna
  V118_canvi_sobre_V117.png       el que canvia de la V117 a la V118: V118/V117 − 1 (lluminància, σ 1 px a 1/4), ±0,5 %; cercles = peu de cada estrella
  V118_capa416.png                el ràster de la capa 416 (u − ½, ±1,5 %): el detall que veuen ELS TRES testimonis, sense estrelles
  V118_estrella_1a1.png           DETALL (a més del llenç): l'estrella més brillant dins la corona (TYC 826-899-1, V 6,8, 2,7 R☉), 1:1:
                                  a dalt, les capes 415 (V117, A·B) i 416 (V118, tres testimonis); a baix, el compost de la V117 i el de la V118
  V118_detall_1a1.png             DETALL: la finestra de raigs de la vista de la V117, V117 i V118 amb el mateix estirament
Ús: v2_vistes_V118.py <render_V118.tif> <carpeta_vistes>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; O6 = ARREL / '4-RESULTATS/v116_20260929'; O7 = ARREL / '4-RESULTATS/v117_20260929'; O8 = ARREL / '4-RESULTATS/v118_20260929'
T118, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
U117 = tifffile.memmap(O7 / 'V117_natiu/visible_complet.tif', mode='r'); U118 = tifffile.memmap(T118, mode='r')
lab = np.load(O6 / 'marques_V115_etiquetes.npy'); M = json.load(open(O6 / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])); TM = MS @ MA
def srgb(u16):
    lin = (np.asarray(u16, np.float32) / 65535) ** 2.19921875; s = np.clip(lin @ TM.T, 0, 1)
    return ((np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)) * 255 + 0.5).astype(np.uint8)
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4, *x.shape[2:]).mean((1, 3))
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 40); FP = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
except Exception: F = FP = ImageFont.load_default()
def titol(img, t):
    im = Image.fromarray(img); ImageDraw.Draw(im).text((20, 16), t, fill=(255, 255, 255), font=F, stroke_width=3, stroke_fill=(0, 0, 0)); return np.asarray(im)
def mapa_div(r, exc, fons):
    x = np.clip(r / exc, -1, 1); c = (np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255).astype(np.uint8); c[fons] = 40; return c
A4 = quart(np.asarray(U117, np.float32)); B4 = quart(np.asarray(U118, np.float32))
sa, sb = srgb(A4), srgb(B4)
Image.fromarray(np.concatenate([titol(sa, 'V117: filtre A·B (415, 25 %)'), np.full((sa.shape[0], 12, 3), 255, np.uint8), titol(sb, 'V118: tres testimonis sense estrelles (416, 25 %)')], 1)).save(OUT / 'V118_V117_llenc_sencer.png')
LA = ndi.gaussian_filter(np.asarray(U117, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(U118, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0); c = mapa_div(r, 0.005, LA <= 0.004)
halo = json.load(open(O8 / 'ABV/b5/B5_AJUSTOS_ESTRELLES.json'))['halo']; im = Image.fromarray(c); d = ImageDraw.Draw(im)
for k, v in halo.items():
    x, y = (int(u) for u in k.split(',')); rp = v['radi'] / 4; d.ellipse((x / 4 - rp, y / 4 - rp, x / 4 + rp, y / 4 + rp), outline=(0, 160, 0), width=2)
d.text((20, 16), 'V118 / V117 − 1, ±0,5 % (vermell = més clar a la V118); cercles verds = peu de cada estrella', fill=(255, 255, 255), font=F, stroke_width=3, stroke_fill=(0, 0, 0))
im.save(OUT / 'V118_canvi_sobre_V117.png')
k = LA > 0.004; rep = dict(canvi_V118_sobre_V117_pct=dict(p1=round(float(np.percentile(r[k], 1) * 100), 3), p50=round(float(np.median(r[k]) * 100), 3), p99=round(float(np.percentile(r[k], 99) * 100), 3)))
G8 = np.load(O8 / 'ABV/capa416/L415_G.npy', mmap_mode='r'); G7 = np.load(O7 / 'AB/capa415/L415_G.npy', mmap_mode='r'); g4 = quart(np.asarray(G8, np.float32) / 65535 - 0.5)
Image.fromarray(titol(mapa_div(g4, 0.015, np.abs(g4) < 1e-6), 'Capa 416: detall que veuen ELS TRES testimonis, sense estrelles (u − ½, ±1,5 %); gris = neutre')).save(OUT / 'V118_capa416.png')
# l'estrella més brillant dins la corona
st = next(s for s in json.load(open(ARREL / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars'] if s['TYC'] == '826-899-1')
sx, sy, hw = int(st['x']), int(st['y']), 160; ys, xs = slice(sy - hw, sy + hw), slice(sx - hw, sx + hw)
def capa(G):
    g = np.asarray(G[ys, xs], np.float32) / 65535 - 0.5; return mapa_div(g, 0.015, np.abs(g) < 1e-6)
crs = [srgb(np.asarray(U[ys, xs])) for U in (U117, U118)]; lo, hi = np.percentile(np.concatenate([c_.ravel() for c_ in crs]), [1, 99.5])
est = lambda c_: np.clip((c_.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
pan = []
for nom, img in (('415 · V117 (A·B)', capa(G7)), ('416 · V118 (tres, sense estrelles)', capa(G8)), ('compost V117', est(crs[0])), ('compost V118', est(crs[1]))):
    im = Image.fromarray(img).resize((2 * hw * 2, 2 * hw * 2), Image.NEAREST); ImageDraw.Draw(im).text((10, 8), nom, fill=(255, 255, 0), font=FP, stroke_width=2, stroke_fill=(0, 0, 0)); pan.append(np.asarray(im))
blanc_v = np.full((pan[0].shape[0], 10, 3), 255, np.uint8); fila1 = np.concatenate([pan[0], blanc_v, pan[1]], 1); fila2 = np.concatenate([pan[2], blanc_v, pan[3]], 1)
Image.fromarray(np.concatenate([fila1, np.full((10, fila1.shape[1], 3), 255, np.uint8), fila2], 0)).save(OUT / 'V118_estrella_1a1.png')
rep['estrella'] = dict(TYC=st['TYC'], V=st['V'], x=sx, y=sy, finestra=[sx - hw, sy - hw, sx + hw, sy + hw], radi_peu=halo.get(f'{sx},{sy}', {}).get('radi'))
# la finestra de raigs de la V117
x0, y0, x1, y1 = json.load(open(O7 / 'vistes/V1_VISTES.json'))['finestra_detall']; wx, wy = x1 - x0, y1 - y0
cr = [srgb(np.asarray(U[y0:y1, x0:x1])) for U in (U117, U118)]; lo, hi = np.percentile(np.concatenate([c_.ravel() for c_ in cr]), [1, 99.5]); fil = []
for nom, c_ in zip(('V117 (A·B, 25 %)', 'V118 (tres testimonis, 25 %)'), cr):
    q = np.clip((c_.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8); im = Image.fromarray(q).resize((wx * 2, wy * 2), Image.NEAREST)
    ImageDraw.Draw(im).text((10, 8), f'{nom} · 1:1 ampliat ×2, mateix estirament · x {x0}–{x1}, y {y0}–{y1}', fill=(255, 255, 0), font=FP, stroke_width=2, stroke_fill=(0, 0, 0)); fil.append(np.asarray(im))
Image.fromarray(np.concatenate([fil[0], np.full((10, fil[0].shape[1], 3), 255, np.uint8), fil[1]], 0)).save(OUT / 'V118_detall_1a1.png')
rep['finestra_detall'] = [x0, y0, x1, y1]
(OUT / 'V2_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))
