"""c2 (V92) · Previsualització EMULADA (sense capes d'ajust) de la protuberància esquerra a les marques grises de Pere: V91 de Pere (00:14) contra
V92 (filtres amb mirall + guspires amb el color real, amb l'alfa de la 267 tal com la té Pere), i la foto 76 sola. Sortida: LAMINA_C2_protuberancia_5a1.png."""
from pathlib import Path
import json, sys, io
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
from psb69 import PSB
from vm_compost import comp, capa_box
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
BX = (4835, 3665, 4955, 3805); w, h = BX[2] - BX[0], BX[3] - BX[1]
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; C91 = comp([CAPES[i] for i in vis], h, w)[0]
Z = np.load(SORT / 'P1B_GUSPIRES.npz'); zb = [int(v) for v in Z['caixa']]; rgb = Z['rgb'][BX[1] - zb[1]:BX[3] - zb[1], BX[0] - zb[0]:BX[2] - zb[0]].astype(np.float32) / 65535
capes = []
for i in vis:
    md, F_, a_ = CAPES[i]
    if i in FILTRES: v = np.load(SORT / 'filtres_v92' / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; capes.append((md, np.repeat(v[..., None], 3, -1), a_))
    elif i == 267: capes.append((md, rgb, a_))
    else: capes.append(CAPES[i])
C92 = comp(capes, h, w)[0]; F76 = np.stack([p.channel_box(76, c, BX) for c in range(3)], -1).astype(np.float32) / 65535
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
a1 = p.channel_box(264, -1, BX).astype(np.float32) / 65535; r1 = np.stack([p.channel_box(264, c, BX) for c in range(3)], -1).astype(np.float32) / 257
gris = ((a1 > 0.03) & (np.abs(r1[..., 0] - r1[..., 1]) < 14) & (np.abs(r1[..., 1] - r1[..., 2]) < 14)).astype(np.uint8)
c = np.asarray(im(C91)).copy(); c[(cv2.dilate(gris, np.ones((3, 3), np.uint8)) & ~gris) > 0] = (0, 255, 255)
pan = [('V91 emulada amb la teva marca', Image.fromarray(c)), ('V91 emulada', im(C91)), ('V92 emulada', im(C92)), ('foto 76 sola', im(F76))]
z = 5; FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 16); S = Image.new('RGB', (4 * (w * z + 8), h * z + 30), 'white'); d = ImageDraw.Draw(S)
for i, (et, img) in enumerate(pan): S.paste(img.resize((w * z, h * z), Image.LANCZOS), (i * (w * z + 8), 28)); d.text((i * (w * z + 8) + 4, 6), et + ' · 5:1', fill='black', font=FB)
S.save(SORT / 'LAMINA_C2_protuberancia_5a1.png'); print('fet')
