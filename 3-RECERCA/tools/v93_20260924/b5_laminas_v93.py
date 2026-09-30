"""b5 · Làmines de la V93 amb el compost de Photoshop: la V92 de Pere (render natiu de la seva V92 amb la capa de marques amagada, c3) contra la V93
(imatge fusionada del desament natiu). 1) marques grises (mirall) a 6:1; 2) marques verdes i línies de la V88 a 6:1; 3) la Lluna sense l'Earthshine
(restes de màscares); 4) les línies marrons: perfils perpendiculars (compost, sense filtres i base lineal ×100); 5) la Lluna a 2:3.
Sortida: LAMINA_V93_1..5 i B5_LAMINES.json."""
from v93_comu import *
from psb69 import PSB
import cv2, tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); B = (4600, 3000, 6150, 4550); cx, cy, R = GEO['cx'] - B[0], GEO['cy'] - B[1], GEO['R']
V92 = tifffile.imread(SORT / 'renders/V0_tal_com_esta_lluna.tif')[..., :3]; C93 = PSB(str(ARREL / '1-PHOTOSHOP/V93.psb')).composite()[..., :3]; V93 = C93[B[1]:B[3], B[0]:B[2]].copy(); del C93
D = np.abs(V93.astype(np.int32) - V92.astype(np.int32)).max(-1); yy, xx = np.mgrid[:D.shape[0], :D.shape[1]]; dd = np.hypot(xx - cx, yy - cy) - R
rep = {f'dif_mes_de_{t}_DN16': dict(px=int((D > t).sum()), d_min=round(float(dd[D > t].min()), 1) if (D > t).any() else None, d_max=round(float(dd[D > t].max()), 1) if (D > t).any() else None) for t in (64, 256)}
rep['dif_max_a_mes_de_20_px'] = int(D[dd > 20].max()); rep['dif_max_dins_de_la_Lluna_d_menys_8'] = int(D[dd < -8].max()); log(json.dumps(rep))
icc = tifffile.TiffFile(SORT / 'vistes/V93_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im = lambda a: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
cols = [(V92, 'V92 (la teva)'), (V93, 'V93')]
def lamina(nom, titol, files, w=64, zf=6):
    S = Image.new('RGB', (2 * (w * zf + 8), 44 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm, et) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t), cy - (R + dm) * np.sin(t); x0, y0 = int(px - w / 2), int(py - w / 2); Y = 44 + j * (w * zf + 24)
        for i, (arr, en) in enumerate(cols): S.paste(im(arr[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y + 20)); d.text((i * (w * zf + 8) + 3, Y + 2), f'{en} · {az:.0f}° · {et}', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_V93_1_mirall.png', 'Marques grises (el mirall de la V92): V92 contra V93, compost de Photoshop, 6:1', [(88, 4, 'gris'), (246, 6, 'gris'), (270, 4, 'gris'), (287, 4, 'gris'), (300, 4, 'gris')])
lamina('LAMINA_V93_2_textura_i_linies.png', 'Marques verdes (textura) i línies de la V88 (no han de tornar): V92 contra V93, compost de Photoshop, 6:1',
       [(200, 8, 'verd'), (219, 6, 'verd'), (211, 5, 'línia V88'), (223, 7, 'línia V88'), (136, 6, 'línia V88'), (112, 5, 'línia V88')])
A = tifffile.imread(SORT / 'renders/V7_sense_earthshine_lluna.tif')[..., :3]; Bn = tifffile.imread(SORT / 'vistes/V93_lluna_sense_earthshine.tif')[..., :3]
k = 900; S3 = Image.new('RGB', (2 * (k + 8), k + 36), 'white'); d3 = ImageDraw.Draw(S3)
for i, (arr, et) in enumerate([(A, 'V92 amb la Earthshine amagada'), (Bn, 'V93 amb la Earthshine amagada')]): S3.paste(im(arr).resize((k, k), Image.LANCZOS), (i * (k + 8), 34)); d3.text((i * (k + 8) + 4, 8), et, fill='black', font=FB)
S3.save(SORT / 'LAMINA_V93_3_zona_earthshine.png')
P = json.loads((SORT / 'C5_PERFILS.json').read_text()); T = np.array(P['T_px']); Wp, Hp = 520, 300; S4 = Image.new('RGB', (3 * Wp, 2 * Hp + 40), 'white'); d4 = ImageDraw.Draw(S4)
d4.text((6, 8), "Línies marrons: perfil perpendicular a cada traç (relatiu), compost de Photoshop (vermell), sense filtres (gris) i base lineal ×100 (blau)", fill='black', font=FB)
bG = {}
for i, tr in enumerate(P['tracos']):
    ox, oy = (i % 3) * Wp, 40 + (i // 3) * Hp; pr = tr['perfils']
    for nm, col, fac in (('V0_tal_com_esta', (220, 40, 40), 1), ('V6_sense_filtres', (120, 120, 120), 1)):
        y = np.array(pr[nm], float); y = (y / np.nanmean(y) - 1) * fac; pts = [(ox + 20 + (tt + 400) / 800 * (Wp - 40), oy + Hp / 2 - v * Hp * 6) for tt, v in zip(T, y)]; d4.line(pts, fill=col, width=2)
    d4.line([(ox + 20 + (Wp - 40) / 2, oy + 20), (ox + 20 + (Wp - 40) / 2, oy + Hp - 20)], fill=(200, 200, 200)); d4.text((ox + 24, oy + 4), f"traç {i}: centre {tr['info']['centre']}", fill='black', font=F)
S4.save(SORT / 'LAMINA_V93_4_linies_marrons.png')
k = 1024; S5 = Image.new('RGB', (2 * (k + 8), k + 36), 'white'); d5 = ImageDraw.Draw(S5)
for i, (arr, et) in enumerate(cols): S5.paste(im(arr).resize((k, k), Image.LANCZOS), (i * (k + 8), 34)); d5.text((i * (k + 8) + 4, 8), 'Lluna 2:3 · ' + et, fill='black', font=FB)
S5.save(SORT / 'LAMINA_V93_5_lluna.png'); desa_json('B5_LAMINES.json', rep); log('fet')
