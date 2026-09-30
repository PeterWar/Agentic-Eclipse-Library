"""a4 (V109 · perles_psb) · Làmines. (0) Llenç SENCER: V107 | V108 | diferència del compost fusionat (×10), amb les caixes de les zones.
(1) Localització de les perles (2:1, limbe esquerre, trets numerats). (2) Lupes 4:1 i 8:1 de PERLES i de dos controls (DRETA, BAIX-DRETA):
V107 | V108 | diferència del fusionat (×20) | part de les capes (recompost, ×20) | resposta de les capes d'ajust (×20). Gris = sense canvi.
Sortida: LAMINA_*.png"""
import struct, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
except OSError: FONT = None
from comu_perles import CAIXA, OUT, V107, V108, geom, desa
X0, Y0 = CAIXA[:2]
F7 = np.load(OUT / 'FUS_V107.npy').astype(np.float32) / 65535; F8 = np.load(OUT / 'FUS_V108.npy').astype(np.float32) / 65535
R7 = np.load(OUT / 'REC_V107.npy'); R8 = np.load(OUT / 'REC_V108.npy'); AJ = np.load(OUT / 'cache/RESPOSTA_AJUST.npy'); CP = np.load(OUT / 'cache/CAPES_PER_CORBA.npy')
L = lambda C: (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
def u8(a): return Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5))
def gris(dif, k): return u8(np.repeat((0.5 + k * dif)[..., None], 3, -1))
def etiqueta(im, t):
    c = Image.new('RGB', (im.width, im.height + 26), '#1e1e1e'); c.paste(im, (0, 26)); ImageDraw.Draw(c).text((6, 5), t, fill='white', font=FONT); return c
def fila(ims, gap=8):
    out = Image.new('RGB', (sum(i.width for i in ims) + gap * (len(ims) - 1), max(i.height for i in ims)), 'white'); x = 0
    for i in ims: out.paste(i, (x, 0)); x += i.width + gap
    return out
ZONES = {'PERLES': (4885, 3600, 4965, 3880), 'DRETA': (5790, 3700, 5870, 3980), 'BAIX_DRETA': (5660, 3960, 5740, 4240)}
LUPA8 = {'PERLES': (4895, 3620, 4955, 3760), 'PERLES_b': (4890, 3740, 4950, 3880), 'DRETA': (5800, 3760, 5860, 3900), 'BAIX_DRETA': (5680, 4010, 5740, 4150)}
fets = []
for esc, zz in ((4, ZONES), (8, LUPA8)):
    for nom, (a, b, c, e) in zz.items():
        s = (slice(b - Y0, e - Y0), slice(a - X0, c - X0)); W, H = (c - a) * esc, (e - b) * esc
        pan = [('V107 (fusionat)', u8(F7[s])), ('V108 (fusionat)', u8(F8[s])), ('V108 - V107 fusionat x20', gris(L(F8[s]) - L(F7[s]), 20)),
               ('part de les capes x20', gris(CP[s], 20)), ("resposta capes d'ajust x20", gris(AJ[s], 20))]
        im = fila([etiqueta(p.resize((W, H), Image.NEAREST), t) for t, p in pan])
        cap = Image.new('RGB', (im.width, 30), 'white'); ImageDraw.Draw(cap).text((6, 9), f'{nom} · caixa x {a}-{c}, y {b}-{e} · {esc}:1 · gris = sense canvi; clar = V108 més clara', fill='black', font=FONT)
        full = Image.new('RGB', (im.width, im.height + 30), 'white'); full.paste(cap, (0, 0)); full.paste(im, (0, 30))
        f = f'LAMINA_{esc}a1_{nom}.png'; full.save(OUT / f); fets.append(f)
# (1) localització de les perles: limbe esquerre a 2:1 amb els trets de la zona PERLES numerats
T = np.load(OUT / 'A2_TRETS.npz'); d, th = geom(CAIXA); ys, xs = T['ys'], T['xs']
sel = np.nonzero((th[ys, xs] >= 150) & (th[ys, xs] < 200) & (d[ys, xs] < 8))[0]
a, b, c, e = 4860, 3520, 5060, 3980; s = (slice(b - Y0, e - Y0), slice(a - X0, c - X0)); esc = 3
im = u8(F7[s]).resize(((c - a) * esc, (e - b) * esc), Image.NEAREST); dr = ImageDraw.Draw(im)
for k, i in enumerate(sel):
    x, y = (xs[i] + X0 - a + 0.5) * esc, (ys[i] + Y0 - b + 0.5) * esc; dr.ellipse((x - 9, y - 9, x + 9, y + 9), outline=(0, 200, 255)); dr.text((x - 34, y - 8), str(k), fill=(0, 200, 255), font=FONT)
for nm, (za, zb, zc, zd) in ZONES.items():
    if nm == 'PERLES': dr.rectangle(((za - a) * esc, (zb - b) * esc, (zc - a) * esc, (zd - b) * esc), outline=(255, 255, 0))
im = etiqueta(im, f'V107 fusionat · limbe esquerre x {a}-{c}, y {b}-{e} · {esc}:1 · cercles = les {len(sel)} perles detectades (0-8 px del limbe, 150-200 graus) · groc = caixa de la lupa 4:1')
im.save(OUT / 'LAMINA_localitzacio_perles.png'); fets.append('LAMINA_localitzacio_perles.png')
# (0) llenç sencer
def fus(p, pas=6):
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, h, w))
    return np.stack([np.asarray(mm[c_, ::pas, ::pas], np.float32) / 65535 for c_ in range(3)], -1)
PAS = 6; A, B = fus(V107, PAS), fus(V108, PAS)
pan = [u8(A), u8(B), gris(L(B) - L(A), 10)]
for p in pan[:1] + pan[2:]:
    dr = ImageDraw.Draw(p)
    for nm, (za, zb, zc, zd) in ZONES.items(): dr.rectangle((za // PAS - 3, zb // PAS - 3, zc // PAS + 3, zd // PAS + 3), outline=(255, 255, 0) if nm == 'PERLES' else (0, 200, 255), width=2)
ims = [etiqueta(p, t) for p, t in zip(pan, ('V107 fusionat (llenç sencer, 1:6)', 'V108 fusionat (llenç sencer, 1:6)', 'V108 - V107 fusionat x10 (gris = igual) · groc: perles; blau: controls'))]
fila(ims).save(OUT / 'LAMINA_0_llenc_sencer.png'); fets.append('LAMINA_0_llenc_sencer.png')
desa(OUT / 'A4_LAMINES.json', dict(fitxers=fets, zones_4a1=ZONES, zones_8a1=LUPA8, escales=dict(diferencies='x20 a les lupes, x10 al llenç sencer; 0,5 = sense canvi')))
print(fets)
