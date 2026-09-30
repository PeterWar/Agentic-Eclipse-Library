"""c1 (V94) · Avaluació EMULADA de les WOW noves sobre la V93: (a) efecte de nivell de gran escala de la 56 (capa / capa neutra − 1, σ 20 px a
1/4) amb la WOW de la V93 i amb la nova, a les marques negres de Pere (l'«ombra quadrada») i a la resta; (b) caixa de la Lluna: nivell per
distància, textura a les marques taronja i làmines a 6:1 (taronja, línies de la V88) i a 1/4 (llenç sencer). Sortida: C1_WOW.json i làmines."""
import sys, json, io
from pathlib import Path
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
from psb69 import PSB
from vm_compost import comp, capa_box
W, H = 10551, 7506; F4 = 4; w4, h4 = W // F4, H // F4
p = PSB(str(ARREL / '1-PHOTOSHOP/V93.psb')); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
NOU = {56: 'P05_WOW_bilateral', 55: 'P04_WOW'}
red = lambda A: cv2.resize(np.asarray(A, np.float32), (w4, h4), interpolation=cv2.INTER_AREA)
nou = {lid: (np.load(SORT / f'wow/{t}_u16.npy', mmap_mode='r'), np.load(SORT / f'wow/{t}_alfa_u16.npy', mmap_mode='r')) for lid, t in NOU.items()}
def capes_llenç(variant, neutre56=False):
    out = []
    for lid in vis:
        md, F_, a_ = capa_box(p, lid, (0, 0, W, H))
        if variant == 'V94' and lid in NOU: u, al = nou[lid]; F_ = np.repeat((np.asarray(u, np.float32) / 65535)[..., None], 3, -1); a_ = a_ * (np.asarray(al, np.float32) / 65535)
        if neutre56 and lid == 56: F_ = np.full_like(F_, 0.5)
        out.append((md, red(F_), red(a_)))
    return out
lum = lambda X: 0.2126 * X[..., 0] + 0.7152 * X[..., 1] + 0.0722 * X[..., 2]
Cn = comp(capes_llenç('V93', True), h4, w4)[0]; rep = {}; COMPQ = {}
mk = cv2.resize(np.load(ARREL / '4-RESULTATS/v93_20260924/marques_FiltreWOW_Pere.npz')['negre'].astype(np.float32), (w4, h4), interpolation=cv2.INTER_AREA) > 0
yy, xx = np.mgrid[:h4, :w4]; dq = np.hypot(xx - 5376 / F4, yy - 3776 / F4) * F4 - 453
for v in ('V93', 'V94'):
    C = comp(capes_llenç(v), h4, w4)[0]; COMPQ[v] = C; ef = cv2.GaussianBlur(lum(C) / np.maximum(lum(Cn), 1e-3) - 1, (0, 0), 20)
    ok = lum(Cn) > 0.02
    rep[v] = dict(efecte_56_marques_negres=round(float(ef[mk & ok].mean()), 4), efecte_56_d_800_1700=round(float(ef[ok & (dq > 800) & (dq < 1700)].mean()), 4),
                  efecte_56_d_150_600=round(float(ef[ok & (dq > 150) & (dq < 600)].mean()), 4), efecte_56_d_2500_4000=round(float(ef[ok & (dq > 2500) & (dq < 4000)].mean()), 4))
    Image.fromarray(np.uint8(np.clip((ef + 0.2) / 0.25, 0, 1) * 255)).save(SORT / f'diag_efecte_nivell_56_{v}_quart.png')
    print(v, json.dumps(rep[v]), flush=True)
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v93_20260924/vistes/V93_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20)
S = Image.new('RGB', (2 * 1320 + 8, 940 + 36), 'white'); dr = ImageDraw.Draw(S)
for i, v in enumerate(('V93', 'V94')): S.paste(im(COMPQ[v]).resize((1320, 940), Image.LANCZOS), (i * 1328, 34)); dr.text((i * 1328 + 6, 6), f'{v} · llenç sencer (EMULAT, sense capes d\'ajust)', fill='black', font=FB)
S.save(SORT / 'LAMINA_C1_llenc_emulat.png')
# caixa de la Lluna a resolució plena
BX = (4600, 3000, 6150, 4550); w_, h_ = BX[2] - BX[0], BX[3] - BX[1]; cx, cy, R = 5375.787, 3775.977, 452.979
CB = {}
for v in ('V93', 'V94'):
    capes = []
    for lid in vis:
        md, F_, a_ = capa_box(p, lid, BX)
        if v == 'V94' and lid in NOU: u, al = nou[lid]; F_ = np.repeat((np.asarray(u[BX[1]:BX[3], BX[0]:BX[2]], np.float32) / 65535)[..., None], 3, -1); a_ = a_ * (np.asarray(al[BX[1]:BX[3], BX[0]:BX[2]], np.float32) / 65535)
        capes.append((md, F_, a_))
    CB[v] = comp(capes, h_, w_)[0]
np.save(SORT / 'c1_compost_emulat_V94_lluna.npy', CB['V94'])
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
def lamina(nom, titol, files, w=60, zf=6):
    S = Image.new('RGB', (2 * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - BX[0], cy - (R + dm) * np.sin(t) - BX[1]; x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, v in enumerate(('V93', 'V94')): S.paste(im(CB[v][y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{v} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_C1_taronja_6a1.png', 'Marques taronja (vora sense textura) · V93 contra V94 (WOW nova), EMULAT, 6:1', [(70, 5), (85, 5), (215, 5), (240, 5), (335, 5), (345, 5)])
lamina('LAMINA_C1_linies_V88_8a1.png', 'Línies de la V88 (no han de tornar) · V93 contra V94, EMULAT, 8:1', [(112, 5), (136, 6), (211, 5), (219, 6), (223, 7)], w=44, zf=8)
(SORT / 'C1_WOW.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); print('fet')
