"""v1 (V116, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER (els detalls, a més, mai en lloc seu):
  V116_V115_llenc_sencer.png          la V115 de Pere (compost desat, sense la 414) i la V116 (render natiu), sRGB, 1/4 cadascuna
  V116_estructura_V115_V116_Brno.png  estructura de 8–300 px (±3 σ de la textura de cada imatge) de V115, V116 i Brno 200 mm (CONTROL), amb les 11 marques
  V116_canvi_V116_sobre_V115.png      on canvia: V116/V115 − 1 (lluminància, σ 8 px), ±6 %, vermell = més clar a la V116
  V116_capa415_efecte.png             la capa nova 415: el seu ràster (u − ½, ±1,5 %) i el que fa si Pere l'encén (V116 amb 415 / V116 − 1, ±3 %)
  V116_marca_taronja_detall.png       DETALL (a més del llenç): la marca taronja a 1:1, V115 i V116
Ús: v1_vistes_V116.py <render_V116.tif> <render_V116_amb_415.tif> <carpeta_vistes>"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v116_20260929'; MQ = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'
T116, T415, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
U115 = tifffile.memmap(ARREL / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r'); U116 = tifffile.memmap(T116, mode='r'); U415 = tifffile.memmap(T415, mode='r')
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
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
A4 = quart(np.asarray(U115, np.float32)).astype(np.float32); B4 = quart(np.asarray(U116, np.float32)).astype(np.float32); C4 = quart(np.asarray(U415, np.float32)).astype(np.float32)
sa, sb = srgb(A4), srgb(B4)
Image.fromarray(np.concatenate([titol(sa, 'V115 de Pere (sense la 414)'), np.full((sa.shape[0], 12, 3), 255, np.uint8), titol(sb, 'V116')], 1)).save(OUT / 'V116_V115_llenc_sencer.png')
SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4; yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def D(L):
    v = L > 0.004; num = ndi.gaussian_filter(np.where(v, L, 0), 75); den = ndi.gaussian_filter(v.astype(np.float32), 75)
    s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-6); ok = v & (den > 0.5)
    return np.where(ok, np.log(np.maximum(s, 1e-6)) - np.log(np.maximum(num / np.maximum(den, 1e-6), 1e-6)), 0), ok
pan = []
for nom, L in (('V115', A4.mean(2) / 65535), ('V116', B4.mean(2) / 65535), ('Brno 200 mm (només control)', np.load(MQ / 'estadis_1a4/brno_230_L.npy'))):
    d, ok = D(L); sd = np.std(d[ok & (rr > 4.5) & (rr < 9.5) & (lab4 == 0)])
    g = np.clip(128 + d / (3 * sd) * 127, 0, 255).astype(np.uint8); g = np.stack([g] * 3, 2); g[~ok] = (40, 40, 40); g[ed4] = (255, 64, 0)
    pan.append(titol(g, f'{nom} · estructura 8–300 px, ±3 σ (σ {sd * 100:.2f} %)', True))
h = min(p.shape[0] for p in pan); sep = np.full((h, 12, 3), 255, np.uint8)
im = Image.fromarray(np.concatenate([pan[0][:h], sep, pan[1][:h], sep, pan[2][:h]], 1)); im.resize((im.width * 2 // 3, im.height * 2 // 3)).save(OUT / 'V116_estructura_V115_V116_Brno.png')
def canvi(Ua, Ub, exc, t, nom):
    LA = ndi.gaussian_filter(np.asarray(Ua, np.float32).mean(2) / 65535, 8)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(Ub, np.float32).mean(2) / 65535, 8)[:H // 4 * 4:4, :W // 4 * 4:4]
    r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0); x = np.clip(r / exc, -1, 1)
    c = np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255; c[LA <= 0.004] = 40
    c = c.astype(np.uint8); c[ed4[:c.shape[0], :c.shape[1]]] = (0, 0, 0); Image.fromarray(titol(c, t, True)).save(OUT / nom)
    k = LA > 0.004; return dict(p1=round(float(np.percentile(r[k], 1) * 100), 2), p50=round(float(np.median(r[k]) * 100), 2), p99=round(float(np.percentile(r[k], 99) * 100), 2))
rep = dict(canvi_V116_sobre_V115_pct=canvi(U115, U116, 0.06, 'V116 / V115 − 1 (lluminància): vermell = més clar a la V116, blau = més fosc; ±6 % = saturat', 'V116_canvi_V116_sobre_V115.png'))
# la 415: el ràster i el seu efecte si s'encén
G = np.load(O / 'AB/capa415/L415_G.npy', mmap_mode='r'); g4 = quart(np.asarray(G, np.float32) / 65535 - 0.5); x = np.clip(g4 / 0.015, -1, 1)
c = (np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255).astype(np.uint8); c[np.abs(g4) < 1e-6] = (60, 60, 60)
LB = ndi.gaussian_filter(np.asarray(U116, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]; LC = ndi.gaussian_filter(np.asarray(U415, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LB > 0.004, LC / np.maximum(LB, 1e-6) - 1, 0); y_ = np.clip(r / 0.03, -1, 1)
e = (np.stack([np.where(y_ > 0, 1, 1 + y_), 1 - np.abs(y_), np.where(y_ < 0, 1, 1 - y_)], 2) * 255).astype(np.uint8); e[LB <= 0.004] = 40
a1 = titol(c, 'Capa 415: detall coherent A·B (u − ½, ±1,5 %); gris fosc = fora del camp comú'); a2 = titol(e, 'Si s\'encén la 415 (40 %): V116 amb 415 / V116 − 1, ±3 %', True)
Image.fromarray(np.concatenate([a1, np.full((a1.shape[0], 12, 3), 255, np.uint8), a2], 1)).save(OUT / 'V116_capa415_efecte.png')
kk = LB > 0.004; rep['efecte_415_si_s_encen_pct'] = dict(p1=round(float(np.percentile(r[kk], 1) * 100), 2), p99=round(float(np.percentile(r[kk], 99) * 100), 2))
# detall de la marca taronja (11), 1:1, a més del llenç sencer
m11 = next(m for m in M if m['marca'] == 11); x0, y0, x1, y1 = m11['caixa']; x0, x1, y0, y1 = x0 - 250, x1 + 250, y0 - 150, y1 + 150
cr = [srgb(np.asarray(U[y0:y1, x0:x1])) for U in (U115, U116)]; l11 = lab[y0:y1, x0:x1] == 11; ed = l11 & ~ndi.binary_erosion(l11)
out_ = []
for nom, cc in zip(('V115', 'V116'), cr):
    q = cc.copy(); lo, hi = np.percentile(q, [1, 99.5]); q = np.clip((q.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8); q2 = q.copy(); q2[ed] = (255, 140, 0)
    im = Image.fromarray(np.concatenate([q, np.full((q.shape[0], 8, 3), 255, np.uint8), q2], 1)); ImageDraw.Draw(im).text((10, 8), f'{nom} · marca taronja a 1:1 (estirat), sense i amb el contorn', fill=(255, 255, 0), font=FP, stroke_width=2, stroke_fill=(0, 0, 0)); out_.append(np.asarray(im))
Image.fromarray(np.concatenate([out_[0], np.full((10, out_[0].shape[1], 3), 255, np.uint8), out_[1]], 0)).save(OUT / 'V116_marca_taronja_detall.png')
(OUT / 'V1_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))
