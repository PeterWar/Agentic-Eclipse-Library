"""b5 · Làmines de la V92 amb el compost de Photoshop (capes d'ajust incloses): la V91 de Pere (imatge fusionada desada dins del PSB de les 00:23)
contra la V92 (imatge fusionada del desament natiu). 1) marques roses de la V90 (la lent) a 5:1; 2) línies de la V88 a 5:1 (no han de tornar);
3) marques grises de la protuberància a 5:1, amb la 76 sola; 4) la Lluna a 2:3. També on difereixen els composts. Sortida: LAMINA_V92_1..4 i B5_LAMINES.json."""
from pathlib import Path
import json, sys, io
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
B = (4600, 3000, 6150, 4550)
P91 = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); C91 = P91.composite()[..., :3]; C92 = PSB(str(ARREL / '1-PHOTOSHOP/V92.psb')).composite()[..., :3]
D = np.abs(C92.astype(np.int32) - C91.astype(np.int32)).max(-1); rep = {}
for llindar in (64, 256):
    ys, xs = np.nonzero(D > llindar); dd = np.hypot(xs - cx, ys - cy) - R; prot = (xs >= 4740) & (xs < 5020) & (ys >= 3470) & (ys < 4040)
    rep[f'dif_mes_de_{llindar}_DN16'] = dict(px=int(xs.size), px_caixa_protuberancia=int(prot.sum()), fora_protuberancia_d_max=round(float(dd[~prot].max()), 1) if (~prot).any() else None,
                                             fora_protuberancia_d_min=round(float(dd[~prot].min()), 1) if (~prot).any() else None)
rep['dif_max_lluny_del_limbe_DN16'] = int(D[(np.hypot(*np.mgrid[:D.shape[0], :D.shape[1]][::-1] - np.array([cx, cy])[:, None, None]) - R) > 30].max())
print(json.dumps(rep), flush=True)
V91 = C91[B[1]:B[3], B[0]:B[2]].copy(); V92 = C92[B[1]:B[3], B[0]:B[2]].copy(); del C91, C92, D
icc = tifffile.TiffFile(SORT / 'vistes/V92_lluna.tif').pages[0].tags['InterColorProfile'].value
tifffile.imwrite(SORT / 'compost_V91_pere_0023_lluna.tif', V91, photometric='rgb', iccprofile=icc); tifffile.imwrite(SORT / 'compost_V92_lluna.tif', V92, photometric='rgb', iccprofile=icc)
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda a: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
def lamina(nom, titol, files, cols, w=80, zf=5):
    S = Image.new('RGB', (len(cols) * (w * zf + 8), 44 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]; x0, y0 = int(px - w / 2), int(py - w / 2); Y = 44 + j * (w * zf + 24)
        for i, (arr, et) in enumerate(cols):
            S.paste(im(arr[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y + 20)); d.text((i * (w * zf + 8) + 3, Y + 2), f'{et} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
cols = [(V91, 'V91 (la teva, 00:23)'), (V92, 'V92')]
lamina('LAMINA_V92_1_lent.png', 'La lent (marques roses de la V90): V91 contra V92, compost de Photoshop, 5:1', [(8, 5), (26, 4), (55, 5), (80, 5), (240, 6), (262, 6), (285, 6), (300, 6)], cols)
lamina('LAMINA_V92_2_linies.png', 'Les línies de la V88 (no han de tornar): V91 contra V92, compost de Photoshop, 5:1', [(112, 5), (136, 5), (211, 5), (223, 5)], cols)
# 3) protuberància: marques grises
BX = (4835, 3665, 4955, 3805); w, h = BX[2] - BX[0], BX[3] - BX[1]; sub = lambda A: A[BX[1] - B[1]:BX[3] - B[1], BX[0] - B[0]:BX[2] - B[0]]
a1 = P91.channel_box(264, -1, BX).astype(np.float32) / 65535; r1 = np.stack([P91.channel_box(264, c, BX) for c in range(3)], -1).astype(np.float32) / 257
gris = ((a1 > 0.03) & (np.abs(r1[..., 0] - r1[..., 1]) < 14) & (np.abs(r1[..., 1] - r1[..., 2]) < 14)).astype(np.uint8)
c = np.asarray(im(sub(V91))).copy(); c[(cv2.dilate(gris, np.ones((3, 3), np.uint8)) & ~gris) > 0] = (0, 255, 255)
F76 = np.stack([P91.channel_box(76, cc, BX) for cc in range(3)], -1)
pan = [('V91 amb la teva marca', Image.fromarray(c)), ('V91', im(sub(V91))), ('V92', im(sub(V92))), ('foto 76 sola', im(F76))]
z = 5; S3 = Image.new('RGB', (4 * (w * z + 8), h * z + 30), 'white'); d3 = ImageDraw.Draw(S3)
for i, (et, img) in enumerate(pan): S3.paste(img.resize((w * z, h * z), Image.LANCZOS), (i * (w * z + 8), 28)); d3.text((i * (w * z + 8) + 4, 6), et + ' · 5:1', fill='black', font=FB)
S3.save(SORT / 'LAMINA_V92_3_protuberancia.png')
k = 1024; S4 = Image.new('RGB', (2 * (k + 8), k + 36), 'white'); d4 = ImageDraw.Draw(S4)
for i, (arr, et) in enumerate(cols): S4.paste(im(arr).resize((k, k), Image.LANCZOS), (i * (k + 8), 34)); d4.text((i * (k + 8) + 4, 8), 'Lluna 2:3 · ' + et, fill='black', font=FB)
S4.save(SORT / 'LAMINA_V92_4_lluna.png'); (SORT / 'B5_LAMINES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); print('fet')
