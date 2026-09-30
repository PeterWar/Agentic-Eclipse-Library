"""v3 (V119, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER (els detalls, a més, mai en lloc seu). Adaptat de v118/v2.
  V119_V118_llenc_sencer.png      la V118 i la V119 (renders natius), sRGB, 1/4 cadascuna
  V119_canvi_sobre_V118.png       el que canvia: V119/V118 − 1 (lluminància, σ 1 px a 1/4), ±1 % (la trama i l'ordit sense costures)
  V119_capa_trama.png             el ràster de la trama (u − ½, ±1 %): arcs, cims de llaços i cascs que veuen ELS TRES testimonis
  V119_corona_interior.png        DETALL (a més del llenç): la corona interior (±3,2 R☉), V118 i V119 amb el mateix estirament, a 1/2
Ús: v3_vistes_V119.py <render_V119.tif> <carpeta_vistes>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; O8 = ARREL / '4-RESULTATS/v118_20260929'; O9 = ARREL / '4-RESULTATS/v119_20260929'
T119, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
U118 = tifffile.memmap(O8 / 'V118_natiu/visible_complet.tif', mode='r'); U119 = tifffile.memmap(T119, mode='r'); H, W = U118.shape[:2]
SOL = (5361.768, 3775.748); RS = 440.603
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])); TM = MS @ MA
def srgb(u16):
    lin = (np.asarray(u16, np.float32) / 65535) ** 2.19921875; s = np.clip(lin @ TM.T, 0, 1)
    return ((np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)) * 255 + 0.5).astype(np.uint8)
def redueix(x, f): return x[:x.shape[0] // f * f, :x.shape[1] // f * f].reshape(x.shape[0] // f, f, x.shape[1] // f, f, *x.shape[2:]).mean((1, 3))
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 40); FP = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
except Exception: F = FP = ImageFont.load_default()
def titol(img, t, font=None):
    im = Image.fromarray(img); ImageDraw.Draw(im).text((20, 16), t, fill=(255, 255, 255), font=font or F, stroke_width=3, stroke_fill=(0, 0, 0)); return np.asarray(im)
def mapa_div(r, exc, fons):
    x = np.clip(r / exc, -1, 1); c = (np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255).astype(np.uint8); c[fons] = 40; return c
A4 = redueix(np.asarray(U118, np.float32), 4); B4 = redueix(np.asarray(U119, np.float32), 4)
sa, sb = srgb(A4), srgb(B4)
Image.fromarray(np.concatenate([titol(sa, 'V118: ordit (416)'), np.full((sa.shape[0], 12, 3), 255, np.uint8), titol(sb, 'V119: ordit sense costures (417) + trama (418)')], 1)).save(OUT / 'V119_V118_llenc_sencer.png')
LA = ndi.gaussian_filter(np.asarray(U118, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(U119, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0)
Image.fromarray(titol(mapa_div(r, 0.01, LA <= 0.004), 'V119 / V118 − 1, ±1 % (vermell = més clar a la V119): la trama i l\'ordit sense costures')).save(OUT / 'V119_canvi_sobre_V118.png')
k = LA > 0.004; rep = dict(canvi_V119_sobre_V118_pct=dict(p1=round(float(np.percentile(r[k], 1) * 100), 3), p50=round(float(np.median(r[k]) * 100), 3), p99=round(float(np.percentile(r[k], 99) * 100), 3)))
G = np.load(O9 / 'trama/capa_trama/L415_G.npy', mmap_mode='r'); g4 = redueix(np.asarray(G, np.float32) / 65535 - 0.5, 4)
Image.fromarray(titol(mapa_div(g4, 0.01, np.abs(g4) < 1e-6), 'Trama (418): arcs, cims de llaços i cascs que veuen ELS TRES testimonis (u − ½, ±1 %); gris = neutre')).save(OUT / 'V119_capa_trama.png')
hw, hh = int(3.2 * RS), int(2.4 * RS); ys, xs = slice(int(SOL[1] - hh), int(SOL[1] + hh)), slice(int(SOL[0] - hw), int(SOL[0] + hw))
cr = [srgb(redueix(np.asarray(U[ys, xs], np.float32), 2)) for U in (U118, U119)]; lo, hi = np.percentile(np.concatenate([c_.ravel() for c_ in cr]), [1, 99.7])
fil = []
for nom, c_ in zip(('V118 (ordit)', 'V119 (ordit + trama 40 %)'), cr):
    q = np.clip((c_.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8); fil.append(titol(q, f'{nom} · corona interior a 1/2, mateix estirament', FP))
Image.fromarray(np.concatenate([fil[0], np.full((fil[0].shape[0], 10, 3), 255, np.uint8), fil[1]], 1)).save(OUT / 'V119_corona_interior.png')
rep['finestra_corona_interior'] = [xs.start, ys.start, xs.stop, ys.stop]
(OUT / 'V3_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))
