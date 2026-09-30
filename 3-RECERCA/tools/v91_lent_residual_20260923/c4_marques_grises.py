"""c4 · Les marques noves de Pere a la capa 264 (V91 desada a les 00:14): «artefactes grisos en la protuberància esquerra». Marques noves =
alfa de la 264 ara menys la de la V90 (21:43, dins de V91_stage). Components, color i posició; làmina a 6:1 amb el compost de Photoshop de
la V91 de Pere (00:14), el de la V90 (22:06), la foto 76 sola, la capa 267 sola i el que Pere n'ha esborrat. Sortida: C4_MARQUES_GRISES.json,
LAMINA_C4_marques_grises.png."""
from pathlib import Path
import json, sys, io
import numpy as np, cv2, tifffile
from scipy import ndimage as ndi
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
P = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); S = PSB(str(ARREL / '4-RESULTATS/v91_20260923/V91_stage.psb')); V0 = PSB(str(ARREL / '1-PHOTOSHOP/V90.psb'))
BX = (4740, 3470, 5020, 4040); w, h = BX[2] - BX[0], BX[3] - BX[1]
a_new = P.channel_box(264, -1, BX).astype(np.float32) / 65535; a_old = S.channel_box(264, -1, BX).astype(np.float32) / 65535
rgb = np.stack([P.channel_box(264, c, BX) for c in range(3)], -1).astype(np.float32) / 65535
nou = (a_new - a_old) > 0.3; lab, n = ndi.label(nou); comps = []
for k in range(1, n + 1):
    ys, xs = np.nonzero(lab == k)
    if xs.size < 5: continue
    X, Y = xs + BX[0], ys + BX[1]; d = np.hypot(X - cx, Y - cy) - R; az = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360
    comps.append(dict(px=int(xs.size), caixa=[int(X.min()), int(Y.min()), int(X.max()), int(Y.max())], azimut=[round(float(az.min()), 1), round(float(np.median(az)), 1), round(float(az.max()), 1)],
                      d_limbe_px=[round(float(d.min()), 1), round(float(np.median(d)), 1), round(float(d.max()), 1)], rgb_mitja=[int(v) for v in (rgb[ys, xs].mean(0) * 255)]))
er = (S.channel_box(267, -1, BX).astype(np.float32) - P.channel_box(267, -1, BX).astype(np.float32)) / 65535     # el que Pere ha esborrat de la 267
ys, xs = np.nonzero(er > 0.02); X, Y = xs + BX[0], ys + BX[1]
esb = dict(px=int(xs.size), caixa=[int(X.min()), int(Y.min()), int(X.max()), int(Y.max())] if xs.size else None,
           azimut=[round(float(v), 1) for v in np.percentile((np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360, [0, 50, 100])] if xs.size else None,
           d_limbe_px=[round(float(v), 1) for v in np.percentile(np.hypot(X - cx, Y - cy) - R, [0, 50, 100])] if xs.size else None, alfa_esborrada_max=round(float(er.max()), 3))
rep = dict(marques_noves=comps, esborrat_de_la_267=esb); print(json.dumps(rep, ensure_ascii=False))
(SORT / 'C4_MARQUES_GRISES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
C91 = P.composite()[BX[1]:BX[3], BX[0]:BX[2], :3]; C90 = V0.composite()[BX[1]:BX[3], BX[0]:BX[2], :3]
np.save(SORT / 'compost_V91_pere_0014_protuberancia.npy', C91)
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
F76 = np.stack([P.channel_box(76, c, BX) for c in range(3)], -1).astype(np.float32) / 65535
E = np.stack([S.channel_box(267, c, BX) for c in range(3)], -1).astype(np.float32) / 65535; aE = S.channel_box(267, -1, BX).astype(np.float32)[..., None] / 65535
aP = P.channel_box(267, -1, BX).astype(np.float32)[..., None] / 65535
c91 = np.asarray(im(C91.astype(np.float32) / 65535)).copy(); vora = cv2.dilate(nou.astype(np.uint8), np.ones((3, 3), np.uint8)) & ~nou.astype(np.uint8); c91[vora > 0] = (0, 255, 255)
pan = [('V91 (00:14) amb la marca', Image.fromarray(c91)), ('V91 (00:14)', im(C91.astype(np.float32) / 65535)), ('V90 (22:06)', im(C90.astype(np.float32) / 65535)),
       ('foto 76 sola', im(F76)), ('267 que vaig posar (×4)', im(np.clip(4 * E * aE, 0, 1))), ('267 com la tens (×4)', im(np.clip(4 * E * aP, 0, 1)))]
ys_, xs_ = np.nonzero(nou | (er > 0.02)); gx, gy = (int(xs_.mean()), int(ys_.mean())) if xs_.size else (w // 2, h // 2)
ww, hh, z = 100, 140, 5; x0 = int(np.clip(gx - ww / 2, 0, w - ww)); y0 = int(np.clip(gy - hh / 2, 0, h - hh))
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 16)
Sh = Image.new('RGB', (len(pan) * (ww * z + 8), hh * z + 30), 'white'); dr = ImageDraw.Draw(Sh)
for i, (et, img) in enumerate(pan):
    Sh.paste(img.crop((x0, y0, x0 + ww, y0 + hh)).resize((ww * z, hh * z), Image.LANCZOS), (i * (ww * z + 8), 28)); dr.text((i * (ww * z + 8) + 4, 6), et + ' · 5:1', fill='black', font=F)
Sh.save(SORT / 'LAMINA_C4_marques_grises.png'); print('caixa de la làmina', (BX[0] + x0, BX[1] + y0, BX[0] + x0 + ww, BX[1] + y0 + hh))
